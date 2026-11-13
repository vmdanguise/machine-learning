"""Preprocesamiento del EEG y extracción de características espectrales.

Para cada ventana de VENTANA_S segundos y cada canal se estima la densidad
espectral de potencia con el método de Welch (segmentos de 1 s, ventana de
Hann, 50 % de solapamiento) y se calculan:

  - log-potencia absoluta por banda (delta, theta, alfa, beta, gamma)
  - potencia relativa por banda (suma 1: es un punto del simplex)
  - entropía espectral normalizada  H(p) / log N  en [0, 1]
  - frecuencia dominante y frecuencia de borde espectral al 90 %
  - line length y log-varianza (dominio del tiempo, como referencia)

Además, por ventana, la coherencia media entre todos los pares de canales
en cada banda (medida de sincronización).
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import signal
from tqdm import tqdm

from .anotaciones import leer_resumen
from .config import (BANDAS, CANALES, CASOS, DIR_CRUDOS, DIR_PROCESADOS, FILTRO_PASABANDA,
                     FRECUENCIA_RED, FS, SUJETO_POR_CASO, VENTANA_S)
from .edf import leer_edf

SEG_WELCH_S = 1.0
EPS = 1e-12


def filtrar(x, fs=FS):
    sos = signal.butter(4, FILTRO_PASABANDA, btype="bandpass", fs=fs, output="sos")
    b, a = signal.iirnotch(FRECUENCIA_RED, Q=30, fs=fs)
    y = signal.sosfiltfilt(sos, x, axis=-1)
    y = signal.filtfilt(b, a, y, axis=-1)
    return y.astype(np.float32)


def ventanear(x, fs=FS, ventana_s=VENTANA_S):
    n = int(ventana_s * fs)
    w = x.shape[-1] // n
    return x[:, : w * n].reshape(x.shape[0], w, n).transpose(1, 0, 2)  # (ventanas, canales, muestras)


def espectros_segmentos(v, fs=FS, seg_s=SEG_WELCH_S):
    """FFT de los segmentos de Welch: devuelve (frecuencias, X) con X de forma (V, C, S, F)."""
    nseg = int(seg_s * fs)
    paso = nseg // 2
    starts = range(0, v.shape[-1] - nseg + 1, paso)
    segs = np.stack([v[..., s: s + nseg] for s in starts], axis=2)
    segs = segs - segs.mean(axis=-1, keepdims=True)
    hann = signal.windows.hann(nseg, sym=False).astype(np.float32)
    X = np.fft.rfft(segs * hann, axis=-1)
    f = np.fft.rfftfreq(nseg, 1 / fs)
    escala = 1.0 / (fs * (hann ** 2).sum())
    return f, X, escala


def psd_welch(X, escala):
    P = (np.abs(X) ** 2).mean(axis=2) * escala  # (V, C, F)
    P[..., 1:-1] *= 2  # espectro unilateral
    return P


def caracteristicas_espectrales(P, f):
    lo, hi = FILTRO_PASABANDA
    mascara = (f >= lo) & (f <= hi)
    Pm, fm = P[..., mascara], f[mascara]

    pot_bandas = np.stack([P[..., (f >= a) & (f < b)].sum(-1) for a, b in BANDAS.values()], axis=-1)
    total = pot_bandas.sum(-1, keepdims=True) + EPS
    relativa = pot_bandas / total

    p = Pm / (Pm.sum(-1, keepdims=True) + EPS)
    entropia = -(p * np.log(p + EPS)).sum(-1) / np.log(p.shape[-1])

    f_pico = fm[Pm.argmax(-1)]
    acumulada = np.cumsum(p, axis=-1)
    f_borde90 = fm[(acumulada < 0.9).sum(-1).clip(max=len(fm) - 1)]

    return {
        "logpot": np.log10(pot_bandas + EPS),
        "rel": relativa,
        "entropia": entropia[..., None],
        "fpico": f_pico[..., None],
        "fborde90": f_borde90[..., None],
    }


def coherencia_media(X, f):
    """Coherencia magnitud-cuadrado media sobre todos los pares de canales, por banda."""
    Sxy = np.einsum("vasf,vbsf->vabf", X, np.conj(X)) / X.shape[2]
    Sxx = np.real(np.einsum("vaaf->vaf", Sxy))
    coh = np.abs(Sxy) ** 2 / (Sxx[:, :, None, :] * Sxx[:, None, :, :] + EPS)
    iu = np.triu_indices(X.shape[1], k=1)
    coh_pares = coh[:, iu[0], iu[1], :]  # (V, pares, F)
    return np.stack([coh_pares[..., (f >= a) & (f < b)].mean(axis=(-1, -2)) for a, b in BANDAS.values()], -1)


def nombres_columnas():
    cols = []
    for canal in CANALES:
        cols += [f"{canal}|logpot_{b}" for b in BANDAS]
        cols += [f"{canal}|rel_{b}" for b in BANDAS]
        cols += [f"{canal}|{n}" for n in ("entropia", "fpico", "fborde90", "line_length", "logvar")]
    cols += [f"coh_{b}" for b in BANDAS]
    return cols


def extraer_ventanas(v, fs=FS, lote=128):
    filas = []
    for i in range(0, len(v), lote):
        vb = v[i: i + lote]
        f, X, escala = espectros_segmentos(vb, fs)
        P = psd_welch(X, escala)
        c = caracteristicas_espectrales(P, f)
        line_length = np.abs(np.diff(vb, axis=-1)).mean(-1, keepdims=True)
        logvar = np.log10(vb.var(-1) + EPS)[..., None]
        por_canal = np.concatenate([c["logpot"], c["rel"], c["entropia"], c["fpico"], c["fborde90"],
                                    line_length, logvar], axis=-1)
        filas.append(np.concatenate([por_canal.reshape(len(vb), -1), coherencia_media(X, f)], axis=1))
    return np.concatenate(filas).astype(np.float32)


def etiquetar(n_ventanas, crisis, ventana_s=VENTANA_S):
    """Fracción de cada ventana que cae dentro de una crisis anotada."""
    inicio = np.arange(n_ventanas) * ventana_s
    fin = inicio + ventana_s
    frac = np.zeros(n_ventanas, np.float32)
    for a, b in crisis:
        frac += np.clip(np.minimum(fin, b) - np.maximum(inicio, a), 0, None) / ventana_s
    return frac.clip(0, 1)


def procesar_archivo(ruta_edf, crisis):
    x, fs, _ = leer_edf(ruta_edf, CANALES)
    if x is None:
        return None
    if fs != FS:
        raise ValueError(f"{ruta_edf}: fs={fs}, se esperaba {FS}")
    v = ventanear(filtrar(x, fs), fs)
    return extraer_ventanas(v, fs), etiquetar(len(v), crisis)


def procesar_todo(dir_crudos=DIR_CRUDOS, dir_salida=DIR_PROCESADOS, casos=CASOS):
    dir_salida = Path(dir_salida)
    (dir_salida / "por_archivo").mkdir(parents=True, exist_ok=True)
    pendientes = []
    for caso in casos:
        resumen = Path(dir_crudos) / caso / f"{caso}-summary.txt"
        if not resumen.exists():
            continue
        for r in leer_resumen(resumen):
            ruta = Path(dir_crudos) / caso / r["archivo"]
            if ruta.exists():
                pendientes.append((caso, r, ruta))

    descartados = []
    for caso, r, ruta in tqdm(pendientes, desc="Características", unit="arch"):
        salida = dir_salida / "por_archivo" / f"{ruta.stem}.npz"
        if salida.exists():
            continue
        res = procesar_archivo(ruta, r["crisis"])
        if res is None:
            descartados.append(r["archivo"])
            continue
        X, frac = res
        np.savez_compressed(salida, X=X, frac=frac)
    if descartados:
        print(f"Descartados por no tener los {len(CANALES)} canales: {', '.join(descartados)}")
    return consolidar(dir_salida, pendientes)


def consolidar(dir_salida, pendientes):
    X, meta = [], []
    for caso, r, ruta in pendientes:
        archivo = Path(dir_salida) / "por_archivo" / f"{ruta.stem}.npz"
        if not archivo.exists():
            continue
        d = np.load(archivo)
        X.append(d["X"])
        meta.append(pd.DataFrame({
            "caso": caso,
            "sujeto": SUJETO_POR_CASO[caso],
            "archivo": r["archivo"],
            "inicio_s": np.arange(len(d["frac"])) * VENTANA_S,
            "frac_crisis": d["frac"],
        }))
    X = np.concatenate(X)
    meta = pd.concat(meta, ignore_index=True)
    meta["y"] = (meta.frac_crisis >= 0.5).astype(np.int8)
    np.save(Path(dir_salida) / "X.npy", X)
    meta.to_csv(Path(dir_salida) / "meta.csv.gz", index=False)
    pd.Series(nombres_columnas()).to_csv(Path(dir_salida) / "columnas.csv", index=False, header=False)
    print(f"X: {X.shape}  |  ventanas con crisis: {meta.y.sum()} ({100 * meta.y.mean():.2f} %)")
    return X, meta


def cargar(dir_procesados=DIR_PROCESADOS):
    d = Path(dir_procesados)
    X = np.load(d / "X.npy")
    meta = pd.read_csv(d / "meta.csv.gz")
    cols = pd.read_csv(d / "columnas.csv", header=None)[0].tolist()
    return X, meta, cols


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--casos", nargs="+", default=CASOS)
    a = p.parse_args()
    procesar_todo(casos=a.casos)

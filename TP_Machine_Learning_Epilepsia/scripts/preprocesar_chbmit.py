"""Preprocesa CHB-MIT: anotaciones, filtrado, ventanas de 4 s, STFT y potencia por bandas.

Uso:
    python preprocesar_chbmit.py DATOS_CHBMIT SALIDA [n_procesos]

Por cada EDF genera SALIDA/<archivo>.npz con:
    stft  (n, 18, 40, 7) float16   log10 de la densidad espectral, 1..40 Hz, 7 cuadros de 0,5 s
    bp    (n, 18, 5)     float32   log10 de la potencia por banda (delta, theta, alfa, beta, gamma)
    t0    (n,)           float32   inicio de la ventana en segundos
    ictal (n,)           int8      1 si la ventana está entera dentro de una crisis
    borde (n,)           int8      1 si la ventana toca una crisis solo en parte
    maxabs(n,)           float32   amplitud máxima absoluta (µV), para detectar artefactos
y además SALIDA/crisis.csv y SALIDA/indice.csv.
Si el npz ya existe no se recalcula.
"""
import re
import sys
import warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import signal

FS = 256
VENTANA_S = 4
N_VENT = FS * VENTANA_S
NPERSEG, NOVERLAP = 256, 128
# Montaje bipolar "doble banana" de 18 canales; el canal 23 repite T8-P8 y se descarta.
CANALES = ["FP1-F7", "F7-T7", "T7-P7", "P7-O1", "FP1-F3", "F3-C3", "C3-P3", "P3-O1",
           "FP2-F4", "F4-C4", "C4-P4", "P4-O2", "FP2-F8", "F8-T8", "T8-P8-0", "P8-O2",
           "FZ-CZ", "CZ-PZ"]
BANDAS = {"delta": (0.5, 4), "theta": (4, 8), "alfa": (8, 13), "beta": (13, 30), "gamma": (30, 40.5)}
SOS = signal.butter(4, [0.5, 40], btype="band", fs=FS, output="sos")


def leer_crisis(dir_datos, pacientes):
    filas = []
    for p in pacientes:
        texto = (dir_datos / p / f"{p}-summary.txt").read_text(errors="replace")
        for bloque in re.split(r"\n(?=File Name:)", texto):
            m = re.search(r"File Name:\s*(\S+)", bloque)
            if not m:
                continue
            inicios = [int(x) for x in re.findall(r"Seizure\s*\d*\s*Start Time:\s*(\d+)", bloque)]
            fines = [int(x) for x in re.findall(r"Seizure\s*\d*\s*End Time:\s*(\d+)", bloque)]
            n_decl = re.search(r"Number of Seizures in File:\s*(\d+)", bloque)
            assert len(inicios) == len(fines) == (int(n_decl.group(1)) if n_decl else 0), m.group(1)
            for a, b in zip(inicios, fines):
                filas.append({"paciente": p, "archivo": m.group(1), "inicio_s": a, "fin_s": b, "duracion_s": b - a})
    return pd.DataFrame(filas)


def procesar(args):
    edf, salida, crisis = args
    destino = salida / (edf.stem + ".npz")
    if destino.exists():
        return edf.name, "ya estaba"
    import mne
    warnings.filterwarnings("ignore")
    mne.set_log_level("ERROR")
    raw = mne.io.read_raw_edf(edf, preload=True, verbose="ERROR").pick(CANALES)
    assert raw.ch_names == CANALES and raw.info["sfreq"] == FS, edf.name
    x = raw.get_data() * 1e6  # V -> µV
    x = signal.sosfiltfilt(SOS, x, axis=-1)

    n = x.shape[1] // N_VENT
    v = x[:, : n * N_VENT].reshape(len(CANALES), n, N_VENT).transpose(1, 0, 2)  # (n, 18, 1024)
    f, _, S = signal.spectrogram(v, fs=FS, window="hann", nperseg=NPERSEG, noverlap=NOVERLAP,
                                 scaling="density", axis=-1)  # (n, 18, 129, 7)
    sel = (f >= 1) & (f <= 40)
    stft = np.log10(S[:, :, sel, :] + 1e-6).astype(np.float16)

    psd = S.mean(axis=-1)  # Welch: promedio de los cuadros
    bp = np.stack([np.trapezoid(psd[..., (f >= lo) & (f < hi)], f[(f >= lo) & (f < hi)], axis=-1)
                   for lo, hi in BANDAS.values()], axis=-1)
    bp = np.log10(bp + 1e-6).astype(np.float32)

    t0 = np.arange(n, dtype=np.float32) * VENTANA_S
    t1 = t0 + VENTANA_S
    ictal = np.zeros(n, np.int8)
    borde = np.zeros(n, np.int8)
    for a, b in crisis:
        dentro = (t0 >= a) & (t1 <= b)
        toca = (t1 > a) & (t0 < b)
        ictal |= dentro
        borde |= toca & ~dentro
    np.savez_compressed(destino, stft=stft, bp=bp, t0=t0, ictal=ictal, borde=borde,
                        maxabs=np.abs(v).max(axis=(1, 2)).astype(np.float32))
    return edf.name, f"{n} ventanas, {int(ictal.sum())} ictales"


def main():
    datos, salida = Path(sys.argv[1]), Path(sys.argv[2])
    procesos = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    salida.mkdir(parents=True, exist_ok=True)
    pacientes = sorted(p.name for p in datos.glob("chb*") if p.is_dir())
    crisis = leer_crisis(datos, pacientes)
    crisis.to_csv(salida / "crisis.csv", index=False)
    print(f"{len(crisis)} crisis en {len(pacientes)} pacientes", flush=True)

    tareas = []
    for p in pacientes:
        for edf in sorted((datos / p).glob("*.edf")):
            c = crisis[crisis.archivo == edf.name][["inicio_s", "fin_s"]].to_numpy()
            tareas.append((edf, salida, [tuple(r) for r in c]))
    with ProcessPoolExecutor(procesos) as ex:
        for nombre, msg in ex.map(procesar, tareas):
            print(nombre, msg, flush=True)

    filas = []
    for edf, _, _ in tareas:
        z = np.load(salida / (edf.stem + ".npz"))
        filas.append({"paciente": edf.parent.name, "archivo": edf.name, "ventanas": len(z["t0"]),
                      "horas": len(z["t0"]) * VENTANA_S / 3600, "ictales": int(z["ictal"].sum()),
                      "borde": int(z["borde"].sum())})
    pd.DataFrame(filas).to_csv(salida / "indice.csv", index=False)
    print("listo", flush=True)


if __name__ == "__main__":
    main()

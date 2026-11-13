"""Métricas de detección de crisis por ventana y por evento, y umbral de Neyman-Pearson.

Se usa en las etapas de modelos clásicos y de la CNN. Supone que las ventanas de cada
registro están contiguas y ordenadas por tiempo dentro de los arreglos.
"""
import numpy as np
import pandas as pd


def suavizar(score, archivo, k=3):
    """Media móvil causal de las últimas k ventanas, sin cruzar de un registro a otro."""
    score = np.asarray(score, dtype=float)
    out = np.empty_like(score)
    for a in pd.unique(archivo):
        idx = np.where(archivo == a)[0]
        c = np.concatenate([[0.0], np.cumsum(score[idx])])
        fin = np.arange(1, len(idx) + 1)
        ini = np.maximum(fin - k, 0)
        out[idx] = (c[fin] - c[ini]) / (fin - ini)
    return out


def umbral_neyman_pearson(score_negativos, alfa):
    """Umbral tau que maximiza la sensibilidad con P(score > tau | sin crisis) <= alfa.

    La sensibilidad es no creciente en tau, así que el óptimo es el menor tau que cumple la
    restricción: el cuantil (1 - alfa) de los scores de la clase negativa.
    """
    return float(np.quantile(score_negativos, 1 - alfa, method="higher"))


def metricas_ventana(y, pred):
    y = np.asarray(y).astype(bool)
    pred = np.asarray(pred).astype(bool)
    tp = int((y & pred).sum()); fn = int((y & ~pred).sum())
    fp = int((~y & pred).sum()); tn = int((~y & ~pred).sum())
    sens = tp / max(tp + fn, 1)
    espec = tn / max(tn + fp, 1)
    vpp = tp / max(tp + fp, 1)
    f1 = 2 * vpp * sens / max(vpp + sens, 1e-12)
    return {"TP": tp, "FN": fn, "FP": fp, "TN": tn, "sensibilidad": sens, "especificidad": espec,
            "VPP": vpp, "F1": f1}


def evaluar_eventos(archivo, t0, pred, crisis, ventana=4.0):
    """Evaluación por evento.

    - Una crisis está detectada si alguna ventana positiva se superpone con [inicio, fin].
    - Una alarma es una racha de ventanas positivas consecutivas; es falsa si no se superpone
      con ninguna crisis. Falsas alarmas por hora = alarmas falsas / horas fuera de crisis.
    - Latencia = fin de la primera ventana positiva - inicio de la crisis (la decisión recién
      se puede tomar cuando termina la ventana).
    """
    pred = np.asarray(pred).astype(bool)
    filas, falsas, horas = [], 0, 0.0
    for a in pd.unique(archivo):
        m = archivo == a
        t, p = t0[m], pred[m]
        cr = crisis.loc[crisis.archivo == a, ["inicio_s", "fin_s"]].to_numpy()
        cambio = np.diff(np.concatenate([[0], p.astype(int), [0]]))
        for i, f in zip(np.where(cambio == 1)[0], np.where(cambio == -1)[0]):
            a0, a1 = t[i], t[f - 1] + ventana
            if not any(a1 > c0 and a0 < c1 for c0, c1 in cr):
                falsas += 1
        en_crisis = np.zeros(len(t), bool)
        for c0, c1 in cr:
            toca = (t + ventana > c0) & (t < c1)
            en_crisis |= toca
            pos = toca & p
            filas.append({"archivo": a, "inicio_s": c0, "fin_s": c1, "detectada": bool(pos.any()),
                          "latencia_s": float(t[pos][0] + ventana - c0) if pos.any() else np.nan})
        horas += (~en_crisis).sum() * ventana / 3600
    det = pd.DataFrame(filas, columns=["archivo", "inicio_s", "fin_s", "detectada", "latencia_s"])
    n = len(det)
    return {"crisis": n, "detectadas": int(det.detectada.sum()),
            "sens_eventos": det.detectada.mean() if n else np.nan,
            "falsas_alarmas": falsas, "horas_sin_crisis": horas, "FA_por_hora": falsas / horas if horas else np.nan,
            "latencia_mediana_s": det.latencia_s.median() if n else np.nan}, det

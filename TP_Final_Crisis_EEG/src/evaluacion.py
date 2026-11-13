"""Métricas de evaluación y elección del umbral de decisión."""

import numpy as np
from sklearn.metrics import average_precision_score, confusion_matrix, roc_auc_score, roc_curve

from .config import VENTANA_S


def matriz_confusion(y, score, umbral):
    tn, fp, fn, tp = confusion_matrix(y, (score >= umbral).astype(int), labels=[0, 1]).ravel()
    return tn, fp, fn, tp


def metricas(y, score, umbral, ventana_s=VENTANA_S):
    tn, fp, fn, tp = matriz_confusion(y, score, umbral)
    horas_normales = (tn + fp) * ventana_s / 3600
    sens = tp / (tp + fn) if tp + fn else np.nan
    espec = tn / (tn + fp) if tn + fp else np.nan
    ppv = tp / (tp + fp) if tp + fp else np.nan
    return {
        "umbral": float(umbral),
        "TP": int(tp), "FP": int(fp), "TN": int(tn), "FN": int(fn),
        "sensibilidad": sens,
        "especificidad": espec,
        "VPP": ppv,
        "F1": 2 * ppv * sens / (ppv + sens) if ppv and sens else 0.0,
        "falsas_alarmas_h": fp / horas_normales if horas_normales else np.nan,
        "AUC": roc_auc_score(y, score),
        "AP": average_precision_score(y, score),
    }


def umbral_youden(y, score):
    """Maximiza J = sensibilidad + especificidad - 1 (sin restricciones)."""
    fpr, tpr, umbrales = roc_curve(y, score)
    i = np.argmax(tpr - fpr)
    return float(umbrales[i])


def envolvente_concava(fpr, tpr):
    """Envolvente cóncava superior (ROC convex hull) de los puntos de la curva ROC."""
    puntos = sorted(set(zip(fpr, tpr)))
    casco = []
    for p in puntos:
        while len(casco) >= 2:
            (x1, y1), (x2, y2) = casco[-2], casco[-1]
            if (x2 - x1) * (p[1] - y1) - (y2 - y1) * (p[0] - x1) >= 0:
                casco.pop()
            else:
                break
        casco.append(p)
    return np.array(casco)


def umbral_neyman_pearson(y, score, alfa):
    """Máxima sensibilidad sujeta a FPR <= alfa.

    Problema:  max_t TPR(t)  s.a.  FPR(t) <= alfa.
    Lagrangiano: L(t, λ) = TPR(t) - λ (FPR(t) - alfa), con λ >= 0.
    Si la restricción está activa, en el óptimo dTPR/dFPR = λ: el
    multiplicador es la pendiente de la ROC en el punto elegido, y por el
    lema de Neyman-Pearson coincide con el umbral sobre el cociente de
    verosimilitudes p(s|crisis)/p(s|normal). λ se estima como la pendiente
    de la envolvente cóncava de la ROC a la izquierda de alfa.
    """
    fpr, tpr, umbrales = roc_curve(y, score)
    validos = np.flatnonzero(fpr <= alfa)
    i = validos[np.argmax(tpr[validos])]

    casco = envolvente_concava(fpr, tpr)
    j = np.clip(np.searchsorted(casco[:, 0], min(fpr[i], alfa), side="right"), 1, len(casco) - 1)
    dx = casco[j, 0] - casco[j - 1, 0]
    lam = (casco[j, 1] - casco[j - 1, 1]) / dx if dx > 0 else np.inf
    return {"umbral": float(umbrales[i]), "fpr": float(fpr[i]), "tpr": float(tpr[i]), "lambda": float(lam)}


def alfa_por_falsas_alarmas(fa_por_hora, ventana_s=VENTANA_S):
    """Convierte 'falsas alarmas por hora' en FPR máximo por ventana."""
    return fa_por_hora * ventana_s / 3600

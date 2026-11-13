"""Partición por sujeto y experimentos (reanudables) de optimizadores y activaciones.

Cada corrida se guarda como una línea JSON en resultados/<experimento>.jsonl;
si se corta (o se cierra Colab) basta con volver a ejecutar: se saltean las
corridas ya hechas.

Uso:
    python -m src.experimentos lr          # ajuste de tasa de aprendizaje
    python -m src.experimentos grilla      # optimizador x activación x semilla
    python -m src.experimentos profundidad # profundidad x activación
"""

import argparse
import json
from itertools import product
from pathlib import Path

import numpy as np
import torch
from sklearn.preprocessing import StandardScaler

from .caracteristicas import cargar
from .config import DIR_PROCESADOS, DIR_RESULTADOS, SEMILLA
from .evaluacion import alfa_por_falsas_alarmas, metricas, umbral_neyman_pearson, umbral_youden
from .modelos import ACTIVACIONES, GRILLA_LR, MLP, OPTIMIZADORES, entrenar, predecir

OPTS_GRILLA = list(OPTIMIZADORES)
ACTS_GRILLA = list(ACTIVACIONES)
SEMILLAS = [0, 1, 2, 3, 4]
FA_POR_HORA = 1.0


def particion_por_sujeto(meta, n_val=4, n_test=5, semilla=SEMILLA):
    """Asigna sujetos completos a train/val/test (todos los conjuntos con crisis)."""
    sujetos = sorted(meta.loc[meta.y == 1, "sujeto"].unique())
    rng = np.random.default_rng(semilla)
    rng.shuffle(sujetos)
    test, val = sujetos[:n_test], sujetos[n_test:n_test + n_val]
    return {"train": sorted(set(meta.sujeto) - set(test) - set(val)), "val": sorted(val), "test": sorted(test)}


def preparar_datos(dir_procesados=DIR_PROCESADOS, semilla=SEMILLA):
    X, meta, cols = cargar(dir_procesados)
    part = particion_por_sujeto(meta, semilla=semilla)
    idx = {k: np.flatnonzero(meta.sujeto.isin(v)) for k, v in part.items()}
    escalador = StandardScaler().fit(X[idx["train"]])
    t = lambda a: torch.from_numpy(np.ascontiguousarray(a, dtype=np.float32))
    datos = {"particion": part, "columnas": cols, "meta": meta, "escalador": escalador, "idx": idx}
    for k, nombre in (("train", "tr"), ("val", "va"), ("test", "te")):
        datos["X" + nombre] = t(escalador.transform(X[idx[k]]))
        datos["y" + nombre] = t(meta.y.values[idx[k]])
    return datos


def evaluar(modelo, datos):
    p_va, p_te = predecir(modelo, datos["Xva"]), predecir(modelo, datos["Xte"])
    y_va, y_te = datos["yva"].numpy(), datos["yte"].numpy()
    if not (np.isfinite(p_va).all() and np.isfinite(p_te).all()):
        return {"divergio": True}
    np_ = umbral_neyman_pearson(y_va, p_va, alfa_por_falsas_alarmas(FA_POR_HORA))
    res = {"divergio": False, "lambda_np": np_["lambda"]}
    for nombre, umbral in (("youden", umbral_youden(y_va, p_va)), ("np", np_["umbral"])):
        for k, v in metricas(y_te, p_te, umbral).items():
            res[f"test_{nombre}_{k}"] = v
    return res


def _hechas(ruta):
    if not ruta.exists():
        return set()
    return {json.loads(l)["clave"] for l in ruta.read_text().splitlines() if l.strip()}


def _guardar(ruta, fila):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "a", encoding="utf-8") as f:
        f.write(json.dumps(fila, default=float) + "\n")


def correr(nombre, configuraciones, datos, epocas=40, dir_resultados=DIR_RESULTADOS):
    ruta = Path(dir_resultados) / f"{nombre}.jsonl"
    hechas = _hechas(ruta)
    pendientes = [c for c in configuraciones if c["clave"] not in hechas]
    print(f"{nombre}: {len(hechas)} hechas, {len(pendientes)} pendientes")
    for i, c in enumerate(pendientes, 1):
        torch.manual_seed(c["semilla"])
        modelo = MLP(datos["Xtr"].shape[1], c["ocultas"], c["activacion"], c.get("dropout", 0.2))
        hist = entrenar(modelo, c["optimizador"], c["lr"], datos, epocas=epocas, semilla=c["semilla"],
                        registrar_gradientes=c.get("gradientes", False))
        fila = {**c, **evaluar(modelo, datos), "historial": hist,
                "inactivas": modelo.unidades_inactivas(datos["Xva"][:4096])}
        _guardar(ruta, fila)
        print(f"[{i}/{len(pendientes)}] {c['clave']}  AUC val={hist['mejor_auc_va']:.4f}  "
              f"AUC test={fila.get('test_np_AUC', float('nan')):.4f}  ({hist['tiempo'][-1]:.0f} s)")


def leer_resultados(nombre, dir_resultados=DIR_RESULTADOS):
    import pandas as pd
    ruta = Path(dir_resultados) / f"{nombre}.jsonl"
    return pd.DataFrame([json.loads(l) for l in ruta.read_text().splitlines() if l.strip()])


def mejores_lr(dir_resultados=DIR_RESULTADOS):
    df = leer_resultados("ajuste_lr", dir_resultados)
    df["auc"] = df.historial.map(lambda h: h["mejor_auc_va"])
    return df.loc[df.groupby("optimizador").auc.idxmax()].set_index("optimizador").lr.to_dict()


def configs_lr():
    return [{"clave": f"{o}|relu|lr={lr}", "optimizador": o, "activacion": "relu", "lr": lr,
             "semilla": 0, "ocultas": [128, 64]} for o, lrs in GRILLA_LR.items() for lr in lrs]


def configs_grilla(lrs):
    return [{"clave": f"{o}|{a}|s{s}", "optimizador": o, "activacion": a, "lr": lrs[o],
             "semilla": s, "ocultas": [128, 64]} for o, a, s in product(OPTS_GRILLA, ACTS_GRILLA, SEMILLAS)]


def configs_logistica(lrs):
    """Regresión logística (sin capas ocultas): caso convexo, para contrastar la variabilidad entre semillas."""
    return [{"clave": f"{o}|logistica|s{s}", "optimizador": o, "activacion": "relu", "lr": lrs[o],
             "semilla": s, "ocultas": [], "dropout": 0.0} for o, s in product(OPTS_GRILLA, SEMILLAS)]


def configs_profundidad(lr=1e-2, profundidades=(2, 4, 8), activaciones=("sigmoide", "tanh", "relu", "gelu")):
    return [{"clave": f"d{d}|{a}|s{s}", "optimizador": "sgd_momentum", "activacion": a, "lr": lr,
             "semilla": s, "ocultas": [64] * d, "dropout": 0.0, "gradientes": True}
            for d, a, s in product(profundidades, activaciones, SEMILLAS[:3])]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("experimento", choices=["lr", "logistica", "grilla", "profundidad"])
    p.add_argument("--epocas", type=int, default=40)
    a = p.parse_args()
    torch.set_num_threads(max(1, torch.get_num_threads()))
    datos = preparar_datos()
    print("Partición por sujeto:", datos["particion"])
    if a.experimento == "lr":
        correr("ajuste_lr", configs_lr(), datos, a.epocas)
    elif a.experimento == "logistica":
        correr("logistica", configs_logistica(mejores_lr()), datos, a.epocas)
    elif a.experimento == "grilla":
        correr("grilla", configs_grilla(mejores_lr()), datos, a.epocas)
    else:
        correr("profundidad", configs_profundidad(), datos, a.epocas)


if __name__ == "__main__":
    main()

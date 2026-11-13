"""CNN sobre espectrogramas de CHB-MIT y comparativa de optimizadores.

Uso:
    python entrenar_cnn.py RAIZ prueba     # 2 épocas, para medir tiempos (no guarda en resultados)
    python entrenar_cnn.py RAIZ busqueda   # 6 optimizadores x 3 tasas de aprendizaje, semilla 0
    python entrenar_cnn.py RAIZ semillas   # mejor tasa de cada optimizador x 5 semillas
    python entrenar_cnn.py RAIZ posthoc    # tasa más alta de cada optimizador x 5 semillas (sensibilidad)

Cada corrida guarda resultados/etapa4/corridas/<nombre>.json (historia) y <nombre>_scores.npz
(puntajes de validación y prueba del mejor modelo). Si el json ya existe, la corrida se saltea,
así que se puede cortar y reanudar.

Partición por paciente (Etapa 2): entrenamiento chb02, chb05, chb08; validación chb01; prueba chb03, chb10.
"""
import copy
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from sklearn.metrics import roc_auc_score
from torch import nn

EPOCAS = 30
LOTE = 64
NEG_POR_POS = 10          # cada época: todas las ventanas ictales + 10 veces más ventanas normales al azar
N_VAL_NEG = 10000         # subconjunto fijo de validación para monitorear cada época
SEMILLAS = [0, 1, 2, 3, 4]

OPTIMIZADORES = {
    "SGD": ([0.3, 0.1, 0.03], lambda p, lr: torch.optim.SGD(p, lr=lr, weight_decay=1e-4)),
    "Momentum": ([0.03, 0.01, 0.003], lambda p, lr: torch.optim.SGD(p, lr=lr, momentum=0.9, weight_decay=1e-4)),
    "Nesterov": ([0.03, 0.01, 0.003],
                 lambda p, lr: torch.optim.SGD(p, lr=lr, momentum=0.9, nesterov=True, weight_decay=1e-4)),
    "RMSprop": ([3e-3, 1e-3, 3e-4], lambda p, lr: torch.optim.RMSprop(p, lr=lr, alpha=0.99, eps=1e-8, weight_decay=1e-4)),
    "Adam": ([3e-3, 1e-3, 3e-4], lambda p, lr: torch.optim.Adam(p, lr=lr, weight_decay=1e-4)),
    "AdamW": ([3e-3, 1e-3, 3e-4], lambda p, lr: torch.optim.AdamW(p, lr=lr, weight_decay=1e-2)),
}


class CNN(nn.Module):
    """Entrada (lote, 18 canales, 40 frecuencias, 7 cuadros de tiempo)."""

    def __init__(self, p_drop=0.3):
        super().__init__()
        self.red = nn.Sequential(
            nn.Conv2d(18, 32, (5, 3), padding=(2, 1)), nn.BatchNorm2d(32), nn.ReLU(), nn.MaxPool2d((2, 1)),
            nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(), nn.MaxPool2d((2, 1)),
            nn.Conv2d(64, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(),
            nn.AdaptiveAvgPool2d(1), nn.Flatten(), nn.Dropout(p_drop), nn.Linear(64, 1))

    def forward(self, x):
        return self.red(x).squeeze(1)


def cargar(raiz):
    """Carga espectrogramas por partición, calibra por paciente y estandariza con el entrenamiento."""
    proc = raiz / "datos" / "chbmit_proc"
    part = json.loads((proc / "particion.json").read_text(encoding="utf-8"))["fija"]
    indice = pd.read_csv(proc / "indice.csv")
    D = {}
    for conjunto, pacientes in part.items():
        X, cols = [], {k: [] for k in ["ictal", "borde", "t0", "archivo", "paciente"]}
        for p in pacientes:
            Xp = []
            for a in indice[indice.paciente == p].archivo:
                z = np.load(proc / (Path(a).stem + ".npz"))
                Xp.append(z["stft"])
                for k in ["ictal", "borde", "t0"]:
                    cols[k].append(z[k])
                cols["archivo"].append(np.full(len(z["t0"]), a))
                cols["paciente"].append(np.full(len(z["t0"]), p))
            Xp = np.concatenate(Xp).astype(np.float32)
            # Calibración no supervisada: se resta la mediana del paciente por canal y frecuencia.
            med = np.median(Xp.transpose(0, 3, 1, 2).reshape(-1, 18 * 40), axis=0).reshape(1, 18, 40, 1)
            X.append((Xp - med).astype(np.float16))
            del Xp
        D[conjunto] = {"X": np.concatenate(X), **{k: np.concatenate(v) for k, v in cols.items()}}
    Xtr = D["entrenamiento"]["X"]
    mu = np.zeros((1, 18, 40, 1), np.float64)
    m2 = np.zeros((1, 18, 40, 1), np.float64)
    for i in range(0, len(Xtr), 10000):
        b = Xtr[i:i + 10000].astype(np.float64)
        mu += b.sum(axis=(0, 3), keepdims=True)
        m2 += (b ** 2).sum(axis=(0, 3), keepdims=True)
    n = len(Xtr) * 7
    mu /= n
    sd = np.sqrt(m2 / n - mu ** 2)
    for c in D:
        X = D[c]["X"]
        for i in range(0, len(X), 10000):
            X[i:i + 10000] = ((X[i:i + 10000].astype(np.float32) - mu) / sd).astype(np.float16)
    return D


@torch.no_grad()
def predecir(modelo, X, lote=4096):
    modelo.eval()
    out = [modelo(torch.from_numpy(X[i:i + lote].astype(np.float32))).numpy() for i in range(0, len(X), lote)]
    return np.concatenate(out)


def correr(D, opt_nombre, lr, semilla, dir_out, epocas=EPOCAS):
    nombre = f"{opt_nombre}_lr{lr:g}_s{semilla}"
    destino = dir_out / f"{nombre}.json"
    if destino.exists():
        return json.loads(destino.read_text(encoding="utf-8"))
    torch.manual_seed(semilla)
    rng = np.random.default_rng(semilla)
    modelo = CNN()
    opt = OPTIMIZADORES[opt_nombre][1](modelo.parameters(), lr)

    tr, va, te = D["entrenamiento"], D["validacion"], D["prueba"]
    limpio_tr = tr["borde"] == 0
    pos = np.where(limpio_tr & (tr["ictal"] == 1))[0]
    neg = np.where(limpio_tr & (tr["ictal"] == 0))[0]
    rv = np.random.default_rng(12345)  # mismo subconjunto de validación para todas las corridas
    idx_v = np.concatenate([np.where((va["borde"] == 0) & (va["ictal"] == 1))[0],
                            rv.choice(np.where((va["borde"] == 0) & (va["ictal"] == 0))[0], N_VAL_NEG, replace=False)])
    Xv, yv = va["X"][idx_v], va["ictal"][idx_v].astype(np.float32)

    hist, mejor_auc, mejor_estado, mejor_ep = [], -1.0, None, -1
    t_ini = time.time()
    for ep in range(epocas):
        modelo.train()
        idx = np.concatenate([pos, rng.choice(neg, NEG_POR_POS * len(pos), replace=False)])
        rng.shuffle(idx)
        perd, normas = [], []
        for i in range(0, len(idx), LOTE):
            j = np.sort(idx[i:i + LOTE])
            if len(j) < 2:
                continue
            xb = torch.from_numpy(tr["X"][j].astype(np.float32))
            yb = torch.from_numpy(tr["ictal"][j].astype(np.float32))
            loss = F.binary_cross_entropy_with_logits(modelo(xb), yb)
            opt.zero_grad()
            loss.backward()
            normas.append(float(torch.nn.utils.clip_grad_norm_(modelo.parameters(), float("inf"))))
            opt.step()
            perd.append(loss.item())
        s_v = predecir(modelo, Xv)
        finito = bool(np.all(np.isfinite(perd)) and np.all(np.isfinite(s_v)))
        auc = float(roc_auc_score(yv, s_v)) if finito else float("nan")
        vloss = float(F.binary_cross_entropy_with_logits(torch.from_numpy(s_v), torch.from_numpy(yv))) if finito else float("nan")
        hist.append({"epoca": ep + 1, "perdida_entrenamiento": float(np.mean(perd)), "norma_grad": float(np.mean(normas)),
                     "perdida_val": vloss, "auc_val": auc, "segundos": time.time() - t_ini})
        print(f"  {nombre} ep {ep + 1:2d} loss {np.mean(perd):.4f} val_loss {vloss:.4f} val_auc {auc:.4f}", flush=True)
        if finito and auc > mejor_auc:
            mejor_auc, mejor_estado, mejor_ep = auc, copy.deepcopy(modelo.state_dict()), ep + 1
        if not finito:
            break

    res = {"optimizador": opt_nombre, "lr": lr, "semilla": semilla, "epocas": epocas, "historia": hist,
           "mejor_epoca": mejor_ep, "auc_val_mejor": mejor_auc, "diverge": mejor_estado is None,
           "parametros": sum(p.numel() for p in modelo.parameters()), "segundos": time.time() - t_ini}
    if mejor_estado is not None:
        modelo.load_state_dict(mejor_estado)
        s_val, s_te = predecir(modelo, va["X"]), predecir(modelo, te["X"])
        lv, lt = va["borde"] == 0, te["borde"] == 0
        res["auc_val_completo"] = float(roc_auc_score(va["ictal"][lv], s_val[lv]))
        res["auc_prueba"] = float(roc_auc_score(te["ictal"][lt], s_te[lt]))
        np.savez_compressed(dir_out / f"{nombre}_scores.npz", val=s_val.astype(np.float32), prueba=s_te.astype(np.float32))
        torch.save(mejor_estado, dir_out / f"{nombre}_modelo.pt")
    destino.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(f"== {nombre}: mejor época {mejor_ep}, AUC val {mejor_auc:.4f}, AUC prueba {res.get('auc_prueba', float('nan')):.4f}, "
          f"{res['segundos']:.0f} s", flush=True)
    return res


def main():
    raiz, fase = Path(sys.argv[1]), sys.argv[2]
    torch.set_num_threads(os.cpu_count())
    t = time.time()
    D = cargar(raiz)
    print("datos:", {c: D[c]["X"].shape for c in D}, f"{time.time() - t:.0f} s", flush=True)

    base = raiz / "resultados" / "etapa4"
    dir_out = base / "corridas"
    dir_out.mkdir(parents=True, exist_ok=True)
    for c in D:  # orden de las ventanas, para evaluar por evento en el notebook
        np.savez_compressed(base / f"ventanas_{c}.npz", **{k: v for k, v in D[c].items() if k != "X"})

    if fase == "prueba":
        tmp = Path(os.environ.get("TEMP", "/tmp")) / "cnn_prueba"
        tmp.mkdir(exist_ok=True)
        for f in tmp.glob("*"):
            f.unlink()
        correr(D, "Adam", 1e-3, 99, tmp, epocas=2)
    elif fase == "busqueda":
        for opt, (lrs, _) in OPTIMIZADORES.items():
            for lr in lrs:
                correr(D, opt, lr, 0, dir_out)
    elif fase == "semillas":
        elegidas = {}
        for opt, (lrs, _) in OPTIMIZADORES.items():
            res = [json.loads((dir_out / f"{opt}_lr{lr:g}_s0.json").read_text(encoding="utf-8")) for lr in lrs]
            elegidas[opt] = max(res, key=lambda r: r["auc_val_mejor"])["lr"]
        (base / "lr_elegidas.json").write_text(json.dumps(elegidas, indent=1), encoding="utf-8")
        print("tasas elegidas:", elegidas, flush=True)
        for opt, lr in elegidas.items():
            for s in SEMILLAS:
                correr(D, opt, lr, s, dir_out)
    elif fase == "posthoc":
        # Análisis de sensibilidad (no se usa para elegir): cada optimizador con su tasa más alta.
        for opt, (lrs, _) in OPTIMIZADORES.items():
            for s in SEMILLAS:
                correr(D, opt, max(lrs), s, dir_out)
    print("listo", flush=True)


if __name__ == "__main__":
    main()

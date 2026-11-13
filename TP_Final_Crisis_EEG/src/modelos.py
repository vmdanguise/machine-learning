"""Modelos, funciones de activación, optimizadores y bucle de entrenamiento."""

import time

import numpy as np
import torch
from sklearn.metrics import roc_auc_score
from torch import nn

ACTIVACIONES = {
    "sigmoide": nn.Sigmoid,
    "tanh": nn.Tanh,
    "relu": nn.ReLU,
    "leaky_relu": lambda: nn.LeakyReLU(0.01),
    "gelu": nn.GELU,
}

# Inicialización que conserva la varianza de la señal según la activación:
# Xavier/Glorot para las saturantes, He/Kaiming para la familia ReLU.
_INIT = {
    "sigmoide": lambda w: nn.init.xavier_normal_(w),
    "tanh": lambda w: nn.init.xavier_normal_(w, gain=nn.init.calculate_gain("tanh")),
    "relu": lambda w: nn.init.kaiming_normal_(w, nonlinearity="relu"),
    "leaky_relu": lambda w: nn.init.kaiming_normal_(w, a=0.01, nonlinearity="leaky_relu"),
    "gelu": lambda w: nn.init.kaiming_normal_(w, nonlinearity="relu"),
}

OPTIMIZADORES = {
    "sgd": lambda p, lr: torch.optim.SGD(p, lr=lr),
    "sgd_momentum": lambda p, lr: torch.optim.SGD(p, lr=lr, momentum=0.9, nesterov=True),
    "rmsprop": lambda p, lr: torch.optim.RMSprop(p, lr=lr, alpha=0.99),
    "adam": lambda p, lr: torch.optim.Adam(p, lr=lr),
    "adamw": lambda p, lr: torch.optim.AdamW(p, lr=lr, weight_decay=1e-2),
    "lbfgs": lambda p, lr: torch.optim.LBFGS(p, lr=lr, max_iter=10, history_size=20,
                                             line_search_fn="strong_wolfe"),
}

GRILLA_LR = {
    "sgd": [3e-3, 1e-2, 3e-2, 1e-1],
    "sgd_momentum": [1e-3, 3e-3, 1e-2, 3e-2],
    "rmsprop": [1e-4, 3e-4, 1e-3, 3e-3],
    "adam": [1e-4, 3e-4, 1e-3, 3e-3],
    "adamw": [1e-4, 3e-4, 1e-3, 3e-3],
    "lbfgs": [0.1, 0.3, 1.0],
}


class MLP(nn.Module):
    """Perceptrón multicapa; con ocultas=() es una regresión logística."""

    def __init__(self, n_entrada, ocultas=(128, 64), activacion="relu", dropout=0.2):
        super().__init__()
        capas, n = [], n_entrada
        for h in ocultas:
            lineal = nn.Linear(n, h)
            _INIT[activacion](lineal.weight)
            nn.init.zeros_(lineal.bias)
            capas += [lineal, ACTIVACIONES[activacion]()]
            if dropout:
                capas.append(nn.Dropout(dropout))
            n = h
        salida = nn.Linear(n, 1)
        nn.init.xavier_normal_(salida.weight)
        nn.init.zeros_(salida.bias)
        self.red = nn.Sequential(*capas, salida)
        self.lineales = [m for m in self.red if isinstance(m, nn.Linear)]

    def forward(self, x):
        return self.red(x).squeeze(-1)

    @torch.no_grad()
    def unidades_inactivas(self, x):
        """Fracción de unidades ocultas cuya preactivación es negativa para todas las muestras."""
        fracciones = []
        for m in self.red:
            if isinstance(m, nn.Linear) and m is not self.lineales[-1]:
                z = m(x)
                fracciones.append((z <= 0).all(0).float().mean().item())
            x = m(x)
        return fracciones


def fijar_semilla(semilla):
    np.random.seed(semilla)
    torch.manual_seed(semilla)


@torch.no_grad()
def predecir(modelo, X, lote=65536):
    modelo.eval()
    return torch.cat([torch.sigmoid(modelo(X[i:i + lote])) for i in range(0, len(X), lote)]).numpy()


def _perdida_completa(modelo, criterio, X, y, lote=65536):
    total = 0.0
    for i in range(0, len(X), lote):
        total += criterio(modelo(X[i:i + lote]), y[i:i + lote]).item() * len(X[i:i + lote])
    return total / len(X)


def entrenar(modelo, optimizador, lr, datos, epocas=40, lote=256, paciencia=8, semilla=0,
             registrar_gradientes=False, pos_weight=None):
    """Entrena con BCE ponderada y devuelve el historial por época.

    `datos` es un dict con tensores Xtr, ytr, Xva, yva. Se guarda el estado con
    mejor AUC de validación (early stopping). Para L-BFGS cada "época" es un
    paso completo sobre todo el conjunto (hasta 10 iteraciones internas), por
    eso además se registra la cantidad de pasadas completas por los datos.
    """
    fijar_semilla(semilla)
    Xtr, ytr, Xva, yva = datos["Xtr"], datos["ytr"], datos["Xva"], datos["yva"]
    if pos_weight is None:
        pos_weight = (ytr == 0).sum() / (ytr == 1).sum().clamp(min=1)
    criterio = nn.BCEWithLogitsLoss(pos_weight=torch.as_tensor(pos_weight, dtype=torch.float32))
    opt = OPTIMIZADORES[optimizador](modelo.parameters(), lr)
    n = len(Xtr)
    hist = {k: [] for k in ("perdida_tr", "perdida_va", "auc_va", "tiempo", "pasadas", "grad_capas")}
    mejor = (-np.inf, None, 0)
    pasadas, t0 = 0.0, time.perf_counter()

    for epoca in range(1, epocas + 1):
        modelo.train()
        normas = np.zeros(len(modelo.lineales))
        pasos = 0

        if optimizador == "lbfgs":
            def cierre():
                nonlocal pasadas
                opt.zero_grad()
                perdida = criterio(modelo(Xtr), ytr)
                perdida.backward()
                pasadas += 1
                return perdida
            opt.step(cierre)
            if registrar_gradientes:
                normas += [m.weight.grad.norm().item() for m in modelo.lineales]
                pasos = 1
        else:
            orden = torch.randperm(n)
            for i in range(0, n, lote):
                idx = orden[i:i + lote]
                opt.zero_grad()
                perdida = criterio(modelo(Xtr[idx]), ytr[idx])
                perdida.backward()
                if registrar_gradientes:
                    normas += [m.weight.grad.norm().item() for m in modelo.lineales]
                    pasos += 1
                opt.step()
            pasadas += 1

        modelo.eval()
        with torch.no_grad():
            perdida_tr = _perdida_completa(modelo, criterio, Xtr, ytr)
            perdida_va = _perdida_completa(modelo, criterio, Xva, yva)
        p_va = predecir(modelo, Xva)
        auc = roc_auc_score(yva.numpy(), p_va) if np.isfinite(p_va).all() else np.nan

        hist["perdida_tr"].append(perdida_tr)
        hist["perdida_va"].append(perdida_va)
        hist["auc_va"].append(auc)
        hist["tiempo"].append(time.perf_counter() - t0)
        hist["pasadas"].append(pasadas)
        if registrar_gradientes:
            hist["grad_capas"].append((normas / max(pasos, 1)).tolist())

        if not np.isfinite(perdida_tr):
            break
        if np.isfinite(auc) and auc > mejor[0]:
            mejor = (auc, {k: v.clone() for k, v in modelo.state_dict().items()}, epoca)
        elif epoca - mejor[2] >= paciencia:
            break

    if mejor[1] is not None:
        modelo.load_state_dict(mejor[1])
    hist["mejor_epoca"] = mejor[2]
    hist["mejor_auc_va"] = float(mejor[0])
    return hist

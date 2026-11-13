"""Experimento de convexidad: regresión logística con regularización L2.

    f(w, b) = (1/n) Σ c_i [ log(1 + e^{z_i}) - y_i z_i ] + (μ/2) ||w||²,  z_i = wᵀx_i + b

con c_i = peso de clase. Para μ > 0 f es estrictamente convexa en w, así que
tiene un único minimizador global: todos los optimizadores deberían llegar
al mismo valor f*. Se compara cuánto tardan y qué tan cerca quedan.
Nelder-Mead (simplex, sin derivadas) se corre en un subespacio de pocas
dimensiones (PCA), porque su costo crece muy rápido con la dimensión.
"""

import time

import numpy as np
import torch
from scipy.optimize import minimize
from scipy.special import expit, log1p
from sklearn.decomposition import PCA

from .modelos import OPTIMIZADORES

MU = 1e-3


def _pesos(y):
    pos = y.mean()
    return np.where(y == 1, 0.5 / pos, 0.5 / (1 - pos))


def objetivo_np(theta, X, y, c, mu=MU):
    w, b = theta[:-1], theta[-1]
    z = X @ w + b
    perdida = np.mean(c * (np.logaddexp(0, z) - y * z)) + 0.5 * mu * w @ w
    r = c * (expit(z) - y) / len(y)
    return perdida, np.append(X.T @ r + mu * w, r.sum())


def optimo_referencia(X, y, mu=MU):
    c = _pesos(y)
    r = minimize(objetivo_np, np.zeros(X.shape[1] + 1), args=(X, y, c, mu), jac=True,
                 method="L-BFGS-B", options={"maxiter": 20000, "ftol": 1e-15, "gtol": 1e-10})
    return r.x, r.fun


def correr_optimizador(nombre, lr, X, y, epocas=100, lote=512, mu=MU, semilla=0):
    torch.manual_seed(semilla)
    Xt, yt = torch.tensor(X, dtype=torch.float64), torch.tensor(y, dtype=torch.float64)
    ct = torch.tensor(_pesos(y), dtype=torch.float64)
    w = torch.zeros(X.shape[1], dtype=torch.float64, requires_grad=True)
    b = torch.zeros(1, dtype=torch.float64, requires_grad=True)
    opt = OPTIMIZADORES[nombre]([w, b], lr)
    if nombre == "adamw":  # en el experimento convexo la regularización ya está en f
        for g in opt.param_groups:
            g["weight_decay"] = 0.0

    def f(idx=None):
        Xi, yi, ci = (Xt, yt, ct) if idx is None else (Xt[idx], yt[idx], ct[idx])
        z = Xi @ w + b
        return (ci * (torch.nn.functional.softplus(z) - yi * z)).mean() + 0.5 * mu * (w @ w)

    curva, t0, n = [], time.perf_counter(), len(y)
    for _ in range(epocas):
        if nombre == "lbfgs":
            def cierre():
                opt.zero_grad()
                v = f()
                v.backward()
                return v
            opt.step(cierre)
        else:
            orden = torch.randperm(n)
            for i in range(0, n, lote):
                opt.zero_grad()
                f(orden[i:i + lote]).backward()
                opt.step()
        with torch.no_grad():
            curva.append(f().item())
        if not np.isfinite(curva[-1]):
            break
    theta = np.append(w.detach().numpy(), b.detach().numpy())
    return {"curva": np.array(curva), "theta": theta, "tiempo": time.perf_counter() - t0}


def nelder_mead(X, y, k=10, mu=MU, max_eval=20000, semilla=0):
    """Compara Nelder-Mead con el óptimo exacto en un subespacio PCA de dimensión k."""
    Z = PCA(k, random_state=semilla).fit_transform(X)
    Z /= Z.std(0)
    c = _pesos(y)
    _, f_ref = optimo_referencia(Z, y, mu)
    historia = []

    def f(theta):
        v = objetivo_np(theta, Z, y, c, mu)[0]
        historia.append(v)
        return v

    t0 = time.perf_counter()
    r = minimize(f, np.zeros(k + 1), method="Nelder-Mead",
                 options={"maxfev": max_eval, "xatol": 1e-8, "fatol": 1e-12, "adaptive": True})
    return {"f_ref": f_ref, "f_nm": r.fun, "evaluaciones": r.nfev, "historia": np.minimum.accumulate(historia),
            "tiempo": time.perf_counter() - t0, "k": k}


def submuestra(X, y, n=30000, semilla=0):
    """Submuestra estratificada que conserva todas las ventanas con crisis si entran."""
    rng = np.random.default_rng(semilla)
    pos, neg = np.flatnonzero(y == 1), np.flatnonzero(y == 0)
    n_pos = min(len(pos), n // 10)
    idx = np.concatenate([rng.choice(pos, n_pos, replace=False), rng.choice(neg, n - n_pos, replace=False)])
    return X[idx], y[idx]

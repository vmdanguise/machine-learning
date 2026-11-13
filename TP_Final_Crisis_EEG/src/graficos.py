"""Estilo común de figuras y guardado en la carpeta del documento LaTeX."""

import matplotlib.pyplot as plt

from .config import DIR_FIGURAS

NOMBRES_OPT = {"sgd": "SGD", "sgd_momentum": "SGD+Nesterov", "rmsprop": "RMSProp",
               "adam": "Adam", "adamw": "AdamW", "lbfgs": "L-BFGS"}
NOMBRES_ACT = {"sigmoide": "Sigmoide", "tanh": "Tanh", "relu": "ReLU",
               "leaky_relu": "Leaky ReLU", "gelu": "GELU"}


def estilo():
    plt.rcParams.update({
        "figure.dpi": 110, "savefig.dpi": 200, "savefig.bbox": "tight",
        "axes.grid": True, "grid.alpha": 0.3, "axes.spines.top": False, "axes.spines.right": False,
        "font.size": 10, "legend.frameon": False,
    })


def guardar(fig, nombre):
    """Guarda en PDF (para LaTeX) y PNG (para Word)."""
    DIR_FIGURAS.mkdir(parents=True, exist_ok=True)
    fig.savefig(DIR_FIGURAS / f"{nombre}.pdf")
    fig.savefig(DIR_FIGURAS / f"{nombre}.png")

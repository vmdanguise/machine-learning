"""Estilo común de los gráficos del TP (notebooks e informe)."""
import matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap

TINTA = "#2B2D42"
GRIS = "#8D99AE"
GRIS_CLARO = "#E3E6EC"
AZUL = "#2E5EAA"
CELESTE = "#7FB7E6"
VERDE = "#00798C"
AMARILLO = "#EDAE49"
NARANJA = "#E07A3F"
ROJO = "#D1495B"
VIOLETA = "#6B4E9B"
CIAN = "#4CC9F0"

# De sano (frío) a crisis (cálido).
SET_BONN = {"A": CELESTE, "B": AZUL, "C": AMARILLO, "D": NARANJA, "E": ROJO}
CLASES_BONN = [AZUL, NARANJA, ROJO]
BANDAS = [AZUL, VERDE, "#7FB069", AMARILLO, ROJO]
OPTIMIZADOR = {"SGD": VERDE, "Momentum": AZUL, "Nesterov": VIOLETA,
               "RMSprop": AMARILLO, "Adam": NARANJA, "AdamW": ROJO}
CICLO = [AZUL, ROJO, VERDE, AMARILLO, VIOLETA, NARANJA, GRIS, CELESTE]

CMAP_SECUENCIAL = LinearSegmentedColormap.from_list("tp_azul", ["#F7F9FC", "#C9D9EF", AZUL, "#1B3A6B"])
CMAP_ESPECTRO = "magma"


def matriz_confusion(ax, cm, etiquetas, titulo=None):
    """Matriz de confusión con conteo y porcentaje por fila (sobre la clase verdadera)."""
    import numpy as np
    cm = np.asarray(cm)
    frac = cm / np.maximum(cm.sum(axis=1, keepdims=True), 1)
    ax.imshow(frac, cmap=CMAP_SECUENCIAL, vmin=0, vmax=1)
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            color = "white" if frac[i, j] > 0.55 else TINTA
            ax.text(j, i - 0.09, f"{cm[i, j]:,}".replace(",", "."), ha="center", va="center",
                    fontsize=13, fontweight="semibold", color=color)
            ax.text(j, i + 0.17, f"{100 * frac[i, j]:.1f} %".replace(".", ","), ha="center", va="center",
                    fontsize=9.5, color=color, alpha=0.85)
    ax.set_xticks(range(len(etiquetas)), etiquetas)
    ax.set_yticks(range(len(etiquetas)), etiquetas)
    ax.set_xlabel("clase predicha"); ax.set_ylabel("clase verdadera")
    ax.grid(False); ax.tick_params(length=0)
    for lado in ax.spines.values():
        lado.set_visible(False)
    if titulo:
        ax.set_title(titulo)


def aplicar():
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "Calibri", "DejaVu Sans"],
        "mathtext.fontset": "dejavusans",
        "font.size": 11.5,
        "axes.titlesize": 12.5,
        "axes.titleweight": "semibold",
        "axes.titlelocation": "left",
        "axes.titlepad": 9,
        "axes.labelsize": 11.5,
        "axes.labelcolor": TINTA,
        "axes.edgecolor": "#5C6178",
        "axes.linewidth": 0.9,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.axisbelow": True,
        "axes.prop_cycle": mpl.cycler(color=CICLO),
        "axes.facecolor": "white",
        "grid.color": GRIS_CLARO,
        "grid.linewidth": 0.8,
        "grid.alpha": 1.0,
        "xtick.color": "#5C6178",
        "ytick.color": "#5C6178",
        "xtick.labelcolor": TINTA,
        "ytick.labelcolor": TINTA,
        "xtick.labelsize": 10.5,
        "ytick.labelsize": 10.5,
        "legend.frameon": False,
        "legend.fontsize": 10,
        "legend.title_fontsize": 10.5,
        "lines.linewidth": 1.9,
        "lines.markersize": 5.5,
        "patch.edgecolor": "white",
        "image.cmap": "magma",
        "text.color": TINTA,
        "figure.facecolor": "white",
        "figure.dpi": 110,
        "savefig.dpi": 220,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.08,
        "savefig.facecolor": "white",
    })

# %% [markdown]
# # Etapa 1 — Dataset de Bonn y análisis de Fourier
#
# **Fuente oficial:** Universitätsklinikum Bonn, Epileptologie, AG Lehnertz.
# Andrzejak RG, Lehnertz K, Rieke C, Mormann F, David P, Elger CE (2001).
# *Phys. Rev. E, 64, 061907*.
#
# | Set | Archivo | Registro | Estado |
# |---|---|---|---|
# | A | Z | superficie, voluntarios sanos | ojos abiertos |
# | B | O | superficie, voluntarios sanos | ojos cerrados |
# | C | N | intracraneal, zona opuesta al foco | entre crisis (interictal) |
# | D | F | intracraneal, zona epileptógena | entre crisis (interictal) |
# | E | S | intracraneal | durante la crisis (ictal) |
#
# Cada segmento: $N = 4097$ muestras a $f_s = 173{,}61$ Hz, o sea $T = N/f_s \approx 23{,}6$ s.
# Ancho de banda del equipo: 0,5–85 Hz. El artículo aplica un pasabajos de 40 Hz como primer paso
# del análisis; las series descargables **no** lo tienen aplicado.

# %%
from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import signal

try:
    import google.colab  # noqa: F401
    RAIZ = Path("/content/drive/MyDrive/TP_Machine_Learning_Epilepsia")
except ImportError:
    RAIZ = Path.cwd().parents[0] if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(RAIZ / "scripts"))
import estilo_graficos as EG
EG.aplicar()

DATOS = RAIZ / "datos" / "bonn"
SALIDA = RAIZ / "resultados" / "etapa1"
SALIDA.mkdir(parents=True, exist_ok=True)

FS = 173.61
SETS = {"A": "Z", "B": "O", "C": "N", "D": "F", "E": "S"}
DESCRIPCION = {"A": "Sano, ojos abiertos", "B": "Sano, ojos cerrados",
               "C": "Interictal, zona opuesta", "D": "Interictal, zona epileptogena",
               "E": "Ictal (crisis)"}
print("RAIZ:", RAIZ)

# %% [markdown]
# ## 1.1 Carga y verificación

# %%
def cargar_set(letra_archivo):
    archivos = sorted((DATOS / letra_archivo).glob("*.[tT][xX][tT]"))
    return np.stack([np.loadtxt(a) for a in archivos]), [a.name for a in archivos]

X, y, nombres = [], [], []
for s, letra in SETS.items():
    datos, n = cargar_set(letra)
    X.append(datos); y += [s] * len(datos); nombres += n
X = np.concatenate(X).astype(np.float32)
y = np.array(y)

assert X.shape == (500, 4097), X.shape
assert all((y == s).sum() == 100 for s in SETS)
print("X:", X.shape, "| duración por segmento: %.2f s" % (X.shape[1] / FS))
print("Nyquist: f_s/2 = %.2f Hz" % (FS / 2))

resumen = pd.DataFrame({
    "set": list(SETS), "descripcion": [DESCRIPCION[s] for s in SETS],
    "media_uV": [X[y == s].mean() for s in SETS],
    "desvio_uV": [X[y == s].std() for s in SETS],
    "max_abs_uV": [np.abs(X[y == s]).max() for s in SETS],
}).round(1)
resumen.to_csv(SALIDA / "resumen_sets.csv", index=False)
resumen

# %% [markdown]
# ### Saturación del conversor
#
# El valor 2047 es el máximo de un conversor de 12 bits con signo ($2^{11}-1$). Las muestras que llegan
# a ese valor están **recortadas**: la amplitud real era mayor. Se cuentan, se documentan y se conservan
# como vienen en la fuente oficial (no se corrigen).

# %%
TOPE = 2047
sat = np.abs(X) >= TOPE
tabla_sat = pd.DataFrame({
    "set": list(SETS),
    "segmentos_saturados": [int(sat[y == s].any(axis=1).sum()) for s in SETS],
    "muestras_saturadas": [int(sat[y == s].sum()) for s in SETS],
})
print("Segmentos afectados:", [nombres[i] for i in np.where(sat.any(axis=1))[0]])
tabla_sat.to_csv(SALIDA / "saturacion_12bits.csv", index=False)
tabla_sat

# %% [markdown]
# ## 1.2 Un ejemplo por set (los mismos que publica el grupo de Bonn)
#
# Series de ejemplo oficiales: Z093, O015, N062, F021, S056.

# %%
ejemplos = {"A": "Z093", "B": "O015", "C": "N062", "D": "F021", "E": "S056"}
t = np.arange(X.shape[1]) / FS
fig, ejes = plt.subplots(5, 1, figsize=(11, 10), sharex=True)
for ax, (s, nom) in zip(ejes, ejemplos.items()):
    i = [k for k, n in enumerate(nombres) if n.upper().startswith(nom)][0]
    ax.plot(t, X[i], lw=0.55, color=EG.SET_BONN[s])
    ax.set_ylabel("µV"); ax.set_xlim(0, t[-1]); ax.grid(axis="x", visible=False)
    ax.set_title(f"Set {s} ({nom}) — {DESCRIPCION[s]}", fontsize=11)
ejes[-1].set_xlabel("tiempo [s]")
fig.tight_layout(); fig.savefig(SALIDA / "ejemplos_por_set.png")

# %% [markdown]
# ## 1.3 Transformada discreta de Fourier
#
# Para una señal muestreada $x[n]$, $n = 0,\dots,N-1$:
#
# $$X[k] = \sum_{n=0}^{N-1} x[n]\, e^{-j 2\pi k n / N}, \qquad f_k = \frac{k\, f_s}{N}.$$
#
# La resolución en frecuencia es $\Delta f = f_s/N \approx 0{,}042$ Hz. Para reducir la varianza del
# estimador se usa el método de Welch: se promedian periodogramas de ventanas de Hann con 50 % de solapamiento.

# %%
def psd_welch(x, nperseg=512):
    return signal.welch(x, fs=FS, window="hann", nperseg=nperseg, noverlap=nperseg // 2, axis=-1)

f, P = psd_welch(X)
fig, ax = plt.subplots(figsize=(10, 5))
for s in SETS:
    m = np.median(P[y == s], axis=0)
    ax.semilogy(f, m, label=f"{s}: {DESCRIPCION[s]}", lw=2.4 if s == "E" else 1.6, color=EG.SET_BONN[s])
ax.axvspan(40, FS / 2, color=EG.GRIS_CLARO, alpha=0.45, lw=0)
ax.axvline(40, ls="--", c=EG.GRIS, lw=1)
ax.text(41, ax.get_ylim()[1] / 3, "eliminado por el\npasabajos de 40 Hz", fontsize=9.5, color=EG.GRIS, va="top")
ax.set_xlim(0, FS / 2); ax.set_xlabel("frecuencia [Hz]"); ax.set_ylabel("PSD [µV²/Hz] (mediana por set)")
ax.set_title("Densidad espectral de potencia (Welch) por set")
ax.legend(loc="upper right", bbox_to_anchor=(1, 0.86))
fig.tight_layout(); fig.savefig(SALIDA / "psd_welch_por_set.png")

# %% [markdown]
# **Observaciones del espectro:**
# - El set E (crisis) tiene entre 10 y 100 veces más potencia que los demás entre 3 y 25 Hz, con un pico cerca de 6 Hz.
#   Esa es la descarga rítmica de la crisis.
# - El set B (ojos cerrados) muestra el ritmo **alfa** cerca de 10–11 Hz, que casi desaparece con los ojos abiertos (A).
# - El pico en **50 Hz** es interferencia de la red eléctrica (Alemania, 50 Hz) y aparece en todos los sets.
#   El pasabajos de 40 Hz lo elimina.
# - El pico cerca de 76 Hz aparece sobre todo en los registros de superficie (A, B); también queda fuera con el filtro.

# %% [markdown]
# ## 1.4 Filtro pasabajos de 40 Hz (primer paso del artículo original)
#
# Butterworth de orden 4 aplicado ida y vuelta (`filtfilt`), así la fase no se distorsiona.

# %%
b, a = signal.butter(4, 40, btype="low", fs=FS)
Xf = signal.filtfilt(b, a, X, axis=-1).astype(np.float32)
f2, Pf = psd_welch(Xf)
print("Energía relativa por encima de 40 Hz (antes del filtro):")
for s in SETS:
    tot = np.trapezoid(P[y == s], f, axis=1); alta = np.trapezoid(P[y == s][:, f > 40], f[f > 40], axis=1)
    print(f"  {s}: {np.median(alta / tot) * 100:.2f} %")

# %% [markdown]
# ## 1.5 Potencia por bandas clínicas
#
# $$P_{[f_1,f_2]} = \int_{f_1}^{f_2} S_{xx}(f)\, df \approx \sum_{f_1 \le f_k < f_2} S_{xx}(f_k)\, \Delta f$$
#
# Bandas: delta 0,5–4, theta 4–8, alfa 8–13, beta 13–30, gamma 30–40 Hz.

# %%
BANDAS = {"delta": (0.5, 4), "theta": (4, 8), "alfa": (8, 13), "beta": (13, 30), "gamma": (30, 40)}

def potencia_bandas(f, P):
    out = {}
    for nombre, (lo, hi) in BANDAS.items():
        m = (f >= lo) & (f < hi)
        out[nombre] = np.trapezoid(P[..., m], f[m], axis=-1)
    return pd.DataFrame(out)

bp = potencia_bandas(f2, Pf)
bp_rel = bp.div(bp.sum(axis=1), axis=0)
bp_rel["set"] = y
# La media por set conserva la suma = 1 (la mediana por banda no).
tabla = bp_rel.groupby("set").mean().round(3)
assert np.allclose(tabla.sum(axis=1), 1, atol=0.01)
tabla.to_csv(SALIDA / "potencia_relativa_bandas_media.csv")
bp_rel.groupby("set").median().round(3).to_csv(SALIDA / "potencia_relativa_bandas_mediana.csv")

fig, ax = plt.subplots(figsize=(9, 4.5))
tabla.plot(kind="bar", stacked=True, ax=ax, color=EG.BANDAS, rot=0, width=0.68, edgecolor="white", lw=1)
ax.set_ylabel("potencia relativa (media por set)"); ax.set_xlabel("set"); ax.grid(axis="x", visible=False)
ax.legend(title="banda", bbox_to_anchor=(1.01, 1), loc="upper left")
fig.tight_layout(); fig.savefig(SALIDA / "potencia_relativa_bandas.png")
tabla

# %% [markdown]
# ## 1.6 Espectrograma (STFT) de un segmento ictal
#
# $$\mathrm{STFT}\{x\}(m, k) = \sum_{n} x[n]\, w[n - mH]\, e^{-j 2\pi k n / L}$$
#
# con ventana $w$ de largo $L$ y salto $H$. La STFT muestra cómo cambia el contenido en frecuencia a lo largo del tiempo.

# %%
i = [k for k, n in enumerate(nombres) if n.upper().startswith("S056")][0]
fs_, ts_, Sxx = signal.spectrogram(Xf[i], fs=FS, window="hann", nperseg=256, noverlap=192)
fig, ax = plt.subplots(figsize=(10, 4))
S_db = 10 * np.log10(Sxx + 1e-12)
vis = S_db[fs_ <= 40]
im = ax.pcolormesh(ts_, fs_, S_db, shading="gouraud", cmap=EG.CMAP_ESPECTRO, rasterized=True,
                   vmin=np.percentile(vis, 2), vmax=vis.max())
ax.set_ylim(0, 40); ax.set_xlabel("tiempo [s]"); ax.set_ylabel("frecuencia [Hz]"); ax.grid(False)
ax.set_title("Espectrograma S056 (ictal) · ventana Hann 256, solape 75 %")
cb = fig.colorbar(im, label="dB", pad=0.015); cb.outline.set_visible(False)
fig.tight_layout(); fig.savefig(SALIDA / "espectrograma_S056.png")

# %% [markdown]
# ## 1.7 Guardado para las etapas siguientes

# %%
np.savez_compressed(SALIDA / "bonn_filtrado_40hz.npz", X=Xf, y=y, nombres=np.array(nombres), fs=FS)
meta = {"fs": FS, "n_muestras": int(X.shape[1]), "n_segmentos": int(X.shape[0]),
        "filtro": "Butterworth orden 4, pasabajos 40 Hz, filtfilt",
        "welch": {"ventana": "hann", "nperseg": 512, "noverlap": 256},
        "fuente": "https://www.ukbonn.de/epileptologie/arbeitsgruppen/ag-lehnertz-neurophysik/downloads/"}
(SALIDA / "metadatos.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
print(sorted(p.name for p in SALIDA.iterdir()))

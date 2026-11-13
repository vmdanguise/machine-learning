"""Genera notebooks/TP_Final_Crisis_EEG.ipynb a partir de las celdas definidas acá.

Mantener el notebook como código hace más fácil versionarlo y regenerarlo:
    python herramientas/construir_notebook.py
"""

from pathlib import Path

import nbformat as nbf

RAIZ = Path(__file__).resolve().parents[1]
celdas = []


def md(texto):
    celdas.append(nbf.v4.new_markdown_cell(texto.strip()))


def py(codigo):
    celdas.append(nbf.v4.new_code_cell(codigo.strip()))


md(r"""
# Detección de crisis epilépticas en EEG de superficie
## Análisis espectral, comparación de optimizadores y funciones de activación

**Trabajo final — Machine Learning — Maestría en Inteligencia Artificial, Universidad de Palermo**

Este notebook contiene el trabajo práctico completo. La lógica reutilizable está en `src/` (scripts `.py`) y acá se ejecuta, se explica y se grafica. Cada sección corresponde a un capítulo del documento escrito (`documentos/`).

| Sección | Contenido | Capítulo |
|---|---|---|
| 0 | Configuración (local o Google Colab) | — |
| 1 | Datos: CHB-MIT y anotaciones | 8 |
| 2 | La señal EEG y su modelo matemático | 2 |
| 3 | Transformada de Fourier: Parseval, Welch, espectrograma | 3 |
| 4 | Entropía espectral en el simplex y multiplicadores de Lagrange (H5) | 3 y 6 |
| 5 | Extracción de características y partición por sujeto | 8 |
| 6 | Caso convexo: regresión logística y óptimo global (H1) | 6 y 9 |
| 7 | Ajuste de tasa de aprendizaje | 9 |
| 8 | Optimizador × activación (H2 y H4) | 9 |
| 9 | Profundidad × activación: desvanecimiento del gradiente (H3) | 5 y 9 |
| 10 | Evaluación final: ROC, AUC, matriz de confusión, umbral de Neyman-Pearson | 7 y 9 |
| 11 | Sobreajuste y resumen de hipótesis | 4 y 10 |
""")

md(r"""
## 0. Configuración

`MODO_RAPIDO = True` corre todo con menos épocas y semillas (sirve para probar que el notebook funciona de punta a punta). Para los resultados del documento usar `False`.

**En Google Colab:** subir la carpeta `TP_Final_Crisis_EEG` a Google Drive (sin `data/`). La celda siguiente monta Drive, baja los EDF al disco local de Colab (más rápido) y guarda las características y los resultados en Drive para que sobrevivan al cierre de la sesión.
""")

py(r"""
MODO_RAPIDO = True
RUTA_DRIVE = "/content/drive/MyDrive/TP_Final_Crisis_EEG"  # solo se usa en Colab

import os, sys
from pathlib import Path

EN_COLAB = "google.colab" in sys.modules
if EN_COLAB:
    from google.colab import drive
    drive.mount("/content/drive")
    os.chdir(RUTA_DRIVE)
    os.environ["TP_DIR_CRUDOS"] = "/content/chbmit"
    os.environ["TP_DIR_PROCESADOS"] = f"{RUTA_DRIVE}/data/procesados"
else:
    while not Path("src").is_dir() and Path.cwd() != Path.cwd().parent:
        os.chdir("..")
# Las corridas rápidas se guardan aparte para no mezclarse con los resultados definitivos.
os.environ["TP_DIR_RESULTADOS"] = str(Path.cwd() / ("resultados/rapido" if MODO_RAPIDO else "resultados"))
sys.path.insert(0, str(Path.cwd()))
print("Directorio del proyecto:", Path.cwd())
""")

py(r"""
import json
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import torch
from scipy import signal, stats

from src import config
from src.anotaciones import tabla_archivos, tabla_crisis
from src.caracteristicas import (cargar, espectros_segmentos, filtrar, procesar_todo, psd_welch,
                                 ventanear)
from src.convexo import correr_optimizador, nelder_mead, optimo_referencia, submuestra
from src.descarga import descargar, descargar_metadatos, seleccionar_archivos
from src.edf import leer_edf
from src.evaluacion import (alfa_por_falsas_alarmas, envolvente_concava, metricas,
                            umbral_neyman_pearson, umbral_youden)
from src.experimentos import (SEMILLAS, configs_grilla, configs_logistica, configs_lr,
                              configs_profundidad, correr, leer_resultados, mejores_lr, preparar_datos)
from src.graficos import NOMBRES_ACT, NOMBRES_OPT, estilo, guardar
from src.modelos import MLP, entrenar, predecir

warnings.filterwarnings("ignore", category=RuntimeWarning)
estilo()
EPOCAS = 8 if MODO_RAPIDO else 40
N_SEMILLAS = 2 if MODO_RAPIDO else 5
print("PyTorch", torch.__version__, "| hilos:", torch.get_num_threads(), "| GPU:", torch.cuda.is_available())
""")

md(r"""
## 1. Datos: CHB-MIT Scalp EEG Database

Registros de EEG de superficie de 23 casos pediátricos del Children's Hospital Boston (22 sujetos: `chb21` es la misma paciente que `chb01`, 1,5 años después), muestreados a 256 Hz con el sistema internacional 10-20 en montaje bipolar. Las crisis están anotadas por especialistas (inicio y fin en segundos) en los archivos `chbXX-summary.txt`.

Se descargan **todos los registros con crisis** y **3 registros sin crisis por caso** (muestra aleatoria con semilla fija), unos 14 GB. La descarga verifica SHA-256 y se puede interrumpir y retomar.
""")

py(r"""
descargar_metadatos(config.DIR_CRUDOS)
archivos = seleccionar_archivos(config.DIR_CRUDOS, n_sin_crisis=3)
faltan = [a for a in archivos if not (config.DIR_CRUDOS / a).exists()]
print(f"Seleccionados {len(archivos)} archivos, faltan {len(faltan)}")
if faltan:
    errores = descargar(archivos, config.DIR_CRUDOS, hilos=6)
    print("Errores:", errores)
""")

py(r"""
info = pd.read_csv(config.DIR_CRUDOS / "SUBJECT-INFO", sep="\t").dropna(how="all")
info.columns = ["caso", "sexo", "edad"]
arch = tabla_archivos()
crisis = tabla_crisis()

resumen = (arch.groupby("caso")
               .agg(archivos=("archivo", "size"), descargados=("descargado", "sum"))
               .join(crisis.groupby("caso").agg(crisis=("duracion_s", "size"),
                                               duracion_media_s=("duracion_s", "mean"),
                                               duracion_total_s=("duracion_s", "sum")))
               .join(info.set_index("caso"))
               .fillna({"crisis": 0}))
display(resumen.round(1))
print(f"{len(crisis)} crisis en {crisis.archivo.nunique()} archivos; duración mediana {crisis.duracion_s.median():.0f} s")
""")

py(r"""
fig, ax = plt.subplots(1, 2, figsize=(11, 3.5))
crisis.duracion_s.clip(upper=300).plot.hist(bins=40, ax=ax[0])
ax[0].set(xlabel="Duración de la crisis [s] (recortada en 300)", ylabel="Cantidad", title="Duración de las crisis")
crisis.groupby("caso").size().plot.bar(ax=ax[1])
ax[1].set(xlabel="Caso", ylabel="Crisis", title="Crisis por caso")
guardar(fig, "datos_crisis")
""")

md(r"""
**Nota sobre los metadatos.** `RECORDS-WITH-SEIZURES` lista `chb07_18.edf`, pero según `chb07-summary.txt` la crisis está en `chb07_19.edf` (segundo 13 688). Las etiquetas se toman siempre de los archivos de resumen, y para la descarga se usa la unión de ambas fuentes.

## 2. La señal EEG y su modelo matemático

Se modela el EEG de un canal como una superposición de oscilaciones en las bandas clásicas más un fondo aperiódico:

$$x(t) = \sum_{b \in \{\delta,\theta,\alpha,\beta,\gamma\}} A_b(t)\,\sin\!\big(2\pi f_b(t)\,t + \varphi_b(t)\big) + \eta(t), \qquad S_\eta(f) \propto \frac{1}{f^{\beta}}$$

Durante una crisis, poblaciones grandes de neuronas se **hipersincronizan**: aparece un ritmo dominante de gran amplitud (típicamente 3–8 Hz) que se propaga a varios canales. En términos espectrales, la potencia se **concentra** alrededor de pocas frecuencias y aumenta la **coherencia** entre canales.
""")

py(r"""
c0 = crisis.iloc[0]
x, fs, etiquetas = leer_edf(config.DIR_CRUDOS / c0.caso / c0.archivo, config.CANALES)
xf = filtrar(x, fs)
t0, t1 = c0.inicio_s - 30, c0.fin_s + 30
seg = xf[:, int(t0 * fs): int(t1 * fs)]
t = np.arange(seg.shape[1]) / fs + t0

fig, ax = plt.subplots(figsize=(11, 7))
sep = 4 * np.median(np.abs(seg))
for i in range(seg.shape[0]):
    ax.plot(t, seg[i] - i * sep, lw=0.4, color="k")
ax.axvspan(c0.inicio_s, c0.fin_s, color="tab:red", alpha=0.15, label="Crisis anotada")
ax.set_yticks(-np.arange(seg.shape[0]) * sep, etiquetas)
ax.set(xlabel="Tiempo [s]", title=f"{c0.archivo}: EEG filtrado (0,5–45 Hz, notch 60 Hz)")
ax.legend(loc="upper right")
guardar(fig, "eeg_crisis_multicanal")
""")

md(r"""
## 3. Transformada de Fourier

Para una señal muestreada $x[n]$, $n = 0,\dots,N-1$, la transformada discreta de Fourier es

$$X[k] = \sum_{n=0}^{N-1} x[n]\, e^{-i 2\pi k n / N}, \qquad f_k = \frac{k\, f_s}{N}.$$

**Teorema de Parseval (versión discreta):** $\displaystyle\sum_{n=0}^{N-1} |x[n]|^2 = \frac{1}{N}\sum_{k=0}^{N-1} |X[k]|^2$. La energía se conserva al cambiar de dominio, lo que justifica interpretar $|X[k]|^2$ como la *distribución de la energía en frecuencia*.

**Estimador de Welch:** se divide la ventana en $K$ segmentos solapados, se multiplica cada uno por una ventana de Hann $w[n]$ (para reducir la fuga espectral) y se promedian los periodogramas. Esto reduce la varianza del estimador aproximadamente en un factor $K$, a costa de resolución en frecuencia.
""")

py(r"""
v = seg[0, : 4 * int(fs)].astype(np.float64)
X = np.fft.fft(v)
print(f"Energía en el tiempo:     {np.sum(v**2):.6e}")
print(f"Energía en la frecuencia: {np.sum(np.abs(X)**2) / len(v):.6e}")
print(f"Diferencia relativa:      {abs(np.sum(v**2) - np.sum(np.abs(X)**2) / len(v)) / np.sum(v**2):.2e}")

f_ref, P_ref = signal.welch(v, fs=fs, nperseg=int(fs), noverlap=int(fs) // 2, window="hann", detrend="constant")
f_np, Xs, escala = espectros_segmentos(v[None, None, :].astype(np.float32), fs)
P_np = psd_welch(Xs, escala)[0, 0]
banda = (f_ref >= 0.5) & (f_ref <= 45)  # fuera de la banda filtrada la PSD es casi nula
print(f"Welch propio vs scipy.signal.welch (0,5–45 Hz): error relativo máx = "
      f"{np.max(np.abs(P_np - P_ref)[banda] / P_ref[banda]):.2e}")
""")

py(r"""
n4 = 4 * int(fs)
def ventana_en(t_s):
    i = int((t_s - t0) * fs)
    return seg[:, i: i + n4]

v_normal = ventana_en(c0.inicio_s - 25)
v_crisis = ventana_en(c0.inicio_s + min(10, (c0.fin_s - c0.inicio_s) / 2))
fig, ax = plt.subplots(1, 3, figsize=(13, 3.6))
for nombre, vv, color in (("Normal", v_normal, "tab:blue"), ("Crisis", v_crisis, "tab:red")):
    f, P = signal.welch(vv, fs=fs, nperseg=int(fs), noverlap=int(fs) // 2)
    ax[0].semilogy(f, P.mean(0), color=color, label=nombre)
    p = P[:, (f >= 0.5) & (f <= 45)].mean(0)
    ax[1].plot(f[(f >= 0.5) & (f <= 45)], p / p.sum(), color=color, label=nombre)
for a, (b0, b1) in config.BANDAS.items():
    ax[0].axvspan(b0, b1, alpha=0.06, color="gray")
    ax[0].text((b0 + b1) / 2, ax[0].get_ylim()[1], a, ha="center", va="top", fontsize=8)
ax[0].set(xlim=(0, 50), xlabel="Frecuencia [Hz]", ylabel="PSD [µV²/Hz]", title="PSD de Welch (media de canales)")
ax[1].set(xlim=(0, 45), xlabel="Frecuencia [Hz]", ylabel="$p_i$", title="Espectro normalizado (punto del simplex)")
ax[0].legend(); ax[1].legend()

f, tt, S = signal.spectrogram(seg[seg.std(1).argmax()], fs=fs, nperseg=int(2 * fs), noverlap=int(1.5 * fs))
ax[2].pcolormesh(tt + t0, f, 10 * np.log10(S + 1e-6), shading="auto", cmap="magma")
ax[2].axvline(c0.inicio_s, color="w", ls="--"); ax[2].axvline(c0.fin_s, color="w", ls="--")
ax[2].set(ylim=(0, 30), xlabel="Tiempo [s]", ylabel="Frecuencia [Hz]", title="Espectrograma (STFT)")
guardar(fig, "fourier_normal_vs_crisis")
""")

md(r"""
## 4. Entropía espectral en el simplex y multiplicadores de Lagrange

Al normalizar la PSD en $N$ frecuencias, $p_i = P(f_i)/\sum_j P(f_j)$, se obtiene un punto del **simplex de probabilidad**

$$\Delta^{N-1} = \Big\{ p \in \mathbb{R}^N : p_i \ge 0,\ \textstyle\sum_i p_i = 1 \Big\}.$$

La **entropía espectral** $H(p) = -\sum_i p_i \log p_i$ mide qué tan repartida está la potencia.

**Proposición.** $\max_{p \in \Delta^{N-1}} H(p) = \log N$, y se alcanza únicamente en $p^* = (1/N,\dots,1/N)$.

*Demostración.* Lagrangiano con la restricción de igualdad: $\mathcal{L}(p,\lambda) = -\sum_i p_i \log p_i + \lambda\big(\sum_i p_i - 1\big)$. La condición de primer orden es $\partial\mathcal{L}/\partial p_i = -\log p_i - 1 + \lambda = 0$, es decir $p_i = e^{\lambda - 1}$ para todo $i$: todas las componentes son iguales y, por la restricción, $p_i = 1/N$ y $\lambda^* = 1 - \log N$. Como $\nabla^2 H = -\operatorname{diag}(1/p_i) \prec 0$, $H$ es estrictamente cóncava sobre el conjunto convexo $\Delta^{N-1}$, así que este punto crítico es el **máximo global y único** (en un problema cóncavo todo óptimo local es global). Las restricciones $p_i \ge 0$ no están activas en el óptimo, por lo que sus multiplicadores KKT son nulos. $\blacksquare$

Se usa la entropía normalizada $\tilde H = H/\log N \in [0,1]$: vale 1 para ruido blanco y tiende a 0 cuando la potencia se concentra en una sola frecuencia. **Hipótesis H5:** $\tilde H$ es menor durante las crisis.
""")

py(r"""
from scipy.optimize import Bounds, LinearConstraint, minimize

N = 16
rng = np.random.default_rng(0)
log_seguro = lambda p: np.log(np.clip(p, 1e-300, None))  # el método puede evaluar fuera del simplex
print(" inicio (H)  →  H en el óptimo   log N     λ numérico   λ teórico = 1 - log N")
for _ in range(4):
    p0 = rng.dirichlet(np.full(N, 0.3)).clip(1e-6); p0 /= p0.sum()
    r = minimize(lambda p: np.sum(p * log_seguro(p)), p0, jac=lambda p: log_seguro(p) + 1, method="trust-constr",
                 constraints=[LinearConstraint(np.ones((1, N)), 1, 1)], bounds=Bounds(1e-10, 1))
    H0 = -np.sum(p0 * np.log(p0))
    # trust-constr minimiza -H, así que su multiplicador es -λ con la convención de arriba
    print(f"  {H0:6.3f}    →   {-r.fun:.6f}      {np.log(N):.6f}   {-r.v[0][0]:+.5f}     {1 - np.log(N):+.5f}")
""")

md(r"""
Desde cualquier punto inicial del simplex el optimizador converge al mismo $p^* = 1/N$ y al mismo multiplicador $\lambda^* = 1-\log N$: es el comportamiento esperado de un problema cóncavo con un único óptimo global.

## 5. Extracción de características y partición por sujeto

Por cada ventana de 4 s y cada uno de los 18 canales bipolares comunes a todos los registros: log-potencia y potencia relativa en 5 bandas, entropía espectral, frecuencia dominante, frecuencia de borde espectral al 90 %, *line length* y log-varianza (15 por canal), más la coherencia media entre canales en las 5 bandas: **275 características** por ventana. Una ventana se etiqueta como crisis si al menos el 50 % de su duración cae dentro de una crisis anotada.

La extracción guarda un archivo por registro y es reanudable.
""")

py(r"""
X_todo, meta = procesar_todo(config.DIR_CRUDOS, config.DIR_PROCESADOS)
X_todo, meta, columnas = cargar(config.DIR_PROCESADOS)
print(meta.groupby("y").size().rename({0: "normal", 1: "crisis"}).to_dict(),
      f"→ prevalencia {100 * meta.y.mean():.2f} %  |  {len(meta) * config.VENTANA_S / 3600:.0f} h de EEG")
""")

py(r"""
i_ent = [k for k, c in enumerate(columnas) if c.endswith("|entropia")]
H_ventana = X_todo[:, i_ent].mean(1)
H_c, H_n = H_ventana[meta.y == 1], H_ventana[meta.y == 0]
test_h5 = stats.mannwhitneyu(H_c, H_n, alternative="less")
efecto = 1 - 2 * test_h5.statistic / (len(H_c) * len(H_n))  # correlación biserial de rangos

por_sujeto = (pd.DataFrame({"sujeto": meta.sujeto, "y": meta.y, "H": H_ventana})
                .groupby(["sujeto", "y"]).H.median().unstack().dropna())
w = stats.wilcoxon(por_sujeto[1], por_sujeto[0], alternative="less")

print(f"H5 por ventana: mediana crisis = {np.median(H_c):.3f}, normal = {np.median(H_n):.3f}; "
      f"Mann-Whitney p = {test_h5.pvalue:.1e}, r biserial = {efecto:.2f}")
print(f"H5 por sujeto ({len(por_sujeto)} sujetos): {(por_sujeto[1] < por_sujeto[0]).sum()} con menor entropía en crisis; "
      f"Wilcoxon p = {w.pvalue:.1e}")

fig, ax = plt.subplots(1, 2, figsize=(11, 3.6))
ax[0].hist(H_n, bins=80, density=True, alpha=0.6, label="Normal")
ax[0].hist(H_c, bins=80, density=True, alpha=0.6, label="Crisis", color="tab:red")
ax[0].set(xlabel=r"Entropía espectral normalizada $\tilde H$", ylabel="Densidad", title="Distribución por ventana")
ax[0].legend()
for s, fila in por_sujeto.iterrows():
    ax[1].plot([0, 1], [fila[0], fila[1]], "o-", color="tab:red" if fila[1] < fila[0] else "tab:gray", alpha=0.7)
ax[1].set_xticks([0, 1], ["Normal", "Crisis"])
ax[1].set(ylabel=r"Mediana de $\tilde H$", title="Por sujeto")
guardar(fig, "h5_entropia")
""")

md(r"""
### Partición por sujeto

Para medir la capacidad de **generalizar a pacientes nuevos** (y no memorizar al paciente), ningún sujeto aparece en más de un conjunto. Es la forma de evitar el sobreajuste más importante en datos biomédicos: con una partición aleatoria de ventanas, ventanas contiguas del mismo registro (casi idénticas) caen en entrenamiento y prueba, y las métricas quedan infladas. `chb01` y `chb21` se tratan como un único sujeto.
""")

py(r"""
datos = preparar_datos(config.DIR_PROCESADOS)
for k, v in datos["particion"].items():
    yk = datos["y" + {"train": "tr", "val": "va", "test": "te"}[k]]
    print(f"{k:5s}: {len(v):2d} sujetos, {len(yk):7d} ventanas, {int(yk.sum()):5d} con crisis ({100 * yk.mean():.2f} %)  {v}")
""")

md(r"""
## 6. Caso convexo: regresión logística (H1)

$$f(w,b) = \frac1n\sum_{i=1}^n c_i\Big[\log\big(1+e^{z_i}\big) - y_i z_i\Big] + \frac{\mu}{2}\|w\|^2,\qquad z_i = w^\top x_i + b.$$

El Hessiano es $\nabla^2_w f = \frac1n X^\top D X + \mu I$ con $D = \operatorname{diag}\big(c_i\,\sigma(z_i)(1-\sigma(z_i))\big) \succeq 0$, así que para $\mu>0$ es definido positivo: **$f$ es estrictamente convexa y tiene un único mínimo global** $f^*$. Cualquier optimizador que converja tiene que llegar al mismo punto; lo que cambia es la velocidad. Se calcula $f^*$ con L-BFGS-B a tolerancia muy fina como referencia, y se mide la **brecha de optimalidad** $f(w_t) - f^*$.

Nelder-Mead busca el mínimo moviendo un **simplex** de $d+1$ vértices en $\mathbb{R}^d$ (reflexión, expansión, contracción y encogimiento) usando solo evaluaciones de $f$, sin gradiente. Como su costo crece rápido con la dimensión, se compara en un subespacio PCA de 10 dimensiones.
""")

py(r"""
Xs_tr, ys_tr = submuestra(datos["Xtr"].numpy().astype(np.float64), datos["ytr"].numpy(), n=20000 if MODO_RAPIDO else 60000)
theta_ref, f_ref = optimo_referencia(Xs_tr, ys_tr)
lrs_convexo = {"sgd": 0.1, "sgd_momentum": 0.02, "rmsprop": 1e-3, "adam": 3e-3, "adamw": 3e-3, "lbfgs": 1.0}
convexo = {o: correr_optimizador(o, lr, Xs_tr, ys_tr, epocas=EPOCAS * 5) for o, lr in lrs_convexo.items()}

fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
filas_convexo = []
for o, r in convexo.items():
    brecha = np.maximum(r["curva"] - f_ref, 1e-16)
    ax[0].semilogy(np.arange(1, len(brecha) + 1), brecha, label=NOMBRES_OPT[o])
    filas_convexo.append({"optimizador": NOMBRES_OPT[o], "brecha_final": brecha[-1],
                  "distancia_rel_a_w*": np.linalg.norm(r["theta"] - theta_ref) / np.linalg.norm(theta_ref),
                  "tiempo_s": r["tiempo"]})
ax[0].set(xlabel="Época (L-BFGS: paso con hasta 10 iteraciones)", ylabel=r"$f(w_t) - f^*$", title="Brecha de optimalidad")
ax[0].legend()

nm = nelder_mead(Xs_tr, ys_tr, k=10, max_eval=4000 if MODO_RAPIDO else 20000)
ax[1].semilogy(np.maximum(nm["historia"] - nm["f_ref"], 1e-16))
ax[1].set(xlabel="Evaluaciones de f", ylabel=r"$f - f^*$", title=f"Nelder-Mead en PCA-{nm['k']}")
guardar(fig, "convexo_brecha")
filas_convexo.append({"optimizador": f"Nelder-Mead (PCA-{nm['k']})", "brecha_final": nm["f_nm"] - nm["f_ref"],
              "distancia_rel_a_w*": np.nan, "tiempo_s": nm["tiempo"]})
display(pd.DataFrame(filas_convexo).set_index("optimizador"))
""")

md(r"""
Con métodos estocásticos (SGD, Adam, etc.) y tasa de aprendizaje constante la brecha no llega a cero: el ruido del minilote los deja oscilando en una vecindad de $w^*$ cuyo tamaño es proporcional a la tasa de aprendizaje. L-BFGS, determinista y con información de curvatura, alcanza $f^*$ a precisión de máquina. Es el resultado que predice la teoría para un problema fuertemente convexo.

## 7. Ajuste de la tasa de aprendizaje

Para que la comparación sea justa, cada optimizador usa **su** mejor tasa de aprendizaje, elegida con el mismo presupuesto (misma red ReLU, misma semilla, 3 o 4 valores por optimizador) según el AUC de validación.
""")

py(r"""
correr("ajuste_lr", configs_lr(), datos, EPOCAS)
lr_df = leer_resultados("ajuste_lr")
lr_df["auc_val"] = lr_df.historial.map(lambda h: h["mejor_auc_va"])
display(lr_df.pivot_table(index="optimizador", columns="lr", values="auc_val").round(4))
LRS = mejores_lr()
print("Tasas elegidas:", LRS)
""")

md(r"""
## 8. Optimizador × función de activación (H2 y H4)

Red de 2 capas ocultas (128 y 64 unidades, *dropout* 0,2), entropía cruzada ponderada por clase y *early stopping* sobre el AUC de validación. La capa de salida es siempre sigmoide; solo cambia la activación de las capas ocultas, con la inicialización que le corresponde (Xavier para sigmoide/tanh, He para la familia ReLU).

Combinaciones: 6 optimizadores × 5 activaciones × 5 semillas = 150 entrenamientos. Además se repite la regresión logística (sin capas ocultas) con las mismas semillas para contrastar la variabilidad del caso convexo con la del no convexo (**H2**).
""")

py(r"""
semillas = SEMILLAS[:N_SEMILLAS]
correr("logistica", [c for c in configs_logistica(LRS) if c["semilla"] in semillas], datos, EPOCAS)
correr("grilla", [c for c in configs_grilla(LRS) if c["semilla"] in semillas], datos, EPOCAS)
""")

py(r"""
def a_tabla(nombre):
    df = leer_resultados(nombre)
    df["auc_val"] = df.historial.map(lambda h: h["mejor_auc_va"])
    df["auc_test"] = df.get("test_np_AUC")
    df["epocas"] = df.historial.map(lambda h: h["mejor_epoca"])
    df["seg_epoca"] = df.historial.map(lambda h: h["tiempo"][-1] / len(h["tiempo"]))
    return df[df.semilla.isin(semillas)]

grilla = a_tabla("grilla")
logistica = a_tabla("logistica")

media = grilla.pivot_table(index="optimizador", columns="activacion", values="auc_test", aggfunc="mean")
desvio = grilla.pivot_table(index="optimizador", columns="activacion", values="auc_test", aggfunc="std")
media = media.loc[list(NOMBRES_OPT), list(NOMBRES_ACT)]
desvio = desvio.loc[list(NOMBRES_OPT), list(NOMBRES_ACT)]
anot = media.map(lambda v: f"{v:.3f}") + "\n±" + desvio.map(lambda v: f"{v:.3f}")

fig, ax = plt.subplots(figsize=(8, 4.5))
sns.heatmap(media.rename(index=NOMBRES_OPT, columns=NOMBRES_ACT), annot=anot.values, fmt="", cmap="viridis", ax=ax,
            cbar_kws={"label": "AUC en prueba"})
ax.set(xlabel="Activación", ylabel="Optimizador", title=f"AUC de prueba: media ± desvío sobre {len(semillas)} semillas")
guardar(fig, "grilla_heatmap_auc")
""")

py(r"""
fig, ax = plt.subplots(1, 2, figsize=(12, 3.8))
sns.pointplot(data=grilla.replace({"optimizador": NOMBRES_OPT, "activacion": NOMBRES_ACT}),
              x="activacion", y="auc_test", hue="optimizador", order=list(NOMBRES_ACT.values()),
              dodge=0.4, errorbar="sd", ax=ax[0])
ax[0].set(xlabel="Activación", ylabel="AUC en prueba", title="Gráfico de interacción")
ax[0].legend(fontsize=8, ncol=2)

var = pd.concat([
    logistica.groupby("optimizador").auc_test.std().rename("Logística (convexa)"),
    grilla[grilla.activacion == "relu"].groupby("optimizador").auc_test.std().rename("MLP ReLU (no convexa)"),
], axis=1).loc[list(NOMBRES_OPT)].rename(index=NOMBRES_OPT)
var.plot.bar(ax=ax[1])
ax[1].set(ylabel="Desvío del AUC entre semillas", title="H2: variabilidad por inicialización")
guardar(fig, "grilla_interaccion_variabilidad")
display(var.round(4))
""")

md(r"""
### Pruebas estadísticas

* **Friedman** (no paramétrica, medidas repetidas): ¿hay diferencias entre optimizadores? Cada bloque es una combinación (activación, semilla).
* **Wilcoxon de rangos con signo** por pares, con corrección de Holm para comparaciones múltiples.
* **ANOVA de dos factores** con interacción sobre el AUC: si la interacción optimizador × activación es significativa, el efecto de la activación depende del optimizador (**H4**).
* **H4, versión directa:** para cada optimizador, el rango del AUC medio entre activaciones; se espera que sea menor para Adam/RMSProp que para SGD.
""")

py(r"""
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multitest import multipletests

bloques = grilla.pivot_table(index=["activacion", "semilla"], columns="optimizador", values="auc_test").dropna()
fr = stats.friedmanchisquare(*[bloques[c] for c in bloques.columns])
print(f"Friedman entre optimizadores: chi2 = {fr.statistic:.2f}, p = {fr.pvalue:.2e}")
print("Rango medio (1 = mejor):", bloques.rank(axis=1, ascending=False).mean().sort_values().round(2).to_dict())

pares, pvals = [], []
cols = list(bloques.columns)
for i in range(len(cols)):
    for j in range(i + 1, len(cols)):
        d = bloques[cols[i]] - bloques[cols[j]]
        pares.append((cols[i], cols[j], d.median()))
        pvals.append(stats.wilcoxon(bloques[cols[i]], bloques[cols[j]]).pvalue if (d != 0).any() else 1.0)
holm = multipletests(pvals, method="holm")[1]
display(pd.DataFrame([(a, b, med, p, ph) for (a, b, med), p, ph in zip(pares, pvals, holm)],
                     columns=["A", "B", "mediana(A-B)", "p", "p Holm"]).sort_values("p Holm").round(4))

modelo_anova = ols("auc_test ~ C(optimizador) * C(activacion)", data=grilla.dropna(subset=["auc_test"])).fit()
display(anova_lm(modelo_anova, typ=2).round(4))

rango_act = media.max(axis=1) - media.min(axis=1)
print("H4: rango del AUC medio entre activaciones, por optimizador")
display(rango_act.rename(index=NOMBRES_OPT).sort_values().round(4).to_frame("rango"))
""")

md(r"""
## 9. Profundidad × activación: desvanecimiento del gradiente (H3)

Para una red con capas $h^{(l)} = \phi(z^{(l)})$, $z^{(l)} = W^{(l)} h^{(l-1)}$, la regla de la cadena da

$$\frac{\partial \mathcal{L}}{\partial h^{(l)}} = \Big(\prod_{k=l+1}^{L} W^{(k)\top} \operatorname{diag}\big(\phi'(z^{(k)})\big)\Big)\frac{\partial \mathcal{L}}{\partial h^{(L)}}.$$

Para la sigmoide $\phi'(z) = \sigma(z)(1-\sigma(z)) \le 1/4$, de modo que si $\|W^{(k)}\| \lesssim 1$ la norma del gradiente se atenúa en un factor del orden de $(1/4)^{L-l}$ al llegar a las primeras capas. Para ReLU $\phi'(z) \in \{0,1\}$ y el gradiente no se atenúa por la activación, pero las unidades con $z \le 0$ para todas las entradas quedan **muertas** (gradiente siempre cero).

Se entrenan redes de 2, 4 y 8 capas ocultas de 64 unidades, sin dropout, con SGD+Nesterov, y se registra la norma media del gradiente de cada capa.
""")

py(r"""
cfg_prof = [c for c in configs_profundidad(lr=LRS["sgd_momentum"]) if c["semilla"] in semillas[:3]]
correr("profundidad", cfg_prof, datos, EPOCAS)
prof = leer_resultados("profundidad")
prof = prof[prof.semilla.isin(semillas[:3])]
prof["d"] = prof.ocultas.map(len)
prof["auc_test"] = prof["test_np_AUC"]

fig, ax = plt.subplots(1, 3, figsize=(14, 3.8))
sns.pointplot(data=prof.replace({"activacion": NOMBRES_ACT}), x="d", y="auc_test", hue="activacion",
              errorbar="sd", ax=ax[0])
ax[0].set(xlabel="Capas ocultas", ylabel="AUC en prueba", title="Rendimiento según profundidad")

d_max = prof.d.max()
for a, g in prof[prof.d == d_max].groupby("activacion"):
    normas = np.mean([np.array(h["grad_capas"][0]) for h in g.historial], axis=0)
    ax[1].semilogy(np.arange(1, len(normas) + 1), normas, "o-", label=NOMBRES_ACT[a])
ax[1].set(xlabel="Capa (1 = entrada)", ylabel=r"$\|\nabla_{W^{(l)}}\mathcal{L}\|$ (1.ª época)",
          title=f"Gradiente por capa, {d_max} capas ocultas")
ax[1].legend()

inactivas = prof.assign(frac=prof.inactivas.map(np.mean)).groupby(["activacion", "d"]).frac.mean().unstack(0)
inactivas.rename(columns=NOMBRES_ACT).plot.bar(ax=ax[2])
ax[2].set(xlabel="Capas ocultas", ylabel="Fracción de unidades muertas", title="Unidades sin activación")
guardar(fig, "profundidad_gradientes")
""")

md(r"""
## 10. Evaluación final: ROC, AUC, matriz de confusión y umbral

Se toma la mejor combinación de la grilla según el AUC **de validación** (no de prueba, para no sesgar la estimación final) y se reentrena. Sobre el conjunto de prueba se reportan la curva ROC, el AUC, la curva precisión-recall (más informativa con clases tan desbalanceadas) y la matriz de confusión con dos criterios de umbral elegidos en validación:

1. **Youden:** $\max_t\ \mathrm{TPR}(t) - \mathrm{FPR}(t)$.
2. **Neyman-Pearson:** $\max_t\ \mathrm{TPR}(t)$ sujeto a $\mathrm{FPR}(t) \le \alpha$, con $\alpha$ equivalente a **1 falsa alarma por hora** ($\alpha = 1 \cdot 4 / 3600 \approx 0{,}0011$).

Para el segundo, el lagrangiano es $\mathcal{L}(t,\lambda) = \mathrm{TPR}(t) - \lambda\big(\mathrm{FPR}(t) - \alpha\big)$, $\lambda \ge 0$. Con la restricción activa, la condición de optimalidad es $\dfrac{d\,\mathrm{TPR}}{d\,\mathrm{FPR}} = \lambda$: **el multiplicador es la pendiente de la ROC en el punto de operación**. Por el lema de Neyman-Pearson, el test óptimo umbraliza el cociente de verosimilitudes $\Lambda(s) = p(s\mid\text{crisis})/p(s\mid\text{normal})$, y la pendiente de la ROC en un umbral es justamente ese cociente: $\lambda$ indica cuántas veces más probable es el puntaje bajo crisis que bajo normalidad en la frontera de decisión.
""")

py(r"""
mejor = grilla.groupby(["optimizador", "activacion"]).auc_val.mean().idxmax()
print("Mejor combinación según validación:", NOMBRES_OPT[mejor[0]], "+", NOMBRES_ACT[mejor[1]])
torch.manual_seed(0)
modelo = MLP(datos["Xtr"].shape[1], (128, 64), mejor[1])
hist = entrenar(modelo, mejor[0], LRS[mejor[0]], datos, epocas=EPOCAS, semilla=0)

y_va, p_va = datos["yva"].numpy(), predecir(modelo, datos["Xva"])
y_te, p_te = datos["yte"].numpy(), predecir(modelo, datos["Xte"])
alfa = alfa_por_falsas_alarmas(1.0)
np_ = umbral_neyman_pearson(y_va, p_va, alfa)
umbrales = {"Youden": umbral_youden(y_va, p_va), "Neyman-Pearson (1 FA/h)": np_["umbral"]}
tabla = pd.DataFrame({k: metricas(y_te, p_te, umb) for k, umb in umbrales.items()}).T
display(tabla[["umbral", "sensibilidad", "especificidad", "VPP", "F1", "falsas_alarmas_h", "AUC", "AP"]].round(4))
print(f"λ* (pendiente de la ROC de validación en el punto NP) = {np_['lambda']:.1f}")
""")

py(r"""
from sklearn.metrics import ConfusionMatrixDisplay, precision_recall_curve, roc_curve

fpr, tpr, _ = roc_curve(y_te, p_te)
fpr_v, tpr_v, _ = roc_curve(y_va, p_va)
casco = envolvente_concava(fpr_v, tpr_v)
fig, ax = plt.subplots(1, 3, figsize=(15, 4.2))
ax[0].plot(fpr, tpr, label=f"Prueba (AUC = {tabla.AUC.iloc[0]:.3f})")
ax[0].plot([0, 1], [0, 1], "k:", lw=0.8)
for (k, umb), marcador in zip(umbrales.items(), ("o", "s")):
    r = metricas(y_te, p_te, umb)
    ax[0].plot(1 - r["especificidad"], r["sensibilidad"], marcador, ms=8, label=k)
ax[0].set(xlabel="1 − especificidad (FPR)", ylabel="Sensibilidad (TPR)", title="Curva ROC")
ax[0].legend(loc="lower right")

ins = ax[0].inset_axes([0.45, 0.35, 0.5, 0.35])
ins.plot(fpr_v, tpr_v, lw=1, label="ROC validación")
ins.plot(casco[:, 0], casco[:, 1], "k--", lw=0.8, label="Envolvente cóncava")
ins.axvline(alfa, color="tab:red", lw=0.8)
x0 = np_["fpr"]; xs = np.linspace(0, 4 * alfa, 10)
ins.plot(xs, np_["tpr"] + np_["lambda"] * (xs - x0), color="tab:red", lw=0.8, ls=":")
ins.set(xlim=(0, 4 * alfa), ylim=(0, 1), title=r"Zoom: FPR $\leq 4\alpha$, pendiente $\lambda^*$", xticks=[0, alfa])
ins.set_xticklabels(["0", r"$\alpha$"]); ins.tick_params(labelsize=7); ins.title.set_size(8)

prec, rec, _ = precision_recall_curve(y_te, p_te)
ax[1].plot(rec, prec)
ax[1].axhline(y_te.mean(), color="k", ls=":", lw=0.8, label=f"Azar (prevalencia {100 * y_te.mean():.2f} %)")
ax[1].set(xlabel="Sensibilidad (recall)", ylabel="Precisión (VPP)", title=f"Precisión-recall (AP = {tabla.AP.iloc[0]:.3f})")
ax[1].legend()

ConfusionMatrixDisplay.from_predictions(y_te, (p_te >= umbrales["Neyman-Pearson (1 FA/h)"]).astype(int),
                                        display_labels=["Normal", "Crisis"], ax=ax[2], colorbar=False, values_format="d")
ax[2].set(title="Matriz de confusión (umbral NP)", xlabel="Predicción", ylabel="Real")
ax[2].grid(False)
guardar(fig, "evaluacion_final")
""")

md(r"""
### Métricas por sujeto y por crisis

En la práctica clínica interesa detectar **cada crisis** (un evento), no cada ventana. Una crisis se cuenta como detectada si al menos una de sus ventanas supera el umbral.
""")

py(r"""
mt = datos["meta"].iloc[datos["idx"]["test"]].reset_index(drop=True).assign(score=p_te)
u_np = umbrales["Neyman-Pearson (1 FA/h)"]
mt["alarma"] = mt.score >= u_np

det = []
for _, c in crisis[crisis.sujeto.isin(datos["particion"]["test"])].iterrows():
    v = mt[(mt.archivo == c.archivo) & (mt.inicio_s + config.VENTANA_S > c.inicio_s) & (mt.inicio_s < c.fin_s)]
    if len(v):
        primera = v[v.alarma].inicio_s.min()
        det.append({"sujeto": c.sujeto, "archivo": c.archivo, "duracion_s": c.duracion_s,
                    "detectada": v.alarma.any(), "latencia_s": max(primera - c.inicio_s, 0) if v.alarma.any() else np.nan})
det = pd.DataFrame(det)
por_suj = mt.groupby("sujeto").apply(lambda g: pd.Series({
    "horas": len(g) * config.VENTANA_S / 3600,
    "AUC": metricas(g.y, g.score, u_np)["AUC"] if g.y.nunique() > 1 else np.nan,
    "FA/h": (g.alarma & (g.y == 0)).sum() / ((g.y == 0).sum() * config.VENTANA_S / 3600),
}), include_groups=False).join(det.groupby("sujeto").agg(crisis=("detectada", "size"), detectadas=("detectada", "sum"),
                                                         latencia_mediana_s=("latencia_s", "median")))
display(por_suj.round(3))
print(f"Sensibilidad por evento: {det.detectada.mean():.3f} ({det.detectada.sum()}/{len(det)} crisis), "
      f"latencia mediana {det.latencia_s.median():.0f} s")
""")

md(r"""
## 11. Sobreajuste y resumen de hipótesis

Curvas de pérdida de entrenamiento y validación de la mejor combinación. Como la partición es por sujeto, la brecha entre ambas mide cuánto del aprendizaje es específico de los pacientes de entrenamiento. El *early stopping* se queda con la época de mejor AUC de validación.
""")

py(r"""
fig, ax = plt.subplots(1, 2, figsize=(11, 3.6))
ep = np.arange(1, len(hist["perdida_tr"]) + 1)
ax[0].plot(ep, hist["perdida_tr"], label="Entrenamiento")
ax[0].plot(ep, hist["perdida_va"], label="Validación (otros sujetos)")
ax[0].axvline(hist["mejor_epoca"], color="k", ls=":", label="Early stopping")
ax[0].set(xlabel="Época", ylabel="BCE ponderada", title="Curvas de aprendizaje")
ax[0].legend()
ax[1].plot(ep, hist["auc_va"])
ax[1].axvline(hist["mejor_epoca"], color="k", ls=":")
ax[1].set(xlabel="Época", ylabel="AUC validación", title="AUC de validación por época")
guardar(fig, "sobreajuste_curvas")

part_aleatoria = np.random.default_rng(0).permutation(len(datos["meta"]))
print("Partición por sujeto vs. aleatoria (misma red, misma semilla):")
from sklearn.preprocessing import StandardScaler
n = len(part_aleatoria); i_tr, i_va, i_te = np.split(part_aleatoria, [int(0.6 * n), int(0.8 * n)])
Xc = np.vstack([datos["escalador"].inverse_transform(datos[k].numpy()) for k in ("Xtr", "Xva", "Xte")])
yc = np.concatenate([datos[k].numpy() for k in ("ytr", "yva", "yte")])
orden = np.concatenate([datos["idx"][k] for k in ("train", "val", "test")])
Xa, ya = np.empty_like(Xc), np.empty_like(yc)
Xa[orden], ya[orden] = Xc, yc
esc = StandardScaler().fit(Xa[i_tr])
t = lambda a: torch.tensor(a, dtype=torch.float32)
da = {"Xtr": t(esc.transform(Xa[i_tr])), "ytr": t(ya[i_tr]), "Xva": t(esc.transform(Xa[i_va])), "yva": t(ya[i_va])}
torch.manual_seed(0)
m_al = MLP(Xa.shape[1], (128, 64), mejor[1])
entrenar(m_al, mejor[0], LRS[mejor[0]], da, epocas=EPOCAS, semilla=0)
auc_al = metricas(ya[i_te], predecir(m_al, t(esc.transform(Xa[i_te]))), 0.5)["AUC"]
print(f"  AUC prueba, partición por sujeto: {tabla.AUC.iloc[0]:.4f}")
print(f"  AUC prueba, partición aleatoria:  {auc_al:.4f}   ← optimista: ventanas del mismo paciente en ambos lados")
""")

py(r"""
p_h2 = stats.wilcoxon(var.iloc[:, 0], var.iloc[:, 1], alternative="less").pvalue if len(var.dropna()) > 5 else np.nan
auc_d = prof.groupby(["activacion", "d"]).auc_test.mean().unstack()
resumen_h = pd.DataFrame([
    ("H1", "Caso convexo: todos los métodos se acercan al mismo óptimo global",
     f"brecha final L-BFGS = {filas_convexo[-2]['brecha_final']:.1e}; Nelder-Mead = {filas_convexo[-1]['brecha_final']:.1e}"),
    ("H2", "Mayor variabilidad entre semillas en el caso no convexo",
     f"desvío medio logística = {var.iloc[:, 0].mean():.4f} vs MLP = {var.iloc[:, 1].mean():.4f} (Wilcoxon p = {p_h2:.3f})"),
    ("H3", "Sigmoide/tanh se degradan con la profundidad",
     "; ".join(f"{NOMBRES_ACT[a]}: {auc_d.loc[a].iloc[0]:.3f}→{auc_d.loc[a].iloc[-1]:.3f}" for a in auc_d.index)),
    ("H4", "Adaptativos menos sensibles a la activación que SGD",
     "; ".join(f"{NOMBRES_OPT[o]}: {rango_act[o]:.3f}" for o in rango_act.index)),
    ("H5", "Menor entropía espectral en crisis",
     f"mediana {np.median(H_c):.3f} vs {np.median(H_n):.3f}; p = {test_h5.pvalue:.1e}; {(por_sujeto[1] < por_sujeto[0]).sum()}/{len(por_sujeto)} sujetos"),
], columns=["Hipótesis", "Enunciado", "Evidencia"]).set_index("Hipótesis")
with pd.option_context("display.max_colwidth", None):
    display(resumen_h)
resumen_h.to_csv(config.DIR_RESULTADOS / "resumen_hipotesis.csv")
""")

nb = nbf.v4.new_notebook(cells=celdas, metadata={
    "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
    "language_info": {"name": "python"},
    "colab": {"provenance": []},
})
salida = RAIZ / "notebooks" / "TP_Final_Crisis_EEG.ipynb"
salida.parent.mkdir(parents=True, exist_ok=True)
nbf.write(nb, salida)
print("Notebook generado:", salida)

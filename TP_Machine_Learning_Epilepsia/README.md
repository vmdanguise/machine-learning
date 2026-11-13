# Detección de crisis epilépticas en EEG

Trabajo final individual de Machine Learning. Maestría en Inteligencia Artificial, Universidad de Palermo.

Cubre la fundamentación matemática (transformada de Fourier, convexidad, óptimo local y global, multiplicadores
de Lagrange, simplex, Neyman-Pearson), modelos convexos (regresión logística, SVM), una red convolucional y una
comparativa de seis optimizadores (SGD, Momentum, Nesterov, RMSprop, Adam, AdamW) sobre las bases **Bonn** y
**CHB-MIT**.

## Estructura

```
datos/                 datos crudos y procesados (no se incluyen; ver "Datos")
notebooks/
  src/*.py             fuente de cada notebook (formato jupytext "percent")
  etapa1_bonn_fourier.ipynb         Fourier, Welch, filtrado y bandas (Bonn)
  etapa2_chbmit.ipynb               análisis exploratorio de CHB-MIT
  etapa3_modelos_clasicos.ipynb     logística, SVM, optimalidad, KKT, Neyman-Pearson
  etapa4_cnn_optimizadores.ipynb    CNN y comparativa de optimizadores
scripts/
  descargar_chbmit.py   descarga desde PhysioNet con verificación SHA256
  preprocesar_chbmit.py filtrado, ventanas de 4 s, espectrogramas y potencia por banda
  metricas.py           métricas por ventana y por evento, umbral de Neyman-Pearson
  entrenar_cnn.py       entrenamiento de la CNN (fases busqueda, semillas, posthoc)
resultados/etapaN/     figuras, tablas CSV y metadatos de cada etapa
informe/               informe en LaTeX (para Overleaf)
```

## Datos

Solo fuentes oficiales:

- **Bonn**: Andrzejak et al. (2001), *Phys. Rev. E* 64, 061907. Cinco sets (Z, O, N, F, S) de 100 segmentos.
  Se bajan a mano de la página del grupo
  (https://www.ukbonn.de/epileptologie/arbeitsgruppen/ag-lehnertz-neurophysik/downloads/) y se descomprimen en
  `datos/bonn/{Z,O,N,F,S}`.
- **CHB-MIT** (PhysioNet, licencia ODC-By 1.0): pacientes chb01, chb02, chb03, chb05, chb08 y chb10;
  son 200 archivos EDF y unos 8,8 GB. Shoeb (2009); Goldberger et al. (2000); Guttag (2010),
  doi:10.13026/C2K01R.

## Reproducir

En Windows con PowerShell, desde la carpeta del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python -m ipykernel install --user --name tp-epilepsia

.\.venv\Scripts\python scripts\descargar_chbmit.py datos\chbmit chb01 chb02 chb03 chb05 chb08 chb10   # unos 8,8 GB
.\.venv\Scripts\python scripts\preprocesar_chbmit.py datos\chbmit datos\chbmit_proc 4                 # 4 procesos

# Notebooks: generar el .ipynb desde la fuente y ejecutarlo (desde notebooks\)
.\.venv\Scripts\jupytext --to ipynb src\etapa1_bonn_fourier.py -o etapa1_bonn_fourier.ipynb
.\.venv\Scripts\jupyter execute --inplace --kernel_name=tp-epilepsia etapa1_bonn_fourier.ipynb
# ... igual con etapa2 y etapa3

# CNN (en CPU, unos 92 s por corrida)
.\.venv\Scripts\python scripts\entrenar_cnn.py . busqueda   # 18 corridas
.\.venv\Scripts\python scripts\entrenar_cnn.py . semillas   # 24 corridas más
.\.venv\Scripts\python scripts\entrenar_cnn.py . posthoc    # sensibilidad a la tasa
# después, ejecutar el notebook de la etapa 4
```

`entrenar_cnn.py` saltea las corridas que ya tienen resultado guardado, así que se puede cortar y reanudar.

Entorno usado: Python 3.12.10, CPU AMD Ryzen 7 5700U, 21,8 GB de RAM, sin GPU.

## Informe

En `informe/`, `main.tex` incluye un archivo por capítulo (`capitulos/`) y `referencias.bib`. Las figuras ya
están copiadas en `informe/figuras/etapaN/`. Para compilarlo en Overleaf hay que subir la carpeta `informe/`
comprimida en un zip (New Project → Upload Project) y elegir el compilador **pdfLaTeX**. La bibliografía usa
biblatex con **biber**, que Overleaf ejecuta solo.

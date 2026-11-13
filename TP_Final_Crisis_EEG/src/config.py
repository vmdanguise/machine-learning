import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DIR_DATOS = RAIZ / "data"
# En Colab conviene bajar los EDF al disco local (/content) y guardar en Drive
# solo las características: se redefinen con estas variables de entorno.
DIR_CRUDOS = Path(os.environ.get("TP_DIR_CRUDOS", DIR_DATOS / "chbmit"))
DIR_PROCESADOS = Path(os.environ.get("TP_DIR_PROCESADOS", DIR_DATOS / "procesados"))
DIR_RESULTADOS = Path(os.environ.get("TP_DIR_RESULTADOS", RAIZ / "resultados"))
# Las figuras van directo a la carpeta del documento LaTeX (Overleaf y Word las toman de ahí).
DIR_FIGURAS = RAIZ / "documentos" / "latex" / "figuras"

# El espejo S3 de PhysioNet suele ser más rápido; physionet.org queda como respaldo.
URLS_BASE = (
    "https://physionet-open.s3.amazonaws.com/chbmit/1.0.0/",
    "https://physionet.org/files/chbmit/1.0.0/",
)

CASOS = [f"chb{i:02d}" for i in range(1, 25)]

# chb21 es la misma paciente que chb01, registrada 1,5 años después:
# deben quedar siempre en la misma partición para no filtrar información.
SUJETO_POR_CASO = {caso: caso for caso in CASOS} | {"chb21": "chb01"}

FS = 256

# Montaje bipolar "doble banana" presente en todos los registros.
CANALES = [
    "FP1-F7", "F7-T7", "T7-P7", "P7-O1",
    "FP1-F3", "F3-C3", "C3-P3", "P3-O1",
    "FP2-F4", "F4-C4", "C4-P4", "P4-O2",
    "FP2-F8", "F8-T8", "T8-P8", "P8-O2",
    "FZ-CZ", "CZ-PZ",
]

BANDAS = {
    "delta": (0.5, 4.0),
    "theta": (4.0, 8.0),
    "alfa": (8.0, 13.0),
    "beta": (13.0, 30.0),
    "gamma": (30.0, 45.0),
}

FILTRO_PASABANDA = (0.5, 45.0)
FRECUENCIA_RED = 60.0  # registros de Boston (EE. UU.)
VENTANA_S = 4

SEMILLA = 42

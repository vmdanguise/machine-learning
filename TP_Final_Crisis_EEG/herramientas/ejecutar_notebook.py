"""Ejecuta el notebook completo y guarda una copia con las salidas.

    python herramientas/ejecutar_notebook.py            # MODO_RAPIDO = True
    python herramientas/ejecutar_notebook.py --completo # MODO_RAPIDO = False
"""

import argparse
import time
from pathlib import Path

import nbformat
from nbclient import NotebookClient

RAIZ = Path(__file__).resolve().parents[1]

p = argparse.ArgumentParser()
p.add_argument("--completo", action="store_true")
a = p.parse_args()

nb = nbformat.read(RAIZ / "notebooks" / "TP_Final_Crisis_EEG.ipynb", as_version=4)
primera = next(c for c in nb.cells if c.cell_type == "code")
primera.source = primera.source.replace("MODO_RAPIDO = True", f"MODO_RAPIDO = {not a.completo}")

salida = RAIZ / "resultados" / ("TP_Final_Crisis_EEG_ejecutado.ipynb" if a.completo else "rapido/TP_Final_Crisis_EEG_ejecutado.ipynb")
salida.parent.mkdir(parents=True, exist_ok=True)
t0 = time.time()
try:
    NotebookClient(nb, timeout=None, kernel_name="python3",
                   resources={"metadata": {"path": str(RAIZ / "notebooks")}}).execute()
finally:
    nbformat.write(nb, salida)
    print(f"Guardado en {salida} ({(time.time() - t0) / 60:.1f} min)")

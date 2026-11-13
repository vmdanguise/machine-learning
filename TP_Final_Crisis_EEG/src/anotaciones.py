"""Lectura de las anotaciones de crisis de los archivos chbXX-summary.txt."""

import re
from pathlib import Path

import pandas as pd

from .config import CASOS, DIR_CRUDOS, SUJETO_POR_CASO

_RE_CANAL = re.compile(r"^Channel\s+\d+:\s*(.+)$")
_RE_INICIO = re.compile(r"^Seizure(?:\s+\d+)?\s+Start Time:\s*(\d+)\s*seconds?", re.I)
_RE_FIN = re.compile(r"^Seizure(?:\s+\d+)?\s+End Time:\s*(\d+)\s*seconds?", re.I)


def leer_resumen(ruta):
    """Devuelve una lista de dicts, uno por archivo EDF del resumen."""
    registros, canales, actual = [], [], None
    for linea in Path(ruta).read_text(errors="replace").splitlines():
        linea = linea.strip()
        if linea.startswith("Channels"):
            canales = []
        elif m := _RE_CANAL.match(linea):
            canales.append(m.group(1).strip())
        elif linea.startswith("File Name:"):
            actual = {
                "archivo": linea.split(":", 1)[1].strip(),
                "hora_inicio": None,
                "hora_fin": None,
                "n_crisis": 0,
                "crisis": [],
                "canales": list(canales),
            }
            registros.append(actual)
        elif actual is None:
            continue
        elif linea.startswith("File Start Time:"):
            actual["hora_inicio"] = linea.split(":", 1)[1].strip()
        elif linea.startswith("File End Time:"):
            actual["hora_fin"] = linea.split(":", 1)[1].strip()
        elif linea.startswith("Number of Seizures in File:"):
            actual["n_crisis"] = int(linea.split(":", 1)[1])
        elif m := _RE_INICIO.match(linea):
            actual["crisis"].append([int(m.group(1)), None])
        elif m := _RE_FIN.match(linea):
            actual["crisis"][-1][1] = int(m.group(1))

    for r in registros:
        if r["n_crisis"] != len(r["crisis"]) or any(fin is None for _, fin in r["crisis"]):
            raise ValueError(f"Anotaciones inconsistentes en {r['archivo']} ({ruta})")
    return registros


def _resumenes(dir_crudos, casos):
    for caso in casos:
        ruta = Path(dir_crudos) / caso / f"{caso}-summary.txt"
        if ruta.exists():
            yield caso, leer_resumen(ruta)


def tabla_archivos(dir_crudos=DIR_CRUDOS, casos=CASOS):
    filas = [
        {
            "caso": caso,
            "sujeto": SUJETO_POR_CASO[caso],
            "archivo": r["archivo"],
            "hora_inicio": r["hora_inicio"],
            "hora_fin": r["hora_fin"],
            "n_crisis": r["n_crisis"],
            "n_canales": len(r["canales"]),
            "descargado": (Path(dir_crudos) / caso / r["archivo"]).exists(),
        }
        for caso, registros in _resumenes(dir_crudos, casos)
        for r in registros
    ]
    return pd.DataFrame(filas)


def tabla_crisis(dir_crudos=DIR_CRUDOS, casos=CASOS):
    filas = [
        {
            "caso": caso,
            "sujeto": SUJETO_POR_CASO[caso],
            "archivo": r["archivo"],
            "inicio_s": ini,
            "fin_s": fin,
            "duracion_s": fin - ini,
        }
        for caso, registros in _resumenes(dir_crudos, casos)
        for r in registros
        for ini, fin in r["crisis"]
    ]
    return pd.DataFrame(filas)

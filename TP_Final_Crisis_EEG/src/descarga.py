"""Descarga selectiva de CHB-MIT Scalp EEG Database (PhysioNet).

Baja los metadatos, todos los registros con crisis y una muestra aleatoria
reproducible de registros sin crisis por caso. Verifica cada archivo con
SHA-256 y saltea los que ya están descargados, así que se puede cortar y
volver a correr.

Uso (desde la raíz del proyecto):
    python -m src.descarga --solo-metadatos
    python -m src.descarga --simular
    python -m src.descarga --sin-crisis 3 --hilos 4
"""

import argparse
import hashlib
import random
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from tqdm import tqdm

from .config import CASOS, DIR_CRUDOS, SEMILLA, URLS_BASE

METADATOS = ["RECORDS", "RECORDS-WITH-SEIZURES", "SHA256SUMS.txt", "SUBJECT-INFO"]
_local = threading.local()


def _sesion():
    if not hasattr(_local, "sesion"):
        _local.sesion = requests.Session()
    return _local.sesion


def _pedir(ruta, metodo="GET", stream=False):
    ultimo_error = None
    for base in URLS_BASE:
        try:
            r = _sesion().request(metodo, base + ruta, stream=stream, timeout=60, allow_redirects=True)
            if r.status_code == 200:
                return r
            ultimo_error = f"HTTP {r.status_code} en {base + ruta}"
        except requests.RequestException as e:
            ultimo_error = f"{type(e).__name__} en {base + ruta}: {e}"
    raise RuntimeError(ultimo_error)


def descargar_metadatos(destino=DIR_CRUDOS, casos=CASOS):
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    rutas = METADATOS + [f"{c}/{c}-summary.txt" for c in casos]
    for ruta in tqdm(rutas, desc="Metadatos"):
        archivo = destino / ruta
        if archivo.exists():
            continue
        archivo.parent.mkdir(parents=True, exist_ok=True)
        archivo.write_bytes(_pedir(ruta).content)


def _leer_lista(destino, nombre):
    return [l.strip() for l in (Path(destino) / nombre).read_text().splitlines() if l.strip()]


def leer_sha256(destino=DIR_CRUDOS):
    sumas = {}
    for linea in _leer_lista(destino, "SHA256SUMS.txt"):
        suma, ruta = linea.split(maxsplit=1)
        sumas[ruta] = suma
    return sumas


def seleccionar_archivos(destino=DIR_CRUDOS, casos=CASOS, n_sin_crisis=3, semilla=SEMILLA):
    """Todos los registros con crisis más n_sin_crisis registros sin crisis por caso.

    RECORDS-WITH-SEIZURES tiene errores (p. ej. lista chb07_18 cuando la crisis
    está en chb07_19 según el resumen), así que se usa la unión con lo que dicen
    los chbXX-summary.txt, que son la fuente de las etiquetas.
    """
    from .anotaciones import tabla_archivos

    todos = _leer_lista(destino, "RECORDS")
    con_crisis = set(_leer_lista(destino, "RECORDS-WITH-SEIZURES"))
    resumen = tabla_archivos(destino, casos)
    con_crisis |= set((resumen.caso + "/" + resumen.archivo)[resumen.n_crisis > 0])
    rng = random.Random(semilla)
    seleccion = []
    for caso in casos:
        del_caso = sorted(r for r in todos if r.startswith(caso + "/"))
        positivos = [r for r in del_caso if r in con_crisis]
        negativos = [r for r in del_caso if r not in con_crisis]
        seleccion += positivos + sorted(rng.sample(negativos, min(n_sin_crisis, len(negativos))))
    return seleccion


def _sha256(archivo):
    h = hashlib.sha256()
    with open(archivo, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def tamanio_remoto(ruta):
    return int(_pedir(ruta, metodo="HEAD").headers.get("Content-Length", 0))


def descargar_archivo(ruta, destino=DIR_CRUDOS, sha_esperado=None, reintentos=3):
    archivo = Path(destino) / ruta
    if archivo.exists() and (sha_esperado is None or _sha256(archivo) == sha_esperado):
        return "existente"
    archivo.parent.mkdir(parents=True, exist_ok=True)
    parcial = archivo.with_name(archivo.name + ".part")
    for intento in range(1, reintentos + 1):
        try:
            with _pedir(ruta, stream=True) as r, open(parcial, "wb") as f:
                for bloque in r.iter_content(1 << 20):
                    f.write(bloque)
            if sha_esperado and _sha256(parcial) != sha_esperado:
                raise RuntimeError(f"SHA-256 no coincide en {ruta}")
            parcial.replace(archivo)
            return "descargado"
        except Exception:
            parcial.unlink(missing_ok=True)
            if intento == reintentos:
                raise
    return None


def descargar(archivos, destino=DIR_CRUDOS, hilos=4):
    sumas = leer_sha256(destino)
    errores = []
    with ThreadPoolExecutor(hilos) as ex, tqdm(total=len(archivos), desc="EDF", unit="arch") as barra:
        futuros = {ex.submit(descargar_archivo, r, destino, sumas.get(r)): r for r in archivos}
        for futuro in as_completed(futuros):
            try:
                futuro.result()
            except Exception as e:
                errores.append((futuros[futuro], str(e)))
            barra.update()
    return errores


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--destino", type=Path, default=DIR_CRUDOS)
    p.add_argument("--casos", nargs="+", default=CASOS, help="ej.: chb01 chb02")
    p.add_argument("--sin-crisis", type=int, default=3, help="registros sin crisis por caso")
    p.add_argument("--semilla", type=int, default=SEMILLA)
    p.add_argument("--hilos", type=int, default=4)
    p.add_argument("--solo-metadatos", action="store_true")
    p.add_argument("--simular", action="store_true", help="muestra qué bajaría y cuánto pesa, sin bajar EDF")
    a = p.parse_args()

    descargar_metadatos(a.destino, a.casos)
    if a.solo_metadatos:
        return

    archivos = seleccionar_archivos(a.destino, a.casos, a.sin_crisis, a.semilla)
    pendientes = [r for r in archivos if not (a.destino / r).exists()]

    with ThreadPoolExecutor(8) as ex:
        total = sum(ex.map(tamanio_remoto, pendientes))
    libre = shutil.disk_usage(a.destino).free
    print(f"Seleccionados: {len(archivos)} archivos ({len(archivos) - len(pendientes)} ya descargados)")
    print(f"A descargar: {total / 1e9:.2f} GB  |  libre en disco: {libre / 1e9:.1f} GB")
    if a.simular:
        return
    if total > libre:
        raise SystemExit("No hay espacio suficiente en el disco.")

    errores = descargar(archivos, a.destino, a.hilos)
    if errores:
        print(f"\n{len(errores)} archivos fallaron (volvé a correr el comando para reintentar):")
        for ruta, msg in errores:
            print(f"  {ruta}: {msg}")


if __name__ == "__main__":
    main()

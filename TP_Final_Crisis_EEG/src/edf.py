"""Lector mínimo de archivos EDF (European Data Format) con numpy.

Alcanza para CHB-MIT: todas las señales tienen la misma frecuencia de
muestreo y se guardan como enteros de 16 bits. Evita depender de mne o
pyedflib, que no siempre están disponibles en Colab o en Windows.
"""

from pathlib import Path

import numpy as np


def _campos(bloque, n, ancho):
    return [bloque[i * ancho:(i + 1) * ancho].decode("latin-1").strip() for i in range(n)]


def leer_encabezado(ruta):
    with open(ruta, "rb") as f:
        general = f.read(256)
        ns = int(general[252:256])
        senales = f.read(ns * 256)

    def bloque(desde, ancho):
        return senales[desde * ns: desde * ns + ancho * ns], ancho

    desplazamientos = [("etiqueta", 16), ("transductor", 80), ("unidad", 8), ("fis_min", 8),
                       ("fis_max", 8), ("dig_min", 8), ("dig_max", 8), ("prefiltro", 80),
                       ("muestras_por_registro", 8), ("reservado", 32)]
    campos, pos = {}, 0
    for nombre, ancho in desplazamientos:
        campos[nombre] = _campos(senales[pos: pos + ns * ancho], ns, ancho)
        pos += ns * ancho

    return {
        "bytes_encabezado": int(general[184:192]),
        "n_registros": int(general[236:244]),
        "duracion_registro": float(general[244:252]),
        "ns": ns,
        "etiquetas": campos["etiqueta"],
        "fis_min": np.array(campos["fis_min"], float),
        "fis_max": np.array(campos["fis_max"], float),
        "dig_min": np.array(campos["dig_min"], float),
        "dig_max": np.array(campos["dig_max"], float),
        "muestras_por_registro": np.array(campos["muestras_por_registro"], int),
    }


def _normalizar(etiqueta):
    e = etiqueta.upper().replace(" ", "")
    # Algunos archivos repiten un canal como "T8-P8-0" / "T8-P8-1".
    for sufijo in ("-0", "-1"):
        if e.endswith(sufijo) and e.count("-") == 2:
            e = e[: -len(sufijo)]
    # chb12_28 y chb12_29 rotulan el electrodo O1 como "01" (cero-uno).
    return "-".join("O1" if p == "01" else p for p in e.split("-"))


def indices_canales(etiquetas, canales):
    """Índice de la primera aparición de cada canal pedido, o None si falta alguno."""
    normalizadas = [_normalizar(e) for e in etiquetas]
    indices = []
    for canal in canales:
        if canal not in normalizadas:
            return None
        indices.append(normalizadas.index(canal))
    return indices


def indices_referenciales(etiquetas, canales):
    """Para registros con referencia común (p. ej. "F7-CS2" o "F7"): índices de los
    electrodos (a, b) de cada canal bipolar "a-b", que se obtiene como (a-ref) - (b-ref)."""
    electrodos = {}
    for i, e in enumerate(etiquetas):
        n = _normalizar(e)
        partes = n.split("-")
        if len(partes) == 1 or (len(partes) == 2 and partes[1].startswith("CS")):
            electrodos.setdefault(partes[0], i)
    pares = []
    for canal in canales:
        a, b = canal.split("-")
        if a not in electrodos or b not in electrodos:
            return None
        pares.append((electrodos[a], electrodos[b]))
    return pares


def _leer_crudo(ruta, enc, sel):
    spr = enc["muestras_por_registro"][0]
    crudo = np.fromfile(ruta, dtype="<i2", offset=enc["bytes_encabezado"])
    n_reg = crudo.size // (enc["ns"] * spr)
    if enc["n_registros"] > 0:
        n_reg = min(n_reg, enc["n_registros"])
    crudo = crudo[: n_reg * enc["ns"] * spr].reshape(n_reg, enc["ns"], spr)
    datos = crudo[:, sel, :].transpose(1, 0, 2).reshape(len(sel), -1).astype(np.float32)

    # Solo se calibran los canales pedidos: los separadores "-" tienen dig_max == dig_min.
    sel = np.asarray(sel)
    ganancia = (enc["fis_max"][sel] - enc["fis_min"][sel]) / (enc["dig_max"][sel] - enc["dig_min"][sel])
    desplazamiento = enc["fis_min"][sel] - ganancia * enc["dig_min"][sel]
    return datos * ganancia[:, None].astype(np.float32) + desplazamiento[:, None].astype(np.float32)


def leer_edf(ruta, canales=None):
    """Devuelve (señales en µV con forma (canales, muestras), fs, etiquetas).

    Si se pasan `canales` (bipolares "a-b"), devuelve solo esos y en ese orden.
    Si el archivo usa referencia común, los reconstruye por diferencia. Si no se
    pueden obtener todos, devuelve (None, fs, etiquetas).
    """
    enc = leer_encabezado(ruta)
    spr = enc["muestras_por_registro"]
    if len(set(spr)) != 1:
        raise ValueError(f"{Path(ruta).name}: frecuencias de muestreo distintas por canal")
    fs = spr[0] / enc["duracion_registro"]

    if canales is None:
        return _leer_crudo(ruta, enc, list(range(enc["ns"]))), fs, enc["etiquetas"]

    sel = indices_canales(enc["etiquetas"], canales)
    if sel is not None:
        return _leer_crudo(ruta, enc, sel), fs, [enc["etiquetas"][i] for i in sel]

    pares = indices_referenciales(enc["etiquetas"], canales)
    if pares is None:
        return None, fs, enc["etiquetas"]
    usados = sorted({i for par in pares for i in par})
    datos = _leer_crudo(ruta, enc, usados)
    fila = {i: k for k, i in enumerate(usados)}
    bipolar = np.stack([datos[fila[a]] - datos[fila[b]] for a, b in pares])
    return bipolar, fs, list(canales)

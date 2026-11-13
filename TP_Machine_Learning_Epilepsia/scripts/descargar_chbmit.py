"""Descarga un subconjunto de CHB-MIT desde PhysioNet (fuente oficial) y verifica SHA256.

Uso:
    python descargar_chbmit.py DESTINO chb01 chb02 ...

Funciona igual en Windows y en Colab (solo usa la libreria estandar).
Si un archivo ya existe con el hash correcto, no se vuelve a bajar.
"""
import hashlib
import sys
import time
import urllib.request
from pathlib import Path

BASE = "https://physionet.org/files/chbmit/1.0.0/"
EXTRAS = ["RECORDS", "RECORDS-WITH-SEIZURES", "SUBJECT-INFO", "SHA256SUMS.txt"]


def bajar(url, destino, intentos=4):
    destino.parent.mkdir(parents=True, exist_ok=True)
    tmp = destino.with_suffix(destino.suffix + ".part")
    for i in range(intentos):
        try:
            with urllib.request.urlopen(url, timeout=120) as r, open(tmp, "wb") as f:
                while True:
                    bloque = r.read(1 << 20)
                    if not bloque:
                        break
                    f.write(bloque)
            tmp.replace(destino)
            return
        except Exception as e:  # reintento con espera creciente
            print(f"  reintento {i + 1} {url}: {e}", flush=True)
            time.sleep(5 * (i + 1))
    raise RuntimeError(f"no se pudo bajar {url}")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def main():
    destino = Path(sys.argv[1])
    pacientes = sys.argv[2:]
    for nombre in EXTRAS:
        if not (destino / nombre).exists():
            bajar(BASE + nombre, destino / nombre)

    hashes = {}
    for linea in (destino / "SHA256SUMS.txt").read_text().splitlines():
        h, _, rel = linea.partition(" ")
        hashes[rel.strip().lstrip("*")] = h

    for p in pacientes:
        archivos = sorted(r for r in hashes if r.startswith(p + "/"))
        total = 0
        for rel in archivos:
            local = destino / rel
            if local.exists() and sha256(local) == hashes[rel]:
                total += local.stat().st_size
                continue
            bajar(BASE + rel, local)
            if sha256(local) != hashes[rel]:
                raise RuntimeError(f"hash distinto en {rel}")
            total += local.stat().st_size
            print(f"OK {rel} ({local.stat().st_size / 1e6:.1f} MB)", flush=True)
        print(f"== {p}: {len(archivos)} archivos, {total / 1e9:.2f} GB verificados", flush=True)


if __name__ == "__main__":
    main()

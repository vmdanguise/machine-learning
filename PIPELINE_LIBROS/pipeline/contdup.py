"""Control de transcripcion por capitulo (reemplaza a los contdup09-12.py que estaban en Temp, 2026-11-02).
Por cada pagina del capitulo informa:
  - DOUBT/DUDA que hayan quedado en la transcripcion;
  - parrafos repetidos dentro de la pagina (ventana de 60 caracteres al final de cada parrafo, buscada en los demas);
  - <<CONT>> inicial cuyo comienzo ya esta en la pagina anterior (posible arrastre);
  - <<CONT>> que no esta en la primera linea (despues de una figura/epigrafe): join_pages no lo une y queda literal
    en es.md y en el PDF (agregado 2026-11-02, caso BENGIO p514);
  - issues del render (logs/render_NN.json), si existe.
Los avisos se revisan contra el original: codigo o ecuaciones que se repiten en el libro son falsos positivos.
El rango sale de books.py (units) o, para BENGIO, de BENGIO_traduccion/pipeline/config.py (UNITS).
Uso: python contdup.py LIBRO CAP [CAP ...]     (ej.: python contdup.py FUNDAMENTALS 13)"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(r"D:\Universidad De Palermo - Maestria en IA\Machine Learning")
sys.path.insert(0, str(Path(__file__).parent))


def rango(book, cap):
    if book == "BENGIO":
        sys.path.insert(0, str(ROOT / "BENGIO_traduccion" / "pipeline"))
        import config
        units = config.UNITS
    else:
        from books import BOOKS
        units = BOOKS[book]["units"]
    for u in units:
        if u[0] == cap:
            return u[2], u[3]
    raise SystemExit(f"{book}: no hay unidad {cap!r}")


def norm(s):
    return re.sub(r"\W+", " ", s).strip().lower()


def revisar(book, cap):
    a, z = rango(book, cap)
    tr = ROOT / f"{book}_traduccion" / "02_transcripcion"
    print(f"== {book} {cap}: p{a}-{z}")
    for p in range(a, z + 1):
        f = tr / f"p{p:04d}.md"
        if not f.exists():
            print(book, p, "SIN TRANSCRIPCION")
            continue
        t = f.read_text(encoding="utf-8")
        for m in re.finditer(r"<!--\s*(DOUBT|DUDA)[^>]*-->", t):
            print(book, p, "DOUBT:", m.group(0)[:220])
        paras = [x for x in re.split(r"\n\s*\n", t) if len(x) > 80]
        for i, x in enumerate(paras):
            tail = norm(x)[-60:]
            for k, y in enumerate(paras):
                if k != i and tail in norm(y):
                    print(book, p, "repetido:", x[:90].replace("\n", " "), "|| en:", y[:60].replace("\n", " "))
                    break
        if "<<CONT>>" in t and not t.lstrip().startswith("<<CONT>>"):
            # join_pages solo reconoce <<CONT>> en la primera linea: si va despues de un flotante queda literal en el PDF
            print(book, p, "CONT NO INICIAL (quedaria literal en es.md/PDF): mover el parrafo a la primera linea")
        if t.startswith("<<CONT>>") and p > a and (tr / f"p{p - 1:04d}.md").exists():
            prev = (tr / f"p{p - 1:04d}.md").read_text(encoding="utf-8")
            first = norm(t[8:].split("\n\n")[0])[:50]
            if first and first in norm(prev):
                print(book, p, "CONT ya en pagina anterior:", first)
    r = ROOT / f"{book}_traduccion" / "logs" / f"render_{cap}.json"
    if r.exists():
        print(book, "render issues:", json.loads(r.read_text(encoding="utf-8")).get("issues"))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    os.chdir(ROOT)
    for c in sys.argv[2:]:
        revisar(sys.argv[1], c)

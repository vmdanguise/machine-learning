"""Chequeo automatico de recortes de figuras de un capitulo (repetible; antes vivia en Temp como cropcheck.py +
contactNN.py). Rangos: indices de pagina 0-based e inclusivos, leidos de books.py (BENGIO: de
BENGIO_traduccion/pipeline/config.py), asi que no hay numeros de pagina a mano.

1) Por cada figura de 01_layout/pNNNN.json con bbox (solo libros con capa de texto):
   - "texto dentro": lineas largas (>45 car.) de cuerpo/epigrafe contenidas en el bbox -> el recorte incluye texto
   - "objetos fuera": dibujos vectoriales / imagenes a <=40 pt del bbox pero fuera de el -> recorte incompleto
   Falsos positivos conocidos: epigrafes bajo la figura (BENGIO), escaneos (DUDAHART marca todo), rotulos de
   paneles, numeros de ecuacion y barras de titulo (GONZALEZ). Es un filtro para la revision visual, no la reemplaza.
2) Hoja de contacto: miniaturas de 01_layout/figs/pNNNN_*.png del capitulo, 20 por hoja, en <salida>/csNN_LIBRO_k.png.

Uso: python check_crops.py LIBRO CAP [--out DIR] [--no-sheet]
     (DIR por defecto: %TEMP%/opencode)
"""
import glob
import json
import os
import re
import sys
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw

ROOT = Path(r"D:\Universidad De Palermo - Maestria en IA\Machine Learning")


def book_info(book, cap):
    if book == "BENGIO":
        txt = (ROOT / "BENGIO_traduccion" / "pipeline" / "config.py").read_text(encoding="utf-8", errors="replace")
        m = re.search(r'\(\s*"' + re.escape(cap) + r'"\s*,\s*"[^"]*"\s*,\s*(\d+)\s*,\s*(\d+)', txt)
        if not m:
            sys.exit(f"cap {cap} no esta en config.py de BENGIO")
        return ROOT / "BENGIO.pdf", int(m.group(1)), int(m.group(2)), False
    sys.path.insert(0, str(Path(__file__).parent))
    from books import BOOKS  # noqa: E402
    B = BOOKS[book]
    for u in B["units"]:
        if u[0] == cap:
            return ROOT / B["pdf"], u[2], u[3], bool(B.get("scanned"))
    sys.exit(f"cap {cap} no esta en books.py para {book}")


def check(book, pdf, a, z):
    doc = pymupdf.open(pdf)
    n = 0
    for p in range(a, z + 1):
        f = ROOT / f"{book}_traduccion" / "01_layout" / f"p{p:04d}.json"
        if not f.exists():
            continue
        info = json.loads(f.read_text(encoding="utf-8"))
        figs = [x for x in info.get("figures", []) if x.get("bbox")]
        if not figs:
            continue
        page = doc[p]
        caps = [pymupdf.Rect(x["caption_bbox"]) for x in info["figures"] if x.get("caption_bbox")]
        lines = []
        for bl in page.get_text("dict")["blocks"]:
            for l in bl.get("lines", []):
                lines.append((pymupdf.Rect(l["bbox"]), "".join(s["text"] for s in l["spans"]).strip()))
        objs = [pymupdf.Rect(d["rect"]) for d in page.get_drawings() if d["rect"].width < page.rect.width * 0.95]
        objs += [pymupdf.Rect(i["bbox"]) for i in page.get_image_info()]
        for x in figs:
            r = pymupdf.Rect(x["bbox"])
            msgs = ["texto dentro: " + t[:60] for lr, t in lines if len(t) > 45 and r.contains(lr)]
            grow = pymupdf.Rect(r.x0 - 40, r.y0 - 40, r.x1 + 40, r.y1 + 40)
            out = [o for o in objs if o.intersects(grow) and not r.contains(o) and o.width * o.height > 4
                   and not any(c.contains(o) for c in caps) and (o & r).get_area() < 0.9 * o.get_area()
                   and o.y0 > 50]
            if out:
                u = out[0]
                for o in out[1:]:
                    u |= o
                msgs.append(f"{len(out)} objetos fuera, union {[round(v) for v in u]} vs bbox {[round(v) for v in r]}")
            if msgs:
                n += 1
                print(book, p, x.get("label"), *msgs[:3], sep=" | ")
    print(f"{book}: {n} figuras con avisos")


def sheet(book, cap, a, z, outdir):
    figs = []
    for p in range(a, z + 1):
        figs += sorted(glob.glob(str(ROOT / f"{book}_traduccion" / "01_layout" / "figs" / f"p{p:04d}_*.png")))
    print(book, cap, "recortes:", len(figs))
    W, H, cols = 300, 230, 5
    for k in range(0, len(figs), 20):
        part = figs[k:k + 20]
        rows = (len(part) + cols - 1) // cols
        im_s = Image.new("RGB", (cols * W, rows * H), "white")
        d = ImageDraw.Draw(im_s)
        for i, f in enumerate(part):
            im = Image.open(f).convert("RGB")
            im.thumbnail((W - 10, H - 25))
            x, y = (i % cols) * W, (i // cols) * H
            im_s.paste(im, (x + 5, y + 20))
            d.rectangle([x + 4, y + 19, x + 6 + im.width, y + 21 + im.height], outline="red")
            d.text((x + 5, y + 3), os.path.basename(f)[:45], fill="blue")
        out = Path(outdir) / f"cs{cap}_{book}_{k // 20}.png"
        im_s.save(out)
        print("  ", out)


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) < 2:
        sys.exit(__doc__)
    book, cap = args[0], args[1]
    outdir = args[args.index("--out") + 1] if "--out" in args else os.path.join(os.environ.get("TEMP", "."), "opencode")
    pdf, a, z, scanned = book_info(book, cap)
    print(f"{book} cap {cap}: paginas {a}-{z} (0-based, inclusivas) de {pdf.name}")
    if scanned:
        print("libro escaneado: chequeo de texto/objetos omitido (solo hoja de contacto)")
    else:
        check(book, pdf, a, z)
    if "--no-sheet" not in args:
        sheet(book, cap, a, z, outdir)

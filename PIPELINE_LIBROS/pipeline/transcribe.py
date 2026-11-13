"""Etapa 2 (pasada A): transcripcion fiel EN INGLES de cada pagina a Markdown+LaTeX usando LLM con vision.
Checkpoint: 02_transcripcion/pXXXX.md (escritura atomica; si existe, se saltea).
Libros escaneados: la "capa de texto" es el OCR de tesseract (01_layout/ocr).

Uso: $env:BOOK="X"; python transcribe.py <unidad|pN|pN-M|all> [...] [--force] [--workers N]
"""
import re
import statistics
import sys
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed

import pymupdf

import layout
from config import SRC_PDF, D_TRANS, D_LOG, MODEL_TRANSCRIBE, UNITS, B, parse_targets
from llm import call, image_block
from prompts import SYSTEM_TRANSCRIBE, USER_TRANSCRIBE

_doc = None


def doc():
    global _doc
    if _doc is None:
        _doc = pymupdf.open(SRC_PDF)
    return _doc


def norm(s):
    return unicodedata.normalize("NFKC", s)


def page_text(pno):
    if B.get("ocr_text"):
        txt, _ = layout.ocr(doc(), pno)
        return txt.strip()
    return norm(doc()[pno].get_text("text", sort=True))


def unit_of(pno):
    for u in UNITS:
        if u[2] <= pno <= u[3]:
            return u
    return None


def body_lines(pno, info):
    """(x0, y0, size, text) de las lineas de texto fuera de figuras/captions/encabezados."""
    figs = [pymupdf.Rect(f["bbox"]) for f in info["figures"] if f.get("bbox")]
    caps = [pymupdf.Rect(f["caption_bbox"]) for f in info["figures"] if not f.get("manual")]
    out = []
    if B.get("scanned"):
        _, ls = layout.ocr(doc(), pno)
        for l in ls:
            r = l["bbox"]
            if r.y0 < info["header_bottom"] or any(r.intersects(f) for f in figs + caps):
                continue
            out.append((r.x0, r.y0, r.height, l["text"], l["n"]))
        return out
    H0, H1 = B["header_y"], B["footer_y"]
    for b in doc()[pno].get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            r = pymupdf.Rect(l["bbox"])
            t = "".join(s["text"] for s in l["spans"]).strip()
            if not t or r.y0 < H0 or r.y0 > H1 or any(r.intersects(f) for f in figs + caps):
                continue
            size = max(s["size"] for s in l["spans"])
            if size < B["body_min"]:
                continue
            out.append((r.x0, r.y0, size, t, len(t.split())))
    return out


def indent_hint(pno, info):
    if B.get("indent") is None and not B.get("scanned"):
        return "unknown: paragraphs are not indented in this book; decide from the sentence flow"
    ls = body_lines(pno, info)
    longs = [l for l in ls if l[4] >= 8]
    if not ls or not longs:
        return "not found"
    base = statistics.median(l[0] for l in longs)
    ls = [l for l in ls if l[0] >= base - 3]          # fuera notas al margen izquierdo
    if not ls:
        return "not found"
    first = min(ls, key=lambda l: l[1])
    if (not B.get("scanned") and first[2] > 12) or re.match(r"^(\d+(\.\d+)+\.?\s|Chapter\s|[A-Z][A-Z ,?:'-]{8,}$)", first[3]):
        return f"is a heading: \"{first[3][:40]}\""
    d = first[0] - base
    if d > 6:
        return f"is INDENTED (new paragraph): \"{first[3][:40]}\""
    return f"is NOT indented (probably continues the previous page's paragraph; verify in the image): \"{first[3][:40]}\""


def page_image(pno, info, dpi=150):
    """Render de la pagina con las figuras tapadas por un rectangulo gris rotulado."""
    d = pymupdf.open()
    d.insert_pdf(doc(), from_page=pno, to_page=pno)
    p = d[0]
    for f in info["figures"]:
        if f.get("bbox"):
            r = pymupdf.Rect(f["bbox"])
            p.draw_rect(r, color=(0.4, 0.4, 0.4), fill=(0.85, 0.85, 0.85), overlay=True)
            p.insert_textbox(r + (0, r.height / 2 - 12, 0, 0), f"FIGURE {f['label']}", fontsize=16,
                             color=(0.2, 0.2, 0.2), align=pymupdf.TEXT_ALIGN_CENTER, overlay=True)
    png = p.get_pixmap(dpi=dpi).tobytes("png")
    d.close()
    return png


def transcribe_page(pno, force=False):
    out = D_TRANS / f"p{pno:04d}.md"
    if out.exists() and not force:
        return "skip"
    layout.run([pno])
    info = layout.load(pno)
    u = unit_of(pno)
    figs = ", ".join(f["label"] + (f" (UNNUMBERED figure: {f['hint']})" if f.get("hint") else "")
                     for f in info["figures"] if f.get("bbox")) or "none"
    user = USER_TRANSCRIBE.format(pno=pno, printed=info.get("printed", "?"), unit_title=u[1], figs=figs,
                                  eqnums=", ".join(info["eqnums"]) or "none",
                                  indent_hint=indent_hint(pno, info),
                                  textkind="OCR text (may contain errors)" if B.get("ocr_text") else "Text layer",
                                  text=page_text(pno))
    content = [image_block(page_image(pno, info, dpi=170 if B.get("scanned") else 150)),
               {"type": "text", "text": user}]
    md = call(MODEL_TRANSCRIBE, SYSTEM_TRANSCRIBE, content, max_tokens=12000, tag=f"A:p{pno}").strip()
    if md.startswith(("```markdown", "```md\n")):
        md = md.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    tmp = out.with_suffix(".tmp")
    tmp.write_text(md + "\n", encoding="utf-8")
    tmp.replace(out)
    return "ok"


def run(pages, force=False, workers=4):
    layout.run(pages)
    errs = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(transcribe_page, p, force): p for p in pages}
        for f in as_completed(futs):
            p = futs[f]
            try:
                st = f.result()
                if st != "skip":
                    print(f"  A p{p:04d} {st}", flush=True)
            except Exception as e:
                errs.append(p)
                print(f"  A p{p:04d} ERROR {e}", flush=True)
                with open(D_LOG / "errores.log", "a", encoding="utf-8") as fh:
                    fh.write(f"A\tp{p:04d}\t{e}\n")
    return sorted(errs)


def cli_args(argv):
    force = "--force" in argv
    workers = 4
    argv = list(argv)
    if "--workers" in argv:
        i = argv.index("--workers")
        workers = int(argv[i + 1])
        del argv[i:i + 2]
    return [a for a in argv if a != "--force"], force, workers


if __name__ == "__main__":
    targets, force, workers = cli_args(sys.argv[1:])
    print("errores:", run(parse_targets(targets), force, workers))

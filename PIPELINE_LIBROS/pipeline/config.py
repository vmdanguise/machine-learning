"""Configuracion comun del pipeline generalizado. El libro se elige con la variable de entorno BOOK
(BISHOP | FUNDAMENTALS | GONZALEZ | DUDAHART). Derivado de BENGIO_traduccion/pipeline (que queda intacto)."""
import os
from pathlib import Path

from books import BOOKS

BOOK = os.environ.get("BOOK", "").upper()
if BOOK not in BOOKS:
    raise SystemExit(f"definir $env:BOOK = uno de {list(BOOKS)} (actual: {BOOK!r})")
B = BOOKS[BOOK]

ROOT = Path(r"D:\Universidad De Palermo - Maestria en IA\Machine Learning")
PIPE = ROOT / "PIPELINE_LIBROS"
SRC_PDF = ROOT / B["pdf"]
WORK = ROOT / B["work"]

D_LAYOUT = WORK / "01_layout"
D_TRANS = WORK / "02_transcripcion"
D_TRAD = WORK / "03_traduccion"
D_HTML = WORK / "04_html"
D_PDF = WORK / "05_pdf_capitulos"
D_LOG = WORK / "logs"
D_OCR = WORK / "01_layout" / "ocr"
D_TOOLS = PIPE / "tools"             # katex (npm local), fuentes: compartidos
for d in (D_LAYOUT, D_TRANS, D_TRAD, D_HTML, D_PDF, D_LOG):
    d.mkdir(parents=True, exist_ok=True)

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
TESSERACT = r"C:\Users\Usuario\Tools\tesseract\tesseract.exe"

LLM_BASE = os.environ.get("ANTHROPIC_BASE_URL", "http://127.0.0.1:4001")
LLM_TOKEN = os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("LITELLM_API_KEY")
MODEL_TRANSCRIBE = os.environ.get("MODEL_A", "claude-sonnet-4-6")
MODEL_TRANSLATE = os.environ.get("MODEL_B", "claude-sonnet-4-6")

UNITS = B["units"]
LABEL = r"[\d]+[.\-][\d]+"   # 1.4 | 1-10


def unit(uid):
    for u in UNITS:
        if u[0] == uid:
            return u
    raise KeyError(uid)


def unit_of_page(pno):
    for u in UNITS:
        if u[2] <= pno <= u[3]:
            return u
    return None


def page_offset(pno):
    """Offset pagina impresa - indice (libros escaneados; DUDAHART reinicia la numeracion en cada capitulo)."""
    u = unit_of_page(pno)
    offs = B.get("page_offsets", {})
    if u and u[0] in offs:
        return offs[u[0]]
    return B.get("page_offset", 0)


def unit_pages(uid):
    u = unit(uid)
    return list(range(u[2], u[3] + 1))


def parse_targets(args):
    ids = {u[0] for u in UNITS}
    pages = []
    for a in args:
        if a in ids:
            pages += unit_pages(a)
        elif a.lower() == "all":
            pages += [p for u in UNITS if u[4] == "llm" for p in range(u[2], u[3] + 1)]
        elif a.lower().startswith("p") and a[1:2].isdigit():
            lo, _, hi = a[1:].partition("-")
            pages += list(range(int(lo), int(hi or lo) + 1))
        else:
            raise SystemExit(f"objetivo desconocido: {a}")
    return pages

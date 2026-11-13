"""Transcribe una ZONA de una pagina (recorte) con un modelo dado. Fallback cuando el filtro de contenido del
proveedor bloquea la pagina completa y transcribe_alt.py devuelve una transcripcion incompleta.
No toca 02_transcripcion: escribe el resultado en <salida> para unirlo a mano con la transcripcion de la pagina.
Uso: $env:BOOK="X"; python transcribe_clip.py <pagina> <x0> <y0> <x1> <y1> <modelo> <salida.md> [<nota para el modelo>]"""
import sys
from pathlib import Path

import pymupdf

import transcribe as T
from llm import call, image_block
from prompts import SYSTEM_TRANSCRIBE

pno = int(sys.argv[1])
x0, y0, x1, y1 = map(float, sys.argv[2:6])
model, out = sys.argv[6], Path(sys.argv[7])
nota = sys.argv[8] if len(sys.argv) > 8 else ""

clip = pymupdf.Rect(x0, y0, x1, y1)
png = T.doc()[pno].get_pixmap(dpi=200, clip=clip).tobytes("png")
txt = T.norm(T.doc()[pno].get_text("text", clip=clip, sort=True))
u = T.unit_of(pno)
user = (f"This image is a CROP (one column) of page {pno} ({u[1]}). Transcribe ONLY the text in the image, following "
        f"all the rules. If the crop starts in the middle of a paragraph continued from the previous page, start with "
        f"<<CONT>>. {nota}\n\nText layer of the crop (may have broken ligatures):\n{txt}")
md = call(model, SYSTEM_TRANSCRIBE, [image_block(png), {"type": "text", "text": user}], max_tokens=8000,
          tag=f"A:p{pno}:clip:{model}", retries=1, timeout=240).strip()
if md.startswith(("```markdown", "```md\n")):
    md = md.split("\n", 1)[1].rsplit("```", 1)[0].strip()
out.write_text(md + "\n", encoding="utf-8")
print("ok", out)

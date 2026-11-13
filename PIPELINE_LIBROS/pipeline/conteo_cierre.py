"""Conteos para anotar en la bitacora al cerrar cada cap (2026-11-02, AJUSTES/2026-11-02 sexta tanda). Solo lectura.
- PDFs de capitulo en <LIBRO>_traduccion/05_pdf_capitulos y cuantos contienen '<<CONT' (TODOS/cont_literal);
- notas visibles de erratas 'N. del T.: errata' en los es.md (pendiente 'Notas visibles de erratas').
Uso: python conteo_cierre.py"""
import glob
import os
import re
from collections import Counter

import pymupdf

R = r"D:\Universidad De Palermo - Maestria en IA\Machine Learning"
pdfs = Counter()
cont = []
for f in sorted(glob.glob(R + r"\*_traduccion\05_pdf_capitulos\*.pdf")):
    lib = os.path.basename(os.path.dirname(os.path.dirname(f))).split("_")[0]
    pdfs[lib] += 1
    with pymupdf.open(f) as d:
        if any("<<CONT" in pg.get_text() for pg in d):
            cont.append(f)
print("PDFs:", sum(pdfs.values()), ", ".join(f"{k} {v}" for k, v in sorted(pdfs.items())), "| con '<<CONT':", cont or 0)
ERR = re.compile(r"(?m)^\[\^(p\d+-\d+)\]: N\. del T\.: errata")
notas = {}
for f in sorted(glob.glob(R + r"\*_traduccion\03_traduccion\[0-9][0-9]\es.md")):
    n = ERR.findall(open(f, encoding="utf-8").read())
    if n:
        notas[os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(f)))).split("_")[0] + " " +
              os.path.basename(os.path.dirname(f))] = n
print("notas de erratas:", sum(len(v) for v in notas.values()), "en", len(notas), "caps")
for k, v in notas.items():
    print("  ", k, v)

"""Chequeo de un cap traducido (paso 3 del procedimiento por cap): matematica en/es (multiset), [[FIG, notas,
algoritmos, marcas de pagina, DOUBT, titulos en/es y voseo/tuteo. Solo lectura.
Uso: python b13txt.py LIBRO CAP   (ej.: python b13txt.py BENGIO 16)
Movido desde Temp/opencode el 2026-11-02 (AJUSTES/2026-11-02, sexta tanda). Cambios respecto de la copia de Temp:
- 'notas def' cuenta las definiciones [^...]: aparte ('[^' suma llamadas + definiciones: 2 por nota);
- las cadenas del chequeo de voseo/tuteo estaban con mojibake y nunca coincidian; ahora son las correctas."""
import os
import re
import sys
from collections import Counter
from pathlib import Path

book, cap = sys.argv[1], sys.argv[2]
W = Path(r"D:\Universidad De Palermo - Maestria en IA\Machine Learning") / f"{book}_traduccion" / "03_traduccion"
d = W / cap
print(sorted(os.listdir(d))[:20])
en = (d / "en.md").read_text(encoding="utf-8")
es = (d / "es.md").read_text(encoding="utf-8")
MATH = re.compile(r"\$\$.+?\$\$|\$[^$\n]+?\$", re.S)
me, ms = MATH.findall(en), MATH.findall(es)
print("math en/es", len(me), len(ms), "iguales(multiset)", sorted(me) == sorted(ms))
if sorted(me) != sorted(ms):
    a, b = Counter(me), Counter(ms)
    print("  solo en:", list((a - b).items())[:8])
    print("  solo es:", list((b - a).items())[:8])
for k in ("[[FIG", "[^", ":::algorithm", "<!-- p. orig", "DOUBT"):
    print(k, en.count(k), es.count(k))
NOTA = re.compile(r"(?m)^\[\^([^\]]+)\]:")
print("notas def", len(NOTA.findall(en)), len(NOTA.findall(es)), NOTA.findall(es))
te = [l for l in en.splitlines() if l.startswith("#")]
ts = [l for l in es.splitlines() if l.startswith("#")]
print("titulos", len(te), len(ts))
for a, b in zip(te, ts):
    print(" ", a[:70], "=>", b[:70])
for w in (" vos ", " tú ", " usted", "podés", "tenés", "sabés", "querés"):
    if w in es.lower():
        print("voseo/tu:", w)

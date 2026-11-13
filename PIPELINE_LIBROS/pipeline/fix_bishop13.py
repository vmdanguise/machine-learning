"""BISHOP cap 13: terminologia unificada (2026-11-02, bitacora BISHOP/13).
El cap mezclaba 'equivariancia' (4) con 'equivarianza' (6) e 'invariancia' (2) con 'invarianza' (6); queda la forma
mayoritaria del cap y del resto de BISHOP ('equivarianza' 16, 'invarianza' 19 en caps 01-12).
Solo toca 'es' de 03_traduccion/13/cNNN.json y regenera es.md ("\\n\\n".join(es) + "\\n"). Idempotente.
Respaldo previo en BISHOP_traduccion/_backup_pre_fix/13_bishop13. Correr de nuevo despues de cualquier
translate/fix_registro/fix_ingles del cap 13, y despues fix_erratas_notas.py."""
import json
import re
import shutil
from pathlib import Path

W = Path(r"D:\Universidad De Palermo - Maestria en IA\Machine Learning\BISHOP_traduccion")
T = W / "03_traduccion" / "13"
BK = W / "_backup_pre_fix" / "13_bishop13"
REPL = [(r"\b([Ee])quivariancia\b", r"\1quivarianza"), (r"\b([Ii])nvariancia\b", r"\1nvarianza")]

cs = sorted(T.glob("c*.json"), key=lambda f: int(f.stem[1:]))
if not BK.exists():
    BK.mkdir(parents=True)
    for f in cs + [T / "es.md"]:
        shutil.copy2(f, BK)
cambios = []
es = []
for c in cs:
    j = json.loads(c.read_text(encoding="utf-8"))
    t = j["es"]
    for a, b in REPL:
        t, n = re.subn(a, b, t)
        if n:
            cambios.append((c.name, a, n))
    if t != j["es"]:
        j["es"] = t
        c.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
    es.append(t)
md = "\n\n".join(es) + "\n"
(T / "es.md").write_text(md, encoding="utf-8")
assert not re.search(r"quivariancia|nvariancia", md)
print("cambios:", cambios or "ninguno (ya aplicado)")

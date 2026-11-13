"""FUNDAMENTALS cap 09: matematica agregada por la traduccion (2026-11-02, bitacora FUNDAMENTALS/09 y AJUSTES).
En c007 (Secc. de RNNs en PyTorch, p234 del original) el src dice 'the outputs of the Output Gates at time, n.' con la n
en texto plano (en el PDF va en la fuente de codigo UbuntuMono, no en matematica). La traduccion escribio
'en el tiempo $n$': un $n$ que no esta en el src (es.md tenia 3 '$n$' fuera de los bloques de codigo contra 2 de en.md).
Regla: matematica byte a byte -> se quitan los $ agregados ('en el tiempo n'). Despues la matematica del fragmento es la
misma que la del src. Toca solo el campo 'es' de 03_traduccion/09/c007.json y regenera es.md ("\\n\\n".join(es) + "\\n").
Backup en FUNDAMENTALS_traduccion/_backup_pre_fix/09_fund09 (una vez). Idempotente. Despues: fix_erratas_notas.py,
re-render y validate del cap 09."""
import collections
import json
import re
import shutil
from pathlib import Path

W = Path(r"D:\Universidad De Palermo - Maestria en IA\Machine Learning\FUNDAMENTALS_traduccion")
D = W / "03_traduccion" / "09"
BK = W / "_backup_pre_fix" / "09_fund09"
MATH = re.compile(r"\$\$.*?\$\$|\$[^$\n]+?\$", re.S)
CODE = re.compile(r"```.*?```", re.S)
TEXTO = [("c007", "(*Output Gates*) en el tiempo $n$. El segundo", "(*Output Gates*) en el tiempo n. El segundo")]


def math(t):
    return collections.Counter(MATH.findall(CODE.sub("", t)))


cs = sorted(D.glob("c*.json"), key=lambda f: int(f.stem[1:]))
assert "\n\n".join(json.loads(f.read_text(encoding="utf-8"))["es"] for f in cs) + "\n" == \
    (D / "es.md").read_text(encoding="utf-8"), "es.md no coincide con los cNNN"
if not BK.exists():
    BK.mkdir(parents=True)
    for f in cs + [D / "es.md"]:
        shutil.copy2(f, BK)
cambios = []
es_all = []
for f in cs:
    j = json.loads(f.read_text(encoding="utf-8"))
    t = j["es"]
    for c, viejo, nuevo in TEXTO:
        if c == f.stem:
            assert t.count(viejo) + t.count(nuevo) == 1, (f.name, viejo, t.count(viejo), t.count(nuevo))
            if viejo in t:
                t = t.replace(viejo, nuevo)
                cambios.append((f.name, viejo[:40]))
    if f.stem == "c007":
        assert math(t) == math(j["src"]), (f.name, math(t) - math(j["src"]), math(j["src"]) - math(t))
    if t != j["es"]:
        j["es"] = t
        f.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
    es_all.append(t)
(D / "es.md").write_text("\n\n".join(es_all) + "\n", encoding="utf-8")
print("cambios:", cambios or "ninguno (ya aplicado)")

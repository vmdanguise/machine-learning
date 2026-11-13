"""BISHOP cap 18: unificacion terminologica dentro del cap (2026-11-02, bitacora BISHOP/18).
1) *normalizing flow*: el titulo ('Flujos Normalizadores') y la definicion ('*flujo normalizador* (*normalizing flow*)')
   usan 'normalizador', pero el cuerpo alternaba con 'normalizante(s)' (c001, c002, c004). Se unifica a
   'flujo(s) normalizador(es)', tambien en 'flujo normalizante continuo' (-> 'flujo normalizador continuo').
2) *ODE solver*: 'solver' (9) y 'solucionador(es)' (2) mezclados (c003, c004). Se unifica a 'solucionador' (como
   BENGIO 06 y GONZALEZ 10).
3) c001: 'flujos ... denominados *coupling flows*' (sin traducir) -> 'denominados *flujos de acoplamiento* (*coupling
   flows*)', como en la introduccion del cap y el titulo 18.1.
Sin matematica: comprueba que la de cada fragmento sigue igual. Solo campo 'es' de 03_traduccion/18/cNNN.json;
regenera es.md ("\\n\\n".join(es) + "\\n"). Backup BISHOP_traduccion/_backup_pre_fix/18_bishop18 (una vez).
Idempotente. Despues: fix_erratas_notas.py, re-render y validate del cap 18."""
import collections
import json
import re
import shutil
from pathlib import Path

W = Path(r"D:\Universidad De Palermo - Maestria en IA\Machine Learning\BISHOP_traduccion")
D = W / "03_traduccion" / "18"
BK = W / "_backup_pre_fix" / "18_bishop18"
MATH = re.compile(r"\$\$.*?\$\$|\$[^$\n]+?\$", re.S)
RE_SUB = [
    (re.compile(r"\b([Ff]lujo) normalizante\b"), r"\1 normalizador"),
    (re.compile(r"\b([Ff]lujos) normalizantes\b"), r"\1 normalizadores"),
    (re.compile(r"\bsolver\b"), "solucionador"),
]
TEXTO = [("c001", "denominados *coupling flows*, en los", "denominados *flujos de acoplamiento* (*coupling flows*), en los")]

cs = sorted(D.glob("c*.json"), key=lambda f: int(f.stem[1:]))
assert "\n\n".join(json.loads(f.read_text(encoding="utf-8"))["es"] for f in cs) + "\n" == \
    (D / "es.md").read_text(encoding="utf-8"), "es.md no coincide con los cNNN"
if not BK.exists():
    BK.mkdir(parents=True)
    for f in cs + [D / "es.md"]:
        shutil.copy2(f, BK)
cambios = collections.Counter()
es_all = []
for f in cs:
    j = json.loads(f.read_text(encoding="utf-8"))
    t = j["es"]
    for c, viejo, nuevo in TEXTO:
        if c == f.stem:
            assert t.count(viejo) + t.count(nuevo) == 1, (f.name, viejo)
            if viejo in t:
                t = t.replace(viejo, nuevo)
                cambios[(f.name, "coupling flows")] += 1
    for rx, rep in RE_SUB:
        t, n = rx.subn(rep, t)
        if n:
            cambios[(f.name, rx.pattern)] += n
    assert collections.Counter(MATH.findall(t)) == collections.Counter(MATH.findall(j["src"])), f.name
    if t != j["es"]:
        j["es"] = t
        f.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
    es_all.append(t)
(D / "es.md").write_text("\n\n".join(es_all) + "\n", encoding="utf-8")
print("cambios:", dict(cambios) or "ninguno (ya aplicado)", "total", sum(cambios.values()))

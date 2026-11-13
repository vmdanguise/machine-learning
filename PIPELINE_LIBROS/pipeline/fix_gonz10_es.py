"""GONZALEZ cap 10: correcciones sobre la traduccion (campo 'es' de 03_traduccion/10/cNNN.json + es.md).
1) Problema 10.10(a) (p806): el original dice "the rate of that descent" (errata del libro: es el ascenso); la
   traduccion lo habia corregido a "ascenso". Se conserva la errata ("descenso") con una NOTA.
2) Seccion 10.7 (p787): el original titula "Background" (igual que en 10.2, p703, traducido "Antecedentes"); la
   traduccion habia puesto "Fundamentos" (que es "Foundation", 10.3). Se unifica a "Antecedentes".
Idempotente: si ya esta aplicado no cambia nada. Correr despues de cualquier translate.py/fix_registro.py del cap 10."""
import json
from pathlib import Path

D = Path(r"D:\Universidad De Palermo - Maestria en IA\Machine Learning\GONZALEZ_traduccion\03_traduccion\10")
OLD = "y que la tasa de ese ascenso es"
NEW = "y que la tasa de ese descenso es"
NOTA = ("<!-- NOTA: en 10.10(a) el original dice 'the rate of that descent' (errata del libro: es el ascenso); "
        "se conserva tal cual. -->")
ANCHOR = "definida en la Ec. (10-17).\n"

cs = sorted(D.glob("c*.json"), key=lambda f: int(f.stem[1:]))
hits = [f for f in cs if OLD in json.loads(f.read_text(encoding="utf-8"))["es"]
        or NOTA in json.loads(f.read_text(encoding="utf-8"))["es"]]
assert len(hits) == 1, [f.name for f in hits]
f = hits[0]
j = json.loads(f.read_text(encoding="utf-8"))
es = j["es"]
if NOTA in es:
    print(f.name, "ya corregido")
else:
    assert es.count(OLD) == 1 and es.count(ANCHOR) >= 1 and es.find(ANCHOR) > es.find(OLD)
    j.setdefault("es_pre_fix10", es)
    es = es.replace(OLD, NEW).replace(ANCHOR, ANCHOR.rstrip("\n") + "\n\n" + NOTA + "\n", 1)
    j["es"] = es
    f.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f.name, "corregido")
# 2) titulo "Background" de 10.7
H_OLD = "\n\n### Fundamentos\n\nEl concepto de cuenca"
H_NEW = "\n\n### Antecedentes\n\nEl concepto de cuenca"
hh = [x for x in cs if H_OLD in (json.loads(x.read_text(encoding="utf-8"))["es"])
      or H_NEW in json.loads(x.read_text(encoding="utf-8"))["es"]]
assert len(hh) == 1, [x.name for x in hh]
j = json.loads(hh[0].read_text(encoding="utf-8"))
if H_NEW in j["es"]:
    print(hh[0].name, "titulo 10.7 ya corregido")
else:
    assert j["es"].count(H_OLD) == 1
    j.setdefault("es_pre_fix10", j["es"])
    j["es"] = j["es"].replace(H_OLD, H_NEW)
    hh[0].write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
    print(hh[0].name, "titulo 10.7 corregido")
(D / "es.md").write_text("\n\n".join(json.loads(x.read_text(encoding="utf-8"))["es"] for x in cs) + "\n",
                         encoding="utf-8")
print("es.md regenerado")

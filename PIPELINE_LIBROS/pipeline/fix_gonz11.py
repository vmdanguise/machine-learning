"""GONZALEZ cap 11: correcciones verificadas contra el original (2026-11-02).
1) p902 (problemas 11.32-11.39, dos columnas): las imagenes de los Problemas 11.38 (fila de botellas) y 11.39 (burbujas)
   no tienen rotulo en el original; la transcripcion puso [[FIG P11.38]]/[[FIG P11.39]] y dos DOUBT "not cropped".
   Se recortan a mano (books.py extra_figs[902], bbox de las imagenes raster; layout.py p902 --force) y los DOUBT pasan a
   una NOTA de proceso (oculta: no es errata).
2) c010: fix_registro falla siempre; revisado a mano (registro ya impersonal) -> register_fix=True (ver abajo).
Aplica el reemplazo en 02_transcripcion/p0902.md, en.md, los cNNN.json (src, es, es_pre_*) y regenera es.md.
Idempotente. Respaldo previo en GONZALEZ_traduccion/_backup_pre_fix/11_gonz11. Correr de nuevo despues de cualquier
transcribe/translate/fix_registro/fix_ingles del cap 11."""
import json
import shutil
from pathlib import Path

W = Path(r"D:\Universidad De Palermo - Maestria en IA\Machine Learning\GONZALEZ_traduccion")
T = W / "03_traduccion" / "11"
D902 = "<!-- DOUBT: figure P11.38 not cropped -->\n<!-- DOUBT: figure P11.39 not cropped -->"
N902 = ("<!-- NOTA: las imagenes de los Problemas 11.38 (botellas) y 11.39 (burbujas) no tienen rotulo en el original; "
        "van como figuras extra P11.38/P11.39 (recorte manual, extra_figs). -->")
REPS = [(D902, N902)]

files = [W / "02_transcripcion" / "p0902.md", T / "en.md"]
cs = sorted(T.glob("c*.json"), key=lambda f: int(f.stem[1:]))
bk = W / "_backup_pre_fix" / "11_gonz11"
if not bk.exists():
    bk.mkdir(parents=True)
    for f in files + cs + [T / "es.md"]:
        shutil.copy2(f, bk / f.name)
cambios = []
for f in files:
    t = f.read_text(encoding="utf-8")
    t2 = t
    for a, b in REPS:
        t2 = t2.replace(a, b)
    if t2 != t:
        f.write_text(t2, encoding="utf-8")
        cambios.append(f.name)
for f in cs:
    j = json.loads(f.read_text(encoding="utf-8"))
    ch = False
    for k in list(j):
        if isinstance(j[k], str) and (k in ("src", "es") or k.startswith("es_pre")):
            s = j[k]
            for a, b in REPS:
                s = s.replace(a, b)
            if s != j[k]:
                j[k] = s
                ch = True
    if ch:
        f.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
        cambios.append(f.name)
# 2) c010: fix_registro falla siempre (el LLM no conserva los 30 bloques). El unico disparador es "You learned in
#    Chapter 4" del src; la traduccion ya es impersonal ("En el Capitulo 4 se mostro"). Revisado a mano: se marca
#    register_fix solo si el es no tiene ningun patron de tu/vos/usted.
import re, sys  # noqa: E401,E402
sys.argv[1:] = ["GONZALEZ"]
sys.path.insert(0, str(Path(__file__).parent))
import fix_registro as FR  # noqa: E402
c010 = T / "c010.json"
j = json.loads(c010.read_text(encoding="utf-8"))
if not j.get("register_fix"):
    pe = FR.strip_nonprose(j["es"])
    assert not any(rx.search(pe) for rx in (FR.VOSEO_WORDS, FR.TU_WORDS, FR.TU_VERB, FR.USTED, FR.IMP)), "c010: registro"
    assert "En el Capítulo 4 se mostró" in j["es"]
    j["register_fix"] = True
    j["register_fix_manual"] = "revisado a mano 2026-11-02: unico disparador 'You learned in Chapter 4' (src), es impersonal"
    c010.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
    cambios.append("c010.json (register_fix manual)")
es = "\n\n".join(json.loads(c.read_text(encoding="utf-8"))["es"] for c in cs) + "\n"
(T / "es.md").write_text(es, encoding="utf-8")
assert "DOUBT" not in es and es.count(N902) == 1
assert es.count("[[FIG P11.38]]") == 1 and es.count("[[FIG P11.39]]") == 1
print("cambios:", cambios or "ninguno (ya aplicado)")

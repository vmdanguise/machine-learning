"""FUNDAMENTALS cap 11, p305 (perdida de LIME): verificado en la imagen del original (2026-11-02).
El original imprime 'zâ' (subindice de la sumatoria y argumento de g), un error de codificacion de z' (el texto usa z').
La transcripcion tenia 'z\\hat{}' (sombrero sin base) y un DOUBT. Se transcribe lo impreso, 'z\\hat{a}', y el DOUBT pasa a
NOTA; la nota al pie visible de la errata la agrega fix_erratas_notas.py (clave FUNDAMENTALS11_zhat).
Aplica el mismo reemplazo en 02_transcripcion/p0305.md, en.md, los cNNN.json (src, es, es_pre_*) y regenera es.md.
Idempotente. Respaldo previo en FUNDAMENTALS_traduccion/_backup_pre_fix/11_fund11."""
import json
import shutil
from pathlib import Path

W = Path(r"D:\Universidad De Palermo - Maestria en IA\Machine Learning\FUNDAMENTALS_traduccion")
T = W / "03_traduccion" / "11"
DOUBT = ("<!-- DOUBT: the summation notation uses z and zâ (z-hat) which appears to be z and z' (z-prime) rendered oddly "
         "in the PDF text layer; transcribed as z\\hat{} based on image showing ẑ -->")
NOTA = ("<!-- NOTA: el original imprime 'zâ' en el subindice de la sumatoria y en g(zâ) (verificado en la imagen; error de "
        "codificacion de z'); se transcribe tal cual como z\\hat{a}. -->")
REPS = [(DOUBT, NOTA), ("z\\hat{}", "z\\hat{a}")]   # el DOUBT contiene "z\hat{}": va primero

files = [W / "02_transcripcion" / "p0305.md", T / "en.md"]
cs = sorted(T.glob("c*.json"), key=lambda f: int(f.stem[1:]))
bk = W / "_backup_pre_fix" / "11_fund11"
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
es = "\n\n".join(json.loads(c.read_text(encoding="utf-8"))["es"] for c in cs) + "\n"
(T / "es.md").write_text(es, encoding="utf-8")
assert "DOUBT" not in es and "z\\hat{}" not in es and es.count("z\\hat{a}") == 3 and es.count(NOTA) == 1   # 2 en la ecuacion + 1 en la NOTA
print("cambios:", cambios or "ninguno (ya aplicado)")

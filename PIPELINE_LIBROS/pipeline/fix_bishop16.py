"""BISHOP cap 16: correcciones verificadas contra el original (2026-11-02, bitacora BISHOP/16).
1) Parrafo duplicado por la transcripcion. En p536 la transcripcion repitio el final del parrafo de 16.4.1 que empieza en p535 ('...machine learning
applications, for example when modelling the distribution of natural images. ... not known in advance.'): una vez
como <<CONT>> (linea 1, antes de la Fig. 16.11) y otra vez como parrafo suelto con la nota al margen 'Section 6.1.4'
(linea 7, despues del epigrafe). En el original ese texto aparece una sola vez (p536, y~198, despues de la Fig. 16.11,
con la nota al margen Section 6.1.4 a su lado). contdup.py lo marco como 'repetido'.
Correccion: en 03_traduccion/16/c012.json (src y es) se borra el parrafo duplicado (par10) y su nota al margen pasa
dentro del par6, justo antes de 'for example' / 'por ejemplo' (mismo formato en linea que 'distri-{{MARGIN: Section
14.1.2}}bution' de la misma pagina). Se regeneran es.md y en.md ("\\n\\n".join(...) + "\\n").
En 02_transcripcion/p0536.md se borra la linea 7 y la nota pasa a la linea 1 (<<CONT>>), para que una nueva
translate no reproduzca el duplicado. es_pre_registro no se toca (historial de fix_registro).
2) Texto (solo 'es'): concordancia 'dado la variable latente' -> 'dada la variable latente' (c007, x2); terminologia
   '*blanqueado* (*whitening*)' -> '*blanqueamiento* (*whitening*)' (c003; igual que el titulo 16.1.4 y BENGIO 12).
Backup en BISHOP_traduccion/_backup_pre_fix/16_bishop16 (solo la primera vez). Idempotente.
Despues: fix_erratas_notas.py, re-render y validate del cap 16."""
import json
import shutil
from pathlib import Path

W = Path(r"D:\Universidad De Palermo - Maestria en IA\Machine Learning\BISHOP_traduccion")
T = W / "03_traduccion" / "16"
P = W / "02_transcripcion" / "p0536.md"
BK = W / "_backup_pre_fix" / "16_bishop16"
C = T / "c012.json"

DUP = {"src": "{{MARGIN: Section 6.1.4}} for example when modelling the distribution of natural images.",
       "es": "{{MARGIN: Sección 6.1.4}} por ejemplo al modelar la distribución de imágenes naturales."}
INS = {"src": ("applications, for example when modelling the distribution of natural images.",
               "applications, {{MARGIN: Section 6.1.4}}for example when modelling the distribution of natural images."),
       "es": ("aprendizaje automático, por ejemplo al modelar la distribución de imágenes naturales.",
              "aprendizaje automático, {{MARGIN: Sección 6.1.4}}por ejemplo al modelar la distribución de imágenes "
              "naturales.")}
L1 = ("<<CONT>> for example when modelling", "<<CONT>> {{MARGIN: Section 6.1.4}}for example when modelling")

if not BK.exists():
    BK.mkdir(parents=True)
    for f in (C, T / "es.md", T / "en.md", P):
        shutil.copy2(f, BK)

cambios = []
j = json.loads(C.read_text(encoding="utf-8"))
for k in ("src", "es"):
    pars = j[k].split("\n\n")
    dup = [i for i, p in enumerate(pars) if p.startswith(DUP[k])]
    assert len(dup) <= 1, (k, dup)
    if dup:
        assert pars[dup[0] - 1].startswith(("**Figure 16.11**", "**Figura 16.11**")), k
        del pars[dup[0]]
        cambios.append(f"c012 {k}: borrado par{dup[0]}")
    old, new = INS[k]
    t = "\n\n".join(pars)
    if old in t:
        assert t.count(old) == 1, k
        t = t.replace(old, new)
        cambios.append(f"c012 {k}: nota al margen 6.1.4 en el parrafo de 16.4.1")
    assert t.count(new) == 1 and t.count("6.1.4}}") == 1, k
    j[k] = t
assert len(j["src"].split("\n\n")) == len(j["es"].split("\n\n")) == 25
C.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")

REPL = [("dado la variable latente", "dada la variable latente"),
        ("*blanqueado* (*whitening*)", "*blanqueamiento* (*whitening*)")]
cs = sorted(T.glob("c*.json"), key=lambda f: int(f.stem[1:]))
for f in cs:
    if not (BK / f.name).exists():
        shutil.copy2(f, BK)
    x = json.loads(f.read_text(encoding="utf-8"))
    t = x["es"]
    for a, b in REPL:
        if a in t:
            cambios.append(f"{f.stem}: {a!r} x{t.count(a)}")
            t = t.replace(a, b)
    if t != x["es"]:
        x["es"] = t
        f.write_text(json.dumps(x, ensure_ascii=False, indent=1), encoding="utf-8")
J = [json.loads(f.read_text(encoding="utf-8")) for f in cs]
assert not any(a in x["es"] for x in J for a, _ in REPL)
for k, md in (("es", "es.md"), ("src", "en.md")):
    t = "\n\n".join(x[k] for x in J) + "\n"
    (T / md).write_text(t, encoding="utf-8")
    assert t.count("imágenes naturales" if k == "es" else "natural images") == 1, md

lines = P.read_text(encoding="utf-8").split("\n")
dl = [i for i, s in enumerate(lines) if s.startswith("{{MARGIN: Section 6.1.4}} for example when modelling")]
if dl:
    assert lines[dl[0] + 1] == ""
    del lines[dl[0]:dl[0] + 2]
    cambios.append(f"p0536.md: borrada la linea {dl[0] + 1}")
if lines[0].startswith(L1[0]):
    lines[0] = lines[0].replace(L1[0], L1[1], 1)
    cambios.append("p0536.md: nota al margen en la linea 1")
t = "\n".join(lines)
assert t.count("natural images") == 1 and t.startswith(L1[1]), "p0536"
P.write_text(t, encoding="utf-8")
print("cambios:", cambios or "ninguno (ya aplicado)")

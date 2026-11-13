"""GONZALEZ cap 12: correcciones verificadas contra el original (2026-11-02).
1) p914: la transcripcion empezaba con un bloque <<CONT>> espurio ("tion would yield d12(x) > 0. Conversely, ... to which
   that pattern belongs.") que repite el final del parrafo "Figure 12.10 shows a plot of this boundary. Substituting ...
   into this equation would yield ..." de la misma pagina (p913 termina con la ecuacion de la frontera, sin oracion
   cortada). Se quita el bloque espurio de p0914.md y, en en.md / cNNN.json (src y es), el parrafo repetido entre
   <<PAGE 914>> y [[FIG 12.10]].
2) p993/p994 (problemas a dos columnas): el diagrama de red del Problema 12.23 y la imagen de elipses del Problema 12.33
   no tienen rotulo en el original; la transcripcion puso [[FIG P12.23]]/[[FIG P12.33]] y dos DOUBT "not cropped". Se
   recortan a mano (books.py extra_figs[993]/[994]; layout.py p993/p994 --force) y los DOUBT pasan a una NOTA de proceso
   (oculta: no es errata).
3) p974: el titulo "THE EQUATIONS OF A FORWARD PASS THROUGH A CNN" quedo como ## (nivel de seccion numerada); en el
   original es una subseccion (misma fuente que "Multiple Input Images") -> ###, en mayusculas como el original.
4) "forward pass": unificado como "pasada hacia adelante" (habia 13 "pasada" y 8 "pase").
Solo toca 'src' y 'es' de los cNNN.json (los es_pre_* quedan como respaldo historico), en.md, p0914.md, p0974.md,
p0993.md, p0994.md y regenera es.md. Idempotente. Respaldo previo en GONZALEZ_traduccion/_backup_pre_fix/12_gonz12. Correr de nuevo
despues de cualquier transcribe/translate/fix_registro/fix_ingles del cap 12, y despues fix_erratas_notas.py."""
import json
import re
import shutil
from pathlib import Path

W = Path(r"D:\Universidad De Palermo - Maestria en IA\Machine Learning\GONZALEZ_traduccion")
T = W / "03_traduccion" / "12"
TR = W / "02_transcripcion"

D993 = ("<!-- DOUBT: figure P12.23 not cropped — the neural network diagram for problem 12.23 appears on the page but is "
        "not in the list of cropped figures -->")
N993 = ("<!-- NOTA: el diagrama de red del Problema 12.23 no tiene rotulo en el original; va como figura extra P12.23 "
        "(recorte manual, extra_figs). -->")
D994 = "<!-- DOUBT: figure in problem 12.33 not in the cropped figures list; used label P12.33 -->"
N994 = ("<!-- NOTA: la imagen de elipses del Problema 12.33 no tiene rotulo en el original; va como figura extra P12.33 "
        "(recorte manual, extra_figs). -->")
REPS = [(D993, N993), (D994, N994)]
# 3) p974: "THE EQUATIONS OF A FORWARD PASS THROUGH A CNN" tiene en el original la misma fuente/tamano que las subsecciones
#    (Futura-Heavy 11, como "Multiple Input Images" y "MULTILAYER FEEDFORWARD NEURAL NETWORKS"): nivel ### y no ##. Se
#    conservan las mayusculas del original. 4) "forward pass" estaba traducido como "pasada" (13, titulos incluidos) y
#    "pase" (8): se unifica en "pasada hacia adelante".
HEAD = [("\n## THE EQUATIONS OF A FORWARD PASS THROUGH A CNN\n", "\n### THE EQUATIONS OF A FORWARD PASS THROUGH A CNN\n")]
ES_ONLY = [("\n## LAS ECUACIONES DE UN PASE HACIA ADELANTE A TRAVÉS DE UNA CNN\n",
            "\n### LAS ECUACIONES DE UNA PASADA HACIA ADELANTE A TRAVÉS DE UNA CNN\n"),
           ("un único pase hacia adelante", "una única pasada hacia adelante"),
           ("en el pase hacia adelante", "en la pasada hacia adelante"),
           ("describen el pase hacia adelante", "describen la pasada hacia adelante"),
           ("para el pase hacia adelante", "para la pasada hacia adelante"),
           ("de un pase hacia adelante", "de una pasada hacia adelante"),
           ("en un pase hacia adelante", "en una pasada hacia adelante")]
# parrafo repetido al comienzo de p914 (en src y en es), hasta la figura 12.10
DUP = re.compile(r"(<<PAGE 914>>\n\n)(?:tion would yield|ción daría) [^\n]*\n\n(\[\[FIG 12\.10\]\])")

cs = sorted(T.glob("c*.json"), key=lambda f: int(f.stem[1:]))
p914, p993, p994 = TR / "p0914.md", TR / "p0993.md", TR / "p0994.md"
bk = W / "_backup_pre_fix" / "12_gonz12"
if not bk.exists():
    bk.mkdir(parents=True)
    for f in [p914, p993, p994, T / "en.md", T / "es.md"] + cs:
        shutil.copy2(f, bk / f.name)
if not (bk / "p0974.md").exists():   # agregado en una 2a version del script (antes de tocar p0974.md)
    shutil.copy2(TR / "p0974.md", bk / "p0974.md")


def aplicar(s, es=False):
    s = DUP.sub(r"\1\2", s)
    for a, b in REPS + (ES_ONLY if es else HEAD):
        s = s.replace(a, b)
    return s


cambios = []
t = p914.read_text(encoding="utf-8")
m = re.match(r"<<CONT>> tion would yield [^\n]*\n\n(?=\[\[FIG 12\.10\]\])", t)
if m:
    p914.write_text(t[m.end():], encoding="utf-8")
    cambios.append(p914.name)
p974 = TR / "p0974.md"
for f in (p993, p994, p974, T / "en.md"):
    t = f.read_text(encoding="utf-8")
    t2 = aplicar("\n" + t)[1:]
    if t2 != t:
        f.write_text(t2, encoding="utf-8")
        cambios.append(f.name)
for f in cs:
    j = json.loads(f.read_text(encoding="utf-8"))
    s2, e2 = aplicar(j["src"]), aplicar(j["es"], es=True)
    if (s2, e2) != (j["src"], j["es"]):
        j["src"], j["es"] = s2, e2
        f.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
        cambios.append(f.name)
es = "\n\n".join(json.loads(c.read_text(encoding="utf-8"))["es"] for c in cs) + "\n"
(T / "es.md").write_text(es, encoding="utf-8")
en = (T / "en.md").read_text(encoding="utf-8")
assert "DOUBT" not in es and "DOUBT" not in en and es.count(N993) == 1 and es.count(N994) == 1
assert es.count("[[FIG P12.23]]") == 1 and es.count("[[FIG P12.33]]") == 1
assert en.count("into this equation would yield") == 1 and "tion would yield" not in en.replace("into this equation would yield", "")
assert "<<PAGE 914>>\n\n[[FIG 12.10]]" in es and "<<PAGE 914>>\n\n[[FIG 12.10]]" in en
assert not re.search(r"(?i)\bpase hacia adelante", es) and "\n## THE EQUATIONS OF A FORWARD" not in en
assert es.count("\n### LAS ECUACIONES DE UNA PASADA HACIA ADELANTE A TRAVÉS DE UNA CNN\n") == 1
assert not p914.read_text(encoding="utf-8").startswith("<<CONT>>")
assert "DOUBT" not in p993.read_text(encoding="utf-8") + p994.read_text(encoding="utf-8")
print("cambios:", cambios or "ninguno (ya aplicado)")

"""BISHOP cap 12: correcciones verificadas contra el original (2026-11-02).
1) p384: la transcripcion empezaba con un bloque <<CONT>> espurio ("efficiency, we can introduce residual connections ...
   same as the input") que repite el comienzo del parrafo con margen "Section 9.5" de la misma pagina. El ensamblado lo
   pego al final de p383 ("To improve training ...", antes del Algoritmo 12.2) y el texto quedaba duplicado despues de
   la Fig. 12.8. Se quita el bloque espurio de p0384.md y, en en.md / cNNN.json, la repeticion del segundo parrafo (el
   primero ya contiene la oracion completa; el segundo sigue con "dimensionality, namely $N \\times D$").
2) p421: la transcripcion empezaba con "<<CONT>> $y_1 = A$" (rotulo de la tabla del Ejercicio 12.15 duplicado, no es texto
   de p420). Se quita de p0421.md y del final del enunciado ("$p(y_1, y_2)$: $y_1 = A$" -> "$p(y_1, y_2)$:").
3) Algoritmos 12.1-12.3 (regla de prompts.py): el Algoritmo 12.2 habia quedado con "**Algorithm 12.2:**", "**Input:**" y
   "**Output:**" en ingles -> Algoritmo/Entrada/Salida. Los comentarios entre backticks de los Algoritmos 12.1 y 12.3
   quedaban en ingles -> se traducen (mismo criterio que BISHOP 07). `Y(X)` (notacion) se mantiene.
Solo toca 'es' y 'src' de los cNNN.json (los es_pre_* quedan como respaldo historico), en.md, p0384.md, p0421.md y
regenera es.md. Idempotente. Respaldo previo en BISHOP_traduccion/_backup_pre_fix/12_bishop12. Correr de nuevo despues de
cualquier transcribe/translate/fix_registro/fix_ingles del cap 12, y despues fix_erratas_notas.py."""
import json
import shutil
from pathlib import Path

W = Path(r"D:\Universidad De Palermo - Maestria en IA\Machine Learning\BISHOP_traduccion")
T = W / "03_traduccion" / "12"
TR = W / "02_transcripcion"

DUP_EN = ("efficiency, we can introduce residual connections that bypass the multi-head structure. To do this we require "
          "that the output dimensionality is the same as the input")
DUP_ES = ("Para mejorar la eficiencia, podemos introducir conexiones residuales que omitan la estructura multi-cabezal. "
          "Para ello requerimos que la dimensionalidad de salida sea la misma que la de entrada")

SRC = [
    # 1) repeticion despues de la Fig. 12.8
    ("{{MARGIN: Section 9.5}} " + DUP_EN + "\n{{MARGIN: Section 7.4.3}} dimensionality, namely",
     "{{MARGIN: Section 9.5}} {{MARGIN: Section 7.4.3}} dimensionality, namely"),
    # 2) rotulo duplicado de la tabla del Ejercicio 12.15
    ("$p(y_1, y_2)$: $y_1 = A$\n\n<<PAGE 421>>", "$p(y_1, y_2)$:\n\n<<PAGE 421>>"),
]
ES = [
    ("{{MARGIN: Sección 9.5}} " + DUP_ES + "\n{{MARGIN: Sección 7.4.3}} dimensionalidad, a saber $N \\times D$.",
     "{{MARGIN: Sección 9.5}} {{MARGIN: Sección 7.4.3}} a saber, $N \\times D$."),
    ("$p(y_1, y_2)$: $y_1 = A$\n\n<<PAGE 421>>", "$p(y_1, y_2)$:\n\n<<PAGE 421>>"),
    ("**Algorithm 12.2:** Atención multi-cabezal", "**Algoritmo 12.2:** Atención multi-cabezal"),
    ("\n**Input:** Conjunto de tokens", "\n**Entrada:** Conjunto de tokens"),
    ("\n**Output:** $\\mathbf{Y} \\in", "\n**Salida:** $\\mathbf{Y} \\in"),
    ("// `compute queries` $", "// `calcular consultas` $"),
    ("// `compute keys` $", "// `calcular claves` $"),
    ("// `compute values` $", "// `calcular valores` $"),
    ("// `Y(X)` from Algorithm 12.2", "// `Y(X)` del Algoritmo 12.2"),
    ("// `shared neural network`", "// `red neuronal compartida`"),
]
P384_DUP = "<<CONT>> " + DUP_EN + "\n\n"
P421_DUP = "<<CONT>> $y_1 = A$\n\n"

cs = sorted(T.glob("c*.json"), key=lambda f: int(f.stem[1:]))
p384, p421 = TR / "p0384.md", TR / "p0421.md"
bk = W / "_backup_pre_fix" / "12_bishop12"
if not bk.exists():
    bk.mkdir(parents=True)
    for f in [p384, p421, T / "en.md", T / "es.md"] + cs:
        shutil.copy2(f, bk / f.name)


def aplicar(s, pares):
    for a, b in pares:
        if a in s:
            assert s.count(a) == 1, a[:60]
            s = s.replace(a, b)
    return s


cambios = []
for f, dup in ((p384, P384_DUP), (p421, P421_DUP)):
    t = f.read_text(encoding="utf-8")
    if t.startswith(dup):
        f.write_text(t[len(dup):], encoding="utf-8")
        cambios.append(f.name)
f = T / "en.md"
t = f.read_text(encoding="utf-8")
t2 = aplicar(t, SRC)
if t2 != t:
    f.write_text(t2, encoding="utf-8")
    cambios.append(f.name)
for f in cs:
    j = json.loads(f.read_text(encoding="utf-8"))
    s2, e2 = aplicar(j["src"], SRC), aplicar(j["es"], ES)
    if (s2, e2) != (j["src"], j["es"]):
        j["src"], j["es"] = s2, e2
        f.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
        cambios.append(f.name)
es = "\n\n".join(json.loads(c.read_text(encoding="utf-8"))["es"] for c in cs) + "\n"
(T / "es.md").write_text(es, encoding="utf-8")
en = (T / "en.md").read_text(encoding="utf-8")
assert es.count("omitan la estructura multi-cabezal") == 1 and en.count("bypass the multi-head structure") == 1
assert "$y_1 = A$\n\n<<PAGE 421>>" not in es and "$y_1 = A$\n\n<<PAGE 421>>" not in en
assert "**Algorithm " not in es and "**Input:**" not in es and "**Output:**" not in es
assert "`compute" not in es and "from Algorithm" not in es and "`shared" not in es
assert not p384.read_text(encoding="utf-8").startswith("<<CONT>>")
assert not p421.read_text(encoding="utf-8").startswith("<<CONT>>")
print("cambios:", cambios or "ninguno (ya aplicado)")

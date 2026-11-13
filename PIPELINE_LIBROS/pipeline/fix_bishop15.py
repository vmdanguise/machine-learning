"""BISHOP cap 15: correcciones de la traduccion verificadas contra el original (2026-11-02, bitacora BISHOP/15).
1) Algoritmo 15.1 (regla de prompts.py): los comentarios entre backticks quedaban en ingles -> se traducen (mismo
   criterio que BISHOP 07, 12 y 14); titulo 'Algoritmo $K$-means' -> 'Algoritmo $K$-medias'.
   Erratas del original que se conservan con nota visible (fix_erratas_notas.py, claves BISHOP15_Alg15.1/2/3):
   Alg. 15.1 '**for** $N \\in \\{1, \\ldots, N\\}$' (deberia ser n); Alg. 15.2 '**return** $\\{\\mathbf{x}_k\\}$'
   (deberia ser mu_k); Alg. 15.3 '$\\mathcal{L} \\leftarrow p(\\mathbf{X}|...)$ // Evaluate log likelihood' (falta ln).
2) Terminologia: '$K$-means' (12) y '$K$*-means*' (1) -> '$K$-medias' / '$K$*-medias*' (28 apariciones, forma del
   titulo 15.1); titulo 15.3 'Expectativa-Maximizacion' -> 'Esperanza-Maximizacion' y 'paso de *expectativa*' ->
   '*esperanza*' (glosario books.py: expectation = esperanza; el resto del cap ya dice esperanza-maximizacion);
   'vectores del libro de codigos' -> 'vectores de codebook' (forma de BISHOP 12 y del resto del cap);
   'mezclas gaussianas' -> 'mezclas de gaussianas'.
Solo toca 'es' de 03_traduccion/15/cNNN.json y regenera es.md ("\\n\\n".join(es) + "\\n"). Idempotente.
Respaldo previo en BISHOP_traduccion/_backup_pre_fix/15_bishop15. Correr de nuevo despues de cualquier
translate/fix_registro/fix_ingles del cap 15, y despues fix_erratas_notas.py."""
import json
import shutil
from pathlib import Path

W = Path(r"D:\Universidad De Palermo - Maestria en IA\Machine Learning\BISHOP_traduccion")
T = W / "03_traduccion" / "15"
BK = W / "_backup_pre_fix" / "15_bishop15"
REPL = [
    ("`// Initially set all assignments to zero`", "`// Inicialmente, todas las asignaciones en cero`"),
    ("`// Update assignments`", "`// Actualizar las asignaciones`"),
    ("`// Update prototype vectors`", "`// Actualizar los vectores prototipo`"),
    ("`// Assignments unchanged`", "`// Asignaciones sin cambios`"),
    ("el algoritmo $K$*-means* (Lloyd, 1982)", "el algoritmo $K$*-medias* (Lloyd, 1982)"),
    ("$K$-means", "$K$-medias"),
    ("## 15.3 Algoritmo de Expectativa-Maximización", "## 15.3 Algoritmo de Esperanza-Maximización"),
    ("En el paso de *expectativa* (*expectation*)", "En el paso de *esperanza* (*expectation*)"),
    ("los $K$ vectores del libro de códigos", "los $K$ vectores de codebook"),
    ("particular de las mezclas gaussianas.", "particular de las mezclas de gaussianas."),
]

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
        n = t.count(a)
        if n:
            cambios.append((c.name, a[:40], n))
            t = t.replace(a, b)
    if t != j["es"]:
        j["es"] = t
        c.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
    es.append(t)
md = "\n\n".join(es) + "\n"
(T / "es.md").write_text(md, encoding="utf-8")
for bad in ("-means", "`// Initially", "`// Update", "`// Assignments", "xpectativa", "libro de códigos",
            "mezclas gaussianas"):
    assert bad not in md, bad
assert md.count("$K$-medias") == 40 and md.count("**Algoritmo 15.") == 3, (md.count("$K$-medias"),)
print("cambios:", cambios or "ninguno (ya aplicado)")

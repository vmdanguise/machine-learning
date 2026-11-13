"""BISHOP cap 14: correcciones de la traduccion verificadas contra el original (2026-11-02, bitacora BISHOP/14).
1) Algoritmos 14.1-14.4 (regla de prompts.py): los rotulos de 14.1-14.3 habian quedado "**Algorithm 14.N:**" y el 14.2
   ademas "**Input:**"/"**Output:**" -> Algoritmo/Entrada/Salida. Los comentarios entre backticks del 14.2 quedaban en
   ingles -> se traducen como en el 14.1 (mismo criterio que BISHOP 07 y 12).
   El comentario "// Iterative message-passing" de 14.1 y 14.2 esta asi en el original (errata: copiado del Algoritmo
   13.1); se conserva traducido y lleva nota visible (fix_erratas_notas.py, clave BISHOP14_Alg14.1).
2) Terminologia: 'distribucion de propuesta' (10) -> 'distribucion propuesta' (15, forma mayoritaria del cap);
   'over-relaxation' quedaba en ingles en 4 lugares -> 'sobre-relajacion' (forma del cap: Ejercicio 14.14), con la
   glosa en ingles en la primera aparicion; 'ordered over-relaxation' -> 'sobre-relajacion ordenada'.
Solo toca 'es' de 03_traduccion/14/cNNN.json y regenera es.md ("\\n\\n".join(es) + "\\n"). Idempotente.
Respaldo previo en BISHOP_traduccion/_backup_pre_fix/14_bishop14. Correr de nuevo despues de cualquier
translate/fix_registro/fix_ingles del cap 14, y despues fix_erratas_notas.py."""
import json
import shutil
from pathlib import Path

W = Path(r"D:\Universidad De Palermo - Maestria en IA\Machine Learning\BISHOP_traduccion")
T = W / "03_traduccion" / "14"
BK = W / "_backup_pre_fix" / "14_bishop14"
REPL = [
    ("**Algorithm 14.1:** Muestreo de Metropolis", "**Algoritmo 14.1:** Muestreo de Metropolis"),
    ("**Algorithm 14.2:** Muestreo de Metropolis-Hastings", "**Algoritmo 14.2:** Muestreo de Metropolis-Hastings"),
    ("**Algorithm 14.3:** Muestreo de Gibbs", "**Algoritmo 14.3:** Muestreo de Gibbs"),
    ("\n**Input:** Distribución no normalizada", "\n**Entrada:** Distribución no normalizada"),
    ("\n**Output:** $\\mathbf{z} \\sim", "\n**Salida:** $\\mathbf{z} \\sim"),
    ("`// get distribution index for this iteration`", "`// obtener el índice de distribución para esta iteración`"),
    ("`// sample from proposal distribution`", "`// muestrear de la distribución propuesta`"),
    ("`// sample from uniform`", "`// muestrear de la distribución uniforme`"),
    ("Distribuciones de propuesta $", "Distribuciones propuestas $"),
    ("distribución de propuesta", "distribución propuesta"),
    ("se denomina *over-relaxation* (Adler, 1981)", "se denomina *sobre-relajación* (*over-relaxation*) (Adler, 1981)"),
    ("En el marco del *over-relaxation*, el valor", "En el marco de la sobre-relajación, el valor"),
    ("El efecto de la sobre-relajación (*over-relaxation*) es", "El efecto de la sobre-relajación es"),
    ("El marco del *ordered over-relaxation* (Neal, 1999)",
     "El marco de la *sobre-relajación ordenada* (*ordered over-relaxation*) (Neal, 1999)"),
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
for bad in ("**Algorithm ", "**Input:**", "**Output:**", "`// get", "`// sample", "distribución de propuesta",
            "del *over-relaxation*", "Distribuciones de propuesta"):
    assert bad not in md, bad
assert md.count("over-relaxation") == 2 and md.count("**Algoritmo 14.") == 4
print("cambios:", cambios or "ninguno (ya aplicado)")

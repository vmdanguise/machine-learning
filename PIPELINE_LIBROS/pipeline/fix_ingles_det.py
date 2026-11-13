"""Reemplazos deterministas de restos en ingles que la pasada LLM (fix_ingles.py) no resolvio (2026-11-01).
Opera sobre el campo 'es' de 03_traduccion/<cap>/cNNN.json (guarda es_pre_ingles_det) y regenera es.md.
La matematica ($...$) no se toca: los reemplazos son solo sobre texto fuera de formulas.
Cada reemplazo declara cuantas veces debe aparecer en el capitulo; si no coincide, aborta sin escribir."""
import json
import sys
from pathlib import Path

ROOT = Path(r"D:\Universidad De Palermo - Maestria en IA\Machine Learning")
FIXES = {
    ("BISHOP", "07"): [
        ("`// evaluate gradient vector`", "`// evaluar el vector gradiente`", 1),
        ("`// element-wise multiply`", "`// multiplicación elemento a elemento`", 1),
        ("`// bias correction`", "`// corrección del sesgo`", 2),
        ("`// element-wise operations`", "`// operaciones elemento a elemento`", 1),
        ("`// weight vector update`", "`// actualización del vector de pesos`", 1),
        ("shuffle data", "mezclar los datos", 1),
        ("**until** convergence", "**until** convergencia", 4),
    ],
    ("GONZALEZ", "07"): [
        ("> **Note:** Recall that $N = 2^n$, so $n = \\log_2 N$.",
         "> **Nota:** Recordemos que $N = 2^n$, por lo que $n = \\log_2 N$.", 1),
        ("> **Note:** $\\mathbf{I}_1$ is a $1 \\times 1$ identity matrix $[1]$ and $\\mathbf{I}_0$ is the empty matrix "
         "of size $0 \\times 0$.",
         "> **Nota:** $\\mathbf{I}_1$ es una matriz identidad de $1 \\times 1$, $[1]$, e $\\mathbf{I}_0$ es la matriz "
         "vacía de tamaño $0 \\times 0$.", 1),
    ],
    ("DUDAHART", "03"): [
        ("**Algoritmo** (Backward algorithm)", "**Algoritmo** (algoritmo hacia atrás)", 1),
    ],
    ("DUDAHART", "04"): [
        ("**train weight:**", "**entrenar el peso:**", 1),
        ("**find nearest pt not in**", "**buscar el punto más cercano que no esté en**", 1),
        ("**set radius:**", "**fijar el radio:**", 1),
        ("**if** cat de todos los", "**if** la categoría de todos los", 1),
    ],
    ("DUDAHART", "05"): [
        ("**Algorithm 2** (Newton descent)", "**Algoritmo 2** (descenso de Newton)", 1),
        ("a_i^-$ for all $i$", "a_i^-$ para todo $i$", 2),
    ],
    ("DUDAHART", "06"): [
        ("add hidden unit", "agregar una unidad oculta", 1),
    ],
    ("DUDAHART", "07"): [
        ("$w_{ij}$ for $i, j", "$w_{ij}$ para $i, j", 1),
        ("$s_i$, for $i", "$s_i$, para $i", 1),
        ("or convergence criterion met", "o se cumple el criterio de convergencia", 1),
    ],
    ("DUDAHART", "08"): [
        ("**while** $j > 0$ and $\\mathbf{x}[j]", "**while** $j > 0$ y $\\mathbf{x}[j]", 1),
        ('**print** "parse of" **x** "successful in $G$"', '**print** "análisis de" **x** "exitoso en $G$"', 1),
        ("read $\\mathbf{x}_i^+$ from $\\mathcal{D}^+$", "leer $\\mathbf{x}_i^+$ de $\\mathcal{D}^+$", 1),
        ("#### $\\oplus$ *Section 8.4*", "#### $\\oplus$ *Sección 8.4*", 1),
        ("$\\oplus$ *Section 8.6*", "$\\oplus$ *Sección 8.6*", 1),
    ],
    # cap 9: el capitulo usa "Teorema No Free Lunch" (31 veces); se unifican 4 variantes sueltas
    ("DUDAHART", "09"): [
        ("Teorema de No Hay Almuerzo Gratis (*No Free Lunch Theorem*)", "Teorema No Free Lunch", 1),
        ('Teorema "Sin Almuerzo Gratis"', 'Teorema "No Free Lunch"', 3),
        ('Teorema "No Free Lunch" (*No Free Lunch Theorem*)', 'Teorema "No Free Lunch"', 1),
    ],
    # cap 10: lineas del Algoritmo 7 (p650) que quedaron en ingles ("threshold" y "no more patterns" van en fix_dudahart10.py)
    ("DUDAHART", "10"): [
        ("**do** accept new $\\mathbf{x}$", "**do** aceptar un nuevo $\\mathbf{x}$", 1),
        ("**else** add new $\\boldsymbol{\\mu}", "**else** agregar un nuevo $\\boldsymbol{\\mu}", 1),
    ],
}

# Uso: python fix_ingles_det.py [LIBRO:CAP ...]   (sin argumentos aplica todo; con argumentos solo esos capitulos,
# para no re-aplicar entradas de capitulos ya corregidos, cuyos conteos ya no coinciden)
if len(sys.argv) > 1:
    sel = {tuple(a.upper().split(":")) for a in sys.argv[1:]}
    FIXES = {k: v for k, v in FIXES.items() if k in sel}
    assert FIXES, f"ningun capitulo coincide con {sys.argv[1:]}"

ok = True
plan = []
for (book, cap), reps in FIXES.items():
    d = ROOT / f"{book}_traduccion" / "03_traduccion" / cap
    cs = sorted(d.glob("c*.json"), key=lambda f: int(f.stem[1:]))
    js = [(c, json.loads(c.read_text(encoding="utf-8"))) for c in cs]
    for a, b, n in reps:
        cnt = sum(j["es"].count(a) for _, j in js)
        if cnt == 0 and sum(j.get("es_pre_ingles_det", "").count(a) for _, j in js) == n:
            continue   # ya aplicado en una corrida anterior (el original queda en es_pre_ingles_det)
        if cnt != n:
            print(f"ERROR {book} {cap}: '{a}' aparece {cnt} veces (esperado {n})")
            ok = False
    plan.append((book, cap, d, js, reps))
if not ok:
    sys.exit(1)
for book, cap, d, js, reps in plan:
    for c, j in js:
        es = j["es"]
        for a, b, _ in reps:
            es = es.replace(a, b)
        if es != j["es"]:
            j.setdefault("es_pre_ingles_det", j["es"])
            j["es"] = es
            c.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"  {book} {cap} {c.name}")
    (d / "es.md").write_text("\n\n".join(j["es"] for _, j in js) + "\n", encoding="utf-8")
print("OK")

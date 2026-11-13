"""DUDAHART cap 10: correcciones manuales verificadas contra el PDF original (2026-11-02).
Aplica cada reemplazo en 02_transcripcion/pNNNN.md (texto en ingles), en en.md, en los cNNN.json
(src = ingles; es y es_pre_* = espanol) y regenera es.md. Idempotente (si el texto nuevo ya esta, no hace nada).
Respaldo previo en DUDAHART_traduccion/_backup_pre_fix/10. Correr de nuevo despues de cualquier transcribe/translate/
fix_registro/fix_ingles del cap 10.

1) Algoritmo 2 (p616/617): el titulo "Algorithm 2 (Fuzzy k-means clustering)" esta al pie de p616 y el cuerpo en p617;
   la transcripcion dejaba el titulo suelto en p616 y un bloque "**Algorithm** (Fuzzy k-means)" inventado en p617.
   Queda un solo bloque en p617 con el encabezado "**Algorithm 2** (Fuzzy k-means clustering)".
2) Algoritmo 3 (p637): titulo duplicado (suelto + encabezado del bloque); se quita el suelto.
3) Algoritmo 7 (p649/650): el bloque de p649 no cerraba ':::' antes del salto de pagina (por eso la Fig. 10.17 quedaba
   dentro del bloque y el render no veia su marcador); se cierra. "threshold" -> "umbral" y
   "**until** no more patterns" -> "**until** no haya mas patrones" (solo en el espanol).
4) DOUBT p623: las dos graficas de p(theta|x_1..x_n) no tienen rotulo en el original -> figura extra EX10.1
   (books.py extra_figs[623]) + NOTA.
5) DOUBT p652 / p674: los 'xx' del epigrafe de la Fig. 10.19 y de los vectores del Problema 23 estan asi en el original
   (placeholders del borrador del libro, verificado en la imagen) -> NOTA.
"""
import json
from pathlib import Path

W = Path(r"D:\Universidad De Palermo - Maestria en IA\Machine Learning\DUDAHART_traduccion")
T = W / "03_traduccion" / "10"

D623 = ("<!-- DOUBT: figure on this page (two plots of p(θ|x_1,...,x_n) vs θ) is not in the list of already cropped "
        "figures; used label P10.22 as a placeholder -->")
N623 = ("<!-- NOTA: las dos graficas de p(θ|x_1,...,x_n) del Ejemplo 1 (prior uniforme ancha arriba, angosta abajo) no "
        "tienen rotulo en el original; van como figura extra EX10.1 (recorte manual, extra_figs). -->")
D652 = ("<!-- DOUBT: Figure 10.19 caption values for ρ are printed as \"xx\" and \"0.xx\" — OCR unreadable; "
        "transcribed as placeholders -->")
N652 = ("<!-- NOTA: el epigrafe de la Fig. 10.19 trae 'ρ = xx' y 'ρ = 0.xx' en el original (placeholders del borrador "
        "del libro, verificado en la imagen; la figura tambien esta vacia en el original); se conserva tal cual. -->")
D674 = ("<!-- DOUBT: Problem 23 vectors are illegible in the image (shown as \"xx/xx\" placeholders); actual values "
        "cannot be determined from the scan. -->")
N674 = ("<!-- NOTA: los vectores x_1..x_4 del Problema 23 figuran como 'xx' en el original (placeholders del borrador "
        "del libro, verificado en la imagen); se conserva tal cual. -->")

# (paginas de transcripcion, viejo_en, nuevo_en, viejo_es, nuevo_es, tambien_en_es_pre)
FIXES = [
    ((616, 617), "**Algorithm 2 (Fuzzy k-means clustering)**\n\n<<PAGE 617>>", "<<PAGE 617>>",
     "**Algoritmo 2 (Agrupamiento *fuzzy* k-means)**\n\n<<PAGE 617>>", "<<PAGE 617>>", True),
    ((617,), ":::algorithm\n**Algorithm** (Fuzzy k-means)\n", ":::algorithm\n**Algorithm 2** (Fuzzy k-means clustering)\n",
     ":::algorithm\n**Algorithm** (Fuzzy k-means)\n", ":::algorithm\n**Algoritmo 2** (Agrupamiento *fuzzy* k-means)\n", True),
    ((637,), "**Algorithm 3 (Basic iterative minimum-squared-error clustering)**\n\n:::algorithm", ":::algorithm",
     "**Algoritmo 3 (Agrupamiento iterativo básico de error cuadrático mínimo)**\n\n:::algorithm", ":::algorithm", True),
    ((649,), "\\leftarrow$ threshold\n\n<<PAGE 650>>", "\\leftarrow$ threshold\n:::\n\n<<PAGE 650>>",
     "\\leftarrow$ threshold\n\n<<PAGE 650>>", "\\leftarrow$ umbral\n:::\n\n<<PAGE 650>>", True),
    ((), None, None, "**until** no more patterns", "**until** no haya más patrones", False),
    ((623,), "[[FIG P10.22]]", "[[FIG EX10.1]]", "[[FIG P10.22]]", "[[FIG EX10.1]]", True),
    ((623,), D623, N623, D623, N623, True),
    ((652,), D652, N652, D652, N652, True),
    ((674,), D674, N674, D674, N674, True),
]

# transcripciones (los textos 'en' sin <<PAGE>>: se arman por pagina)
TRANS = {
    616: [("\n\n**Algorithm 2 (Fuzzy k-means clustering)**\n", "\n")],
    617: [(":::algorithm\n**Algorithm** (Fuzzy k-means)\n", ":::algorithm\n**Algorithm 2** (Fuzzy k-means clustering)\n")],
    637: [("**Algorithm 3 (Basic iterative minimum-squared-error clustering)**\n\n:::algorithm", ":::algorithm")],
    649: [("\\leftarrow$ threshold\n", "\\leftarrow$ threshold\n:::\n")],
    623: [("[[FIG P10.22]]", "[[FIG EX10.1]]"), (D623, N623)],
    652: [(D652, N652)],
    674: [(D674, N674)],
}
cambios = []
for p, reps in TRANS.items():
    f = W / "02_transcripcion" / f"p{p:04d}.md"
    t = f.read_text(encoding="utf-8")
    t0 = t
    for a, b in reps:
        if p == 649:
            if t.rstrip("\n").endswith(":::"):
                continue
            assert t.endswith(a), repr(t[-80:])
            t = t[: -len(a)] + b
        elif a in t:
            t = t.replace(a, b)
        else:
            assert b in t or (p == 616 and t.endswith("algorithm:\n")), (p, a[:50])
    if t != t0:
        f.write_text(t, encoding="utf-8")
        cambios.append(f.name)

en = T / "en.md"
t = en.read_text(encoding="utf-8")
t0 = t
for _, a, b, _, _, _ in FIXES:
    if a is None or (a in b and b in t):
        continue
    t = t.replace(a, b)
if t != t0:
    en.write_text(t, encoding="utf-8")
    cambios.append("en.md")

cs = sorted(T.glob("c*.json"), key=lambda f: int(f.stem[1:]))
for f in cs:
    j = json.loads(f.read_text(encoding="utf-8"))
    ch = False
    for k in list(j):
        if not isinstance(j[k], str) or not (k in ("src", "es") or k.startswith("es_pre")):
            continue
        s = j[k]
        for _, a_en, b_en, a_es, b_es, pre in FIXES:
            if k == "src":
                a, b = a_en, b_en
            else:
                if k != "es" and not pre:
                    continue
                a, b = a_es, b_es
                if k != "es" and a_es == "\\leftarrow$ threshold\n\n<<PAGE 650>>":
                    b = "\\leftarrow$ threshold\n:::\n\n<<PAGE 650>>"   # es_pre_*: solo cerrar el bloque
            if a is None:
                continue
            if a in b and b in s:      # ya aplicado (el nuevo contiene al viejo)
                continue
            if a in s:
                s = s.replace(a, b)
        if s != j[k]:
            j[k] = s
            ch = True
    if ch:
        f.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
        cambios.append(f.name)

es = "\n\n".join(json.loads(c.read_text(encoding="utf-8"))["es"] for c in cs) + "\n"
(T / "es.md").write_text(es, encoding="utf-8")
src = "".join(json.loads(c.read_text(encoding="utf-8"))["src"] for c in cs)
for bad in ("DOUBT", "P10.22", "**Algorithm** (Fuzzy", "Algoritmo 2 (Agrupamiento", "Algoritmo 3 (Agrupamiento",
            "no more patterns", "$ threshold\n\n"):
    assert bad not in es, bad
for bad in ("DOUBT", "P10.22", "**Algorithm** (Fuzzy", "**Algorithm 2 (", "**Algorithm 3 ("):
    assert bad not in src, bad
assert es.count("**Algoritmo 2** (Agrupamiento *fuzzy* k-means)") == 1
assert es.count("Algoritmo 3") >= 1 and es.count("**Algoritmo 3** (") == 1
assert es.count("[[FIG EX10.1]]") == 1 and es.count("umbral\n:::") == 1
print("cambios:", cambios or "ninguno (ya aplicado)")

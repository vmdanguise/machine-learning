"""Resuelve a mano los DOUBT del cap 9 (verificados contra el PDF original el 2026-11-01).
Aplica el mismo reemplazo en 02_transcripcion/pNNNN.md, en los cNNN.json (src/es/es_pre_*) y en es.md."""
import json
from pathlib import Path

ROOT = Path(r"D:\Universidad De Palermo - Maestria en IA\Machine Learning")
CAP = "09"
FIXES = {
    ("DUDAHART", 584): [(
        "<!-- DOUBT: The three circle diagrams (P=1/3, P=1/4, P=1/2) are inline figures with no \"Figure N\" label; "
        "placed [[FIG EX9.38]] as an unnumbered figure marker but the exact label is uncertain -->",
        "<!-- NOTA: los tres diagramas de circulos (P=1/3, P=1/4, P=1/2) del Problema 38 no tienen rotulo en el original; "
        "van como figura extra EX9.38 (recorte manual, extra_figs). -->")],
    # omision de transcripcion: faltaba la frase que introduce la Ec. 5 (verificado en la imagen de p537)
    ("DUDAHART", 537): [(
        "| | | $\\mathbf{x}_3$ OR $\\mathbf{x}_4$ | NOT $f_1$ | | |\n\n$$\n\\sum_{r=0}^{n}",
        {"en": "| | | $\\mathbf{x}_3$ OR $\\mathbf{x}_4$ | NOT $f_1$ | | |\n\nThe total number of predicates in the absence of constraints is\n\n$$\n\\sum_{r=0}^{n}",
         "es": "| | | $\\mathbf{x}_3$ OR $\\mathbf{x}_4$ | NOT $f_1$ | | |\n\nEl número total de predicados en ausencia de restricciones es\n\n$$\n\\sum_{r=0}^{n}"})],
}


def apply(s, reps, lang="en"):
    for a, b in reps:
        if isinstance(b, dict):
            b = b[lang]
        if b in s:
            continue   # ya aplicado
        s = s.replace(a, b)
    return s


for (book, page), reps in FIXES.items():
    W = ROOT / f"{book}_traduccion"
    p = W / "02_transcripcion" / f"p{page:04d}.md"
    t = p.read_text(encoding="utf-8")
    t2 = apply(t, reps)
    p.write_text(t2, encoding="utf-8")
    print(book, page, "transcripcion", t != t2)
    d = W / "03_traduccion" / CAP
    cs = sorted(d.glob("c*.json"), key=lambda f: int(f.stem[1:]))
    for f in cs:
        j = json.loads(f.read_text(encoding="utf-8"))
        ch = False
        for k in [k for k in j if k in ("src", "es") or k.startswith("es_pre")]:
            if isinstance(j[k], str):
                n = apply(j[k], reps, "en" if k == "src" else "es")
                if n != j[k]:
                    j[k] = n
                    ch = True
        if ch:
            f.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
            print("  ", f.name)
    en = d / "en.md"
    if en.exists():
        en.write_text(apply(en.read_text(encoding="utf-8"), reps, "en"), encoding="utf-8")
    (d / "es.md").write_text("\n\n".join(json.loads(c.read_text(encoding="utf-8"))["es"] for c in cs) + "\n",
                             encoding="utf-8")

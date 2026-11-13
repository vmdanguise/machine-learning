"""Resuelve a mano los DOUBT del cap 7 (verificados contra el PDF original el 2026-11-01).
Aplica el mismo reemplazo en 02_transcripcion/pNNNN.md, en los cNNN.json (src/es/es_pre_registro) y en es.md."""
import json
from pathlib import Path

ROOT = Path(r"D:\Universidad De Palermo - Maestria en IA\Machine Learning")
T71_DOUBT = ("<!-- DOUBT: The table contains scaling function and wavelet function graphs (plots) which are figures "
             "embedded within table cells; they have been omitted per instructions as they are part of the table's "
             "figure content. The table structure has been simplified since the graph cells cannot be rendered in "
             "Markdown. -->")
FIXES = {
    ("BISHOP", 245): [(
        "<!-- DOUBT: equation 7.59 uses $(a_{ni} - \\mu_i)^2$ but may be $(a_{ni} - \\mu_n)^2$ given context; transcribed as printed -->",
        "<!-- NOTA: la Ec. (7.59) dice mu_i en el original (errata del libro: deberia ser mu_n); se conserva tal cual. -->")],
    ("GONZALEZ", 521): [(
        "<!-- DOUBT: Equation (7-152) is partially illegible; the full integrand/limits are unclear from the image. -->",
        "<!-- NOTA: la Ec. (7-152) esta corrupta en el propio PDF fuente (se ve solo '1 int^inf c'); se conserva como esta. -->")],
    ("GONZALEZ", 526): [
        ("| [[FIG T7.1]] | |", "| (ver gráficas abajo) | |"),
        (T71_DOUBT, "[[FIG T7.1]]\n\n<!-- NOTA: las columnas de graficas de la Tabla 7.1 van como una sola figura recortada (T7.1) debajo de la tabla. -->")],
    ("DUDAHART", 428): [(
        "<!-- DOUBT: the expression \"+1\\sqrt{3/N}\" for the upper bound of the weight range may be \"+\\sqrt{3/N}\" — the OCR shows \"+14/3/N\" which is ambiguous; image suggests $+\\sqrt{3/N}$ -->",
        "<!-- NOTA: el original imprime '+1 sqrt(3/N)' (verificado en la imagen); se conserva tal cual. -->")],
}
# en la traduccion el texto de celda va en espanol; en src/transcripcion en ingles
CELL_EN = "| (see plots below) | |"


def apply(s, reps, lang):
    for a, b in reps:
        if lang == "en" and b == "| (ver gráficas abajo) | |":
            b = CELL_EN
        s = s.replace(a, b)
    return s


for (book, page), reps in FIXES.items():
    W = ROOT / f"{book}_traduccion"
    p = W / "02_transcripcion" / f"p{page:04d}.md"
    t = p.read_text(encoding="utf-8")
    t2 = apply(t, reps, "en")
    p.write_text(t2, encoding="utf-8")
    print(book, page, "transcripcion", t != t2)
    d = W / "03_traduccion" / "07"
    for f in sorted(d.glob("c*.json"), key=lambda f: int(f.stem[1:])):
        j = json.loads(f.read_text(encoding="utf-8"))
        ch = False
        for k, lang in (("src", "en"), ("es", "es"), ("es_pre_registro", "es")):
            if k in j:
                n = apply(j[k], reps, lang)
                if n != j[k]:
                    j[k] = n
                    ch = True
        if ch:
            f.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
            print("  ", f.name)
    cs = sorted(d.glob("c*.json"), key=lambda f: int(f.stem[1:]))
    (d / "es.md").write_text("\n\n".join(json.loads(c.read_text(encoding="utf-8"))["es"] for c in cs) + "\n", encoding="utf-8")

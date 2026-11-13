"""Genera las versiones Word (.docx) a partir de los .tex con pandoc.

El LaTeX es la fuente: editar en Overleaf, bajar los .tex y correr
    python herramientas/latex_a_word.py
Las ecuaciones quedan como ecuaciones nativas de Word (editables) y las
figuras se toman en PNG desde documentos/latex/figuras.
"""

import re
import tempfile
from pathlib import Path

import pypandoc

RAIZ = Path(__file__).resolve().parents[1]
LATEX = RAIZ / "documentos" / "latex"
WORD = RAIZ / "documentos" / "word"

# Macros propias y entornos que pandoc no conoce: se reemplazan por equivalentes estándar.
MACROS = r"""
\newcommand{\R}{\mathbb{R}}
\newcommand{\E}{\mathbb{E}}
\newcommand{\simplex}{\Delta^{N-1}}
\newcommand{\TPR}{\mathrm{TPR}}
\newcommand{\FPR}{\mathrm{FPR}}
\newcommand{\bm}[1]{\boldsymbol{#1}}
"""
ENTORNOS = {"teorema": "Teorema", "proposicion": "Proposición", "lema": "Lema",
            "definicion": "Definición", "hipotesis": "Hipótesis"}


def _expandir_includes(texto, base):
    def reemplazar(m):
        ruta = base / (m.group(2) if m.group(2).endswith(".tex") else m.group(2) + ".tex")
        return _expandir_includes(ruta.read_text(encoding="utf-8"), base)
    return re.sub(r"\\(include|input)\{([^}]+)\}", reemplazar, texto)


def _preparar(texto):
    texto = re.sub(r"\\pendiente\{", r"\\textbf{[Pendiente: }\\emph{", texto)
    contador = {"hipotesis": 0}
    for env, nombre in ENTORNOS.items():
        def abrir(m, env=env, nombre=nombre):
            titulo = nombre
            if env == "hipotesis":
                contador["hipotesis"] += 1
                titulo = f"Hipótesis H{contador['hipotesis']}"
            extra = f" ({m.group(1)})" if m.group(1) else ""
            return f"\\par\\noindent\\textbf{{{titulo}{extra}.}} \\emph{{"
        texto = re.sub(rf"\\begin\{{{env}\}}(?:\[([^\]]*)\])?", abrir, texto)
        texto = texto.replace(f"\\end{{{env}}}", "}\\par")
    texto = re.sub(r"\\begin\{proof\}", r"\\par\\noindent\\emph{Demostración.} ", texto)
    texto = texto.replace(r"\end{proof}", r" $\blacksquare$\par")
    texto = re.sub(r"\\label\{h:[^}]+\}", "", texto)
    texto = re.sub(r"\\ref\{h:(\w+)\}", lambda m: {"convexo": "H1", "noconvexo": "H2", "profundidad": "H3",
                                                    "adaptativos": "H4", "entropia": "H5"}[m.group(1)], texto)
    return texto


def convertir(nombre_tex, nombre_docx):
    fuente = LATEX / nombre_tex
    texto = fuente.read_text(encoding="utf-8").replace(r"\input{preambulo}", "")
    texto = _expandir_includes(texto, LATEX)
    nuevas = "".join(l + "\n" for l in MACROS.strip().splitlines()
                     if l.split("}")[0] + "}" not in texto)
    texto = texto.replace(r"\begin{document}", nuevas + r"\begin{document}", 1)
    texto = _preparar(texto)
    texto = re.sub(r"\\includegraphics(\[[^\]]*\])?\{([^}.]+)\}", r"\\includegraphics\1{figuras/\2.png}", texto)

    WORD.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".tex", dir=LATEX, delete=False, encoding="utf-8") as tmp:
        tmp.write(texto)
        ruta_tmp = Path(tmp.name)
    try:
        args = ["--citeproc", f"--bibliography={LATEX / 'referencias.bib'}", f"--resource-path={LATEX}",
                "--number-sections", "-M", "lang=es-AR", "-M", "reference-section-title=Bibliografía"]
        if nombre_tex == "main.tex":
            args += ["--toc", "-M", "toc-title=Índice"]
        plantilla = WORD / "plantilla.docx"
        if plantilla.exists():
            args.append(f"--reference-doc={plantilla}")
        pypandoc.convert_file(str(ruta_tmp), "docx", format="latex", outputfile=str(WORD / nombre_docx), extra_args=args)
    finally:
        ruta_tmp.unlink(missing_ok=True)
    print("Generado:", WORD / nombre_docx)


if __name__ == "__main__":
    convertir("anteproyecto.tex", "Anteproyecto.docx")
    convertir("main.tex", "TP_Final_Crisis_EEG.docx")

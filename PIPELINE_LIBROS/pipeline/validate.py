"""Validador de capitulos traducidos (los 5 libros, incluido BENGIO con su pipeline original).

Chequeos por capitulo:
  - paginas: cada pagina del rango tiene transcripcion y marcador <<PAGE n>> en es.md, y el HTML tiene un
    'p. orig.' por pagina
  - KaTeX: 0 errores en logs/render_NN.json y ningun 'katex-error' en el HTML; render sin observaciones
  - DOUBT/DUDA: ninguno en es.md ni en las transcripciones
  - <<CONT>>: ninguno en es.md (marcador de continuacion no unido: quedaria literal en el PDF)
  - registro: sin voseo, tu ni usted (fuera de formulas y codigo); avisos de 'usted implicito' y de imperativos de
    usted al inicio de oracion ('Considere', 'Repita') para revisar
  - titulos duplicados en el HTML final (mismo titulo no numerado repetido, o dos titulos iguales seguidos)
  - figuras: cada [[FIG X]] tiene epigrafe 'Figura X' (negrita o cursiva) cerca, salvo excepciones documentadas
    (figuras que en el original no tienen epigrafe); cada epigrafe tiene figura recortada
  - PDF presente y mas nuevo que el HTML

Uso: python validate.py [LIBRO ...] [--caps 01,02] [--json salida.json]
"""
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(r"D:\Universidad De Palermo - Maestria en IA\Machine Learning")
sys.path.insert(0, str(Path(__file__).parent))
from books import BOOKS  # noqa: E402

# Figuras que en el ORIGINAL no tienen epigrafe (o lo tienen compartido con otra) -> no es error.
# clave: (LIBRO, etiqueta) -> motivo
FIG_NO_CAPTION = {
}
# Ademas, toda figura definida a mano en books.py "extra_figs" (graficos de ejemplos/problemas/tablas sin rotulo
# "Figure N" en el original: P2.14, T2.3, EX3.1a...) es por definicion una figura sin epigrafe -> aviso, no error.

# Epigrafes que en el ORIGINAL no tienen figura recortable (figura vacia/placeholder, o "figura" que es una ecuacion)
CAPTION_NO_FIG = {
    ("BENGIO", "2.2"): "la 'figura' es la matriz identidad tipografiada (se transcribe como ecuacion)",
    ("DUDAHART", "6.10"): "en el original la figura esta vacia (epigrafe con 'xxx' de borrador)",
}

# Citas textuales de terceros (epigrafes) que usan 2a persona en su traduccion canonica: se excluyen del chequeo de
# registro (aviso, no error). Texto exacto tal como aparece en es.md.
CITAS_TEXTUALES = {
    ("GONZALEZ", "07"): [("No os conforméis a este siglo, sino transformaos por medio de la renovación de vuestro "
                          "entendimiento.", "epígrafe: Romanos 12:2, cita textual (Reina-Valera)")],
    ("BENGIO", "08"): [("Tu and Honavar, 2011", "cita bibliográfica: 'Tu' es apellido de autor")],
    ("DUDAHART", "10"): [("Te Won Lee", "bibliografía [38]: 'Te Won Lee' es nombre de autor")],
}
# Titulos no numerados que se repiten legitimamente en el original
TITULO_REPETIDO_OK = {
    ("DUDAHART", "07", "representación"): "el original tiene 'Representation' en 7.5.1 (p435) y en 7.6 (p439)",
    ("GONZALEZ", "10", "antecedentes"): "el original tiene 'Background' en 10.2 (p703) y en 10.7 (p787)",
    ("GONZALEZ", "12", "formulación matricial"): ("el original tiene 'Matrix Formulation' en la pasada hacia adelante (p951) "
                                                  "y en la retropropagacion (p957), ambas en 12.5"),
    ("DUDAHART", "08", "sección 8 3"): "'Section 8.3' encabeza los Problemas (p503) y los Computer exercises (p514)",
}

STOP_ES = set("""mas más después despues través traves inglés ingles francés frances país pais además ademas
atrás atras jamás jamas detrás detras demás demas quizás quizas interés interes revés reves japonés japones
alemán aleman según segun también tambien está esta están estan será sera serán seran podrá podra podrán podran
habrá habra habrán habran tendrá tendra deberá debera dará dara hará hara irá ira vendrá vendra saldrá saldra
cortés holandés escocés danés finlandés portugués chino aún aun allá alla acá aca sofás sofas mamás papás
compás compas atrás anís maíz raíz raiz país marqués marques burgués estrés estres ciprés tapiz
""".split())

VOSEO_WORDS = re.compile(
    r"\b(vos|sos|podés|tenés|querés|sabés|hacés|decís|venís|sentís|elegís|seguís|conocés|necesitás|"
    r"usás|mirás|pensás|fijate|fíjate|mirá|tomá|usá|notá|considerá|observá|recordá|pensá|imaginá|probá|"
    r"intentá|escribí|leé|elegí|seguí|andá|vení|hacé|poné|tené|decí|sabé|calculá|definí|suponé|"
    r"verificá|comprobá|ejecutá|instalá|descargá|abrí|corré|cargá|guardá|creá|agregá|reemplazá)\b", re.I)
TU_WORDS = re.compile(r"\b(tú|tu|tus|ti|contigo|te|usted|ustedes|vosotros|vuestro|vuestra|os)\b", re.I)
# usted implicito (3a persona dirigida al lector): avisos para revisar a mano
USTED_HINT = re.compile(
    r"\b(si (ya )?(está|esta|conoce|tiene|desea|quiere|necesita|prefiere|es usted)|"
    r"(puede|podrá|debe|deberá) (usted|saltar|consultar|omitir|leer)\b|le (recomendamos|sugerimos|invitamos)|"
    r"(su|sus) (computadora|máquina|código|propio|propia|lector))", re.I)

# imperativo de usted al inicio de oracion o de inciso ('Considere', '**5.2** Repita', '(*Sugerencia:* Estudie',
# '(c) Suponga'): aviso, no error (2026-11-02, AJUSTES/2026-11-02 octava tanda). Solo formas mayusculas que no
# coinciden con sustantivos (Ajuste, Detalle, Trace, Pase), autores (Lea, Halle, Lee), 3a persona del indicativo
# (Cree, Toma, Nota) ni ingles (Use, Note). Las impersonales con -se (Considerese, Notese) no coinciden.
USTED_IMP_VERBS = (
    "Considere|Suponga|Demuestre|Muestre|Calcule|Determine|Encuentre|Obtenga|Verifique|Compruebe|Explique|Utilice|"
    "Escriba|Dibuje|Grafique|Repita|Pruebe|Deduzca|Exprese|Evalúe|Discuta|Esboce|Bosqueje|Describa|Implemente|Elija|"
    "Imagine|Recuerde|Observe|Tenga|Asuma|Compare|Justifique|Proponga|Diseñe|Construya|Identifique|Indique|Resuelva|"
    "Estime|Aplique|Simplifique|Escoja|Realice|Ejecute|Consulte|Fíjese|Piense|Modifique|Interprete|Analice|"
    "Desarrolle|Formule|Enumere|Sugiera|Preste|Quede|Asegúrese|Estudie|Especifique|Programe|Investigue|Plantee|"
    "Reescriba|Intente|Comience|Empiece|Continúe|Enuncie|Sustituya|Haga|Ponga|Vuelva|Busque|Revise|Responda|Defina|"
    "Normalice|Entrene|Clasifique|Seleccione|Etiquete|Represente|Mida|Juzgue|Decida|Visualice")
USTED_IMP = re.compile(
    r"(?:^|(?<=[.!?:;])\s+|(?<=[.!?:;][\"”)*_])\s+|\(\s*)(?:[\s*_\\\-–—\"“]|\*\*[\w.()]+\*\*|\(\w{1,3}\)|\d+[.)])*"
    rf"({USTED_IMP_VERBS})\b", re.M)

HEAD_RE = re.compile(r"<h([1-4])[^>]*>(.*?)</h\1>", re.S)
PAGE_RE = re.compile(r"^<<PAGE (\d+)>>\s*$", re.M)
FIG_RE = re.compile(r"^\[\[FIG ([\w.\-]+)\]\]\s*$", re.M)


def load_bengio_units():
    spec = importlib.util.spec_from_file_location("bengio_config", ROOT / "BENGIO_traduccion" / "pipeline" / "config.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.UNITS


def book_info(book):
    if book == "BENGIO":
        w = ROOT / "BENGIO_traduccion"
        units = [u for u in load_bengio_units() if re.fullmatch(r"\d\d", u[0])]
        return w, units, (lambda uid: w / "04_html" / f"{uid}.html"), (lambda uid: w / "05_pdf_capitulos" / f"{uid}.pdf")
    b = BOOKS[book]
    w = ROOT / b["work"]
    return (w, b["units"], (lambda uid: w / "04_html" / f"{book}_cap{uid}_es.html"),
            (lambda uid: w / "05_pdf_capitulos" / f"{book}_cap{uid}_es.pdf"))


def strip_nonprose(md):
    md = re.sub(r"```.*?```", " ", md, flags=re.S)
    md = re.sub(r"\$\$.*?\$\$", " ", md, flags=re.S)
    md = re.sub(r"(?<!\\)\$(?:\\.|[^$\\])+?\$", " ", md)
    md = re.sub(r"`[^`]*`", " ", md)
    md = re.sub(r"\[\^p\d+-\d+\]:.*", " ", md)   # notas bibliograficas (titulos en ingles)
    return md


def ctx(text, m, w=60):
    a, b = max(0, m.start() - w), min(len(text), m.end() + w)
    return text[a:b].replace("\n", " ")


def head_key(t):
    t = re.sub(r"<[^>]+>", "", t)
    return re.sub(r"\W+", " ", t).strip().lower()


def check_unit(book, w, u, html_of, pdf_of):
    uid = u[0]
    pages = list(range(u[2], u[3] + 1))
    errs, warns = [], []
    es_p = w / "03_traduccion" / uid / "es.md"
    if not es_p.exists():
        return {"uid": uid, "errors": ["falta es.md"], "warnings": [], "pages": len(pages)}
    es = es_p.read_text(encoding="utf-8")
    # paginas
    marks = [int(x) for x in PAGE_RE.findall(es)]
    miss = [p for p in pages if p not in marks]
    if miss:
        errs.append(f"paginas sin marcador en es.md: {miss}")
    extra = [p for p in marks if p not in pages]
    if extra:
        errs.append(f"marcadores fuera de rango: {extra}")
    notr = [p for p in pages if not (w / "02_transcripcion" / f"p{p:04d}.md").exists()]
    if notr:
        errs.append(f"paginas sin transcripcion: {notr}")
    # DOUBT
    for m in re.finditer(r"DOUBT|DUDA", es):
        errs.append(f"DOUBT en es.md: {ctx(es, m)}")
    for p in pages:
        f = w / "02_transcripcion" / f"p{p:04d}.md"
        if f.exists() and re.search(r"DOUBT|DUDA", f.read_text(encoding="utf-8")):
            errs.append(f"DOUBT en transcripcion p{p}")
    # <<CONT>> no unido por join_pages (iba despues de un flotante en la transcripcion): queda literal en el PDF
    for m in re.finditer(r"<<CONT>>", es):
        errs.append(f"CONT literal en es.md (correr fix_cont_literal.py): {ctx(es, m)}")
    # registro
    prose = strip_nonprose(es)
    for cita, why in CITAS_TEXTUALES.get((book, uid), []):
        if cita in prose:
            prose = prose.replace(cita, " ")
            warns.append(f"registro: cita textual excluida ({why})")
    for m in VOSEO_WORDS.finditer(prose):
        errs.append(f"voseo: …{ctx(prose, m)}…")
    for m in TU_WORDS.finditer(prose):
        errs.append(f"tú/usted: …{ctx(prose, m)}…")
    for m in USTED_HINT.finditer(prose):
        warns.append(f"usted implícito?: …{ctx(prose, m)}…")
    for m in USTED_IMP.finditer(prose):
        warns.append(f"imperativo de usted? ({m.group(1)}): …{ctx(prose, m)}…")
    # html / pdf / render
    hp, pp = html_of(uid), pdf_of(uid)
    if not hp.exists():
        errs.append("falta HTML")
    else:
        h = hp.read_text(encoding="utf-8")
        n_orig = h.count('class="origpage"')
        if n_orig != len(pages):
            errs.append(f"HTML con {n_orig} marcas de pagina original, se esperaban {len(pages)}")
        if "katex-error" in h:
            errs.append(f"HTML con {h.count('katex-error')} katex-error")
        heads = [(int(l), head_key(t)) for l, t in HEAD_RE.findall(h)]
        seen = {}
        for i, (l, k) in enumerate(heads):
            if i and heads[i - 1][1] == k:
                errs.append(f"titulo duplicado consecutivo: {k!r}")
            if not re.match(r"^(capítulo )?\d", k) and k in seen:
                if (book, uid, k) in TITULO_REPETIDO_OK:
                    warns.append(f"titulo repetido {k!r} (excepción: {TITULO_REPETIDO_OK[(book, uid, k)]})")
                else:
                    errs.append(f"titulo no numerado repetido: {k!r}")
            seen[k] = 1
        if not pp.exists():
            errs.append("falta PDF")
        elif pp.stat().st_mtime + 1 < hp.stat().st_mtime:
            errs.append("PDF mas viejo que el HTML")
    lg = w / "logs" / f"render_{uid}.json"
    if lg.exists():
        j = json.loads(lg.read_text(encoding="utf-8"))
        if j.get("katex_errors"):
            errs.append(f"render: {j['katex_errors']} errores KaTeX")
        for it in j.get("issues", []):
            errs.append(f"render: {it}")
    else:
        errs.append("falta log de render")
    # figuras y epigrafes
    blocks = [b.strip() for b in re.split(r"\n\s*\n", es) if b.strip()]
    labels = []
    extra_labels = {lab for v in BOOKS.get(book, {}).get("extra_figs", {}).values() for lab, _, _ in v}
    for i, b in enumerate(blocks):
        m = FIG_RE.match(b)
        if not m:
            continue
        lab = m.group(1)
        labels.append(lab)
        # "2.24c" = continuacion de la figura 2.24 en otra pagina: su epigrafe es "Figura 2.24 (Continuación)"
        base = lab[:-1] if re.fullmatch(r"[\d]+[.\-][\d]+c", lab) else lab
        cap_re = re.compile(r"^\*{1,2}_?(Figura|Figure)\s+" + re.escape(base) + r"(?![\d])")
        near = blocks[max(0, i - 4): i + 6]
        if any(cap_re.match(x) for x in near):
            continue
        # epigrafe compartido: [[FIG 3-2]] [[FIG 3-3]] seguidos y un solo epigrafe que cubre ambos
        if (book, lab) in FIG_NO_CAPTION:
            warns.append(f"figura {lab} sin epígrafe (excepción: {FIG_NO_CAPTION[(book, lab)]})")
            continue
        if lab in extra_labels:
            warns.append(f"figura {lab} sin epígrafe (excepción: figura sin rótulo en el original, extra_figs)")
            continue
        errs.append(f"figura {lab} sin epígrafe cercano")
    for m in re.finditer(r"^\*{1,2}_?(?:Figura|Figure)\s+([\d]+[.\-][\d]+[a-z]?)", es, re.M):
        if m.group(1) not in labels and m.group(1) + "c" not in labels:
            if (book, m.group(1)) in CAPTION_NO_FIG:
                warns.append(f"epígrafe de figura {m.group(1)} sin figura (excepción: {CAPTION_NO_FIG[(book, m.group(1))]})")
            else:
                warns.append(f"epígrafe de figura {m.group(1)} sin marcador [[FIG]]")
    return {"uid": uid, "errors": errs, "warnings": warns, "pages": len(pages)}


def main():
    args = sys.argv[1:]
    out_json = None
    caps = None
    if "--json" in args:
        i = args.index("--json")
        out_json = args[i + 1]
        del args[i:i + 2]
    if "--caps" in args:
        i = args.index("--caps")
        caps = set(args[i + 1].split(","))
        del args[i:i + 2]
    books = args or ["BENGIO", "BISHOP", "FUNDAMENTALS", "GONZALEZ", "DUDAHART"]
    res = {}
    tot_e = 0
    for bk in books:
        w, units, html_of, pdf_of = book_info(bk)
        for u in units:
            if caps and u[0] not in caps:
                continue
            if not (w / "03_traduccion" / u[0] / "es.md").exists():
                continue
            r = check_unit(bk, w, u, html_of, pdf_of)
            res[f"{bk} {u[0]}"] = r
            tot_e += len(r["errors"])
            flag = "OK " if not r["errors"] else "ERR"
            print(f"{flag} {bk:12s} {u[0]}  pags={r['pages']:3d}  errores={len(r['errors'])}  avisos={len(r['warnings'])}")
            for e in r["errors"]:
                print(f"     E {e}")
            for wn in r["warnings"]:
                print(f"     w {wn}")
    print(f"TOTAL capitulos={len(res)} errores={tot_e}")
    if out_json:
        Path(out_json).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()

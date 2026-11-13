"""Etapa 4: Markdown traducido -> HTML (KaTeX server-side) -> PDF (Chrome headless) por unidad.
(Derivado de BENGIO_traduccion/pipeline/render.py; agrega notas al margen, bloques de codigo, citas/notas y
etiquetas de figura con guion.)

Uso: $env:BOOK="X"; python render.py 01   -> <LIBRO>_traduccion/05_pdf_capitulos/01.pdf (+ 04_html/01.html)
"""
import base64
import html
import json
import re
import subprocess
import sys
from pathlib import Path

from markdown_it import MarkdownIt

import layout
from config import (D_TRAD, D_HTML, D_PDF, D_LOG, D_TOOLS, D_LAYOUT, CHROME, UNITS, B, BOOK, unit, unit_pages)
from mdblocks import split_blocks, INLINE_MATH, dedup_running_heads

MD = MarkdownIt("commonmark", {"html": False, "typographer": False}).enable("table")
KATEX_DIR = D_TOOLS / "node_modules" / "katex" / "dist"
FONTS = D_TOOLS / "fonts"

CSS = r"""
@font-face { font-family: "LMRoman"; src: url("FONTS/lmroman10-regular.otf"); font-weight: normal; font-style: normal; }
@font-face { font-family: "LMRoman"; src: url("FONTS/lmroman10-italic.otf"); font-weight: normal; font-style: italic; }
@font-face { font-family: "LMRoman"; src: url("FONTS/lmroman10-bold.otf"); font-weight: bold; font-style: normal; }
@font-face { font-family: "LMRoman"; src: url("FONTS/lmroman10-bolditalic.otf"); font-weight: bold; font-style: italic; }
@font-face { font-family: "LMMono"; src: url("FONTS/lmmono10-regular.otf"); }
@page { size: Letter; margin: 22mm 24mm 22mm 24mm;
  @bottom-center { content: counter(page); font-family: "LMRoman"; font-size: 9.5pt; } }
html { font-family: "LMRoman", "Cambria", serif; font-size: 11pt; line-height: 1.38; color: #000; }
body { margin: 0; hyphens: auto; -webkit-hyphens: auto; }
p { margin: 0 0 0.55em 0; text-align: justify; orphans: 2; widows: 2; }
h1 { font-size: 24pt; font-weight: bold; margin: 0 0 1.2em 0; line-height: 1.2; break-before: page; }
h1.first { break-before: avoid; }
h1 .num { display: block; font-size: 18pt; margin: 2.2em 0 0.4em 0; }
h2 { font-size: 15pt; margin: 1.3em 0 0.5em 0; break-after: avoid; }
h3 { font-size: 12.5pt; margin: 1.1em 0 0.4em 0; break-after: avoid; }
h4 { font-size: 11pt; margin: 1em 0 0.3em 0; break-after: avoid; }
.katex { font-size: 1.0em; }
.katex-display > .katex { font-size: 1.0em; }
.katex-display { margin: 0.7em 0; overflow: hidden; }
@media screen { body { width: 167.9mm; } }
.eq { break-inside: avoid; }
figure { margin: 1em 0 0.4em 0; text-align: center; break-inside: avoid; break-after: avoid; }
figure img { max-width: 100%; max-height: 200mm; }
p.caption { font-size: 9.8pt; text-align: justify; line-height: 1.32; margin-bottom: 1em; }
table { border-collapse: collapse; margin: 0.8em auto; font-size: 9.6pt; break-inside: auto; }
th, td { border: 0.6pt solid #444; padding: 3pt 5pt; vertical-align: top; text-align: left; }
th { background: #f0f0f0; }
.fn { font-size: 9.3pt; text-align: justify; margin: 0 0 0.5em 0; line-height: 1.3; }
.fnblock { border-top: 0.5pt solid #888; margin: 0.6em 0 0.8em 0; padding-top: 0.3em; }
sup.fnref { font-size: 0.72em; }
.origpage { text-align: right; font-size: 7pt; color: #aaa; margin: 0.15em 0 -0.35em 0; line-height: 1; }
pre.code { font-family: "LMMono", monospace; font-size: 8.8pt; line-height: 1.25; border: 0.8pt solid #b00;
  border-radius: 4pt; padding: 0.6em 1em; margin: 1em 2em; white-space: pre-wrap; break-inside: avoid; color: #500; }
code, .tt { font-family: "LMMono", monospace; font-size: 0.95em; }
blockquote { margin: 0.8em 1.5em; padding: 0.3em 0.8em; border-left: 2pt solid #888; font-size: 10pt; color: #222; }
blockquote p { margin: 0.2em 0; }
.margin { float: right; clear: right; width: 0; height: 0; overflow: visible; }
.mnote { color: #b00; font-style: italic; font-size: 8.5pt; white-space: nowrap; background: #fff5f5;
  border: 0.4pt solid #e0b0b0; border-radius: 2pt; padding: 0 3pt; margin: 0 2pt; }
.note { color: #a00; font-size: 8pt; }
.algorithm { border-top: 1pt solid #000; border-bottom: 1pt solid #000; margin: 1em 0; padding: 0.3em 0; break-inside: avoid; font-size: 10.2pt; }
.algorithm .algcap { border-bottom: 0.6pt solid #000; padding-bottom: 0.3em; margin-bottom: 0.3em; text-align: justify; }
.algorithm .algline { white-space: normal; margin: 0.08em 0; text-align: left; }
"""

HEAD_RE = re.compile(r"^(#{1,4})\s+(.*)$")
FIG_RE = re.compile(r"^\[\[FIG ([\w.\-]+)\]\]$")
FN_DEF = re.compile(r"^\[\^(p\d+-\d+)\]:\s*(.*)$", re.S)
FN_REF = re.compile(r"\[\^(p\d+-\d+)\]")
PAGE_RE = re.compile(r"^<<PAGE (\d+)>>$")
CAP_RE = re.compile(r"^\*\*(Figura|Figure|Tabla|Table|Ecuación|Equation)\s+([\d.\-]+)[:.]?\*\*")
MARGIN_RE = re.compile(r"\{\{MARGIN:\s*(.*?)\}\}")


class MathRenderer:
    def __init__(self):
        self.items = []
        self.res = {}

    def add(self, tex, display):
        i = f"⟪{len(self.items)}⟫"
        self.items.append({"id": i, "tex": tex, "display": display})
        return i

    def run(self):
        if not self.items:
            return
        p = subprocess.run(["node", str(D_TOOLS / "katex_render.js")], input=json.dumps(self.items),
                           capture_output=True, text=True, encoding="utf-8", cwd=str(D_TOOLS))
        if p.returncode != 0:
            raise RuntimeError(p.stderr[:2000])
        self.res = json.loads(p.stdout)


def fig_index(pages):
    idx = {}
    for p in pages:
        f = D_LAYOUT / f"p{p:04d}.json"
        if not f.exists():
            continue
        for fg in json.loads(f.read_text(encoding="utf-8"))["figures"]:
            if fg.get("png"):
                idx[fg["label"]] = D_LAYOUT / "figs" / fg["png"]
    return idx


def data_uri(path):
    return "data:image/png;base64," + base64.b64encode(Path(path).read_bytes()).decode("ascii")


class Renderer:
    def __init__(self, uid):
        self.uid = uid
        self.u = unit(uid)
        self.pages = unit_pages(uid)
        layout.run(self.pages)
        self.figs = fig_index(self.pages)
        self.used_figs = set()
        self.math = MathRenderer()
        self.issues = []
        self.cur_page = self.pages[0]

    def printed(self, pno):
        try:
            return layout.load(pno).get("printed", str(pno))
        except Exception:
            return str(pno)

    def _post(self, h):
        h = re.sub(r"FNREF(p\d+_\d+)FNREF", lambda m: f'<sup class="fnref">{m.group(1).split("_")[1]}</sup>', h)
        h = re.sub(r"MARGIN⟨(.*?)⟩", lambda m: f'<span class="mnote">{m.group(1)}</span>', h)
        return h

    def _pre(self, text):
        t = INLINE_MATH.sub(lambda m: self.math.add(m.group(1), False), text)
        t = FN_REF.sub(lambda m: f"FNREF{m.group(1).replace('-', '_')}FNREF", t)
        t = MARGIN_RE.sub(lambda m: f"MARGIN⟨{html.escape(m.group(1))}⟩", t)
        return t

    def inline(self, text):
        return self._post(MD.renderInline(self._pre(text)))

    def block_html(self, b):
        s = b.strip()
        m = PAGE_RE.match(s)
        if m:
            self.cur_page = int(m.group(1))
            return f'<div class="origpage">[p. orig. {self.printed(self.cur_page)}]</div>'
        if s.startswith("<!--"):
            if "DUDA" in s or "DOUBT" in s:
                self.issues.append(f"p{self.cur_page}: {s}")
            return ""
        if s.startswith(":::"):
            return self.algorithm(s)
        if s.startswith("```"):
            body = s.split("\n", 1)[1] if "\n" in s else ""
            body = body.rsplit("```", 1)[0].rstrip("\n")
            return f'<pre class="code">{html.escape(body)}</pre>'
        m = HEAD_RE.match(s)
        if m and "\n" not in s:
            lvl = len(m.group(1))
            txt = m.group(2)
            if lvl == 1:
                mm = re.match(r"^(Capítulo|Chapter)\s+(\d+)\s*[:.]\s*(.*)$", txt)
                if mm:
                    return (f'<h1 id="C{mm.group(2)}"><span class="num">Capítulo {mm.group(2)}</span>'
                            f'{self.inline(mm.group(3))}</h1>')
            return f"<h{lvl}>{self.inline(txt)}</h{lvl}>"
        if s.startswith("$$"):
            tex = s[2:]
            tex = tex[:-2] if tex.endswith("$$") else tex
            return f'<div class="eq">{self.math.add(tex.strip(), True)}</div>'
        m = FIG_RE.match(s)
        if m:
            lab = m.group(1)
            if lab in self.figs:
                self.used_figs.add(lab)
                return f'<figure class="fig"><img src="{data_uri(self.figs[lab])}" alt="Figura {lab}"></figure>'
            self.issues.append(f"p{self.cur_page}: figura {lab} sin recorte")
            return f'<p class="note">[Figura {lab}: no se pudo recortar — ver página original {self.printed(self.cur_page)}]</p>'
        m = FN_DEF.match(s)
        if m:
            return f'<div class="fnblock"><p class="fn"><sup>{m.group(1).split("-")[1]}</sup> {self.inline(m.group(2))}</p></div>'
        if s.startswith("|"):
            return self._post(MD.render(self._pre(s)))
        if s.startswith(">"):
            return self._post(MD.render(self._pre(s)))
        if CAP_RE.match(s):
            return f'<p class="caption">{self.inline(s)}</p>'
        if re.match(r"^(- |\* |\d+\. )", s):
            return self._post(MD.render(self._pre(s)))
        return f"<p>{self.inline(s)}</p>"

    def algorithm(self, s):
        lines = s.split("\n")[1:]
        if lines and lines[-1].strip() == ":::":
            lines = lines[:-1]
        cap, body, seen = [], [], False
        for ln in lines:
            if ln.strip() == "---" and not seen:
                seen = True
                continue
            (body if seen else cap).append(ln)
        if not seen:
            body, cap = cap, []
        out = ['<div class="algorithm">']
        if cap:
            out.append(f'<div class="algcap">{self.inline(" ".join(c.strip() for c in cap if c.strip()))}</div>')
        for ln in body:
            if not ln.strip():
                continue
            ind = (len(ln) - len(ln.lstrip(" "))) // 2
            out.append(f'<div class="algline" style="padding-left:{1.4 * ind:.1f}em">{self.inline(ln.strip())}</div>')
        out.append("</div>")
        return "\n".join(out)

    def build(self, es_md):
        blocks, removed = dedup_running_heads(split_blocks(es_md))
        for r in removed:
            print(f"  aviso: titulo repetido tras salto de pagina quitado: {r}", flush=True)
        parts = [self.block_html(b) for b in blocks]
        self.math.run()
        htmls = "\n".join(parts)
        bad = []

        def sub(m):
            k = m.group(0)
            r = self.math.res.get(k)
            if r is None:
                return k
            if r["error"]:
                it = next(x for x in self.math.items if x["id"] == k)
                bad.append((it["tex"], r["error"]))
                return r["html"] or f'<span class="note">${html.escape(it["tex"])}$</span>'
            return r["html"]
        htmls = re.sub(r"⟪\d+⟫", sub, htmls)
        for tex, err in bad:
            self.issues.append(f"KaTeX: {err[:160]} :: {tex[:200]}")
        for lab in sorted(set(self.figs) - self.used_figs):
            self.issues.append(f"figura {lab} recortada pero sin marcador [[FIG]] en el texto")
        return htmls, len(self.math.items), len(bad)


FIT_JS = r"""<script>
// ecuaciones desplegadas mas anchas que la caja: reducir la fuente (min ~56%) en vez de scroll / tag superpuesto
function fitEqs() {
  let n = 0;
  document.querySelectorAll('.katex-display').forEach(function (d) {
    const k = d.querySelector(':scope > .katex');
    if (!k) return;
    const tag = k.querySelector('.tag');
    function need() {
      let w = 0;
      k.querySelectorAll(':scope > .katex-html > .base').forEach(function (b) { w += b.getBoundingClientRect().width; });
      const tw = tag ? tag.getBoundingClientRect().width + 14 : 0;
      return Math.max(w + 2 * tw, k.scrollWidth);
    }
    let s = 1.0;
    while (need() > d.clientWidth && s > 0.57) { s -= 0.04; k.style.fontSize = s.toFixed(2) + 'em'; n++; }
  });
  document.body.setAttribute('data-fit', n);
}
document.fonts.ready.then(fitEqs);
</script>"""


def html_doc(body, title):
    css = CSS.replace("FONTS/", FONTS.as_uri() + "/")
    return f"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><title>{html.escape(title)}</title>
<link rel="stylesheet" href="{(KATEX_DIR / 'katex.min.css').as_uri()}">
<style>{css}</style></head><body>
<p style="font-size:8.5pt;color:#666;margin:0 0 1em 0">{html.escape(B['title_es'].strip('"').replace('" (', ' — ').rstrip(')'))} · traducción al español (uso personal)</p>
{body}
{FIT_JS}
</body></html>"""


def chrome_pdf(html_path, pdf_path):
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = pdf_path.with_suffix(".tmp.pdf")
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--allow-file-access-from-files",
           "--run-all-compositor-stages-before-draw", "--virtual-time-budget=20000",
           f"--print-to-pdf={tmp}", html_path.as_uri()]
    subprocess.run(cmd, capture_output=True, timeout=600)
    if not tmp.exists() or tmp.stat().st_size < 1000:
        raise RuntimeError(f"Chrome no genero el PDF de {html_path}")
    tmp.replace(pdf_path)


def render_unit(uid):
    u = unit(uid)
    es = D_TRAD / uid / "es.md"
    if not es.exists():
        raise SystemExit(f"falta traduccion de {uid} (correr translate.py {uid})")
    r = Renderer(uid)
    body, nmath, nbad = r.build(es.read_text(encoding="utf-8"))
    body = body.replace("<h1", '<h1 class="first"', 1)
    name = f"{BOOK}_cap{uid}_es"
    hp = D_HTML / f"{name}.html"
    hp.write_text(html_doc(body, f"{u[1]} — {BOOK}"), encoding="utf-8")
    pdf = D_PDF / f"{name}.pdf"
    chrome_pdf(hp, pdf)
    rep = {"uid": uid, "math": nmath, "katex_errors": nbad, "issues": r.issues}
    (D_LOG / f"render_{uid}.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  R {uid}: {nmath} formulas, {nbad} errores KaTeX, {len(r.issues)} observaciones -> {pdf}")
    return rep


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["all"]:
        args = [u[0] for u in UNITS]
    for a in args:
        render_unit(a)

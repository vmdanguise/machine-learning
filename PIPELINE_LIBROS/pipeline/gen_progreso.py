"""Genera PROGRESO_TRADUCCION.md en la raiz a partir del estado real en disco.

- Avance por libro: capitulos/paginas hechos, tokens (logs/usage.jsonl). Capitulo HECHO = cerrado (validado y con la
  revision visual aprobada): figura en la lista "cerrados" de progreso_notas.json Y tiene PDF. Con PDF pero sin
  cerrar = EN REVISION (no suma al avance).
- Pendientes y bitacora: se leen de progreso_notas.json (editable a mano) y se combinan con datos de disco
  (rango de paginas, fragmentos, fecha del PDF, tokens del capitulo).
Uso: python gen_progreso.py
"""
import ast
import datetime as dt
import json
import re
from pathlib import Path

ROOT = Path(r"D:\Universidad De Palermo - Maestria en IA\Machine Learning")
HERE = Path(__file__).parent
NOTAS = HERE / "progreso_notas.json"

TOTAL_CAPS = {"BENGIO": 20, "BISHOP": 20, "FUNDAMENTALS": 13, "GONZALEZ": 12, "DUDAHART": 10}
TOTAL_PAGS = {"BENGIO": 713, "BISHOP": 597, "FUNDAMENTALS": 357, "GONZALEZ": 972, "DUDAHART": 627}
ORDEN = ["BENGIO", "BISHOP", "FUNDAMENTALS", "GONZALEZ", "DUDAHART"]


def units(book):
    if book == "BENGIO":
        src = (ROOT / "BENGIO_traduccion" / "pipeline" / "config.py").read_text(encoding="utf-8")
        m = re.search(r"UNITS\s*=\s*(\[.*?\n\])", src, re.S)
        return ast.literal_eval(m.group(1))
    src = (HERE / "books.py").read_text(encoding="utf-8")
    i = src.index(f'"{book}": {{')
    m = re.search(r'"units":\s*(\[.*?\]),\s*\n', src[i:], re.S)
    return ast.literal_eval(m.group(1))


def pdf_path(book, cap):
    d = ROOT / f"{book}_traduccion" / "05_pdf_capitulos"
    return d / (f"{cap}.pdf" if book == "BENGIO" else f"{book}_cap{cap}_es.pdf")


def usage(book):
    tot, por_cap = [0, 0], {}
    f = ROOT / f"{book}_traduccion" / "logs" / "usage.jsonl"
    if not f.exists():
        return tot, por_cap
    for line in f.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
        except Exception:
            continue
        tot[0] += r.get("in", 0)
        tot[1] += r.get("out", 0)
        m = re.search(r"(?:^|:)c?(\d\d)(?::|$)", r.get("tag", ""))
        if m:
            c = por_cap.setdefault(m.group(1), [0, 0])
            c[0] += r.get("in", 0)
            c[1] += r.get("out", 0)
    return tot, por_cap


def fmt(n):
    return f"{n:,}".replace(",", ".")


def main():
    notas = json.loads(NOTAS.read_text(encoding="utf-8")) if NOTAS.exists() else {"pendientes": [], "bitacora": {}}
    cerrados = set(notas.get("cerrados", []))
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    filas, bita = [], []
    g = dict(caps=0, tcaps=0, pags=0, tpags=0, tin=0, tout=0)
    for b in ORDEN:
        us = units(b)
        con_pdf = [u for u in us if pdf_path(b, u[0]).exists()]
        hechos = [u for u in con_pdf if f"{b}/{u[0]}" in cerrados]
        revision = [u for u in con_pdf if f"{b}/{u[0]}" not in cerrados]
        pags = sum(u[3] - u[2] + 1 for u in hechos)
        (tin, tout), _ = usage(b)
        caps_txt = ", ".join(u[0] for u in hechos) or "-"
        rev_txt = ", ".join(u[0] for u in revision) or "-"
        filas.append(f"| {b} | {len(hechos)}/{TOTAL_CAPS[b]} | {pags}/{TOTAL_PAGS[b]} | {100 * pags / TOTAL_PAGS[b]:.0f}% | "
                     f"{caps_txt} | {rev_txt} | {fmt(tin)} / {fmt(tout)} |")
        g["caps"] += len(hechos); g["tcaps"] += TOTAL_CAPS[b]; g["pags"] += pags; g["tpags"] += TOTAL_PAGS[b]
        g["tin"] += tin; g["tout"] += tout
        for u in con_pdf:
            cap = u[0]
            d = ROOT / f"{b}_traduccion" / "03_traduccion" / cap
            nfr = len(list(d.glob("c*.json"))) if d.exists() else 0
            fecha = dt.datetime.fromtimestamp(pdf_path(b, cap).stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            nota = notas.get("bitacora", {}).get(f"{b}/{cap}", "")
            est = "cerrado" if u in hechos else "en revisión"
            bita.append(f"| {b} | {cap} | {est} | {u[2]}-{u[3]} ({u[3] - u[2] + 1}) | {nfr} | {fecha} | {nota} |")
    out = [
        "# Progreso de traducción de libros de ML",
        "",
        f"_Generado automáticamente por `PIPELINE_LIBROS/pipeline/gen_progreso.py` — {now}._",
        "_Notas de bitácora y pendientes: `PIPELINE_LIBROS/pipeline/progreso_notas.json`._",
        "",
        "## Avance por libro",
        "",
        "| Libro | Capítulos | Páginas | % págs | Caps hechos | En revisión | Tokens in / out |",
        "|---|---|---|---|---|---|---|",
        *filas,
        f"| **TOTAL** | **{g['caps']}/{g['tcaps']}** | **{g['pags']}/{g['tpags']}** | "
        f"**{100 * g['pags'] / g['tpags']:.0f}%** | | | **{fmt(g['tin'])} / {fmt(g['tout'])}** |",
        "",
        "Capítulo hecho = cerrado (validado con validate.py y revisión visual de recortes aprobada). \"En revisión\" = ya tiene PDF pero todavía no está cerrado; no suma al avance. Páginas = índices del PDF original (0-based, inclusivos). Los tokens incluyen los capítulos en revisión.",
        "",
        "## Pendientes",
        "",
        "| # | Libro | Cap | Pendiente | Estado |",
        "|---|---|---|---|---|",
        *[f"| {i} | {p.get('libro', '')} | {p.get('cap', '')} | {p['texto']} | {p.get('estado', 'abierto')} |"
          for i, p in enumerate(notas.get("pendientes", []), 1)],
        "",
        "## Bitácora por capítulo",
        "",
        "| Libro | Cap | Estado | Págs PDF (n) | Fragmentos | PDF generado | Notas |",
        "|---|---|---|---|---|---|---|",
        *bita,
        "",
    ]
    (ROOT / "PROGRESO_TRADUCCION.md").write_text("\n".join(out), encoding="utf-8")
    print(f"PROGRESO: {g['caps']}/{g['tcaps']} caps, {g['pags']}/{g['tpags']} pags, tokens {g['tin']}/{g['tout']}")


if __name__ == "__main__":
    main()

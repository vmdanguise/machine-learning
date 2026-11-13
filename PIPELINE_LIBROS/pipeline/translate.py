"""Etapa 3 (pasada B): traduccion al espanol de la transcripcion de cada unidad, por fragmentos.

La matematica se PROTEGE con placeholders (⟦M12⟧ en linea, ⟦D3⟧ display, ⟦C1⟧ bloques de codigo) antes de mandar el
texto al LLM y se restaura despues => las formulas quedan byte a byte identicas a la transcripcion. Se valida que todos
los placeholders, marcadores de figura, notas, notas al margen, paginas y filas de tabla sobrevivan; si no, se reintenta.

Checkpoints: 03_traduccion/<unidad>/en.md, cNNN.json, es.md
Uso: $env:BOOK="X"; python translate.py <unidad> [...] [--force] [--workers N]
"""
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor

from config import D_TRANS, D_TRAD, D_LOG, MODEL_TRANSLATE, UNITS, unit, unit_pages
from llm import call
from mdblocks import split_blocks, join_pages, chunk, INLINE_MATH, chunk_dedup
from prompts import SYSTEM_TRANSLATE, USER_TRANSLATE, GLOSSARY_FULL

SYSTEM = SYSTEM_TRANSLATE.replace("{glossary}", GLOSSARY_FULL) + r"""
- PLACEHOLDERS: el texto trae marcadores ⟦M1⟧, ⟦M2⟧... (fórmulas en línea) y líneas ⟦D1⟧... / ⟦C1⟧... (ecuaciones y
  bloques de código). Copialos EXACTAMENTE, cada uno una sola vez, en la posición gramatical que corresponda en español.
  No los traduzcas ni inventes nuevos. Si en inglés dice "the ⟦M3⟧ function" escribí "la función ⟦M3⟧".
"""

PH_RE = re.compile(r"⟦[MDC]\d+⟧")


def protect(blocks):
    mp = {}
    out = []
    for b in blocks:
        s = b.strip()
        if s.startswith("$$") or s.startswith("```"):
            k = f"⟦{'D' if s.startswith('$$') else 'C'}{len(mp) + 1}⟧"
            mp[k] = b
            out.append(k)
            continue

        def rep(m):
            k = f"⟦M{len(mp) + 1}⟧"
            mp[k] = m.group(0)
            return k
        out.append(INLINE_MATH.sub(rep, b))
    return "\n\n".join(out), mp


def restore(text, mp):
    return PH_RE.sub(lambda m: mp.get(m.group(0), m.group(0)), text)


def signature(text):
    return {
        "ph": sorted(PH_RE.findall(text)),
        "fig": sorted(re.findall(r"\[\[FIG [\w.\-]+\]\]", text)),
        "fn": sorted(re.findall(r"\[\^p\d+-\d+\]:?", text)),
        "page": sorted(re.findall(r"<<PAGE \d+>>", text)),
        "margin": len(re.findall(r"\{\{MARGIN:", text)),
        "alg": len(re.findall(r"^:::algorithm", text, re.M)),
        "rows": len(re.findall(r"^\|.*\|\s*$", text, re.M)),
        "h": [len(h) for h in re.findall(r"^(#+) ", text, re.M)],
    }


def diff_sig(a, b):
    return [k for k in a if a[k] != b[k]]


def clean(out):
    out = out.strip()
    if out.startswith("```") and out.endswith("```") and out.count("```") == 2:
        out = out.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return out


def repair(out, sig):
    """Reparaciones deterministas: un titulo extra al inicio copiado del contexto previo."""
    s2 = signature(out)
    if s2["h"] != sig["h"] and s2["h"][1:] == sig["h"]:
        bl = split_blocks(out)
        for k, b in enumerate(bl):
            if PH_RE.fullmatch(b.strip()) or b.startswith("<<PAGE"):
                continue
            if re.match(r"^#+ ", b):
                del bl[k]
                return "\n\n".join(bl)
            break
    return out


def translate_chunk(uid, title, i, n, src, prev, path, force):
    if path.exists() and not force:
        j = json.loads(path.read_text(encoding="utf-8"))
        if j.get("src") == src and j.get("ok") is not None:
            if not j["ok"] and j["issues"] == ["h"]:
                es2 = repair(j["es"], signature(j["src"]))
                if es2 != j["es"] and signature(es2)["h"] == signature(j["src"])["h"]:
                    j.update(es=es2, ok=True, issues=[], repaired="titulo duplicado del contexto previo")
                    path.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
            return j
    prot, mp = protect(split_blocks(src))
    sig = signature(prot)
    user = USER_TRANSLATE.format(unit_title=title, i=i + 1, n=n, prev=prev or "(inicio)", chunk=prot)
    best, best_bad = None, None
    for attempt in range(3):
        extra = "" if attempt == 0 else (
            "\n\nATENCIÓN: en el intento anterior se perdieron o duplicaron estos elementos: "
            + ", ".join(best_bad) + ". Conservá TODOS los placeholders ⟦..⟧, [[FIG]], [^..], {{MARGIN: ..}}, <<PAGE>>, "
            "filas de tabla y títulos.")
        out = clean(call(MODEL_TRANSLATE, SYSTEM, user + extra, max_tokens=16000, temperature=0.2,
                         tag=f"B:{uid}:c{i}:a{attempt}"))
        out = repair(out, sig)
        bad = diff_sig(sig, signature(out))
        if not bad:
            best, best_bad = out, []
            break
        if best is None or len(bad) < len(best_bad):
            best, best_bad = out, bad
    missing = [k for k in mp if k not in best]
    if missing:
        best = best + "\n\n" + "\n\n".join(mp[k] if k[1] in "DC" else k for k in missing)
    es = restore(best, mp)
    j = {"uid": uid, "i": i, "src": src, "es": es, "ok": not best_bad, "issues": best_bad, "missing_math": missing}
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(path)
    if best_bad:
        with open(D_LOG / "traduccion_issues.log", "a", encoding="utf-8") as fh:
            fh.write(f"{uid}\tc{i}\t{best_bad}\tmissing={missing}\n")
    return j


def build_en(uid):
    pages = []
    for p in unit_pages(uid):
        f = D_TRANS / f"p{p:04d}.md"
        if not f.exists():
            raise SystemExit(f"falta transcripcion de la pagina {p} (correr transcribe.py {uid})")
        pages.append((p, normalize_md(f.read_text(encoding="utf-8"))))
    return join_pages(pages)


def normalize_md(md):
    """Limpiezas deterministas de la transcripcion: titulos sin negrita ni punto final en el numero."""
    out = []
    for ln in md.split("\n"):
        m = re.match(r"^(#{1,4})\s+(.*)$", ln)
        if m:
            t = m.group(2).replace("**", "").strip()
            t = re.sub(r"^(\d+(?:\.\d+)*)\.\s", r"\1 ", t)
            ln = f"{m.group(1)} {t}"
        if re.fullmatch(r"\s*\[\[FIG [\w.\-]+\]\]\s*", ln):
            out += ["", ln.strip(), ""]   # el marcador siempre como bloque propio
            continue
        out.append(ln)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out))


def translate_unit(uid, force=False, workers=3):
    u = unit(uid)
    d = D_TRAD / uid
    d.mkdir(parents=True, exist_ok=True)
    en = build_en(uid)
    (d / "en.md").write_text(en, encoding="utf-8")
    parts, removed = chunk_dedup(split_blocks(en))
    if removed:
        print(f"  {uid}: titulos repetidos de encabezado de pagina quitados: {removed}", flush=True)
    chunks = ["\n\n".join(c) for c in parts]
    prevs = [""] + [c[-600:] for c in chunks[:-1]]
    with ThreadPoolExecutor(max_workers=workers) as ex:
        res = list(ex.map(lambda a: translate_chunk(uid, u[1], a[0], len(chunks), a[1], prevs[a[0]],
                                                    d / f"c{a[0]:03d}.json", force), enumerate(chunks)))
    for f in d.glob("c*.json"):
        if int(f.stem[1:]) >= len(chunks):
            f.unlink()
    es = "\n\n".join(r["es"] for r in res) + "\n"
    (d / "es.md").write_text(es, encoding="utf-8")
    bad = [r["i"] for r in res if not r["ok"]]
    print(f"  B {uid}: {len(chunks)} fragmentos, con observaciones: {bad}", flush=True)
    return bad


if __name__ == "__main__":
    args = sys.argv[1:]
    force = "--force" in args
    workers = 3
    if "--workers" in args:
        i = args.index("--workers")
        workers = int(args[i + 1])
        del args[i:i + 2]
    args = [a for a in args if a != "--force"]
    if args == ["all"]:
        args = [u[0] for u in UNITS if u[4] == "llm"]
    for uid in args:
        translate_unit(uid, force, workers)

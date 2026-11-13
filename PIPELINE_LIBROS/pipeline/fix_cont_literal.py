"""Une los parrafos '<<CONT>> ...' que quedaron literales (2026-11-02, bitacora TODOS/cont_literal).
Causa: la transcripcion puso <<CONT>> despues de una figura/epigrafe y no en la primera linea (regla de prompts.py);
mdblocks.join_pages solo lo reconoce al comienzo de la pagina, asi que el marcador quedaba literal en en.md, cNNN.json,
es.md y el PDF, y el parrafo quedaba partido en dos (antes y despues de la figura).
Por cada cap:
  1) transcripcion: el parrafo <<CONT>> pasa a la primera linea de la pagina (si se re-traduce, join_pages lo une bien);
  2) en.md, cNNN.json (src y es): el bloque '<<CONT>> x' se quita y x se pega al ultimo parrafo de prosa anterior
     (salteando <<PAGE>>, [[FIG]], epigrafes, notas al pie y comentarios; puede estar en el fragmento anterior),
     con la misma regla de join_pages (espacio, o se quita el guion final si el parrafo termina en letra + '-');
  3) es.md se regenera con "\\n\\n".join(es) + "\\n".
Despues correr fix_erratas_notas.py, re-render y validate de los caps tocados.
Backup en <LIBRO>_traduccion/_backup_pre_fix/cont_literal/NN. Idempotente.
Uso: python fix_cont_literal.py [--dry] LIBRO:CAP [LIBRO:CAP ...]   (ej.: BISHOP:09 DUDAHART:08)"""
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(r"D:\Universidad De Palermo - Maestria en IA\Machine Learning")
SKIP = ("<<PAGE", "<!--", ":::", "[[FIG", "|", "**Fig", "**Tab", "[^")
CONT = "<<CONT>>"


def prev_prose(blocks, i):
    """indice del ultimo bloque de prosa antes de i, o None si antes hay titulo/ecuacion."""
    for m in range(i - 1, -1, -1):
        if blocks[m] is None:
            continue
        b = blocks[m].lstrip()
        if b.startswith(SKIP):
            continue
        if b.startswith(("#", "$$", "```")):
            return None
        return m
    return None


def join(prev, x):
    return prev[:-1] + x if re.search(r"[A-Za-z]-$", prev) else prev + " " + x


def fix_blocks(blocks):
    """blocks: lista de bloques (puede abarcar varios fragmentos). Devuelve (blocks, n)."""
    n = 0
    i = 0
    while i < len(blocks):
        b = blocks[i]
        if b is not None and b.startswith(CONT):
            x = b[len(CONT):].strip()
            m = prev_prose(blocks, i)
            if m is None:
                blocks[i] = x
            else:
                blocks[m] = join(blocks[m], x)
                blocks[i] = None
            n += 1
        i += 1
    return blocks, n


def fix_unit(book, cap, dry):
    W = ROOT / f"{book}_traduccion"
    D = W / "03_traduccion" / cap
    cs = sorted(D.glob("c*.json"), key=lambda f: int(f.stem[1:]))
    js = [json.loads(c.read_text(encoding="utf-8")) for c in cs]
    BK = W / "_backup_pre_fix" / "cont_literal" / cap
    tocados = []
    # 2) cNNN.json: src y es, con bloques encadenados entre fragmentos
    total = {}
    for k in ("src", "es"):
        flat, owner = [], []
        for ci, j in enumerate(js):
            for b in j[k].split("\n\n"):
                flat.append(b)
                owner.append(ci)
        flat, n = fix_blocks(flat)
        total[k] = n
        if n:
            new = [[] for _ in js]
            for b, ci in zip(flat, owner):
                if b is not None:
                    new[ci].append(b)
            for ci, j in enumerate(js):
                t = "\n\n".join(new[ci])
                if t != j[k]:
                    j[k] = t
                    tocados.append(cs[ci].name)
    assert total["src"] == total["es"], (book, cap, total)
    en_p = D / "en.md"
    en = en_p.read_text(encoding="utf-8")
    eb, n_en = fix_blocks(en.rstrip("\n").split("\n\n"))
    # 1) transcripciones con <<CONT>> no inicial
    trs = []
    for p in sorted(set(int(x) for x in re.findall(r"<<PAGE (\d+)>>", en))):
        f = W / "02_transcripcion" / f"p{p:04d}.md"
        if f.exists():
            t = f.read_text(encoding="utf-8")
            if CONT in t and not t.lstrip().startswith(CONT):
                trs.append(f)
    print(f"{book} {cap}: <<CONT>> literales src={total['src']} es={total['es']} en.md={n_en}; "
          f"transcripciones a corregir: {[f.name for f in trs]}; fragmentos: {sorted(set(tocados))}")
    if dry or not (total["src"] or n_en or trs):
        return bool(total["src"] or n_en or trs)
    if not BK.exists():
        BK.mkdir(parents=True)
        for f in cs + [en_p, D / "es.md"] + trs:
            shutil.copy2(f, BK)
    for f in trs:
        t = f.read_text(encoding="utf-8")
        bl = t.strip("\n").split("\n\n")
        k = [i for i, b in enumerate(bl) if b.startswith(CONT)]
        assert len(k) == 1, f
        para = bl.pop(k[0])[len(CONT):].strip()
        f.write_text(CONT + "\n" + para + "\n\n" + "\n\n".join(bl) + "\n", encoding="utf-8")
    for c, j in zip(cs, js):
        if c.name in tocados:
            c.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
    if n_en:
        en_p.write_text("\n\n".join(b for b in eb if b is not None) + "\n", encoding="utf-8")
    es = "\n\n".join(j["es"] for j in js) + "\n"
    (D / "es.md").write_text(es, encoding="utf-8")
    for s in (es, en_p.read_text(encoding="utf-8")) + tuple(j["src"] for j in js):
        assert CONT not in s
    return True


if __name__ == "__main__":
    args = sys.argv[1:]
    dry = "--dry" in args
    args = [a for a in args if a != "--dry"]
    if not args:
        raise SystemExit(__doc__)
    for a in args:
        b, c = a.split(":")
        fix_unit(b, c, dry)

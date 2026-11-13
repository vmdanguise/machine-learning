"""Utilidades sobre el Markdown intermedio: union de paginas, division en bloques, extraccion de matematica."""
import re

PAGE_MARK = re.compile(r"^<<PAGE (\d+)>>$")
INLINE_MATH = re.compile(r"(?<![\\$])\$(?!\$)((?:\\.|[^$\\])+?)\$(?!\$)")


def split_blocks(md):
    """Divide en bloques separados por linea en blanco, sin cortar $$...$$, :::...::: ni tablas."""
    lines = md.replace("\r\n", "\n").split("\n")
    blocks, cur = [], []
    in_disp = in_alg = in_code = False
    for ln in lines:
        s = ln.strip()
        if in_code:
            cur.append(ln)
            if s.startswith("```"):
                in_code = False
                blocks.append("\n".join(cur))
                cur = []
            continue
        if s.startswith("```") and not in_disp and not in_alg:
            if cur:
                blocks.append("\n".join(cur))
                cur = []
            cur.append(ln)
            in_code = True
            continue
        if in_disp:
            cur.append(ln)
            if s.endswith("$$"):
                in_disp = False
            continue
        if in_alg:
            cur.append(ln)
            if s == ":::":
                in_alg = False
                blocks.append("\n".join(cur))
                cur = []
            continue
        if s.startswith("$$"):
            if cur:
                blocks.append("\n".join(cur))
                cur = []
            cur.append(ln)
            if not (len(s) > 2 and s.endswith("$$") and s != "$$"):
                in_disp = True
            if not in_disp:
                blocks.append("\n".join(cur))
                cur = []
            continue
        if s.startswith(":::") and s != ":::":
            if cur:
                blocks.append("\n".join(cur))
                cur = []
            cur.append(ln)
            in_alg = True
            continue
        if not s:
            if cur:
                blocks.append("\n".join(cur))
                cur = []
            continue
        if PAGE_MARK.match(s) or s.startswith("#"):
            if cur:
                blocks.append("\n".join(cur))
                cur = []
            blocks.append(ln)
            continue
        cur.append(ln)
    if cur:
        blocks.append("\n".join(cur))
    # cerrar bloques display que hayan quedado juntos a la siguiente
    out = []
    for b in blocks:
        if b.strip():
            out.append(b.strip("\n"))
    return out


def is_display(block):
    return block.strip().startswith("$$")


STRUCT_PREFIX = (":::", "#", "|", "[[FIG", "**Figure", "**Table", "**Algorithm", "**Equation", "[^", "<!--", "$$", "```", ">")


def last_prose(blocks):
    for b in reversed(blocks):
        if PAGE_MARK.match(b) or b.startswith("<!--"):
            continue
        return b
    return None


def looks_continuation(first, blocks):
    """Heuristica: la pagina empieza a mitad de oracion aunque el LLM no haya puesto <<CONT>>."""
    if first.startswith(STRUCT_PREFIX) or re.match(r"^(- |\d+\. )", first):
        return False
    prev = last_prose(blocks)
    if prev is None or prev.startswith(STRUCT_PREFIX):
        return False
    starts_lower = bool(re.match(r"^[a-z(,;]", first)) or first.startswith("$")
    prev_open = not re.search(r"[.!?:\"”)]\s*$", prev)
    return starts_lower or prev_open


def join_pages(pages):
    """pages: lista de (pno, md_ingles). Devuelve md de la unidad con marcadores <<PAGE n>>.
    Las paginas que empiezan con <<CONT>> se pegan al ultimo parrafo de texto de la anterior."""
    blocks = []
    for pno, md in pages:
        md = md.strip()
        if md in ("<!-- EMPTY -->", ""):
            blocks.append(f"<<PAGE {pno}>>")
            continue
        cont = False
        if md.startswith("<<CONT>>"):
            cont = True
            md = md[len("<<CONT>>"):].lstrip()
        bl = split_blocks(md)
        if not cont and bl and looks_continuation(bl[0], blocks):
            cont = True
        if cont and bl:
            first = bl.pop(0)
            # ultimo bloque de prosa de la pagina anterior
            idx = None
            for i in range(len(blocks) - 1, -1, -1):
                b = blocks[i]
                # los flotantes (figuras, pies, tablas, algoritmos, notas) se saltean: el parrafo sigue detras
                if PAGE_MARK.match(b) or b.startswith(("<!--", ":::", "[[FIG", "|", "**Figure", "**Table", "[^",
                                                       "```", "> **Note")):
                    continue
                if is_display(b) or b.startswith("#"):
                    break
                idx = i
                break
            if idx is not None and not is_display(first) and not first.startswith((":::", "#", "|", "[[FIG", "```")):
                prev = blocks[idx]
                if re.search(r"[A-Za-z]-$", prev):
                    blocks[idx] = prev[:-1] + first
                else:
                    blocks[idx] = prev + " " + first
                blocks.append(f"<<PAGE {pno}>>")
            else:
                blocks.append(f"<<PAGE {pno}>>")
                blocks.append(first)
        else:
            blocks.append(f"<<PAGE {pno}>>")
        blocks.extend(bl)
    return "\n\n".join(blocks) + "\n"


_RUNHEAD = re.compile(r"^(#{1,3})\s+(.*)$")


def _head_key(t):
    return re.sub(r"\W+", " ", t.replace("*", "")).strip().lower()


def dedup_running_heads(blocks, seen=None):
    """Quita los titulos repetidos como encabezado de pagina (p. ej. 'Exercises', 'Problems',
    'Bibliography', 'Computer exercises'): un titulo de nivel 1-3, no numerado, que aparece
    inmediatamente despues de un <<PAGE n>> y cuyo texto ya aparecio antes en la unidad.
    Devuelve (bloques, quitados). `seen` permite arrastrar el contexto entre fragmentos."""
    idx = running_head_indices(blocks, seen)
    return [b for i, b in enumerate(blocks) if i not in idx], [blocks[i].strip() for i in sorted(idx)]


def running_head_indices(blocks, seen=None):
    seen = set() if seen is None else seen
    idx, after_page = set(), False
    for i, b in enumerate(blocks):
        s = b.strip()
        h = _RUNHEAD.match(s) if "\n" not in s else None
        if h:
            k = _head_key(h.group(2))
            if after_page and k in seen and not re.match(r"^\d", k):
                idx.add(i)
                after_page = False
                continue
            seen.add(k)
        after_page = bool(PAGE_MARK.match(s))
    return idx


def chunk_dedup(blocks, max_chars=7000):
    """Como chunk(), pero quitando los titulos repetidos de encabezado de pagina DESPUES de partir,
    para que los limites de los fragmentos no cambien (y no se invalide la cache de traduccion)."""
    idx = running_head_indices(blocks)
    out, gi = [], 0
    for c in chunk(blocks, max_chars):
        keep = [b for j, b in enumerate(c) if gi + j not in idx]
        gi += len(c)
        if keep:
            out.append(keep)
    return out, [blocks[i].strip() for i in sorted(idx)]


def chunk(blocks, max_chars=7000):
    chunks, cur, n = [], [], 0
    for b in blocks:
        if cur and n + len(b) > max_chars and not b.startswith("[[FIG"):
            chunks.append(cur)
            cur, n = [], 0
        cur.append(b)
        n += len(b) + 2
    if cur:
        chunks.append(cur)
    return chunks


def inline_math(text):
    """Lista de expresiones $...$ (excluye display)."""
    t = re.sub(r"\$\$.*?\$\$", " ", text, flags=re.S)
    return INLINE_MATH.findall(t)


def display_math(text):
    return re.findall(r"\$\$(.*?)\$\$", text, flags=re.S)


def norm_math(m):
    return re.sub(r"\s+", "", m)

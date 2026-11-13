"""Detecta texto que quedo en ingles en las traducciones (es.md de 03_traduccion/NN).
Excluye matematica, codigo, bibliografia y referencias. Lista bloques con alta proporcion de palabras funcionales
inglesas. Uso: python english_residue.py [LIBRO ...] [--caps 01,02]"""
import re
import sys
from pathlib import Path

ROOT = Path(r"D:\Universidad De Palermo - Maestria en IA\Machine Learning")
sys.path.insert(0, str(Path(__file__).parent))
from mdblocks import split_blocks  # noqa: E402

EN = set("the of and to in is that for with as by this are be we which on it an from at can or not have has "
         "its into these where when then than our will was were been also such each so if there their them "
         "they would should must may using use used shown figure note recall see".split())
ES = set("el la los las de del y que en es por con para una un se como al lo su sus son más este esta "
         "estos estas donde cuando entonces también cada si hay puede pueden debe usando usar figura nota".split())
BIB_HEAD = re.compile(r"(?i)^#+\s*(bibliograf|referencias|references|bibliography|notas bibliogr|bibliographical)")


def clean(b):
    b = re.sub(r"```.*?```", " ", b, flags=re.S)
    b = re.sub(r"\$\$.*?\$\$", " ", b, flags=re.S)
    b = re.sub(r"(?<!\\)\$(?:\\.|[^$\\])+?\$", " ", b)
    b = re.sub(r"`[^`]*`", " ", b)
    b = re.sub(r"\*\*(initialize|for|do|end|if|then|else|return|while|begin|until)\*\*", " ", b)
    b = re.sub(r"\[\^p\d+-\d+\]:.*", " ", b)
    b = re.sub(r"\([A-Z][^()]{0,80}\d{4}[a-z]?\)", " ", b)       # citas (Autor, 2014)
    b = re.sub(r"\[[^\]]*\]", " ", b)
    b = re.sub(r"\*[^*]+\*", " ", b)                            # terminos en cursiva (originales entre parentesis)
    return b


def scan(book, caps):
    out = []
    for d in sorted((ROOT / f"{book}_traduccion" / "03_traduccion").glob("[0-9][0-9]")):
        if caps and d.name not in caps:
            continue
        es = d / "es.md"
        if not es.exists():
            continue
        in_bib = False
        page = None
        for b in split_blocks(es.read_text(encoding="utf-8")):
            s = b.strip()
            m = re.match(r"<<PAGE (\d+)>>", s)
            if m:
                page = m.group(1)
                continue
            if s.startswith("#"):
                in_bib = bool(BIB_HEAD.match(s))
            if in_bib or s.startswith("<!--"):
                continue
            words = re.findall(r"[A-Za-záéíóúñü]+", clean(s).lower())
            en = sum(w in EN for w in words)
            es_ = sum(w in ES for w in words)
            if en >= 3 and en > 1.5 * es_:
                out.append((book, d.name, page, en, es_, s[:150].replace("\n", " / ")))
            elif re.search(r"^\s*>?\s*\*\*(Note|Figure|Table|Algorithm|Example|Problem|Equation)\b", s, re.M):
                out.append((book, d.name, page, en, es_, "ROTULO: " + s[:140].replace("\n", " / ")))
    return out


if __name__ == "__main__":
    args = sys.argv[1:]
    caps = None
    if "--caps" in args:
        i = args.index("--caps")
        caps = set(args[i + 1].split(","))
        del args[i:i + 2]
    books = args or ["BENGIO", "BISHOP", "FUNDAMENTALS", "GONZALEZ", "DUDAHART"]
    tot = 0
    for bk in books:
        for r in scan(bk, caps):
            tot += 1
            print(f"{r[0]} {r[1]} p{r[2]} en={r[3]} es={r[4]} | {r[5]}")
    print("TOTAL bloques sospechosos:", tot)

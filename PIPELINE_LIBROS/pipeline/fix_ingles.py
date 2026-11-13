"""Pasada de correccion de RESTOS EN INGLES en traducciones ya hechas (los 5 libros).

Detecta fragmentos (03_traduccion/<cap>/cNNN.json) con rotulos sin traducir (**Note:**, **Figure**, **Algorithm**...),
parrafos/tablas que quedaron en ingles, o texto en ingles dentro de bloques :::algorithm (fuera de las palabras clave
en negrita, que quedan en ingles por regla). Le pide al LLM que traduzca SOLO eso. Matematica protegida y estructura
validada igual que fix_registro.py. Marca el json con english_fix y guarda es_pre_ingles.

Uso: python fix_ingles.py LIBRO [caps...] [--dry]
"""
import difflib
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(r"D:\Universidad De Palermo - Maestria en IA\Machine Learning")
book = sys.argv[1].upper()
os.environ["BOOK"] = "BISHOP" if book == "BENGIO" else book
sys.path.insert(0, str(Path(__file__).parent))
import llm  # noqa: E402
from mdblocks import split_blocks  # noqa: E402
from translate import protect, restore, signature, diff_sig, clean  # noqa: E402
import english_residue as ER  # noqa: E402

WORK = ROOT / f"{book}_traduccion"
llm.USAGE_LOG = WORK / "logs" / "usage.jsonl"

KW = r"\*\*(initialize|for|do|end|end for|end while|if|then|else|return|while|begin|begin for|begin initialize|until|exit|and|or|not|repeat|loop|step)\*\*"
# palabras inglesas claras dentro de algoritmos (sin for/in/to/from/is/no, que son pseudocodigo o espanol)
ALG_EN = re.compile(r"\b(the|of|and|all|each|with|test|pattern|sequence|visible|known|state|cat|label|continued|"
                    r"descent|Algorithm|algorithm|select|randomly|compute|update|otherwise|set|new|best|change|stop|"
                    r"pick|add|remove|replace|data|point|points|training|sample|samples|weights|weight|criterion|"
                    r"threshold|shuffle|vector|hidden|unit|node|met|convergence|iterate|over|train|find|nearest|radius)\b")
ROT = re.compile(r"^\s*>?\s*\*\*(Note|Figure|Table|Algorithm|Example|Problem|Equation)\b", re.M)


def needs_fix(j):
    es = j["es"]
    if ROT.search(es):
        return True
    for m in re.finditer(r":::algorithm\n(.*?)\n:::", es, re.S):
        for l in m.group(1).split("\n"):
            l2 = re.sub(r"\$[^$]*\$", " ", l)
            l2 = re.sub(KW, " ", l2)
            l2 = re.sub(r"`[^`]*`", " ", l2)
            if ALG_EN.search(l2):
                return True
    for b in split_blocks(es):
        s = b.strip()
        if s.startswith("<!--") or s.startswith("<<PAGE") or s.startswith(":::"):
            continue
        words = re.findall(r"[A-Za-záéíóúñü]+", ER.clean(s).lower())
        en = sum(w in ER.EN for w in words)
        es_ = sum(w in ER.ES for w in words)
        if en >= 3 and en > 1.5 * es_ and not ER.BIB_HEAD.match(s):
            return True
    return False


SYSTEM = """Sos un corrector de traducciones técnicas inglés→español (español neutro técnico, registro académico, sin
tú/vos/usted). El fragmento ya está traducido, pero QUEDARON RESTOS EN INGLÉS. Tu ÚNICA tarea es traducir esos restos:
- rótulos: "**Note:**" → "**Nota:**", "**Figure 7-20.**" → "**Figura 7-20.**", "**Table 5.1**" → "**Tabla 5.1**",
  "**Algorithm 2** (HMM Forward)" → "**Algoritmo 2** (HMM Forward)", "(continued)" → "(continuación)";
- oraciones, notas, celdas de tabla o pies que hayan quedado en inglés;
- dentro de bloques :::algorithm ... ::: el texto en inglés ("visible sequence" → "secuencia visible", "test pattern"
  → "patrón de prueba", "criterion" → "criterio", "shuffle data" → "mezclar los datos", "// update weight vector" →
  "// actualizar el vector de pesos", "Select node $i$ randomly" → "Seleccionar el nodo $i$ al azar"), PERO las
  palabras clave en negrita **for**, **do**, **end**, **if**, **then**, **else**, **return**, **while**, **begin**,
  **initialize**, **until**, **exit** quedan en inglés, igual que las palabras de pseudocódigo "for/in/to/from" que
  acompañan a esas palabras clave (p. ej. "**for** $i$ from $1$ to $k$ **do**" no se toca).
Se conservan en inglés: nombres propios, nombres de algoritmos/métodos que el texto ya deja en inglés (HMM Forward,
Widrow-Hoff, Ho-Kashyap), citas bibliográficas, títulos de obras, código, nombres de software.
Si una celda de tabla está truncada en el original (palabras cortadas como "soluti", "Rema"), se traduce lo
reconocible y se deja la palabra truncada tal cual.
TODO LO DEMÁS debe quedar EXACTAMENTE igual, carácter por carácter: placeholders ⟦M1⟧ ⟦D1⟧ ⟦C1⟧ (cada uno una vez, en
su lugar), marcadores [[FIG ...]], notas [^p..], {{MARGIN: ...}}, líneas <<PAGE n>>, títulos #, estructura de tablas
(misma cantidad de filas y columnas), listas, negritas, cursivas, saltos de línea/párrafo, sangrías y números de línea
de los algoritmos, &nbsp;. El texto que ya está en español NO se retoca.
Devolvé SOLO el texto, sin comentarios ni ``` ."""


def fix_chunk(path, dry):
    j = json.loads(path.read_text(encoding="utf-8"))
    if j.get("english_fix") or not needs_fix(j):
        return path.name, "skip", 0
    if dry:
        return path.name, "candidato", 0
    prot, mp = protect(split_blocks(j["es"]))
    sig = signature(prot)
    nb = len(split_blocks(prot))
    pbl = split_blocks(prot)
    head, tail = [], []
    while pbl and (pbl[0].startswith("<<PAGE") or pbl[0].startswith("#")):
        head.append(pbl.pop(0))
    while pbl and pbl[-1].startswith("<<PAGE"):
        tail.insert(0, pbl.pop())
    body = "\n\n".join(pbl)
    for attempt in range(3):
        out = clean(llm.call("claude-sonnet-4-6", SYSTEM, body, max_tokens=16000, temperature=0.0 if attempt == 0 else 0.3,
                             tag=f"E:{path.parent.name}:{path.stem}:a{attempt}"))
        out = "\n\n".join(head + [out] + tail)
        bad = diff_sig(sig, signature(out))
        ob = split_blocks(out)
        if bad or len(ob) != nb:
            continue
        pb = split_blocks(prot)
        changed = [(a, b) for a, b in zip(pb, ob) if a != b]
        # bloques largos: deben parecerse; bloques cortos (rotulos) pueden cambiar mas
        if any(len(a) > 200 and difflib.SequenceMatcher(None, a, b, autojunk=False).ratio() < 0.5 for a, b in changed):
            continue
        es = restore(out, mp)
        if changed:
            j["es_pre_ingles"] = j["es"]
            j["es"] = es
        j["english_fix"] = True
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(path)
        with open(WORK / "logs" / "ingles.log", "a", encoding="utf-8") as fh:
            for a, b in changed:
                fh.write(f"### {path.parent.name}/{path.name}\n- {restore(a, mp)}\n+ {restore(b, mp)}\n\n")
        return path.name, "ok", len(changed)
    return path.name, "FALLO", 0


def main():
    args = [a for a in sys.argv[2:] if not a.startswith("--")]
    dry = "--dry" in sys.argv
    caps = args or sorted(d.name for d in (WORK / "03_traduccion").iterdir() if re.fullmatch(r"\d\d", d.name))
    for cap in caps:
        d = WORK / "03_traduccion" / cap
        cs = sorted(d.glob("c*.json"), key=lambda f: int(f.stem[1:]))
        with ThreadPoolExecutor(max_workers=4) as ex:
            res = list(ex.map(lambda p: fix_chunk(p, dry), cs))
        cands = [r[0] for r in res if r[1] in ("ok", "candidato")]
        fails = [r[0] for r in res if r[1] == "FALLO"]
        if not dry and (cands or fails):
            res_j = [json.loads(p.read_text(encoding="utf-8")) for p in cs]
            (d / "es.md").write_text("\n\n".join(r["es"] for r in res_j) + "\n", encoding="utf-8")
        print(f"  {book} {cap}: fragmentos={cands} parrafos cambiados={sum(r[2] for r in res)} fallos={fails}", flush=True)


if __name__ == "__main__":
    main()

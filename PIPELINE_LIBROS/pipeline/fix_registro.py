"""Pasada de correccion de REGISTRO sobre traducciones ya hechas (los 5 libros).

Detecta fragmentos (03_traduccion/<cap>/cNNN.json) cuya traduccion se dirige al lector con tu/vos/usted (incluidos los
imperativos de usted en enunciados de ejercicios: "Demuestre", "Considere"...) o cuyo original dice "you", y le pide al
LLM que reescriba SOLO esas frases (ejercicios -> infinitivo; prosa -> nosotros / impersonal / "el lector").
La matematica va protegida con placeholders (como en translate.py) y se valida que la estructura no cambie.
Actualiza el cNNN.json (campo es, register_fix) y regenera es.md. Hace backup previo en 03_traduccion/_pre_registro/.

Uso: python fix_registro.py LIBRO [caps...] [--dry]      (LIBRO = BENGIO|BISHOP|FUNDAMENTALS|GONZALEZ|DUDAHART)
"""
import difflib
import json
import os
import re
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(r"D:\Universidad De Palermo - Maestria en IA\Machine Learning")
book = sys.argv[1].upper()
os.environ["BOOK"] = "BISHOP" if book == "BENGIO" else book   # solo para poder importar config/llm
sys.path.insert(0, str(Path(__file__).parent))
import llm  # noqa: E402
from mdblocks import split_blocks  # noqa: E402
from translate import protect, restore, signature, diff_sig, clean  # noqa: E402
from validate import strip_nonprose, VOSEO_WORDS, TU_WORDS  # noqa: E402

WORK = ROOT / f"{book}_traduccion"
llm.USAGE_LOG = WORK / "logs" / "usage.jsonl"

IMP = re.compile(
    r"(?:^|[.:;)\]]\s+|\*\*\s*|\(\w\)\s*|^\s*[-*]\s+)(Demuestre|Muestre|Considere|Suponga|Calcule|Determine|Encuentre|"
    r"Obtenga|Verifique|Compruebe|Explique|Utilice|Use|Escriba|Dibuje|Grafique|Repita|Pruebe|Derive|Deduzca|Exprese|"
    r"Evalúe|Discuta|Esboce|Describa|Implemente|Elija|Imagine|Recuerde|Observe|Tenga|Asuma|Compare|Justifique|"
    r"Proponga|Diseñe|Defina|Dé|Construya|Identifique|Indique|Resuelva|Halle|Estime|Aplique|Simplifique|Escoja|"
    r"Genere|Trace|Realice|Ejecute|Instale|Descargue|Abra|Cargue|Guarde|Cree|Agregue|Reemplace|Consulte|Lea|Vea|"
    r"Fíjese|Piense|Complete|Modifique|Interprete|Analice|Desarrolle|Formule|Enumere|Sugiera|Trate|Sea|Note|"
    r"Haga|Ponga|Diga|Vuelva|Grafíquese|Demuéstrese|Muéstrese|Considérese|Supóngase|Tome|Fije|Sume|Reste|"
    r"Multiplique|Divida|Integre|Diferencie|Normalice|Entrene|Clasifique|Seleccione|Ordene|Etiquete|Agrupe)\b",
    re.M)
TU_VERB = re.compile(
    r"\b(puedes|tienes|quieres|sabes|necesitas|debes|estés|estás familiarizad\w*|podrías|tendrías|habrías|quieras|"
    r"agregas|escribes|usas|ves|verás|notarás|encontrarás|recuerdes|recuerda que|imagina que|considera que|nota que|"
    r"observa que|fíjate|mira|hazlo|tuyo|tuya|tuyos|tuyas|eres|has visto|has leído|leíste|vayas|seas)\b", re.I)
USTED = re.compile(
    r"(?i)\b(si (ya )?(está familiarizad|desea|quiere|necesita|prefiere|tiene (experiencia|alguna|ninguna)|no tiene)|"
    r"puede (omitir|saltar)|le (recomendamos|sugerimos|invitamos|animamos|enseñará|ayudará|permitirá)|ayudarle|"
    r"su (computadora|máquina|propio código|propia implementación)|consulte|recuerde)")
YOU = re.compile(r"(?i)\byou(r|rs|rself|'ll|'re|'ve|'d)?\b")

SYSTEM = """Sos un corrector de estilo de traducciones técnicas al español (registro académico neutro).
Tu ÚNICA tarea es corregir el REGISTRO del fragmento: el texto NO debe dirigirse al lector con "tú", "vos" ni
"usted". Eso incluye:
- pronombres y verbos en segunda persona (te, ti, contigo, tu/tus como posesivo, puedes, tienes, estés, quieras,
  podrías, agregas, habrías...);
- formas de usted: "Si ya está familiarizado…", "puede omitir…", "si desea…", "le enseñará…", "consulte…",
  "recuerde que…", y los IMPERATIVOS de usted ("Demuestre", "Muestre", "Considere", "Suponga", "Calcule",
  "Utilice", "Repita", "Explique", "Esboce", "Dibuje", "Grafique", "Pruebe", "Derive", "Indique"...).
Cómo reescribir:
- En enunciados de ejercicios/problemas usá INFINITIVO: "Demuestre que…" → "Demostrar que…", "Considere un…" →
  "Considerar un…", "Suponga que…" → "Suponer que…", "Use el resultado…" → "Usar el resultado…", "(a) Calcule…" →
  "(a) Calcular…". Ajustá lo que dependa del verbo para que la oración quede gramatical (p. ej. "Considere el caso en
  que usted…" → "Considerar el caso en que…").
- En prosa usá "nosotros", construcciones impersonales con "se" o "el lector": "Si ya está familiarizado con X, puede
  omitir este capítulo" → "El lector que ya esté familiarizado con X puede omitir este capítulo"; "te animamos a…" →
  "animamos al lector a…"; "Recuerde que…" → "Recordemos que…"; "consulte [12]" → "véase [12]".
- Si es un ejemplo narrado en primera y segunda persona (yo/tú), pasá la segunda persona a "el lector" / "el escriba"
  o a impersonal, manteniendo el sentido y la primera persona del autor.
- "nosotros" ("Consideremos", "Supongamos", "Demostremos") ya es correcto: no lo toques.
TODO LO DEMÁS debe quedar EXACTAMENTE igual, carácter por carácter: placeholders ⟦M1⟧ ⟦D1⟧ ⟦C1⟧ (cada uno una vez, en su
lugar), marcadores [[FIG ...]], notas [^p..], {{MARGIN: ...}}, líneas <<PAGE n>>, títulos #, tablas, listas, negritas,
cursivas, terminología, puntuación y saltos de línea/párrafo. No mejores ni retoques nada que no sea el registro.
Si no hay nada que corregir, devolvé el texto idéntico. Devolvé SOLO el texto, sin comentarios ni ``` ."""


def needs_fix(j):
    prose = strip_nonprose(j["es"])
    return bool(VOSEO_WORDS.search(prose) or TU_WORDS.search(prose) or TU_VERB.search(prose)
                or USTED.search(prose) or IMP.search(prose) or YOU.search(strip_nonprose(j["src"])))


def fix_chunk(path, dry):
    j = json.loads(path.read_text(encoding="utf-8"))
    if j.get("register_fix") or not needs_fix(j):
        return path.name, "skip", 0
    if dry:
        return path.name, "candidato", 0
    prot, mp = protect(split_blocks(j["es"]))
    sig = signature(prot)
    nb = len(split_blocks(prot))
    # los <<PAGE n>> del borde del fragmento se separan (el LLM tiende a comerse el primero) y se reponen
    pbl = split_blocks(prot)
    head, tail = [], []
    # (idem con los titulos # del comienzo: el LLM se comia el "# Capitulo N" inicial)
    while pbl and (pbl[0].startswith("<<PAGE") or pbl[0].startswith("#")):
        head.append(pbl.pop(0))
    while pbl and pbl[-1].startswith("<<PAGE"):
        tail.insert(0, pbl.pop())
    body = "\n\n".join(pbl)
    for attempt in range(3):
        out = clean(llm.call("claude-sonnet-4-6", SYSTEM, body, max_tokens=16000, temperature=0.0 if attempt == 0 else 0.3,
                             tag=f"R:{path.parent.name}:{path.stem}:a{attempt}"))
        out = "\n\n".join(head + [out] + tail)
        bad = diff_sig(sig, signature(out))
        ob = split_blocks(out)
        if bad or len(ob) != nb:
            continue
        pb = split_blocks(prot)
        changed = [(a, b) for a, b in zip(pb, ob) if a != b]
        if any(difflib.SequenceMatcher(None, a, b, autojunk=False).ratio() < 0.6 for a, b in changed):
            continue
        es = restore(out, mp)
        if changed:
            j["es_pre_registro"] = j["es"]
            j["es"] = es
        j["register_fix"] = True
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(path)
        with open(WORK / "logs" / "registro.log", "a", encoding="utf-8") as fh:
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
        if not dry:
            bk = WORK / "03_traduccion" / "_pre_registro" / cap
            if not bk.exists():
                shutil.copytree(d, bk)
        cs = sorted(d.glob("c*.json"), key=lambda f: int(f.stem[1:]))
        with ThreadPoolExecutor(max_workers=4) as ex:
            res = list(ex.map(lambda p: fix_chunk(p, dry), cs))
        n_c = sum(1 for r in res if r[1] in ("ok", "candidato"))
        n_b = sum(r[2] for r in res)
        fails = [r[0] for r in res if r[1] == "FALLO"]
        if not dry:
            res_j = [json.loads(p.read_text(encoding="utf-8")) for p in cs]
            (d / "es.md").write_text("\n\n".join(r["es"] for r in res_j) + "\n", encoding="utf-8")
        print(f"  {book} {cap}: fragmentos revisados={n_c}/{len(cs)} parrafos cambiados={n_b} fallos={fails}", flush=True)


if __name__ == "__main__":
    main()

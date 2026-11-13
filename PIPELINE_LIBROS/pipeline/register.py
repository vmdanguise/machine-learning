"""Deteccion (y correccion opcional por LLM) de formas que se dirigen al lector: tu, voseo, usted
(incluidos los imperativos de usted de los ejercicios: 'Muestre que' -> 'Mostrar que').

La correccion trabaja sobre los checkpoints cNNN.json de 03_traduccion/<cap>/ (campo 'es'), con la matematica
protegida por placeholders, verifica que la firma estructural no cambie y reconstruye es.md como lo hace translate.py
(join de los 'es'). Se guarda el texto previo en el json ('es_pre_register').

Uso:
  python register.py scan  [LIBRO ...]          -> lista fragmentos con formas sospechosas
  python register.py fix   LIBRO CAP [CAP ...]  -> corrige con LLM los fragmentos marcados
"""
import difflib
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(r"D:\Universidad De Palermo - Maestria en IA\Machine Learning")
sys.path.insert(0, str(Path(__file__).parent))
from mdblocks import split_blocks, INLINE_MATH  # noqa: E402

VERBS_USTED = (
    "Demuestre|Considere|Muestre|Calcule|Desarrolle|Repita|Explique|Suponga|Encuentre|Utilice|Use|Escriba|Verifique|"
    "Derive|Obtenga|Determine|Pruebe|Compare|Grafique|Dibuje|Implemente|Analice|Discuta|Esboce|Exprese|Evalúe|Defina|"
    "Justifique|Elija|Indique|Imagine|Note|Observe|Recuerde|Dé|Halle|Trace|Complete|Proponga|Diseñe|Genere|Entrene|"
    "Aplique|Describa|Especifique|Interprete|Resuelva|Estime|Construya|Asuma|Tome|Piense|Intente|Lea|Vea|Consulte|"
    "Simplifique|Identifique|Seleccione|Ejecute|Mida|Sume|Reste|Multiplique|Divida|Integre|Diferencie|Sustituya|"
    "Reemplace|Agregue|Añada|Modifique|Ignore|Normalice|Ordene|Cuente|Comente|Enumere|Liste|Clasifique|Elabore|"
    "Realice|Fíjese|Verifíquelo|Demuéstrelo|Muéstrelo|Compruebe|Deduzca|Reescriba|Reformule|Generalice|Extienda|"
    "Busque|Descargue|Instale|Abra|Cargue|Guarde|Cree|Ilustre|Investigue|Reproduzca|Pase|Haga|Ponga|Diga|Vuelva|"
    "Comience|Empiece|Continúe|Sugiera|Critique|Relacione|Represente|Codifique|Visualice|Etiquete|Agrupe|Combine|"
    "Recupere|Exprese|Resuma|Argumente|Formule|Plantee|Cambie|Varíe|Incremente|Disminuya|Reduzca|Aumente|Grafíquelo|"
    "Explíquelo|Calcúlelo|Pruébelo|Encuéntrelo|Escríbalo|Justifíquelo")
# imperativo de usted: verbo con mayuscula al inicio de oracion / item / tras el numero del ejercicio,
# o en minuscula coordinado tras otro imperativo ("..., y demuestre que")
USTED_IMP = re.compile(r"(?:^|(?<=[.:;?!]\s)|(?<=\*\*\s)|(?<=\)\s)|(?<=-\s)|(?<=\*\s)|(?<=[¿(]))(" + VERBS_USTED + r")\b"
                       r"|\b[ye]\s(" + VERBS_USTED.lower() + r")\s(que|el|la|los|las|un|una|por|cómo|si|qué|su|sus|esta|este)\b",
                       re.M)
TU_WORDS = re.compile(r"\b(tú|tu|tus|ti|contigo|te|usted|ustedes|vosotros|vuestro|vuestra|os)\b", re.I)
VOSEO = re.compile(
    r"\b(vos|sos|podés|tenés|querés|sabés|hacés|decís|venís|fijate|fíjate|mirá|tomá|usá|notá|considerá|observá|"
    r"recordá|pensá|imaginá|probá|intentá|escribí|elegí|seguí|andá|vení|hacé|poné|tené|decí|calculá|definí|suponé|"
    r"verificá|comprobá|ejecutá|instalá|descargá|abrí|corré|cargá|guardá|creá|agregá|reemplazá)\b", re.I)
TU_VERB = re.compile(r"\b(podrías|habrías|tendrías|deberías|puedes|tienes|quieres|sabes|necesitas|agregas|escribes|"
                     r"anotas|eliges|recuerdas|verás|notarás|encontrarás|has|eres|estás)\b", re.I)
USTED_IMPL = re.compile(
    r"\b(si (ya )?(está|esta) (familiarizado|interesado|seguro|claro)|si (ya )?(conoce|desea|quiere|necesita|prefiere)\b|"
    r"\bpuede (usted|saltar|omitir)\b|\ble (recomendamos|sugerimos|invitamos|animamos)\b|"
    r"\b(ayudarle|indicarle|mostrarle|recordarle)\b|\bsu (computadora|máquina|propio código|respuesta|solución)\b)", re.I)


def prose(text):
    t = re.sub(r"```.*?```", " ", text, flags=re.S)
    t = re.sub(r"\$\$.*?\$\$", " ", t, flags=re.S)
    t = INLINE_MATH.sub(" ", t)
    t = re.sub(r"`[^`]*`", " ", t)
    t = re.sub(r"\[\^p\d+-\d+\]:.*", " ", t)
    return t


def hits(text):
    p = prose(text)
    out = []
    for name, rx in (("usted-imp", USTED_IMP), ("tú", TU_WORDS), ("voseo", VOSEO), ("tú-verbo", TU_VERB),
                     ("usted-impl", USTED_IMPL)):
        for m in rx.finditer(p):
            # 'Use'/'Note' en ingles dentro de titulos de obras: se toleran si van en cursiva
            out.append((name, m.group(0), p[max(0, m.start() - 50):m.end() + 50].replace("\n", " ")))
    return out


def work_dir(book):
    return ROOT / ("BENGIO_traduccion" if book == "BENGIO" else f"{book}_traduccion")


def chunk_files(book, cap):
    d = work_dir(book) / "03_traduccion" / cap
    return sorted(d.glob("c[0-9][0-9][0-9].json"), key=lambda f: int(f.stem[1:]))


def scan(books):
    tot = 0
    for bk in books:
        for d in sorted((work_dir(bk) / "03_traduccion").glob("[0-9][0-9]")):
            for f in chunk_files(bk, d.name):
                j = json.loads(f.read_text(encoding="utf-8"))
                h = hits(j["es"])
                if h:
                    tot += 1
                    print(f"{bk} {d.name} {f.stem}: {len(h)} -> " + "; ".join(f"{a}:{b}" for a, b, _ in h[:6]))
    print("fragmentos marcados:", tot)


SYSTEM_FIX = r"""Sos un corrector de estilo de traducciones técnicas al español. Recibís un fragmento YA TRADUCIDO de un
libro técnico. Tu única tarea es eliminar las formas que se dirigen al lector en segunda persona, ya sea con "tú",
voseo o "usted", y DEJAR TODO LO DEMÁS EXACTAMENTE IGUAL.

Reglas:
- Imperativos de usted o de tú (típicos de ejercicios y problemas) pasan a INFINITIVO: "Muestre que" → "Mostrar que",
  "Considere el caso" → "Considerar el caso", "y demuestre que" → "y demostrar que", "Demuéstrelo" → "Demostrarlo",
  "Repita el Problema 5.1" → "Repetir el Problema 5.1", "Use un filtro" → "Usar un filtro", "Explique por qué" → "Explicar por qué".
- Otras formas dirigidas al lector pasan a construcciones impersonales con "se", a "nosotros" o a "el lector":
  "Si ya está familiarizado con X, puede omitir este capítulo" → "Quien ya esté familiarizado con X puede omitir este
  capítulo"; "te animamos a" → "invitamos al lector a"; "Si desea aprender más" → "Para profundizar"; "podrías
  denotar" → "el lector podría denotar"; "me reúno contigo" → "me reúno con el lector". Mantené la persona del autor
  ("yo", "nosotros") cuando el original la usa.
- "Sea x ..." / "Sean ..." (subjuntivo matemático) NO es tratamiento al lector: dejalo igual. Tampoco toques "su"
  cuando se refiere a una cosa ("su propia transpuesta"), ni "si está" impersonal ("si está correctamente clasificado").
- Conservá byte a byte: los placeholders ⟦M1⟧ ⟦D1⟧ ⟦C1⟧, [[FIG ...]], [^p..], {{MARGIN: ...}}, <<PAGE n>>, títulos #,
  tablas, negritas, cursivas, números de ejercicio, saltos de párrafo. No traduzcas ni reformules nada más, no corrijas
  erratas ni cambies terminología.
- Si el fragmento no tiene nada que corregir, devolvelo idéntico.
Devolvé SOLO el fragmento corregido, sin comentarios."""


def fix(book, caps):
    os.environ.setdefault("BOOK", "BISHOP" if book == "BENGIO" else book)
    from llm import call
    from translate import protect, restore, signature, diff_sig, clean
    for cap in caps:
        fs = chunk_files(book, cap)
        changed = 0
        for f in fs:
            j = json.loads(f.read_text(encoding="utf-8"))
            if not hits(j["es"]):
                continue
            prot, mp = protect(split_blocks(j["es"]))
            sig = signature(prot)
            ok = None
            for attempt in range(3):
                out = clean(call("claude-sonnet-4-6", SYSTEM_FIX, prot, max_tokens=16000, temperature=0.0,
                                 tag=f"R:{book}:{cap}:{f.stem}:a{attempt}"))
                bad = diff_sig(sig, signature(out))
                ratio = difflib.SequenceMatcher(None, prot, out, autojunk=False).ratio()
                if not bad and ratio > 0.93 and all(k in out for k in mp):
                    ok = out
                    break
                print(f"  {book} {cap} {f.stem}: intento {attempt} rechazado bad={bad} ratio={ratio:.3f}")
            if ok is None:
                print(f"  !! {book} {cap} {f.stem}: sin corrección válida, queda igual")
                continue
            es2 = restore(ok, mp)
            if es2 != j["es"]:
                j.setdefault("es_pre_register", j["es"])
                j["es"] = es2
                j["register_fixed"] = True
                tmp = f.with_suffix(".tmp")
                tmp.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
                tmp.replace(f)
                changed += 1
                left = hits(es2)
                print(f"  {book} {cap} {f.stem}: corregido; restan {len(left)} -> {[b for _, b, _ in left][:8]}")
        rebuild_es(book, cap)
        print(f"{book} {cap}: {changed} fragmentos corregidos")


def rebuild_es(book, cap):
    d = work_dir(book) / "03_traduccion" / cap
    es = "\n\n".join(json.loads(f.read_text(encoding="utf-8"))["es"] for f in chunk_files(book, cap)) + "\n"
    (d / "es.md").write_text(es, encoding="utf-8")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "scan":
        scan(a[1:] or ["BENGIO", "BISHOP", "FUNDAMENTALS", "GONZALEZ", "DUDAHART"])
    elif a[0] == "fix":
        fix(a[1], a[2:])

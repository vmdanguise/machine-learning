"""FUNDAMENTALS cap 13 (Deep Reinforcement Learning, p340-376): correcciones verificadas contra el original (2026-11-02).
1) Niveles de titulo: el original usa MyriadPro-SemiboldCond 18.9 pt para las secciones (##) y 15.8 pt para las
   subsecciones (###). La transcripcion dejo 21 subsecciones de 15.8 pt como ## (Policy, Future Return, Annealed
   e-Greedy, Building the Model and Optimizer, ..., UNsupervised REinforcement and Auxiliary Learning): pasan a ###
   en 02_transcripcion, en.md y en src/es de los cNNN.json.
2) Terminologia unificada en es (solo 'es'; el codigo y la matematica no se tocan):
   Q-Function / *Q-function* / Q-funcion -> funcion Q (se conserva la glosa "*funcion Q* (*Q-function*)");
   Q-valor(es) -> valor(es) Q; Q-red(es) -> red(es) Q; *Q-table* -> tabla Q (glosa en la primera aparicion);
   "replay de experiencias" -> "repeticion de experiencias"; "Deep Q-Network" (titulo) -> "Red Q Profunda (*Deep
   Q-Network*)"; anneal: "Anillado"/"aniquila" -> "con Recocido"/"somete a recocido" (el resto ya decia recocido);
   referencia cruzada "Q-Learning and Deep Q-Networks" -> titulo traducido; epigrafe de la Fig. 13-7 con *annealing*
   anidado dentro de la cursiva (rompia la cursiva) -> "recocido de $\\epsilon$-greedy".
La errata "Qtheta" (p364, impreso asi en lugar de Q_theta) la anota fix_erratas_notas.py (FUNDAMENTALS13_Qtheta).
Idempotente. Respaldo previo en FUNDAMENTALS_traduccion/_backup_pre_fix/13_fund13. Correr de nuevo despues de cualquier
transcribe/translate/fix_registro/fix_ingles del cap 13, y despues fix_erratas_notas.py."""
import json
import re
import shutil
from pathlib import Path

W = Path(r"D:\Universidad De Palermo - Maestria en IA\Machine Learning\FUNDAMENTALS_traduccion")
T = W / "03_traduccion" / "13"
TR = W / "02_transcripcion"

H_EN = ["Policy", "Future Return", "Annealed $\\epsilon$-Greedy", "Building the Model and Optimizer", "Sampling Actions",
        "Keeping Track of History", "Policy Gradient Main Function", "PGAgent Performance on Pole-Cart", "Training DQN",
        "Learning Stability", "DQN and the Markov Assumption", "DQN's Solution to the Markov Assumption",
        "Playing Breakout with DQN", "Building Our Architecture", "Stacking Frames", "Setting Up Training Operations",
        "Updating Our Target Q-Network", "Implementing Experience Replay", "DQN Main Loop",
        "Asynchronous Advantage Actor-Critic Agent", "UNsupervised REinforcement and Auxiliary Learning"]
H_ES = ["Política", "Retorno Futuro", "$\\epsilon$-Greedy con Recocido", "Construcción del Modelo y el Optimizador",
        "Muestreo de Acciones", "Seguimiento del Historial", "Función Principal del Gradiente de Política",
        "Desempeño del PGAgent en Pole-Cart", "Entrenamiento de DQN", "Estabilidad del Aprendizaje",
        "DQN y el Supuesto de Markov", "La Solución de DQN al Supuesto de Markov", "Jugando Breakout con DQN",
        "Construcción de Nuestra Arquitectura", "Apilamiento de Fotogramas",
        "Configuración de las Operaciones de Entrenamiento", "Actualización de Nuestra Red Q Objetivo",
        "Implementación de la Repetición de Experiencias", "Bucle Principal de DQN",
        "Agente Actor-Crítico con Ventaja Asíncrona", "Aprendizaje No Supervisado por Refuerzo y Auxiliar"]
assert len(H_EN) == len(H_ES) == 21

ES_TXT = [
    ("\n## $\\epsilon$-Greedy Anillado\n", "\n## $\\epsilon$-Greedy con Recocido\n"),
    ("se lo aniquila (*anneal*) a lo largo del tiempo", "se lo somete a recocido (*anneal*) a lo largo del tiempo"),
    ("ε *greedy* y ε *greedy* con *annealing*.", "ε *greedy* y ε *greedy* con recocido (*annealing*)."),
    ("con el recocido *greedy* de $\\epsilon$ de 1.0 a 0.001. Nótese cómo, en general, el método *greedy* estándar de "
     "$\\epsilon$ tiene", "con $\\epsilon$ *greedy* con recocido de 1.0 a 0.001. Nótese cómo, en general, $\\epsilon$ "
     "*greedy* estándar tiene"),
    ("gracias al recocido (*annealing*) $\\epsilon$-greedy*", "gracias al recocido de $\\epsilon$-greedy*"),
    ("### Aproximación de la Q-Function\n", "### Aproximación de la Función Q\n"),
    ("### De la Q-Función a la Política\n", "### De la Función Q a la Política\n"),
    ("Q-función", "función Q"),
    ("mayor Q-valor", "mayor valor Q"), ("nuestros Q-valores", "nuestros valores Q"),
    ("dos Q-redes", "dos redes Q"), ("Q-red objetivo", "red Q objetivo"),
    ("\n## Actualización de Nuestra Q-Red Objetivo\n", "\n## Actualización de Nuestra Red Q Objetivo\n"),
    ("o una *Q-table*.", "o una *tabla Q* (*Q-table*)."),
    ("\n## Implementación del Replay de Experiencias\n", "\n## Implementación de la Repetición de Experiencias\n"),
    ("cómo el *replay* de experiencias (experience replay) puede", "cómo la repetición de experiencias (*experience "
     "replay*) puede"),
    ("implementación sencilla del replay de experiencias", "implementación sencilla de la repetición de experiencias"),
    ("\n### Deep Q-Network\n", "\n### Red Q Profunda (*Deep Q-Network*)\n"),
    ('"Q-Learning and Deep Q-Networks" en la página 347', '"Q-Learning y Redes Q Profundas" en la página 347'),
]
ES_RE = [(re.compile(r"(?<!\()\*Q-function\*(?!\))"), "función Q"),
         (re.compile(r"(?<!\()\*Q-table\*(?!\))"), "tabla Q")]


def code_split(s):
    """Partes alternas texto / bloque de codigo (los impares son codigo y no se tocan)."""
    return re.split(r"(```.*?```)", s, flags=re.S)


def niveles(s, titulos):
    for h in titulos:
        s = s.replace("\n## " + h + "\n", "\n### " + h + "\n")
    return s


def fix_en(s):
    parts = code_split("\n" + s + "\n")
    parts = [p if i % 2 else niveles(p, H_EN) for i, p in enumerate(parts)]
    return "".join(parts)[1:-1]


def fix_es(s):
    parts = code_split("\n" + s + "\n")
    out = []
    for i, p in enumerate(parts):
        if i % 2 == 0:
            for a, b in ES_TXT:
                p = p.replace(a, b)
            for r, b in ES_RE:
                p = r.sub(b, p)
            p = niveles(p, H_ES)
        out.append(p)
    return "".join(out)[1:-1]


cs = sorted(T.glob("c*.json"), key=lambda f: int(f.stem[1:]))
trs = sorted(TR.glob("p03[4-7]?.md"))
trs = [f for f in trs if 340 <= int(f.stem[1:]) <= 376]
bk = W / "_backup_pre_fix" / "13_fund13"
if not bk.exists():
    bk.mkdir(parents=True)
    for f in trs + cs + [T / "en.md", T / "es.md"]:
        shutil.copy2(f, bk / f.name)

cambios = []
for f in trs + [T / "en.md"]:
    t = f.read_text(encoding="utf-8")
    t2 = fix_en(t)
    if t2 != t:
        f.write_text(t2, encoding="utf-8")
        cambios.append(f.name)
for f in cs:
    j = json.loads(f.read_text(encoding="utf-8"))
    s2, e2 = fix_en(j["src"]), fix_es(j["es"])
    if (s2, e2) != (j["src"], j["es"]):
        j["src"], j["es"] = s2, e2
        f.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
        cambios.append(f.name)
es = "\n\n".join(json.loads(c.read_text(encoding="utf-8"))["es"] for c in cs) + "\n"
(T / "es.md").write_text(es, encoding="utf-8")
en = (T / "en.md").read_text(encoding="utf-8")

# controles
sc = lambda s: re.sub(r"```.*?```", "", s, flags=re.S)
for h in H_EN:
    assert sc(en).count("\n### " + h + "\n") == 1 and "\n## " + h + "\n" not in sc(en), h
for h in H_ES:
    assert sc(es).count("\n### " + h + "\n") == 1 and "\n## " + h + "\n" not in sc(es), h
txt = sc(es)
for bad in ("Q-Function", "Q-función", "Q-Función", "Q-valor", "Q-red", "Q-Red", "Anillad", "aniquila", "Replay de",
            "replay de", "*replay*", "Q-Learning and"):
    assert bad not in txt, bad
assert txt.count("*Q-function*") == 1 and txt.count("*Q-table*") == 1
for a, b in ES_TXT:
    assert b.strip("\n").lstrip("#").strip() in txt, "reemplazo no aplicado: " + b
hs_en = re.findall(r"(?m)^#{1,4} ", sc(en))
hs_es = re.findall(r"(?m)^#{1,4} ", sc(es))
assert hs_en == hs_es, "niveles de titulo en != es"
assert re.findall(r"```.*?```", en, re.S) == re.findall(r"```.*?```", es, re.S)
assert re.findall(r"\$\$.*?\$\$", en, re.S) == re.findall(r"\$\$.*?\$\$", es, re.S)
print("cambios:", cambios or "ninguno (ya aplicado)")

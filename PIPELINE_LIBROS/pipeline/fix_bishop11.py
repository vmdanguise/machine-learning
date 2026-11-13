"""BISHOP cap 11: correcciones verificadas contra el original (2026-11-02).
1) p343: la transcripcion empezaba con un <<CONT>> espurio seguido del epigrafe de la Fig. 11.2. En el original p342
   termina con una oracion completa ("...to refer to both.") y p343 empieza con la figura (epigrafe arriba a la izquierda).
   El ensamblado pego el epigrafe al final del parrafo de p342, antes de <<PAGE 343>> -> validate: "figura 11.2 sin
   epigrafe cercano". Se quita el <<CONT>> y el epigrafe pasa a su propio bloque despues de <<PAGE 343>>.
Aplica el reemplazo en 02_transcripcion/p0343.md, en.md, los cNNN.json (src, es, es_pre_*) y regenera es.md.
Idempotente. Respaldo previo en BISHOP_traduccion/_backup_pre_fix/11_bishop11. Correr de nuevo despues de cualquier
transcribe/translate/fix_registro/fix_ingles del cap 11."""
import json
import shutil
from pathlib import Path

W = Path(r"D:\Universidad De Palermo - Maestria en IA\Machine Learning\BISHOP_traduccion")
T = W / "03_traduccion" / "11"
FIN = "use the same symbol to refer to both."
FIN_ES = "usaremos el mismo símbolo para referirnos a ambos."


def mover(s, fin, rot):
    """'<fin> **<rot> 11.2** <epigrafe>\n\n<<PAGE 343>>' -> '<fin>\n\n<<PAGE 343>>\n\n**<rot> 11.2** <epigrafe>'"""
    a = s.find(fin + f" **{rot} 11.2**")
    if a < 0:
        return s
    b = s.index("\n\n<<PAGE 343>>", a)
    cap = s[a + len(fin) + 1:b]
    return s[:a + len(fin)] + "\n\n<<PAGE 343>>\n\n" + cap + s[b + len("\n\n<<PAGE 343>>"):]


p343 = W / "02_transcripcion" / "p0343.md"
cs = sorted(T.glob("c*.json"), key=lambda f: int(f.stem[1:]))
bk = W / "_backup_pre_fix" / "11_bishop11"
if not bk.exists():
    bk.mkdir(parents=True)
    for f in [p343, T / "en.md", T / "es.md"] + cs:
        shutil.copy2(f, bk / f.name)
cambios = []
t = p343.read_text(encoding="utf-8")
if t.startswith("<<CONT>>\n\n**Figure 11.2**"):
    p343.write_text(t[len("<<CONT>>\n\n"):], encoding="utf-8")
    cambios.append(p343.name)
f = T / "en.md"
t = f.read_text(encoding="utf-8")
t2 = mover(t, FIN, "Figure")
if t2 != t:
    f.write_text(t2, encoding="utf-8")
    cambios.append(f.name)
for f in cs:
    j = json.loads(f.read_text(encoding="utf-8"))
    ch = False
    for k in list(j):
        if not isinstance(j[k], str):
            continue
        if k == "src":
            s = mover(j[k], FIN, "Figure")
        elif k == "es" or k.startswith("es_pre"):
            s = mover(j[k], FIN_ES, "Figura")
        else:
            continue
        if s != j[k]:
            j[k] = s
            ch = True
    if ch:
        f.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
        cambios.append(f.name)
es = "\n\n".join(json.loads(c.read_text(encoding="utf-8"))["es"] for c in cs) + "\n"
(T / "es.md").write_text(es, encoding="utf-8")
assert f"{FIN_ES}\n\n<<PAGE 343>>\n\n**Figura 11.2**" in es, "es: epigrafe 11.2 no reubicado"
assert f"{FIN}\n\n<<PAGE 343>>\n\n**Figure 11.2**" in (T / "en.md").read_text(encoding="utf-8")
assert not p343.read_text(encoding="utf-8").startswith("<<CONT>>")
print("cambios:", cambios or "ninguno (ya aplicado)")

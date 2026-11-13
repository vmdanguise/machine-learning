"""GONZALEZ cap 10, p811 (problemas 10.50-10.55): bloqueada por el filtro de contenido del proveedor con
claude-sonnet-4-6 (5 intentos) y claude-opus-5. transcribe_alt.py con claude-sonnet-5 devolvio SOLO la columna derecha
(continuacion de 10.54 + 10.55). La columna izquierda (10.50-10.54) se transcribio aparte con transcribe_clip.py
(recorte [30,50,258,570], claude-sonnet-4-6; salida guardada en data/p0811_left.md) y aca se unen las dos, con el formato de p810 ("- **(a)**\\* ...").
Idempotente: si p0811.md ya empieza con **10.50** no hace nada."""
import re
from pathlib import Path

W = Path(r"D:\Universidad De Palermo - Maestria en IA\Machine Learning\GONZALEZ_traduccion")
f = W / "02_transcripcion" / "p0811.md"
t = f.read_text(encoding="utf-8")
if t.startswith("**10.50**"):
    print("p811 ya unida; nada que hacer")
    raise SystemExit(0)

LEFT = (Path(__file__).parent / "data" / "p0811_left.md").read_text(encoding="utf-8").strip()
right = t.strip()
assert right.startswith("<<CONT>>") and "**10.55**" in right, right[:60]
assert LEFT.startswith("**10.50**") and LEFT.endswith("understood by"), LEFT[-40:]
right = right[len("<<CONT>>"):].strip()
LEFT = LEFT.replace("**10.53**\\* ", "**10.53** \\* ")
# sub-items de 10.55 con el formato de p810
right = re.sub(r"^- \((\w)\) \\\* ", r"- **(\1)**\\* ", right, flags=re.M)
right = re.sub(r"^- \((\w)\) ", r"- **(\1)** ", right, flags=re.M)
f.write_text(LEFT + " " + right + "\n", encoding="utf-8")
print("ok")

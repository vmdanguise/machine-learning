"""DUDAHART cap 9, p580 y p589: el encabezado de pagina "9.7. PROBLEMS" se transcribio como el subtitulo
"#### Section 9.7" al comienzo de la pagina. No existe en el original: en p580 siguen los problemas de la
Seccion 9.2 (10-27) y en p589 el unico marcador es "(+) Section 9.7" de los Computer exercises.
Se elimina de la transcripcion, de c023/c026 (src, es, es_pre_*), de en.md y se regenera es.md. Idempotente."""
import json
from pathlib import Path

W = Path(r"D:\Universidad De Palermo - Maestria en IA\Machine Learning\DUDAHART_traduccion")
T = W / "03_traduccion" / "09"
HDR = {"en": "#### Section 9.7\n\n", "es": "#### Sección 9.7\n\n"}
cambios = 0

for p in (580, 589):
    f = W / "02_transcripcion" / f"p0{p}.md"
    t = f.read_text(encoding="utf-8")
    if t.startswith(HDR["en"]):
        f.write_text(t[len(HDR["en"]):], encoding="utf-8")
        cambios += 1

for c in ("c023.json", "c026.json"):
    f = T / c
    d = json.loads(f.read_text(encoding="utf-8"))
    for k, v in d.items():
        if not isinstance(v, str):
            continue
        h = HDR["en"] if k == "src" else HDR["es"]
        for p in (580, 589):
            a = f"<<PAGE {p}>>\n\n{h}"
            if a in v:
                v = v.replace(a, f"<<PAGE {p}>>\n\n")
                cambios += 1
        d[k] = v
    f.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

f = T / "en.md"
t = f.read_text(encoding="utf-8")
for p in (580, 589):
    a = f"<<PAGE {p}>>\n\n{HDR['en']}"
    if a in t:
        t = t.replace(a, f"<<PAGE {p}>>\n\n")
        cambios += 1
f.write_text(t, encoding="utf-8")

cs = sorted(T.glob("c*.json"))
es = "\n\n".join(json.loads(c.read_text(encoding="utf-8"))["es"] for c in cs) + "\n"
(T / "es.md").write_text(es, encoding="utf-8")
assert "#### Sección 9.7" not in es and "#### Section 9.7" not in t
print("cambios:", cambios)

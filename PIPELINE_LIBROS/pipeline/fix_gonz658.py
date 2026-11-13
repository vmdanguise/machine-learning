"""GONZALEZ cap 9, p658: el <<CONT>> inicial de la transcripcion era un fragmento espurio ("$\\times$ 5 SE of 1's...")
que duplica el parrafo '"significant" size ...' (continuacion real de "only objects of" de p657).
Se elimina el CONT espurio y el parrafo real pasa a ser el <<CONT>>."""
import json, re
from pathlib import Path

W = Path(r"D:\Universidad De Palermo - Maestria en IA\Machine Learning\GONZALEZ_traduccion")
# transcripcion
p = W / "02_transcripcion" / "p0658.md"
t = p.read_text(encoding="utf-8")
paras = t.split("\n\n")
if paras[0].startswith('<<CONT>> "significant" size'):
    print("p658 ya corregida; nada que hacer")
    raise SystemExit(0)
assert paras[0].startswith("<<CONT>> $\\times$ 5 SE"), paras[0][:40]
k = next(i for i, x in enumerate(paras) if x.startswith('"significant" size'))
real = paras.pop(k)
paras[0] = "<<CONT>> " + real
p.write_text("\n\n".join(paras), encoding="utf-8")
print("transcripcion ok")


def fix(s, bad_start, real_start):
    i = s.find(bad_start)
    j = s.find("\n\n<<PAGE 658>>", i)
    a = s.find("\n\n" + real_start)
    b = s.find("\n\n### ", a + 2)
    assert -1 not in (i, j, a, b) and i < j < a < b, (i, j, a, b)
    para = s[a + 2:b]
    return s[:i] + para + s[j:a] + s[b:]


d = W / "03_traduccion" / "09"
c = d / "c007.json"
jj = json.loads(c.read_text(encoding="utf-8"))
jj["src"] = fix(jj["src"], "$\\times$ 5 SE of 1's. Figure 9.20(c)", '"significant" size')
for k in [k for k in jj if k == "es" or k.startswith("es_pre")]:
    if isinstance(jj[k], str) and "<<PAGE 658>>" in jj[k]:
        jj[k] = fix(jj[k], "$\\times$ elemento estructurante de 1's. La figura 9.20(c)", 'tamaño "significativo"')
        print("  ", k)
c.write_text(json.dumps(jj, ensure_ascii=False, indent=1), encoding="utf-8")
en = d / "en.md"
if en.exists():
    s = en.read_text(encoding="utf-8")
    if "only objects of $\\times$" in s:
        en.write_text(fix(s, "$\\times$ 5 SE of 1's. Figure 9.20(c)", '"significant" size'), encoding="utf-8")
        print("en.md ok")
cs = sorted(d.glob("c*.json"), key=lambda f: int(f.stem[1:]))
(d / "es.md").write_text("\n\n".join(json.loads(x.read_text(encoding="utf-8"))["es"] for x in cs) + "\n", encoding="utf-8")
print("c007 + es.md ok")

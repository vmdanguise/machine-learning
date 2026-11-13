"""GONZALEZ cap 10, p806 (problemas 10.8-10.14, dos columnas): la transcripcion mezclo las columnas (empezaba por la
derecha: cola de 10.11(b) + 10.12-10.13(a), luego la izquierda) y dejo un DOUBT sobre el orden de lectura.
Orden correcto (verificado contra el original): columna izquierda = cola de 10.8 (viene de p805: "Consider a
horizontal intensity profile through | the middle of a binary image..."), 10.9 + [[FIG P10.9]], 10.10, 10.11(a) y
el comienzo de 10.11(b); columna derecha = resto de 10.11(b) ("in Fig. 10.14, and in (a) above..."), 10.12, 10.13,
10.14 + [[FIG P10.14]]. Las figuras P10.9/P10.14 se recortan a mano (books.py extra_figs[806]).
Reordena 02_transcripcion/p0806.md y quita el DOUBT; despues hay que correr translate.py 10 (retraduce los
fragmentos cuyo src cambio). Idempotente: si p0806.md ya empieza con la cola de 10.8 no hace nada."""
from pathlib import Path

W = Path(r"D:\Universidad De Palermo - Maestria en IA\Machine Learning\GONZALEZ_traduccion")
f = W / "02_transcripcion" / "p0806.md"
raw = f.read_bytes().decode("utf-8")
crlf = "\r\n" in raw
t = raw.replace("\r\n", "\n")
if t.startswith("<<CONT>> the middle of a binary image"):
    print("p806 ya reordenada; nada que hacer")
    raise SystemExit(0)

A = "<<CONT>> in Fig. 10.14, and in (a) above,"
L0 = "the middle of a binary image that contains"
B11 = "- **(b)**\\* Show that the Sobel and Prewitt kernels"
P14 = "**10.14** The rectangle in the following binary image"
assert t.startswith(A), t[:60]
i_left, i_b11, i_14 = t.index(L0), t.index(B11), t.index(P14)
i_doubt = t.index("<!-- DOUBT:")
assert i_left < i_b11 < i_14 < i_doubt

right_head = t[len("<<CONT>> "):i_left].strip()          # cola de 10.11(b) ... 10.13(b)
left = t[i_left:i_b11].strip()                             # cola de 10.8 ... 10.11(a)
b11 = t[i_b11:i_14].strip()                                # comienzo de 10.11(b)
p14 = t[i_14:i_doubt].strip()                              # 10.14
cont11, rest = right_head.split("\n\n", 1)                 # "in Fig. 10.14, ... respectively." | 10.12 ...
new = ("<<CONT>> " + left + "\n\n" + b11 + " " + cont11.strip() + "\n\n" + rest.strip() + "\n\n" + p14 + "\n")
for k in ("**10.9**", "[[FIG P10.9]]", "**10.10**", "**10.11**", "**10.12**", "**10.13**", "**10.14**", "[[FIG P10.14]]"):
    assert new.count(k) == 1, k
assert len(new.split()) == len(t[:i_doubt].split()), (len(new.split()), len(t[:i_doubt].split()))
f.write_bytes((new.replace("\n", "\r\n") if crlf else new).encode("utf-8"))
print("ok p806 reordenada")

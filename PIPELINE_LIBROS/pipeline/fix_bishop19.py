"""BISHOP cap 19 (Autoencoders, p573-589): retoques de texto de la revision contra el original (2026-11-02, bitacora BISHOP/19).
- Titulo '## 19.1 Autoencoders deterministas' -> 'Autoencoders Deterministas' (las ## del cap van con mayusculas: 19.2
  'Autoencoders Variacionales').
- c003 (p582): la transcripcion conservo el corte de linea del original dentro de la glosa: '(*decoder net-*
  {{MARGIN: Seccion 19.1}} *work*)' -> '(*decoder network*). {{MARGIN: Seccion 19.1}}' (la nota al margen pasa al final
  de la oracion).
- Epigrafe de la Fig. 19.8: 'optimizacion de la ELBO' -> 'del ELBO' (el resto del cap y BISHOP 15-16 usan 'el ELBO').
- Ejercicio 19.3: 'Se debe mostrar que' -> 'Mostrar que' (infinitivo, como los demas ejercicios).
- Algoritmo 19.1: '**until** converged' -> '**until** convergencia' (como los algoritmos de BISHOP 07 y 15; 'until' es
  palabra clave y queda en ingles, 'converged' no).
Sin matematica: comprueba que la de cada fragmento sigue igual a la del src.
Toca solo el campo 'es' de 03_traduccion/19/cNNN.json y regenera es.md ("\\n\\n".join(es) + "\\n").
Backup en BISHOP_traduccion/_backup_pre_fix/19_bishop19. Idempotente. Despues correr fix_erratas_notas.py
(erratas BISHOP19_19.18, BISHOP19_Alg19.1, BISHOP19_19.22).
ORDEN si se re-traduce: fix_bishop19.py -> fix_erratas_notas.py -> fix_moda.py."""
import collections
import json
import re
import shutil
from pathlib import Path

W = Path(r"D:\Universidad De Palermo - Maestria en IA\Machine Learning\BISHOP_traduccion")
D = W / "03_traduccion" / "19"
BK = W / "_backup_pre_fix" / "19_bishop19"
MATH = re.compile(r"\$\$.*?\$\$|\$[^$\n]+?\$", re.S)
TEXTO = [
    ("## 19.1 Autoencoders deterministas\n", "## 19.1 Autoencoders Deterministas\n"),
    ("(*decoder net-* {{MARGIN: Sección 19.1}} *work*). Esto", "(*decoder network*). {{MARGIN: Sección 19.1}} Esto"),
    ("Ilustración de la optimización de la ELBO (cota", "Ilustración de la optimización del ELBO (cota"),
    ("iguales a cero). Se debe mostrar que $\\mathbf{z}$", "iguales a cero). Mostrar que $\\mathbf{z}$"),
    ("**until** converged\n", "**until** convergencia\n"),
]

cs = sorted(D.glob("c*.json"), key=lambda f: int(f.stem[1:]))
js = [json.loads(f.read_text(encoding="utf-8")) for f in cs]
assert "\n\n".join(j["es"] for j in js) + "\n" == (D / "es.md").read_text(encoding="utf-8"), "es.md no coincide con los cNNN"
for viejo, nuevo in TEXTO:
    n = sum(j["es"].count(viejo) + j["es"].count(nuevo) for j in js)
    assert n == 1, (viejo, n)
if not BK.exists():
    BK.mkdir(parents=True)
    for f in cs + [D / "es.md"]:
        shutil.copy2(f, BK)
cambios = []
for f, j in zip(cs, js):
    t = j["es"]
    for viejo, nuevo in TEXTO:
        if viejo in t:
            t = t.replace(viejo, nuevo)
            cambios.append((f.name, viejo[:40]))
    if t != j["es"]:
        assert collections.Counter(MATH.findall(t)) == collections.Counter(MATH.findall(j["es"])), f.name
        j["es"] = t
        f.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
(D / "es.md").write_text("\n\n".join(j["es"] for j in js) + "\n", encoding="utf-8")
print("cambios:", cambios or "ninguno (ya aplicado)")

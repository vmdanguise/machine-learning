"""BISHOP cap 20 (Diffusion Models, p590-616): retoques de texto de la revision contra el original (2026-11-02, bitacora BISHOP/20).
- Algoritmo 20.1: '**until** converged' -> '**until** convergencia' (como BISHOP 07, 15 y 19) y 'Take optimizer step' (sin
  traducir) -> 'Realizar un paso del optimizador'.
- Comentarios // `...` de los Algoritmos 20.1 y 20.2 traducidos (como BISHOP 07 y 12: infinitivo en minuscula).
- {{MARGIN: Exercise 20.11/20.12/20.13}} -> 'Ejercicio ...' (los demas margenes del cap ya estaban traducidos).
- c009 (p611): la transcripcion conservo el corte de linea del original dentro de la glosa: '(*latent diffu-*)
  {{MARGIN: Seccion 19.1}} *sion models* (Rombach...)' -> '(*latent diffusion models*) (Rombach *et al.*, 2021).
  {{MARGIN: Seccion 19.1}}' (la nota al margen pasa al final de la oracion, como BISHOP 19 c003).
- Epigrafe de la Fig. 20.7: 'guia sin clasificador' -> 'guia libre de clasificador' (como el titulo 20.4.2 y el cuerpo).
- 'figura 20.5' en minuscula -> 'Figura 20.5' (x2).
- 'el inpainting de imagenes' -> 'la reconstruccion de imagenes (*inpainting*)' (como c009 y la Fig. 20.9);
  'prompt' sin cursiva -> '*prompt*' (x2, como la definicion en c008).
- Registro de los ejercicios: los imperativos del original traducidos con 'se + verbo' pasan a infinitivo
  (20.6, 20.7, 20.8, 20.10, 20.11, 20.12, 20.13, 20.14, 20.15, 20.16, 20.17, 20.18, 20.19 y 20.20); las frases con
  'we' del original ('Here we take...', 'We see...') quedan impersonales. 'en donde' -> 'donde'.
- Terminologia de score unificada a 'funcion *score*' / 'el *score*', como la definicion del cap (c005, '*funcion
  score* (*score function*)') y BISHOP 14 y 19 (habia 'funcion de puntuacion' x21, 'funcion de *score*' x9 y
  'funcion *score*' x8). Se mantiene '*puntuacion de Stein* (*Stein score*)' de la definicion.
Sin matematica: comprueba que la de cada fragmento sigue igual a la del src.
Toca solo el campo 'es' de 03_traduccion/20/cNNN.json y regenera es.md ("\\n\\n".join(es) + "\\n").
Backup en BISHOP_traduccion/_backup_pre_fix/20_bishop20. Idempotente (los reemplazos se aplican en orden; si ninguno
encuentra su texto, ya estaba aplicado). VECES: cuantas veces debe aparecer cada texto (por defecto 1).
Despues correr fix_erratas_notas.py (erratas BISHOP20_*).
ORDEN si se re-traduce: fix_bishop20.py -> fix_erratas_notas.py -> fix_moda.py.
Uso: python fix_bishop20.py [--contar]"""
import collections
import json
import re
import shutil
import sys
from pathlib import Path

W = Path(r"D:\Universidad De Palermo - Maestria en IA\Machine Learning\BISHOP_traduccion")
D = W / "03_traduccion" / "20"
BK = W / "_backup_pre_fix" / "20_bishop20"
MATH = re.compile(r"\$\$.*?\$\$|\$[^$\n]+?\$", re.S)
TEXTO = [
    # algoritmos
    ("**until** converged\n", "**until** convergencia\n"),
    ("  Take optimizer step\n", "  Realizar un paso del optimizador\n"),
    ("// `Calculate alphas from betas`", "// `calcular los alfas a partir de los betas`"),
    ("// `Sample a data point`", "// `muestrear un punto de datos`"),
    ("// `Sample a point along the Markov chain`", "// `muestrear un punto a lo largo de la cadena de Markov`"),
    ("// `Sample a noise vector`", "// `muestrear un vector de ruido`"),
    ("// `Evaluate noisy latent variable`", "// `evaluar la variable latente ruidosa`"),
    ("// `Compute loss term`", "// `calcular el término de pérdida`"),
    ("// `Sample from final latent space`", "// `muestrear del espacio latente final`"),
    ("// `Calculate alpha`", "// `calcular alfa`"),
    ("// `Evaluate network output`", "// `evaluar la salida de la red`"),
    ("// `Add scaled noise`", "// `sumar el ruido escalado`"),
    ("// `Final denoising step`", "// `paso final de eliminación de ruido`"),
    # margenes, glosas, epigrafes
    ("{{MARGIN: Exercise 20.11}}", "{{MARGIN: Ejercicio 20.11}}"),
    ("{{MARGIN: Exercise 20.12}}", "{{MARGIN: Ejercicio 20.12}}"),
    ("{{MARGIN: Exercise 20.13}}", "{{MARGIN: Ejercicio 20.13}}"),
    ("(*latent diffu-*) {{MARGIN: Sección 19.1}} *sion models* (Rombach *et al.*, 2021). Aquí",
     "(*latent diffusion models*) (Rombach *et al.*, 2021). {{MARGIN: Sección 19.1}} Aquí"),
    ("Ilustración de la guía sin clasificador (*classifier-free guidance*)",
     "Ilustración de la guía libre de clasificador (*classifier-free guidance*)"),
    ("La figura 20.5 muestra", "La Figura 20.5 muestra"),
    ("mostrada en la figura 20.5,", "mostrada en la Figura 20.5,"),
    ("la superresolución de imágenes, el inpainting de imágenes,",
     "la superresolución de imágenes, la reconstrucción de imágenes (*inpainting*),"),
    ("condicionada en un prompt textual", "condicionada en un *prompt* textual"),
    ("puede tomar un prompt de texto", "puede tomar un *prompt* de texto"),
    # registro de los ejercicios (imperativo del original -> infinitivo)
    ("Primero, se observa que los dos términos", "Primero, observar que los dos términos"),
    ("Para ello, se consideran únicamente", "Para ello, considerar únicamente"),
    ("y se observa que el producto de dos exponenciales", "y observar que el producto de dos exponenciales"),
    ("Se agrupan todos los términos", "Agrupar todos los términos"),
    ("y luego se reorganizan en la forma", "y luego reorganizarlos en la forma"),
    ("por inspección, se encuentran expresiones", "por inspección, encontrar expresiones"),
    ("Se considera la distribución condicional inversa", "Considerar la distribución condicional inversa"),
    ("centrada en el valor $\\mathbf{z}_t$, se muestra que,", "centrada en el valor $\\mathbf{z}_t$, mostrar que,"),
    ("Se encuentran expresiones para las correcciones", "Encontrar expresiones para las correcciones"),
    (", se verifica que la función de log-verosimilitud", ", verificar que la función de log-verosimilitud"),
    ("Se muestra que si todos estos términos omitidos", "Mostrar que si todos estos términos omitidos"),
    ("\\mathbf{w})$, se muestra que la divergencia", "\\mathbf{w})$, mostrar que la divergencia"),
    (", se reescribe la media", ", reescribir la media"),
    ("Para ello, se sustituye $\\boldsymbol{\\mu}", "Para ello, sustituir $\\boldsymbol{\\mu}"),
    ("y se sustituye $\\mathbf{x}$ usando (20.1), y luego se hace uso de",
     "y sustituir $\\mathbf{x}$ usando (20.1), y luego hacer uso de"),
    ("Se considera una matriz cuyos elementos", "Considerar una matriz cuyos elementos"),
    ("Se muestra que si la función *score* se define tomando", "Mostrar que si la función *score* se define tomando"),
    ("Se considera una representación mediante", "Considerar una representación mediante"),
    ("Se compara la complejidad computacional", "Comparar la complejidad computacional"),
    ("Se muestra que este último enfoque", "Mostrar que este último enfoque"),
    ("en donde $D$ es la dimensionalidad", "donde $D$ es la dimensionalidad"),
    ("Se deriva el resultado (20.65)", "Derivar el resultado (20.65)"),
    ("Considérese ahora la fórmula", "Considerar ahora la fórmula"),
    ("Se integran ambos lados de esta fórmula", "Integrar ambos lados de esta fórmula"),
    ("y se reordena para obtener", "y reordenar para obtener"),
    ("Se aplica este resultado junto con", "Aplicar este resultado junto con"),
    ("Para ello, se expande primero el cuadrado en (20.49) y, usando (20.47), se muestra que",
     "Para ello, expandir primero el cuadrado en (20.49) y, usando (20.47), mostrar que"),
    ("A continuación, nótese que el término", "A continuación, observar que el término"),
    ("Por último, considérese el término cruzado", "Por último, considerar el término cruzado"),
    ("(20.47), se muestra que este es igual", "(20.47), mostrar que este es igual"),
    ("De este modo, se muestra que las dos funciones", "De este modo, mostrar que las dos funciones"),
    ("$(\\star)$ Considérese una distribución de probabilidad", "$(\\star)$ Considerar una distribución de probabilidad"),
    ("Se muestra que cuando la función de puntuación", "Mostrar que cuando la función de puntuación"),
    ("(20.3), se muestra que la actualización infinitesimal", "(20.3), mostrar que la actualización infinitesimal"),
    (", se muestra que la función de puntuación en (20.59)", ", mostrar que la función de puntuación en (20.59)"),
    # terminologia de score
    ("función de puntuación (*score function*)", "función *score*"),
    ("función de puntuación", "función *score*"),
    ("Función de pérdida de puntuación", "Función de pérdida de *score*"),
    ("sus puntuaciones son iguales", "sus *scores* son iguales"),
    ("entre la puntuación del modelo y la puntuación verdadera", "entre el *score* del modelo y el *score* verdadero"),
    ("conocemos la puntuación de datos verdadera", "conocemos el *score* verdadero de los datos"),
    ("obtenemos la puntuación correspondiente", "obtenemos el *score* correspondiente"),
    ("la contribución de la puntuación incondicional", "la contribución del *score* incondicional"),
    ("función de *score*", "función *score*"),
]
VECES = {
    "// `Sample a noise vector`": 2,
    "función de puntuación (*score function*)": 4,
    "función de puntuación": 17,
    "Función de pérdida de puntuación": 2,
    "función de *score*": 9,
}
CONTAR = "--contar" in sys.argv

cs = sorted(D.glob("c*.json"), key=lambda f: int(f.stem[1:]))
js = [json.loads(f.read_text(encoding="utf-8")) for f in cs]
assert "\n\n".join(j["es"] for j in js) + "\n" == (D / "es.md").read_text(encoding="utf-8"), "es.md no coincide con los cNNN"
# simulacion en orden sobre el texto completo: cada texto aparece VECES veces (primera corrida) o ninguna (ya aplicado)
full = "\n\n".join(j["es"] for j in js)
ns = []
for viejo, nuevo in TEXTO:
    ns.append(full.count(viejo))
    full = full.replace(viejo, nuevo)
if CONTAR:
    for (viejo, _), n in zip(TEXTO, ns):
        marca = "" if n == VECES.get(viejo, 1) else "   <-- distinto de VECES"
        print(f"{n:3d} {viejo[:70]!r}{marca}")
    print("restantes 'puntuaci':", re.findall(r"[^\s]*\s[^\s]*\s[Pp]untuaci\w*\s[^\s]*\s[^\s]*", full))
    sys.exit()
if not any(ns):
    print("cambios: ninguno (ya aplicado)")
    sys.exit()
mal = [(v[:50], n, VECES.get(v, 1)) for (v, _), n in zip(TEXTO, ns) if n != VECES.get(v, 1)]
assert not mal, mal
if not BK.exists():
    BK.mkdir(parents=True)
    for f in cs + [D / "es.md"]:
        shutil.copy2(f, BK)
cambios = collections.Counter()
for f, j in zip(cs, js):
    t = j["es"]
    for viejo, nuevo in TEXTO:
        if viejo in t:
            cambios[f.name] += t.count(viejo)
            t = t.replace(viejo, nuevo)
    if t != j["es"]:
        assert collections.Counter(MATH.findall(t)) == collections.Counter(MATH.findall(j["es"])), f.name
        assert collections.Counter(MATH.findall(t)) == collections.Counter(MATH.findall(j["src"])), f.name + " vs src"
        j["es"] = t
        f.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
assert "\n\n".join(j["es"] for j in js) == full
(D / "es.md").write_text("\n\n".join(j["es"] for j in js) + "\n", encoding="utf-8")
print(f"cambios: {sum(cambios.values())} en {dict(cambios)}")

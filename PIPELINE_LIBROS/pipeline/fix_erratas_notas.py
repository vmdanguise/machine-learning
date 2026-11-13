"""Notas visibles para las erratas conservadas del original (regla del usuario, 2026-11-02:
"toda errata conservada lleva nota visible").

Por cada errata agrega, en el campo 'es' de 03_traduccion/NN/cNNN.json (respaldo en es_pre_erratas):
  - la llamada [^pNNN-k] junto al texto conservado (fuera de $...$),
  - el bloque "[^pNNN-k]: N. del T.: errata del original: ..." despues del parrafo/tabla/epigrafe,
  - un comentario oculto "<!-- NOTA (fix_erratas_notas: CLAVE) ... -->" que marca que ya esta aplicada.
Las <!-- NOTA --> de erratas que ya existian quedan intactas (otros fix_* las usan como ancla de idempotencia).
Despues regenera es.md ("\\n\\n".join(es) + "\\n"). No toca src, transcripciones, en.md ni la matematica.

Incluye tambien una nota por capitulo de DUDAHART en la primera aparicion de '??' (referencias sin resolver del
original) y en la primera aparicion de marcadores de relleno 'xx'/'xxx' del borrador.
Las NOTA de proceso (figuras sin rotulo EX9.38 y EX10.1 de DUDAHART, P11.38/P11.39 y P12.23/P12.33 de GONZALEZ, columnas
de la Tabla 7.1 de GONZALEZ) siguen ocultas.

Al final renumera las notas al pie de las paginas que tienen alguna nota de este script, en el orden en que aparecen
sus llamadas (una nota nueva toma el primer numero libre y podia quedar antes que una previa: DUDAHART 06 p332).
Idempotente: si la marca de una nota ya esta en es.md no hace nada. Si un ancla no aparece exactamente una vez,
aborta sin escribir nada. Respaldo previo (solo la primera vez) en <LIBRO>_traduccion/_backup_pre_fix/erratas_notas/NN.
Correr de nuevo despues de cualquier translate.py / fix_registro / fix_ingles* / fix_* de los caps afectados.
Las claves de DUDAHART usan el prefijo "DH" (un comentario con "DUDA" lo toman como DOUBT render.py y validate.py).
Uso: python fix_erratas_notas.py [--dry]
"""
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(r"D:\Universidad De Palermo - Maestria en IA\Machine Learning")
DRY = "--dry" in sys.argv
PRE = "N. del T.: errata del original: "
QQ = ("todas las referencias '??' (Cap., Secc., Ec., Fig., Problema, Algoritmo, Apéndice) de este capítulo son "
      "marcadores sin resolver del original; se conservan tal cual.")
XX = ("los 'xx' y 'xxx' que aparecen en este capítulo en lugar de valores, fórmulas, referencias o texto son "
      "marcadores de relleno del borrador del libro; se conservan tal cual.")

# (clave, libro, cap, ancla, modo, texto, ya_tenia_NOTA)
#   modo "after": la llamada va justo despues del ancla (nunca pegada a una formula: el superindice se
#   confundiria con un exponente); "endblock": al final del bloque que contiene el ancla.
#   ancla None = primera aparicion de '??' en el capitulo.
N = [
    ("BISHOP07_7.59", "BISHOP", "07",
     "donde las sumas $i = 1, \\ldots, M$ se toman sobre todas las unidades ocultas de la capa.", "after",
     "en la Ec. (7.59) el original escribe $\\mu_i$; por el contexto debería ser $\\mu_n$. Se conserva tal cual.",
     True),
    ("GONZALEZ07_7-152", "GONZALEZ", "07", "producen la función de escalado *separable*", "after",
     "la Ec. (7-152) está corrupta en el propio PDF fuente (solo se ve '1 ∫^∞ ,'); se conserva tal cual.", True),
    ("GONZALEZ10_10.10a", "GONZALEZ", "10", "y que la tasa de ese descenso", "after",
     "en el Problema 10.10(a) el original dice *the rate of that descent* (debería ser el ascenso: el gradiente "
     "apunta en la dirección de máximo crecimiento); se conserva 'descenso' tal cual.", True),
    ("GONZALEZ04_T4.4", "GONZALEZ", "04",
     "| 12) | Diferenciación", "after",
     "en la entrada 12 de la Tabla 4.4 el original escribe $\\partial z^m$ en el denominador de la derivada "
     "$n$-ésima respecto de $z$ (debería ser $\\partial z^n$); se conserva tal cual.", False),
    ("DH02_Laplace", "DUDAHART", "02", "*Théorie Analytique des Probabiltiés*", "after",
     "'Probabiltiés' (por 'Probabilités') en la referencia [25]; se conserva tal cual.", False),
    ("DH07_sqrt_sup", "DUDAHART", "07", "$-\\sqrt{3/N} < w_{ij} < +1\\sqrt{3/N}$ (Problema 17).", "after",
     "el límite superior se imprime $+1\\sqrt{3/N}$, con un '1' sobrante (debería ser $+\\sqrt{3/N}$); se conserva "
     "tal cual.", True),
    ("DH07_sqrt_inf", "DUDAHART", "07", "$-1\\sqrt{3/N} < w_{ij} < +\\sqrt{3/N}$.", "after",
     "en el Problema 17 el límite inferior se imprime $-1\\sqrt{3/N}$, con un '1' sobrante (debería ser "
     "$-\\sqrt{3/N}$); se conserva tal cual.", False),
    ("DH05_T5.1", "DUDAHART", "05", "| **Rema**", "after",
     "la última columna de la Tabla 5.1 (*Remarks*) está cortada por el margen derecho de la página en el "
     "original; se conserva el texto truncado tal cual, en inglés.", False),
    ("DH06_F6.10", "DUDAHART", "06", "**Figura 6.10:** Una red con xxx pesos", "endblock",
     "la Fig. 6.10 no tiene imagen en el original y su epígrafe trae 'xxx'. En general, " + XX, False),
    ("DH10_F10.17", "DUDAHART", "10", "**Figura 10.17:** Puede surgir inestabilidad", "endblock",
     "la Fig. 10.17 es un marco vacío en el original (igual que las Figs. 10.18 y 10.19); se conserva tal cual.",
     False),
    ("DH10_F10.18", "DUDAHART", "10", "**Figura 10.18:** Red de Resonancia Adaptativa", "endblock",
     "la Fig. 10.18 es un marco vacío en el original y a su epígrafe le falta una palabra ('el sistema orientador "
     "controla el , y ...'); se conservan tal cual.", False),
    ("DH10_F10.19", "DUDAHART", "10", "$\\rho = 0.xx$.", "after",
     "el epígrafe de la Fig. 10.19 trae 'ρ = xx' y 'ρ = 0.xx' y la figura es un marco vacío en el original. "
     "En general, los 'xx', 'xxx' (y en las ecuaciones de la Sección 10.13, 'WWW', 'yyy', 'zzz') que aparecen en "
     "este capítulo en lugar de valores, fórmulas o texto son marcadores de relleno del borrador del libro; se "
     "conservan tal cual.", True),
    ("DH10_P23", "DUDAHART", "10", "$\\mathbf{x}_4 = \\binom{xx}{xx}$, y considérense las siguientes tres particiones:", "after",
     "los vectores $\\mathbf{x}_1, \\ldots, \\mathbf{x}_4$ del Problema 23 figuran como 'xx' en el original "
     "(marcadores de relleno del borrador del libro); se conservan tal cual.", True),
    ("DH10_P43", "DUDAHART", "10",
     "**43.** Mostrar que una red neuronal de autoasociación compuesta de $d - k - d$ capas de entrada, oculta y "
     "de salida (con $k < d$)", "after",
     "el enunciado del Problema 43 y el inciso (b) quedan cortados en el original (el comienzo del enunciado se "
     "repite en (a) y en (b)); se conservan tal cual.", False),
    ("FUNDAMENTALS10_Dstar", "FUNDAMENTALS", "10",
     "podemos expresar alternativamente la puntuación óptima del discriminador propuesta en términos de "
     "probabilidades condicionales:", "after",
     "la fracción de la puntuación óptima del discriminador aparece sola en esta ecuación y se repite en la "
     "primera línea de la derivación de $D^\\star(x)$ que sigue; se conserva tal cual.", False),
    ("FUNDAMENTALS11_zhat", "FUNDAMENTALS", "11", "la función de pérdida tiene la siguiente forma:", "after",
     "en la ecuación que sigue el original imprime 'zâ' en el subíndice de la sumatoria y en $g(\\cdot)$ (error de "
     "codificación; por el texto debería ser $z'$); se conserva tal cual.", False),
    ("FUNDAMENTALS12_softmax", "FUNDAMENTALS", "12",
     "los modos de lectura deben tener una distribución softmax válida:", "after",
     "en la ecuación que sigue el denominador de softmax se imprime $\\Sigma_j e^z j$, con la $j$ fuera del "
     "exponente (debería ser $\\Sigma_j e^{z_j}$); se conserva tal cual.", False),
    ("FUNDAMENTALS13_Qtheta", "FUNDAMENTALS", "13", "de nuestro modelo como Qtheta", "after",
     "el original imprime literalmente 'Qtheta' (texto plano, sin formato matemático) en lugar de "
     "$\\widehat{Q}(s, a \\mid \\theta)$ o $Q_\\theta$, la notación de la ecuación anterior; se conserva tal cual.", False),
    ("BISHOP12_EX12.15", "BISHOP", "12",
     "Vemos que la secuencia más probable es $y_1 = B$, $y_2 = B$ y que esta tiene probabilidad 0.4.", "after",
     "en la tabla del Ejercicio 12.15 las cuatro probabilidades conjuntas suman 0.75 (no 1) y la entrada 0.4 "
     "corresponde a $y_1 = B$, $y_2 = A$ (para $y_1 = B$, $y_2 = B$ la tabla da 0.25), en contradicción con el texto; "
     "se conserva tal cual.", False),
    ("BISHOP12_Alg12.2", "BISHOP", "12", "se resume en el Algoritmo 12.2", "after",
     "en el Algoritmo 12.2 la salida se imprime $\\{\\mathbf{y}_1, \\ldots, \\mathbf{x}_N\\}$ (debería ser "
     "$\\mathbf{y}_N$) y la concatenación $\\text{Concat}[\\mathbf{H}_1, \\ldots, \\mathbf{H}_N]$ (debería terminar "
     "en $\\mathbf{H}_H$, un cabezal por cada $h = 1, \\ldots, H$); se conservan tal cual.", False),
    ("BISHOP14_Alg14.1", "BISHOP", "14", "El algoritmo de Metropolis se resume en el Algoritmo 14.1", "after",
     "en los Algoritmos 14.1 y 14.2 el comentario «// Iterative message-passing» («Paso de mensajes iterativo») "
     "parece copiado del Algoritmo 13.1: el muestreo de Metropolis y el de Metropolis-Hastings no hacen paso de "
     "mensajes; se conserva tal cual.", False),
    ("BISHOP15_Alg15.1", "BISHOP", "15", "Se resume en el Algoritmo 15.1", "after",
     "en el Algoritmo 15.1 el primer bucle se imprime **for** $N \\in \\{1, \\ldots, N\\}$ (la variable del bucle "
     "debería ser $n$, como en $\\mathbf{x}_n$); se conserva tal cual.", False),
    ("BISHOP15_Alg15.2", "BISHOP", "15", "lo resumimos en el Algoritmo 15.2", "after",
     "en el Algoritmo 15.2 la salida se imprime **return** $\\{\\mathbf{x}_k\\}$, $\\{\\boldsymbol{\\Sigma}_k\\}$, "
     "$\\{\\pi_k\\}$ (debería ser $\\{\\boldsymbol{\\mu}_k\\}$, como en la línea **Salida**); se conserva tal cual.", False),
    ("BISHOP15_Alg15.3", "BISHOP", "15", "El algoritmo EM general se resume en el Algoritmo 15.3", "after",
     "en el Algoritmo 15.3 la línea comentada como log-verosimilitud se imprime "
     "$\\mathcal{L} \\leftarrow p(\\mathbf{X}|\\boldsymbol{\\theta}^{\\text{new}})$, sin el logaritmo (debería ser "
     "$\\ln p(\\mathbf{X}|\\boldsymbol{\\theta}^{\\text{new}})$); se conserva tal cual.", False),
    ("BENGIO17_tempering", "BENGIO", "17", "Los estados de mayor temperatura mezclan lentamente", "after",
     "en la Secc. 17.5.1 el original dice *The highest temperature states mix slowly* (debería ser *rapidly*: "
     "subir la temperatura aplana la distribución justamente para mezclar entre modas con más facilidad, como "
     "explica el párrafo anterior); se conserva 'lentamente' tal cual.", False),
    ("BISHOP19_19.18", "BISHOP", "19", "donde $l = 1, \\ldots, L$ indexa las muestras.", "after",
     "la Ec. (19.18) se imprime $\\mu_j(\\mathbf{x}_n, \\phi)\\epsilon_{nj}^{(l)} + \\sigma_j^2(\\mathbf{x}_n, \\phi)$; "
     "según (19.17) debería ser $\\mu_j(\\mathbf{x}_n, \\phi) + \\sigma_j(\\mathbf{x}_n, \\phi)\\epsilon_{nj}^{(l)}$ "
     "(el texto de la Figura 19.11 lo escribe bien: $\\sigma_{nj}\\epsilon^{(l)} + \\mu_{nj}$); se conserva tal cual.",
     False),
    ("BISHOP19_Alg19.1", "BISHOP", "19", "El entrenamiento del VAE se resume en el Algoritmo 19.1", "after",
     "en el Algoritmo 19.1 la línea del muestreo repite el error de la Ec. (19.18): se imprime "
     "$z_{nj} \\leftarrow \\mu_j(\\mathbf{x}_n, \\phi)\\epsilon_{nj} + \\sigma_j^2(\\mathbf{x}_n, \\phi)$ (debería ser "
     "$\\mu_j(\\mathbf{x}_n, \\phi) + \\sigma_j(\\mathbf{x}_n, \\phi)\\epsilon_{nj}$); se conserva tal cual.", False),
    ("BISHOP19_19.22", "BISHOP", "19", "extraído de una gaussiana simple:", "after",
     "en la Ec. (19.22) se imprime $\\boldsymbol{\\epsilon} \\sim \\mathcal{N}(\\mathbf{z}|\\mathbf{0}, \\mathbf{I})$; "
     "la variable de la densidad debería ser $\\boldsymbol{\\epsilon}$: "
     "$\\mathcal{N}(\\boldsymbol{\\epsilon}|\\mathbf{0}, \\mathbf{I})$. Se conserva tal cual.", False),
    ("BISHOP20_Alg20.2", "BISHOP", "20", "El procedimiento de muestreo se resume en el Algoritmo 20.2.", "after",
     "en el paso final del Algoritmo 20.2 (fuera del bucle) se imprime $\\mathbf{g}(\\mathbf{z}_1, \\mathbf{w}, t)$; "
     "debería ser $\\mathbf{g}(\\mathbf{z}_1, \\mathbf{w}, 1)$, es decir, (20.36) con $t = 1$. Se conserva tal cual.", False),
    ("BISHOP20_20.3", "BISHOP", "20", "marginal de $\\mathbf{x}_t$ para el proceso hacia adelante", "after",
     "en el Ejercicio 20.3 el original habla de la distribución marginal de $\\mathbf{x}_t$; la variable del proceso "
     "hacia adelante es $\\mathbf{z}_t$, cuya distribución da (20.6). Se conserva tal cual.", False),
    ("BISHOP20_20.10", "BISHOP", "20", "Nótese que el proceso de ruido se construye de tal manera", "endblock",
     "en la nota del Ejercicio 20.10 se imprime que $q(\\mathbf{z}_T|\\mathbf{x})$ y $p(\\mathbf{z}_T)$ son iguales a "
     "$\\mathcal{N}(\\mathbf{x}|\\mathbf{0}, \\mathbf{I})$; la variable de la densidad debería ser $\\mathbf{z}_T$: "
     "$\\mathcal{N}(\\mathbf{z}_T|\\mathbf{0}, \\mathbf{I})$. Se conserva tal cual.", False),
    ("BISHOP20_20.14", "BISHOP", "20", "Mostrar que si la función *score* se define tomando", "endblock",
     "en el Ejercicio 20.14 la función *score* se imprime dos veces como "
     "$\\mathbf{s}(\\mathbf{x}) = \\nabla_\\mathbf{x} p(\\mathbf{x}|\\mathbf{w})$, sin el logaritmo; según (20.42) "
     "debería ser $\\nabla_\\mathbf{x} \\ln p(\\mathbf{x}|\\mathbf{w})$. Se conserva tal cual.", False),
    ("BISHOP20_20.16", "BISHOP", "20", "No es posible minimizar la función *score* (20.43)", "after",
     "en el Ejercicio 20.16 el original dice *minimize the score function (20.43)*; (20.43) es la función de pérdida "
     "de *score*, no la función *score*. Se conserva tal cual.", False),
    ("BISHOP20_sD", "BISHOP", "20", "para completar la demostración.", "after",
     "en el Ejercicio 20.16 se imprime aquí $\\mathbf{s}_\\mathcal{D} = \\nabla \\ln p(\\mathbf{x})$; unas líneas antes "
     "se definió $\\mathbf{s}_\\mathcal{D} = \\nabla \\ln p_\\mathcal{D}(\\mathbf{x})$ (la densidad de los datos). "
     "Se conserva tal cual.", False),
    # marcadores de relleno: una nota por capitulo (06 y 10 van en las notas de las Figs. 6.10 y 10.19)
    ("DH03_xx", "DUDAHART", "03", "[22] Andrei Andreivich Markov. xxx. *xxx*, xxx(xxx):xxx–xxx, 1907.",
     "after", XX, False),
    ("DH04_xx", "DUDAHART", "04", "(en el centro de cada cuadrado) son xxx.", "after", XX, False),
    ("DH05_xx", "DUDAHART", "05", "Mostrar que los primeros $xx$ puntos", "after", XX, False),
    ("DH07_xx", "DUDAHART", "07", "$c$ unidades ocultas y xx unidades visibles", "after", XX, False),
    ("DH09_xx", "DUDAHART", "09", "Caso en el que MDL es más fácil que imponer probabilidades. xxx", "after",
     XX, False),
] + [("DH%02d_qq" % c, "DUDAHART", "%02d" % c, None, "after", QQ, False) for c in range(1, 11)]

FN_REF = re.compile(r"\[\^p(\d+)-(\d+)\]")


def in_math(block_before):
    """True si la posicion (final de block_before) cae dentro de $...$ o $$...$$."""
    if block_before.count("$$") % 2 == 1:
        return True
    s = block_before.replace("$$", "")
    return len(re.findall(r"(?<!\\)\$", s)) % 2 == 1


def page_at(es_all, pos):
    p = re.findall(r"<<PAGE (\d+)>>", es_all[:pos])
    assert p, pos
    return int(p[-1])


def main():
    plan = {}   # (libro, cap) -> [notas]
    for n in N:
        plan.setdefault((n[1], n[2]), []).append(n)
    total, cambiados = 0, []
    for (book, cap), notas in plan.items():
        W = ROOT / f"{book}_traduccion"
        D = W / "03_traduccion" / cap
        cs = sorted(D.glob("c*.json"), key=lambda f: int(f.stem[1:]))
        js = [json.loads(f.read_text(encoding="utf-8")) for f in cs]
        es_md = (D / "es.md").read_text(encoding="utf-8")
        assert "\n\n".join(j["es"] for j in js) + "\n" == es_md, f"{book} {cap}: es.md no coincide con los json"
        pend = []
        for key, _, _, anc, modo, txt, tenia in notas:
            mark = f"<!-- NOTA (fix_erratas_notas: {key})"
            if mark in es_md:
                print(f"{book} {cap} {key}: ya aplicada")
                continue
            if anc is None:
                anc = "??"
                ci = next(i for i, j in enumerate(js) if "??" in j["es"])
                pos = js[ci]["es"].find("??")
            else:
                assert es_md.count(anc) == 1, f"{book} {cap} {key}: ancla aparece {es_md.count(anc)} veces"
                hit = [i for i, j in enumerate(js) if anc in j["es"]]
                assert len(hit) == 1, f"{book} {cap} {key}: ancla en {len(hit)} fragmentos"
                ci = hit[0]
                pos = js[ci]["es"].find(anc)
            pend.append((key, anc, modo, txt, tenia, ci, pos))
        if not pend:
            continue
        # aplicar de atras hacia adelante dentro de cada fragmento no hace falta: se recalcula todo por nota
        for key, anc, modo, txt, tenia, ci, _ in pend:
            es = js[ci]["es"]
            pos = es.find(anc) if anc != "??" else es.find("??")
            end_blk = es.find("\n\n", pos)
            end_blk = len(es) if end_blk < 0 else end_blk
            if modo == "after":
                ins = pos + len(anc)
            else:
                ins = len(es[:end_blk].rstrip())
            blk_start = es.rfind("\n\n", 0, pos)
            blk_start = 0 if blk_start < 0 else blk_start + 2
            assert not in_math(es[blk_start:ins]), f"{book} {cap} {key}: la llamada caeria dentro de $...$"
            # pagina y numero libre
            prev = "\n\n".join(j["es"] for j in js[:ci])
            prev = prev + "\n\n" if prev else ""
            pg = page_at(prev + es, len(prev) + pos)
            all_now = "\n\n".join(j["es"] for j in js)
            used = [int(m.group(2)) for m in FN_REF.finditer(all_now) if int(m.group(1)) == pg]
            k = max(used, default=0) + 1
            fid = f"p{pg}-{k}"
            ref = f"[^{fid}]"
            fdef = f"[^{fid}]: {PRE}{txt}"
            nota = (f"<!-- NOTA (fix_erratas_notas: {key}) nota al pie visible [^{fid}]; la NOTA original se mantiene. -->"
                    if tenia else
                    f"<!-- NOTA (fix_erratas_notas: {key}) {txt} -->")
            new = es[:ins] + ref + es[ins:end_blk] + "\n\n" + fdef + "\n\n" + nota + es[end_blk:]
            if end_blk == len(es):
                new = es[:ins] + ref + es[ins:] + "\n\n" + fdef + "\n\n" + nota
            js[ci].setdefault("es_pre_erratas", es)
            js[ci]["es"] = new
            total += 1
            linea = es[blk_start:ins].replace("\n", " ")
            print(f"{book} {cap} {key}: {fid} en {cs[ci].name} | ...{linea[-70:]}{ref}")
        new_md = "\n\n".join(j["es"] for j in js) + "\n"
        # controles: la matematica y el texto previo quedan iguales (salvo llamadas, notas y comentarios agregados)
        def strip_added(t):
            t = re.sub(r"\n\n\[\^p\d+-\d+\]: N\. del T\.: errata del original: [^\n]*", "", t)
            t = re.sub(r"\n\n<!-- NOTA \(fix_erratas_notas: [^\n]*?-->", "", t)
            return t
        added_refs = [r for r in FN_REF.findall(new_md)]
        base = strip_added(new_md)
        for key, *_ in pend:
            pass
        old_refs = set(FN_REF.findall(es_md))
        for pg_, k_ in set(added_refs) - old_refs:
            base = base.replace(f"[^p{pg_}-{k_}]", "", 1)
        # se compara contra es_md sin las notas del script ya presentes (un cap puede recibir notas en corridas distintas)
        assert base == strip_added(es_md), f"{book} {cap}: el control de solo-agregados fallo"
        cambiados.append(f"{book}/{cap}")
        if DRY:
            continue
        bk = W / "_backup_pre_fix" / "erratas_notas" / cap
        if not bk.exists():
            bk.mkdir(parents=True)
            for f in cs:
                shutil.copy2(f, bk / f.name)
            shutil.copy2(D / "es.md", bk / "es.md")
        for f, j in zip(cs, js):
            f.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
        (D / "es.md").write_text(new_md, encoding="utf-8")
    print(("[dry] " if DRY else "") + f"notas agregadas: {total}; caps cambiados: {cambiados or 'ninguno (ya aplicado)'}")
    ren = [f"{b}/{c}" for b, c in plan if renumerar(b, c)]
    print(("[dry] " if DRY else "") + f"renumeradas: {ren or 'ninguna (orden ya correcto)'}")


def renumerar(book, cap):
    """Numera las notas al pie de cada pagina en el orden en que aparecen sus llamadas en el texto (las notas
    nuevas toman el primer numero libre y pueden quedar antes que una nota previa de la misma pagina, p. ej.
    DUDAHART 06 p332). Renombra llamadas, definiciones y las menciones dentro de los comentarios NOTA.
    Idempotente: si el orden ya es correcto no escribe nada. Devuelve True si cambio algo."""
    W = ROOT / f"{book}_traduccion"
    D = W / "03_traduccion" / cap
    cs = sorted(D.glob("c*.json"), key=lambda f: int(f.stem[1:]))
    js = [json.loads(f.read_text(encoding="utf-8")) for f in cs]
    full = "\n\n".join(j["es"] for j in js)
    prosa = re.sub(r"<!--.*?-->", "", full, flags=re.S)
    orden = {}
    for m in re.finditer(r"\[\^p(\d+)-(\d+)\](?!:)", prosa):
        ks = orden.setdefault(m.group(1), [])
        if m.group(2) not in ks:
            ks.append(m.group(2))
    # solo paginas con alguna nota de este script: en las demas el numero viene del original (p. ej. FUNDAMENTALS
    # numera las notas por capitulo: p264-2 es la nota 2 del libro) y no se toca
    nuestras = set(re.findall(r"^\[\^p(\d+)-\d+\]: " + re.escape(PRE), full, re.M))
    mapa = {}
    for pg, ks in orden.items():
        if pg not in nuestras:
            continue
        for nuevo, viejo in enumerate(ks, 1):
            if int(viejo) != nuevo:
                mapa[f"p{pg}-{viejo}"] = f"p{pg}-{nuevo}"
    if not mapa:
        return False
    # las definiciones sin llamada no se tocan; los numeros nuevos tienen que salir de los ya usados en la pagina
    defs = set(re.findall(r"^\[\^(p\d+-\d+)\]:", full, re.M))
    assert set(mapa) <= defs and set(mapa.values()) <= set(mapa) | defs, f"{book} {cap}: renumeracion ambigua {mapa}"
    print(f"{book} {cap}: renumerar {mapa}")
    if DRY:
        return True
    sub = lambda s: re.sub(r"\[\^(p\d+-\d+)\]", lambda m: f"[^{mapa.get(m.group(1), m.group(1))}]", s)
    for f, j in zip(cs, js):
        nuevo = sub(j["es"])
        if nuevo != j["es"]:
            j.setdefault("es_pre_erratas", j["es"])
            j["es"] = nuevo
            f.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
    (D / "es.md").write_text("\n\n".join(j["es"] for j in js) + "\n", encoding="utf-8")
    return True


if __name__ == "__main__":
    main()

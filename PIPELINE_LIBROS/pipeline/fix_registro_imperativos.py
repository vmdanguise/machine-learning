"""Imperativos de usted (y un 'Nota que') dirigidos al lector que quedaron en caps cerrados (2026-11-02, auditoria de
voseo/tuteo/usted, bitacora AJUSTES/2026-11-02 septima tanda). validate.py no los detecta (VOSEO_WORDS/TU_WORDS solo
buscan pronombres y voseo; USTED_HINT es aviso) y fix_registro los dejo en algunos fragmentos.
Criterio (igual que el resto de DUDAHART/GONZALEZ): en enunciados de ejercicios el imperativo pasa a infinitivo
('Considerar', 'Suponer', 'Repetir', 'Escribir'); en epigrafes y prosa, forma impersonal ('Comparese', 'vease',
'Notese que', 'Conviene prestar atencion', 'Cabe advertir que').
Toca solo el campo 'es' de <LIBRO>_traduccion/03_traduccion/NN/cNNN.json (reemplazo exacto dentro del parrafo que
contiene el ancla; assert de unicidad), comprueba que la matematica del fragmento no cambia y regenera es.md
("\\n\\n".join(es) + "\\n", cNNN en orden numerico).
Backup en <LIBRO>_traduccion/_backup_pre_fix/registro_imp/NN (cNNN.json tocados + es.md), solo la primera vez.
Idempotente. Despues: fix_erratas_notas.py, re-render y validate de los caps tocados.
Uso: python fix_registro_imperativos.py [--dry]"""
import collections
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(r"D:\Universidad De Palermo - Maestria en IA\Machine Learning")
MATH = re.compile(r"\$\$.*?\$\$|\$[^$\n]+?\$", re.S)
DRY = "--dry" in sys.argv

# (libro, cap, fragmento, ancla del parrafo, viejo, nuevo)
FIX = [
    ("GONZALEZ", "03", "c027", "**3.17**",
     "kernel y muestre que el resultado de su expansión corresponde a su figura.",
     "kernel y mostrar que el resultado de la expansión corresponde a la figura."),
    ("GONZALEZ", "04", "c036", "DIP4E Student Support Package",
     "(consulte el sitio web del libro:", "(véase el sitio web del libro:"),
    ("GONZALEZ", "05", "c014", "**Figura 5.30**",
     "Compare (a), (b) y (c) con los resultados", "Compárense (a), (b) y (c) con los resultados"),
    ("GONZALEZ", "05", "c024", "Compare (d) con la Fig. 5.43(b)",
     "Compare (d) con la Fig. 5.43(b)", "Compárese (d) con la Fig. 5.43(b)"),
    ("GONZALEZ", "05", "c024", "Compare (d) con la Fig. 5.44(b)",
     "Compare (d) con la Fig. 5.44(b)", "Compárese (d) con la Fig. 5.44(b)"),
    ("GONZALEZ", "05", "c024", "DIP4E Student Support Package",
     "(consulte el sitio web del libro:", "(véase el sitio web del libro:"),
    ("GONZALEZ", "05", "c024", "**5.2**", "**5.2** Repita el Problema 5.1", "**5.2** Repetir el Problema 5.1"),
    ("GONZALEZ", "05", "c024", "**5.4**", "**5.4** Repita el Problema 5.1", "**5.4** Repetir el Problema 5.1"),
    ("GONZALEZ", "05", "c024", "**5.6**", "**5.6** Repita el Problema 5.1", "**5.6** Repetir el Problema 5.1"),
    ("GONZALEZ", "05", "c024", "**5.8**", "**5.8** Repita el Problema 5.1", "**5.8** Repetir el Problema 5.1"),
    # segunda pasada (barrido amplio: inicio de oracion con cualquier marcador, *Sugerencia:*, 'se le pide')
    ("GONZALEZ", "05", "c024", "**5.3**", "**5.3**\\* Repita el Problema 5.1", "**5.3**\\* Repetir el Problema 5.1"),
    ("GONZALEZ", "05", "c024", "**5.5**", "**5.5**\\* Repita el Problema 5.1", "**5.5**\\* Repetir el Problema 5.1"),
    ("GONZALEZ", "05", "c024", "**5.7**", "**5.7**\\* Repita el Problema 5.1", "**5.7**\\* Repetir el Problema 5.1"),
    ("GONZALEZ", "05", "c024", "**5.9**", "**5.9**\\* Repita el Problema 5.1", "**5.9**\\* Repetir el Problema 5.1"),
    ("GONZALEZ", "05", "c024", "como esquinas redondeadas",
     "Asegúrese de describir cualquier deformación", "Se debe describir cualquier deformación"),
    ("GONZALEZ", "05", "c026", "**5.39**",
     "Como experto en procesamiento digital de imágenes y amigo del profesor, se le pide como favor que determine",
     "Al lector, como experto en procesamiento digital de imágenes y amigo del profesor, se le pide como favor que "
     "determine"),
    ("GONZALEZ", "03", "c029", "**3.46**", "(*Sugerencia:* Estudie los enunciados", "(*Sugerencia:* Estudiar los enunciados"),
    ("GONZALEZ", "04", "c040", "**4.63**", "(*Hint:* Use proof by induction.)",
     "(*Sugerencia:* Usar demostración por inducción.)"),
    ("DUDAHART", "03", "c028", "**44.**", "**44.** Considere una", "**44.** Considerar una"),
    ("DUDAHART", "03", "c028", "**45.**", "**45.** Considere el", "**45.** Considerar el"),
    ("DUDAHART", "03", "c028", "**48.**", "**48.** Considere el", "**48.** Considerar el"),
    ("DUDAHART", "03", "c028", "**1.** Considere modelos", "**1.** Considere modelos", "**1.** Considerar modelos"),
    ("DUDAHART", "03", "c028", "**2.** Considere un modelo", "**2.** Considere un modelo", "**2.** Considerar un modelo"),
    ("DUDAHART", "03", "c028", "**3.** Considere la estimación", "**3.** Considere la estimación",
     "**3.** Considerar la estimación"),
    ("DUDAHART", "04", "c020", "**24.**", "**24.** Considere la", "**24.** Considerar la"),
    ("DUDAHART", "04", "c020", "**24.**", "Suponga que nos restringimos", "Suponer que nos restringimos"),
    ("DUDAHART", "04", "c020", "**25.**", "**25.** Considere la", "**25.** Considerar la"),
    ("DUDAHART", "04", "c020", "**25.**", "Suponga que el número de operaciones", "Suponer que el número de operaciones"),
    ("DUDAHART", "04", "c020", "**25.**", "Suponga también que", "Suponer también que"),
    ("DUDAHART", "04", "c020", "(c) Suponga que hay", "(c) Suponga que hay", "(c) Suponer que hay"),
    ("DUDAHART", "04", "c020", "**27.**", "**27.** Considere la", "**27.** Considerar la"),
    ("DUDAHART", "04", "c020", "**28.**", "**28.** Suponga que alguien le pregunta si",
     "**28.** Suponer que alguien pregunta si"),
    ("DUDAHART", "04", "c020", "**29.**", "**29.** Considere el", "**29.** Considerar el"),
    ("DUDAHART", "04", "c020", "Suponga que para la longitud", "Suponga que para la longitud",
     "Suponer que para la longitud"),
    ("DUDAHART", "04", "c020", "Suponga que para la longitud", "Suponga que el diseñador", "Suponer que el diseñador"),
    ("DUDAHART", "04", "c020", "**30.**", "**30.** Suponga que", "**30.** Suponer que"),
    ("DUDAHART", "04", "c020", "**31.**", "**31.** Considere una", "**31.** Considerar una"),
    ("DUDAHART", "10", "c033", "clasificador de agrupamiento dirigido por decisión", "7. Escriba un clasificador", "7. Escribir un clasificador"),
    ("BISHOP", "12", "c016", "Nota que el uso", "Nota que el uso", "Nótese que el uso"),
    ("BENGIO", "02", "c003", "matrices ortogonales son de interés",
     "Preste atención a la definición", "Conviene prestar atención a la definición"),
    ("FUNDAMENTALS", "04", "c003", "tomar atajos al compilar los datos de prueba",
     "Quede advertido: si el conjunto de prueba", "Cabe advertir que, si el conjunto de prueba"),
]

por_cap = collections.OrderedDict()
for lib, cap, c, anc, old, new in FIX:
    por_cap.setdefault((lib, cap), []).append((c, anc, old, new))

hechos, ya = [], []
for (lib, cap), fixes in por_cap.items():
    W = ROOT / f"{lib}_traduccion"
    D = W / "03_traduccion" / cap
    BK = W / "_backup_pre_fix" / "registro_imp" / cap
    cs = sorted(D.glob("c*.json"), key=lambda f: int(f.stem[1:]))
    tocados = sorted({c for c, *_ in fixes})
    if not DRY:  # backup por archivo, solo la primera vez (es.md: el de antes de la primera corrida)
        BK.mkdir(parents=True, exist_ok=True)
        for c in tocados:
            if not (BK / f"{c}.json").exists():
                shutil.copy2(D / f"{c}.json", BK)
        if not (BK / "es.md").exists():
            shutil.copy2(D / "es.md", BK)
    es_all = []
    for f in cs:
        j = json.loads(f.read_text(encoding="utf-8"))
        t = j["es"]
        mine = [x for x in fixes if x[0] == f.stem]
        if mine:
            pars = t.split("\n\n")
            def ya_corregida(s):  # el ancla tal como queda despues de aplicar los reemplazos del fragmento
                for _, _, o, n in mine:
                    s = s.replace(o, n)
                return s
            for _, anc, old, new in mine:
                hit = [k for k, p in enumerate(pars)
                       if (anc in p or ya_corregida(anc) in p) and (old in p or new in p)]
                assert len(hit) == 1, (lib, cap, f.stem, anc, len(hit))
                k = hit[0]
                if old in pars[k]:
                    assert pars[k].count(old) == 1, (lib, cap, f.stem, old)
                    pars[k] = pars[k].replace(old, new)
                    hechos.append(f"{lib} {cap} {f.stem} par{k}: {old!r} -> {new!r}")
                else:
                    ya.append(f"{lib} {cap} {f.stem} par{k}")
            t2 = "\n\n".join(pars)
            assert collections.Counter(MATH.findall(t2)) == collections.Counter(MATH.findall(j["es"])), f.name
            if t2 != t and not DRY:
                j["es"] = t2
                f.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
            t = t2
        es_all.append(t)
    if not DRY:
        (D / "es.md").write_text("\n\n".join(es_all) + "\n", encoding="utf-8")

print(("DRY " if DRY else "") + f"reemplazos aplicados: {len(hechos)}; ya aplicados: {len(ya)}; total previstos: {len(FIX)}")
for h in hechos:
    print("  ", h)
print("caps:", " ".join(f"{l}/{c}" for l, c in por_cap))

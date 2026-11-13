"""Unificacion terminologica: *mode* (maximo de una distribucion) -> 'moda' (2026-11-02, decision del usuario tras el
cierre de BENGIO 17; bitacora AJUSTES/2026-11-02, novena tanda).

'moda' es el termino estandar en estadistica. BISHOP ya lo usaba en todos los caps salvo uno; BENGIO 03 y 12 tambien.
Quedaban 'modo/modos' en BENGIO 06 (output mode de las redes de densidad de mezcla), BENGIO 17 (Secc. 17.5, mezcla
entre modas, y la nota de la errata p618-1) y BISHOP 03 (concentracion de von Mises alrededor de la moda theta_0).
NO se tocan otros sentidos de 'modo': 'modo directo/inverso' (forward/reverse mode de la diferenciacion automatica,
BENGIO 06 y BISHOP 08), 'modo por lotes', 'modo de bucle abierto', 'modo de ejecucion libre', ni locuciones ('de modo
que', 'del mismo modo', 'de este modo'). Por eso los reemplazos son explicitos, con contexto y concordancia de genero.

Toca solo el campo 'es' de 03_traduccion/NN/cNNN.json (no src, es_pre_erratas, transcripciones ni matematica) y
regenera es.md ("\\n\\n".join(es) + "\\n"). Backup en <LIBRO>_traduccion/_backup_pre_fix/moda_unif/NN (una vez).
27 pares (viejo, nuevo, n) y 28 ocurrencias (un par vale 2: la nota p618-1 y su <!-- NOTA -->).
Idempotente: cada par exige que 'viejo' aparezca n veces (sin aplicar) o 0 veces con 'nuevo' n veces (ya aplicado).
Un par puede llevar un 4.o campo con la clave de una nota de fix_erratas_notas.py (BENGIO17_tempering): si esa nota
todavia no esta aplicada (falta su marca) y no aparece ni 'viejo' ni 'nuevo', el par se saltea con un aviso en vez de
cortar (el texto de la nota en fix_erratas_notas.py ya dice 'modas').
ORDEN si se re-traduce un cap tocado (2026-11-02, bitacora AJUSTES y BENGIO/17): fix_<libro>NN*.py ->
fix_erratas_notas.py -> fix_moda.py (p. ej. BENGIO 17: fix_bengio17_es.py -> fix_erratas_notas.py -> fix_moda.py).
Probado en un sandbox de Temp con la copia previa a fix_bengio17_es: la version anterior (backup
PIPELINE_LIBROS/_backup_pre_fix/fix_moda.pre_orden.py) cortaba si fix_moda.py iba antes que fix_erratas_notas.py; esta
da el mismo es.md en los dos ordenes. Despues: re-render y validate de los caps tocados."""
import json
import shutil
from pathlib import Path

ROOT = Path(r"D:\Universidad De Palermo - Maestria en IA\Machine Learning")

R = {
    ("BENGIO", "06", "c008"): [
        ("con un único modo de salida", "con una única moda de salida", 1),
        ("representar múltiples modos de salida", "representar múltiples modas de salida", 1),
    ],
    ("BISHOP", "03", "c018"): [
        ("concentrada alrededor del modo $\\theta_0$", "concentrada alrededor de la moda $\\theta_0$", 1),
    ],
    ("BENGIO", "17", "c004"): [
        ("se mueve hacia otro modo.", "se mueve hacia otra moda.", 1),
        ("a la que llamamos modo, la cadena tenderá a recorrer ese modo (",
         "a la que llamamos moda, la cadena tenderá a recorrer esa moda (", 1),
        ("saldrá de ese modo y, en general, volverá a él o", "saldrá de esa moda y, en general, volverá a ella o", 1),
        ("se moverá hacia otro modo.", "se moverá hacia otra moda.", 1),
        ("muestreando el mismo modo durante", "muestreando la misma moda durante", 1),
        ("pasar de un modo a un modo cercano", "pasar de una moda a una moda cercana", 1),
        ("entre estos modos. Las transiciones entre dos modos separados por",
         "entre estas modas. Las transiciones entre dos modas separadas por", 1),
        ("existen múltiples modos con alta probabilidad que están separados por",
         "existen múltiples modas con alta probabilidad que están separadas por", 1),
        ("inicializada en el modo en ambos casos", "inicializada en la moda en ambos casos", 1),
        ("con modos ampliamente separados que no están alineados",
         "con modas ampliamente separadas que no están alineadas", 1),
        ("cambiar de modo alterando", "cambiar de moda alterando", 1),
        ("transiciones entre dos modos, sino más generalmente entre todos los muchos modos que",
         "transiciones entre dos modas, sino más generalmente entre todas las muchas modas que", 1),
        ("mezclar entre modos, entonces", "mezclar entre modas, entonces", 1),
        ("la mayoría de los modos,", "la mayoría de las modas,", 1),
    ],
    ("BENGIO", "17", "c005"): [
        ("transición de un modo de la distribución a otro,", "transición de una moda de la distribución a otra,", 1),
        ("alrededor de muchos modos y estos modos están separados por",
         "alrededor de muchas modas y estas modas están separadas por", 1),
        ("deficiente entre modos.", "deficiente entre modas.", 1),
        ("Mezclar entre Modos", "Mezclar entre Modas", 1),
        ("los diferentes modos de la distribución", "las diferentes modas de la distribución", 1),
        ("mezclar entre modos de $p_1$", "mezclar entre modas de $p_1$", 1),
        ("hacia diferentes modos,", "hacia diferentes modas,", 1),
        # nota al pie p618-1 y su <!-- NOTA --> (mismo texto): solo existe despues de fix_erratas_notas.py
        ("mezclar entre modos con más facilidad", "mezclar entre modas con más facilidad", 2, "BENGIO17_tempering"),
        ("correspondientes a diferentes modos (", "correspondientes a diferentes modas (", 1),
        ("mezclar más rápido entre modos.", "mezclar más rápido entre modas.", 1),
    ],
}


def main():
    cambios, caps, avisos = [], {}, []
    for (lib, cap, c) in R:
        caps.setdefault((lib, cap), []).append(c)
    for (lib, cap), frs in caps.items():
        W = ROOT / f"{lib}_traduccion"
        D = W / "03_traduccion" / cap
        cs = sorted(D.glob("c*.json"), key=lambda f: int(f.stem[1:]))
        js = [json.loads(f.read_text(encoding="utf-8")) for f in cs]
        assert "\n\n".join(j["es"] for j in js) + "\n" == (D / "es.md").read_text(encoding="utf-8"), (lib, cap)
        BK = W / "_backup_pre_fix" / "moda_unif" / cap
        if not BK.exists():
            BK.mkdir(parents=True)
            for f in cs + [D / "es.md"]:
                shutil.copy2(f, BK)
        for f, j in zip(cs, js):
            if f.stem not in frs:
                continue
            t = j["es"]
            for par in R[(lib, cap, f.stem)]:
                viejo, nuevo, n = par[:3]
                nota = par[3] if len(par) > 3 else None
                nv, nn = t.count(viejo), t.count(nuevo)
                if nv == 0 and nn >= n:
                    continue
                if nota and f"<!-- NOTA (fix_erratas_notas: {nota})" not in t and nv == 0 and nn == 0:
                    # texto de una nota de errata que todavia no se aplico: no es error; la nota ya sale con 'moda'
                    # (el texto de fix_erratas_notas.py dice 'modas'), asi que no hace falta volver a correr.
                    avisos.append((lib, cap, f.stem, nota))
                    continue
                assert nv == n, (lib, cap, f.stem, viejo, nv, nn)
                t = t.replace(viejo, nuevo)
                cambios.append((lib, cap, f.stem, viejo[:40], n))
            if t != j["es"]:
                j["es"] = t
                f.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
        (D / "es.md").write_text("\n\n".join(j["es"] for j in js) + "\n", encoding="utf-8")
    print("cambios:", len(cambios), "reemplazos" if cambios else "(ninguno: ya aplicado)")
    for x in cambios:
        print("  ", x)
    for x in avisos:
        print("   aviso: nota de errata todavia no aplicada (se saltea; correr fix_erratas_notas.py):", x)


if __name__ == "__main__":
    main()

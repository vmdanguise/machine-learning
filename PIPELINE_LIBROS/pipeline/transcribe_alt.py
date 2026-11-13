"""Transcribe UNA pagina con un modelo alternativo cuando el modelo por defecto falla de forma persistente
(p. ej. falso positivo del filtro de contenido del proveedor). Un intento por modelo, timeout corto.
Uso: $env:BOOK="X"; python transcribe_alt.py <pagina> <modelo> [<modelo> ...]"""
import sys

import llm
import transcribe as T

pno = int(sys.argv[1])
for model in sys.argv[2:]:
    T.MODEL_TRANSCRIBE = model
    orig = llm.call

    def call_once(m, s, c, max_tokens=8000, temperature=0.0, tag="", retries=5, timeout=600):
        return orig(m, s, c, max_tokens=max_tokens, temperature=temperature, tag=tag + f":{m}", retries=1, timeout=240)

    T.call = call_once
    try:
        print(model, T.transcribe_page(pno, force=True), flush=True)
        break
    except Exception as e:  # noqa: BLE001
        print(model, "ERROR", str(e)[:300], flush=True)
    finally:
        T.call = orig

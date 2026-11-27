# Machine Learning — Maestría en IA (Universidad de Palermo)

Trabajos de la materia Machine Learning. Autor: Vicente Matias Danguise.

| Carpeta | Contenido |
|---|---|
| [`TP_Machine_Learning_Epilepsia/`](TP_Machine_Learning_Epilepsia/) | **Trabajo final.** Detección de crisis epilépticas en EEG (Bonn y CHB-MIT): Fourier, modelos convexos, CNN, comparativa de optimizadores, ROC/AUC y umbral de Neyman-Pearson. Incluye notebooks, scripts, resultados e informe en LaTeX. |
| [`PIPELINE_LIBROS/`](PIPELINE_LIBROS/) | Código del pipeline usado para traducir la bibliografía de la materia (layout, transcripción, traducción con LLM, render a PDF y validación). Documentado en [`TECNICA_Y_DECISIONES_TRADUCCION.md`](TECNICA_Y_DECISIONES_TRADUCCION.md) y [`PROGRESO_TRADUCCION.md`](PROGRESO_TRADUCCION.md). |

## Qué no está en el repo

- **Libros y traducciones:** los PDF originales y las carpetas `*_traduccion/` tienen copyright y quedan fuera.
- **Datos:** los EDF de CHB-MIT y los archivos de Bonn se bajan de las fuentes oficiales con los scripts de cada TP
  (ver sus README). Tampoco se incluyen los datos procesados.
- **Entornos y respaldos:** `.venv/`, `node_modules/`, `.rar`, `_backup*`.

El pipeline necesita las variables de entorno `ANTHROPIC_BASE_URL` y `ANTHROPIC_AUTH_TOKEN` (o `LITELLM_API_KEY`);
no hay credenciales en el código.

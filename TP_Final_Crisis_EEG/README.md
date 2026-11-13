# TP Final — Detección de crisis epilépticas en EEG

Maestría en IA (Universidad de Palermo), materia Machine Learning. Trabajo individual. Entrega: alrededor del 12/12/2026.

**Tema:** detección de crisis epilépticas en el EEG de superficie (base CHB-MIT), usando características espectrales obtenidas con Fourier. Incluye la comparación de **6 optimizadores × 5 funciones de activación**, la fundamentación matemática (Parseval, Welch, entropía en el simplex, Lagrange y KKT, convexidad, óptimo local y global, Nelder-Mead, Neyman-Pearson) y la evaluación con ROC, AUC, matriz de confusión, sensibilidad y especificidad.

## Estructura

```
TP_Final_Crisis_EEG/
├── notebooks/TP_Final_Crisis_EEG.ipynb   ← TRABAJO COMPLETO (Jupyter / Colab)
├── src/                                  ← lógica reutilizable (.py)
│   ├── config.py           rutas, canales, bandas, semilla
│   ├── descarga.py         descarga selectiva de CHB-MIT con SHA-256 (reanudable)
│   ├── anotaciones.py      lectura de chbXX-summary.txt
│   ├── edf.py              lector EDF en numpy (sin mne/pyedflib)
│   ├── caracteristicas.py  filtrado, ventanas, Welch, entropía, coherencia
│   ├── modelos.py          MLP, activaciones + init, optimizadores, entrenamiento
│   ├── convexo.py          regresión logística: óptimo global, Nelder-Mead
│   ├── evaluacion.py       métricas, Youden, Neyman-Pearson (λ = pendiente ROC)
│   ├── experimentos.py     partición por sujeto, grillas reanudables
│   └── graficos.py         estilo y guardado de figuras (PDF + PNG)
├── herramientas/
│   ├── construir_notebook.py   regenera el .ipynb
│   └── latex_a_word.py         genera los .docx a partir del LaTeX
├── documentos/
│   ├── latex/              ← fuente para Overleaf (main.tex, anteproyecto.tex, capitulos/, figuras/)
│   └── word/               ← versiones .docx generadas (Anteproyecto.docx, TP_Final_Crisis_EEG.docx)
├── data/                   (no se sube) EDF crudos y características
└── resultados/             corridas de los experimentos (.jsonl)
```

## Cómo correrlo

### Local
```powershell
pip install -r requirements.txt
python -m src.descarga --simular            # muestra qué baja (~14 GB) sin bajarlo
python -m src.descarga                      # descarga (se puede cortar y retomar)
python -m src.caracteristicas               # extrae características (reanudable)
jupyter notebook notebooks/TP_Final_Crisis_EEG.ipynb
```
Los experimentos largos también se pueden correr por consola (son reanudables):
```powershell
python -m src.experimentos lr
python -m src.experimentos logistica
python -m src.experimentos grilla
python -m src.experimentos profundidad
```

### Google Colab
1. Subir la carpeta `TP_Final_Crisis_EEG` a Google Drive **sin** `data/chbmit` (los EDF se bajan directo en Colab).
2. Abrir `notebooks/TP_Final_Crisis_EEG.ipynb` desde Drive con Colab.
3. Ajustar `RUTA_DRIVE` en la primera celda y ejecutar. Los EDF van al disco local de Colab y las características y los resultados se guardan en Drive, así no se pierden si se corta la sesión.

`MODO_RAPIDO = True` corre todo con menos épocas y semillas (resultados en `resultados/rapido/`). Para los resultados del documento hay que usar `False`.

## Documentos: Overleaf y Word

- **Overleaf:** subir el contenido de `documentos/latex/` (con `figuras/`). Compilar `main.tex` con **pdfLaTeX + Biber**. Mientras falten figuras, aparece un recuadro "Figura pendiente".
- **Word:** el LaTeX es la fuente. Después de editar, correr `python herramientas/latex_a_word.py` para regenerar los `.docx`, que tienen ecuaciones nativas de Word y bibliografía APA. Para cambiar el formato de Word (fuentes, márgenes), guardar un `documentos/word/plantilla.docx` con los estilos deseados.
- Las marcas **[Pendiente: …]** (en naranja en el PDF) indican lo que falta escribir.
- Las figuras las genera el notebook directamente en `documentos/latex/figuras/` (PDF para LaTeX y PNG para Word).

## Cronograma

| Semana | Código | Escritura |
|---|---|---|
| 1 (12–18/11) | Descarga, características, H5 | Caps. 2 y 3 |
| 2 (19–25/11) | Caso convexo, ajuste de tasas, evaluación | Caps. 4 y 7 |
| 3 (26/11–2/12) | Grilla, profundidad | Caps. 5 y 6 |
| 4 (3–9/12) | Estadística, figuras finales | Caps. 8, 9 y 10 |
| 10–12/12 | — | Revisión |

## Decisiones tomadas

- **Partición por sujeto.** `chb01` y `chb21` son la misma paciente y siempre van juntos.
- **Etiquetas.** Se toman de los `chbXX-summary.txt`. `RECORDS-WITH-SEIZURES` tiene un error: lista `chb07_18` cuando la crisis está en `chb07_19`.
- **Canales.** Se usan los 18 canales bipolares comunes a todos los registros. Los archivos que no los tienen se descartan.
- **Etiquetado de ventanas.** Ventanas de 4 s; una ventana es crisis si tiene al menos 50 % de solapamiento con una crisis anotada.
- **Umbral clínico.** El umbral de Neyman-Pearson se fija en 1 falsa alarma por hora, es decir, FPR ≤ 4/3600.

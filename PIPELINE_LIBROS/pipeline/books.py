"""Configuracion especifica de cada libro (se elige con la variable de entorno BOOK)."""

BOOKS = {
    # ------------------------------------------------------------------------------------------------
    "BISHOP": {
        "pdf": "BISHOP.pdf",
        "work": "BISHOP_traduccion",
        "units": [("01", "Capítulo 1", 20, 41, "llm"), ("02", "Capítulo 2", 42, 82, "llm"), ("03", "Capítulo 3", 83, 128, "llm"),
                  ("04", "Capítulo 4", 129, 148, "llm"), ("05", "Capítulo 5", 149, 187, "llm"), ("06", "Capítulo 6", 188, 224, "llm"),
                  ("07", "Capítulo 7", 225, 248, "llm"),
                  ("08", "Capítulo 8", 249, 268, "llm"),
                  ("09", "Capítulo 9", 269, 301, "llm"),
                  ("10", "Capítulo 10", 302, 339, "llm"),
                  ("11", "Capítulo 11", 340, 371, "llm"),
                  ("12", "Capítulo 12", 372, 421, "llm"),
                  ("13", "Capítulo 13", 422, 442, "llm"),
                  ("14", "Capítulo 14", 443, 472, "llm"),
                  ("15", "Capítulo 15", 473, 507, "llm"),
                  ("16", "Capítulo 16", 508, 544, "llm"),
                  ("17", "Capítulo 17", 545, 557, "llm"),
                  ("18", "Capítulo 18", 558, 572, "llm"),
                  ("19", "Capítulo 19", 573, 589, "llm"),
                  ("20", "Capítulo 20", 590, 616, "llm")],
        "title": '"Deep Learning: Foundations and Concepts" (Christopher M. Bishop and Hugh Bishop, Springer 2024)',
        "title_es": '"Deep Learning: Foundations and Concepts" (Christopher M. Bishop y Hugh Bishop)',
        "scanned": False,
        "ocr_text": False,
        "header_y": 50, "footer_y": 625,      # zonas de encabezado / pie (pt) que se ignoran en la deteccion
        "body_min": 10.0,                     # lineas de texto con tamanio >= body_min se consideran texto (no figura)
        "cap_re": r"^\s*(Figure|Table)\s+(\d+\.\d+)\b",
        "cap_font": "NimbusSanL-Bold",
        "side_captions": True,
        # bbox a mano (de get_drawings/get_image_info) para figuras cuyo recorte automatico incluia el epigrafe
        "fig_bbox": {562: {"18.2": [80, 63, 432, 196]}, 546: {"17.1": [145, 63, 450, 235]}, 510: {"16.2": [312, 62, 477, 227]}, 529: {"16.9": [301, 64, 477, 135]}, 536: {"16.12": [422, 531, 449, 601]},
                     481: {"15.4": [450, 64, 477, 133]}, 490: {"15.9": [369, 64, 459, 165]}, 492: {"15.10": [369, 64, 459, 165]}, 494: {"15.11": [301, 64, 476, 134]},
                     500: {"15.13": [279, 64, 477, 188], "15.14": [241, 482, 476, 610]}, 501: {"15.15": [273, 64, 475, 230]},
                     446: {"14.2": [293, 62, 479, 221]}, 450: {"14.6": [268, 62, 478, 193]}, 471: {"14.14": [302, 397, 465, 556]},
                     141: {"4.6": [44, 62, 476, 375]}, 145: {"4.7": [44, 90, 476, 517]},
                     # cap 12: el recorte por tinta perdia rotulos y flechas (N/D en 12.3, X de entrada en 12.6/12.8/12.9/12.19,
                     # Y de salida en 12.8, (a)/(b) en 12.11, "...." y x1-x3 en 12.13, encoder/decoder en 12.14, ejes en 12.16)
                     376: {"12.3": [320, 62, 422, 218]}, 381: {"12.6": [295, 64, 423, 290]}, 384: {"12.8": [155, 66, 457, 241]},
                     385: {"12.9": [329, 66, 423, 277]}, 391: {"12.11": [61, 73, 446, 271]}, 395: {"12.13": [236, 62, 478, 175]},
                     396: {"12.14": [53, 65, 469, 212]}, 400: {"12.16": [281, 63, 478, 258]}, 406: {"12.19": [308, 66, 422, 374]},
                     # cap 11: el recorte por tinta perdia partes (fila de mu en 11.4, lambda/sigma2 en 11.10-11.11, nodo c y
                     # (a)/(b) en 11.21, "....." en 11.28-11.30, flecha de salida en 11.31, nodo d en 11.32)
                     346: {"11.4": [319, 62, 478, 129]}, 350: {"11.10": [368, 63, 475, 157], "11.11": [368, 517, 475, 611]},
                     358: {"11.21": [226, 63, 478, 197]}, 366: {"11.28": [276, 63, 475, 92], "11.29": [276, 558, 475, 587]},
                     367: {"11.30": [277, 63, 475, 110], "11.31": [300, 525, 478, 598]}, 370: {"11.32": [388, 63, 478, 165]},
                     194: {"6.6": [87, 62, 409, 226]}, 195: {"6.8": [146, 65, 449, 266]},
                     # cap 09: 9.5 tomaba solo la fila superior (q=0.5, q=1) de la grilla 2x2
                     281: {"9.5": [195, 60, 455, 340]},
                     # 9.13 cortaba los extremos 'x'/'y' y 9.16 las flechas de salida (recorte por tinta incompleto)
                     291: {"9.13": [78, 63, 444, 105]}, 293: {"9.16": [66, 449, 455, 566]},
                     # cap 01: 1.11 cortaba los rotulos "run 1..4"
                     34: {"1.11": [324, 63, 478, 152]},
                     # cap 02: los recortes incluian el epigrafe al costado/debajo y texto del cuerpo
                     43: {"2.1": [45, 53, 463, 235]}, 44: {"2.2": [253, 57, 487, 170]},
                     45: {"2.3": [257, 56, 491, 243]}, 46: {"2.4": [322, 59, 477, 168]},
                     48: {"2.5": [40, 76, 468, 381]}, 51: {"2.6": [257, 63, 478, 224]},
                     53: {"2.7": [277, 62, 478, 211]}, 55: {"2.8": [257, 63, 478, 224]},
                     57: {"2.9": [276, 62, 479, 210]}, 59: {"2.10": [45, 62, 476, 158]},
                     60: {"2.11": [276, 62, 478, 263]}, 63: {"2.12": [269, 57, 481, 212]},
                     64: {"2.13": [20, 50, 505, 329]}, 68: {"2.14": [39, 79, 468, 263]},
                     71: {"2.15": [295, 63, 476, 224]}, 77: {"2.16": [273, 310, 478, 459]}},
        "eq_re": r"^\((\d+\.\d+)\)$", "eq_x0": 430,
        "indent": {"base": 122, "indent": 135},
        "page_label": "header",
        "book_rules": r"""BOOK-SPECIFIC
- Omit the running header (page number + "2. PROBABILITIES" / the current section title / "Exercises") and, on the
  chapter opening page, the Springer copyright footer ("© The Author(s) ... https://doi.org/...") and the decorative
  opening image (no caption; ignore it). The chapter opening has a big red chapter number N and the title (possibly split
  over several lines): output "# Chapter N: <title>" (title on one line).
- Sections: "## 2.1 <title>" (printed "2.1." -> drop the final dot), subsections "### 2.1.1 <title>".
- The end-of-chapter "Exercises" section: "## Exercises" (only on the page where the heading is printed). Each exercise is
  one paragraph starting with the bold number and the difficulty stars as math: "**2.1** $(\star)$ <text>",
  "**2.7** $(\star\star)$ <text>"; display equations of an exercise go in their own $$ block.
- Numbers with thousands separators are written without spaces: "1,665.69", and a negative number in a table cell is
  one math expression: $-15{,}566.61$ (use {,} inside math).
- Captions are printed "Figure 2.4" in bold sans followed by the text (often in a side column). Write the caption as one
  paragraph "**Figure 2.4** <text>". Tables: "**Table 2.1** <text>" + Markdown pipe table.
- Algorithm boxes ("Algorithm 7.1: <title>", pseudocode with Input/Output/Return): write them as
  :::algorithm
  **Algorithm 7.1:** <title>
  ---
  **Input:** ...
  **for** $n \in \{1, \ldots, N\}$ **do**
    $\mathbf{w} \leftarrow ...$
  **end for**
  **return** $\mathbf{w}$
  :::
  one pseudocode line per line, 2 spaces of indentation per level, keywords in bold, comments "// ..." kept as text.
- Margin notes (red italic cross-references in the left margin such as "Chapter 12", "Section 1.2", "Exercise 1.3"):
  insert them INLINE exactly at the start of the line where they appear, written {{MARGIN: Chapter 12}}.
- Monospaced boxed samples (e.g. generated text) are a fenced code block (```text ... ```) copied as printed.
- Notation: vectors bold upright lowercase ($\mathbf{x}$, $\mathbf{w}$), matrices bold upright uppercase ($\mathbf{W}$),
  scalars italic; $\ln$; $w^\star$ (printed with a star); $\widetilde{E}$; $\mathrm{RMS}$ as $E_{\mathrm{RMS}}$;
  $\exp$; $\sin(2\pi x)$; $p(x)$, $\mathbb{E}[x]$, $\operatorname{var}[x]$, $\operatorname{cov}[x,y]$,
  $\mathcal{N}(x|\mu,\sigma^2)$, $\mathrm{KL}(p\|q)$, bold Greek vectors/matrices with \boldsymbol ($\boldsymbol{\mu}$,
  $\boldsymbol{\Sigma}$), transpose printed as upright T: $\mathbf{x}^{\mathrm{T}}$. Equation numbers "(2.12)" -> \tag{2.12}.""",
        "glossary_extra": """error function → función de error | sum-of-squares error → error de suma de cuadrados | root-mean-square (RMS) error → error cuadrático medio (RMS)
polynomial curve fitting → ajuste de curvas polinómicas | over-fitting → sobreajuste | model complexity → complejidad del modelo | model selection → selección de modelo
large language model (LLM) → modelo de lenguaje grande (LLM) | foundation model → modelo fundacional | generative AI → IA generativa | prompt → prompt (instrucción)
self-supervised learning → aprendizaje autosupervisado | artificial general intelligence (AGI) → inteligencia artificial general (AGI) | perceptron → perceptrón
compute → cómputo | scaling → escalado | universal approximation → aproximación universal | inductive bias → sesgo inductivo | automatic differentiation → diferenciación automática
protein structure → estructura de proteínas | image synthesis → síntesis de imágenes | medical diagnosis → diagnóstico médico | lesion → lesión
sum rule / product rule → regla de la suma / regla del producto | joint / marginal / conditional probability → probabilidad conjunta / marginal / condicional | Bayes' theorem → teorema de Bayes
probability density → densidad de probabilidad | cumulative distribution function → función de distribución acumulada | Gaussian distribution → distribución gaussiana | precision → precisión
independent and identically distributed (i.i.d.) → independientes e idénticamente distribuidos (i.i.d.) | sample mean / sample variance → media muestral / varianza muestral | biased / unbiased → sesgado / insesgado
entropy → entropía | differential entropy → entropía diferencial | Kullback–Leibler (KL) divergence → divergencia de Kullback–Leibler (KL) | mutual information → información mutua | Jensen's inequality → desigualdad de Jensen
Lagrange multiplier → multiplicador de Lagrange | Jacobian factor → factor jacobiano | change of variables → cambio de variables | noiseless coding theorem → teorema de codificación sin ruido
Bernoulli / binomial / multinomial distribution → distribución de Bernoulli / binomial / multinomial | one-hot encoding → codificación one-hot | Mahalanobis distance → distancia de Mahalanobis
conjugate prior → prior conjugada (distribución a priori conjugada) | exponential family → familia exponencial | sufficient statistics → estadísticos suficientes | von Mises distribution → distribución de von Mises
mixture of Gaussians → mezcla de gaussianas | mode (of a distribution) → moda (no 'modo') | mixing coefficients → coeficientes de mezcla | histogram → histograma | kernel density estimator → estimador de densidad por kernel | Parzen estimator → estimador de Parzen | nearest neighbours → vecinos más cercanos
linear regression → regresión lineal | basis function → función base | design matrix → matriz de diseño | pseudo-inverse → pseudoinversa | sequential learning → aprendizaje secuencial | squared loss → pérdida cuadrática
decision theory → teoría de la decisión | bias–variance trade-off → compromiso sesgo-varianza | regularized least squares → mínimos cuadrados regularizados | multiple outputs → salidas múltiples
discriminant function → función discriminante | decision boundary / decision region → frontera de decisión / región de decisión | one-versus-the-rest / one-versus-one → uno contra el resto / uno contra uno
reject option → opción de rechazo | misclassification rate → tasa de clasificación errónea | loss matrix → matriz de pérdida | receiver operating characteristic (ROC) curve → curva ROC (característica operativa del receptor)
generative / discriminative classifier → clasificador generativo / discriminativo | logistic regression → regresión logística | cross-entropy → entropía cruzada | probit regression → regresión probit | canonical link function → función de enlace canónica
confusion matrix → matriz de confusión | true / false positive → verdadero / falso positivo | inverse problem → problema inverso | prior knowledge → conocimiento previo
residual connection → conexión residual | skip-layer connection → conexión de salto | representation → representación | heteroscedastic → heterocedástico | mixture density network → red de densidad de mezcla
error surface → superficie de error | universal approximator → aproximador universal | hierarchical representation → representación jerárquica | distributed representation → representación distribuida | multimodal → multimodal""",
        "margin_notes": True,
    },
    # ------------------------------------------------------------------------------------------------
    "FUNDAMENTALS": {
        "pdf": "FUNDAMENTALS_OF_DEEP_LEARNING.pdf",
        "work": "FUNDAMENTALS_traduccion",
        "units": [("01", "Capítulo 1", 16, 30, "llm"), ("02", "Capítulo 2", 32, 53, "llm"), ("03", "Capítulo 3", 54, 69, "llm"),
                  ("04", "Capítulo 4", 70, 91, "llm"), ("05", "Capítulo 5", 92, 109, "llm"), ("06", "Capítulo 6", 110, 131, "llm"),
                  ("07", "Capítulo 7", 132, 170, "llm"),
                  ("08", "Capítulo 8", 172, 203, "llm"),
                  ("09", "Capítulo 9", 204, 257, "llm"),
                  ("10", "Capítulo 10", 258, 289, "llm"),
                  ("11", "Capítulo 11", 290, 312, "llm"),
                  ("12", "Capítulo 12", 314, 338, "llm"),
                  ("13", "Capítulo 13", 340, 376, "llm")],
        "title": '"Fundamentals of Deep Learning", 2nd ed. (Nithin Buduma, Nikhil Buduma, Joe Papa; O\'Reilly 2022)',
        "title_es": '"Fundamentals of Deep Learning", 2.ª ed. (Nithin Buduma, Nikhil Buduma y Joe Papa)',
        "scanned": False,
        "ocr_text": False,
        # bbox a mano: el recorte automatico de la Fig. 8-5 incluia el bloque de codigo de arriba (ya transcrito);
        # el diagrama esta enmarcado en 72-432.5 x 253.8-553.6
        "fig_bbox": {177: {"8-5": [71, 252.5, 434, 555]}},
        "header_y": 45, "footer_y": 600,
        "body_min": 10.0,
        "cap_re": r"^\s*(Figure|Table|Equation)\s+(\d+-\d+)\.",
        "cap_font": "MinionPro-It",
        "side_captions": False,
        "eq_re": None, "eq_x0": 9999,
        "indent": None,
        "page_label": "footer",
        "book_rules": r"""BOOK-SPECIFIC
- Omit the footer ("8 | Chapter 1: Fundamentals of Linear Algebra for Deep Learning" or "Data Structures and
  Operations | 9") and the page number. Chapter opening ("CHAPTER N" + title): output "# Chapter N: <title>".
- Code listings (Python / PyTorch, monospaced) and console output: fenced code block ```python ... ``` (or ```text for
  output) copied EXACTLY as printed (keep indentation, comments and blank lines; do not fix the code). Inline code in
  prose (monospaced words like torch.nn or backward()): in `backticks`.
- Section titles are unnumbered: big ones "## <title>", smaller ones "### <title>".
- Paragraphs are NOT indented in this book (they are separated by vertical space): use the image and the sentence flow to
  decide whether the first text on the page continues the previous page's paragraph.
- Captions are printed in italics UNDER the figure: "Figure 2-10. The sum, ..." -> write "**Figure 2-10.** The sum, ...",
  marker [[FIG 2-10]] BEFORE the caption. Table captions are above the table: "**Table 2-1.** <text>" then the pipe table.
  Display equations with a caption "Equation 2-1. <title>": write the paragraph "**Equation 2-1.** <title>" followed by
  the $$ block (no \tag). Uncaptioned display equations: plain $$ block.
- Note / tip / warning boxes with a bird or other icon: blockquote starting "> **Note:** " ("> **Tip:** " /
  "> **Warning:** " if so labelled; all lines of the box prefixed by "> ").
- The PDF text layer of the math is corrupted (Symbola glyphs, "�" characters, missing symbols): rebuild ALL math from the
  image. Matrices printed as images (not grey boxes) must be transcribed as LaTeX with \begin{bmatrix}.
- Notation as printed: vectors and matrices in plain italic ($v$, $A$), transpose $A^T$, $\|v\|_2$, null space $N(A)$,
  column space $C(A)$, $\mathbb{R}^n$, $P(A|B)$, $\mathbb{E}[X]$, $\mathrm{Var}(X)$.""",
        "glossary_extra": """linear algebra → álgebra lineal | column space → espacio columna | null space → espacio nulo | vector space → espacio vectorial | subspace → subespacio
linear combination → combinación lineal | linear independence / linearly independent → independencia lineal / linealmente independiente | basis → base | rank → rango
dot product → producto punto (producto escalar) | outer product → producto exterior | matrix-vector multiplication → multiplicación matriz-vector | identity matrix → matriz identidad
matrix inversion / inverse → inversión de matrices / inversa | invertible → invertible | square matrix → matriz cuadrada | diagonal matrix → matriz diagonal | entry → entrada | spreadsheet → hoja de cálculo
eigenvalue / eigenvector → autovalor / autovector | characteristic polynomial → polinomio característico | orthogonal → ortogonal | perpendicular → perpendicular | span → espacio generado (span)
event → evento | sample space → espacio muestral | outcome → resultado | conditional probability → probabilidad condicional | joint probability → probabilidad conjunta | Bayes' theorem → teorema de Bayes
random variable → variable aleatoria | expectation → esperanza | variance → varianza | linearity of expectation → linealidad de la esperanza | entropy → entropía | cross entropy → entropía cruzada | KL divergence → divergencia KL
continuous / discrete probability distribution → distribución de probabilidad continua / discreta | probability density function (PDF) → función de densidad de probabilidad (PDF) | cumulative distribution function (CDF) → función de distribución acumulada (CDF)
neuron → neurona | perceptron → perceptrón | linear perceptron → perceptrón lineal | feed-forward neural network → red neuronal prealimentada (feed-forward) | sigmoid / tanh / ReLU neuron → neurona sigmoide / tanh / ReLU | softmax output layer → capa de salida softmax
dendrite / axon / cell body → dendrita / axón / cuerpo celular | logit → logit | fast-food problem → problema de la comida rápida | delta rule → regla delta | error surface → superficie de error | local minima → mínimos locales
backpropagation → retropropagación | stochastic and minibatch gradient descent → descenso por gradiente estocástico y por minilotes | test set → conjunto de prueba | validation set → conjunto de validación | empirical risk minimization → minimización del riesgo empírico
tensor → tensor | autograd → autograd | in-place operation → operación in situ (in-place) | device → dispositivo | dataset / dataloader → Dataset / DataLoader (clases de PyTorch, sin traducir) | training loop → bucle de entrenamiento | broadcasting → broadcasting (difusión)
ill-conditioning → mal condicionamiento | spurious local minima → mínimos locales espurios | flat regions → regiones planas | saddle point → punto de silla | momentum-based optimization → optimización basada en momento | learning rate adaptation → adaptación de la tasa de aprendizaje
second-order methods → métodos de segundo orden | conjugate gradient descent → descenso por gradiente conjugado | AdaGrad / RMSProp / Adam → AdaGrad / RMSProp / Adam | model identifiability → identificabilidad del modelo | Hessian → hessiana""",
        "margin_notes": False,
    },
    # ------------------------------------------------------------------------------------------------
    "GONZALEZ": {
        "pdf": "Gonzalez Woods.pdf",
        "work": "GONZALEZ_traduccion",
        "units": [("01", "Capítulo 1", 18, 47, "llm"), ("02", "Capítulo 2", 48, 119, "llm"), ("03", "Capítulo 3", 120, 202, "llm"),
                  ("04", "Capítulo 4", 204, 316, "llm"), ("05", "Capítulo 5", 318, 398, "llm"), ("06", "Capítulo 6", 400, 462, "llm"),
                  ("07", "Capítulo 7", 464, 539, "llm"),
                  ("08", "Capítulo 8", 540, 635, "llm"),
                  ("09", "Capítulo 9", 636, 698, "llm"),
                  ("10", "Capítulo 10", 700, 811, "llm"),
                  ("11", "Capítulo 11", 812, 903, "llm"),
                  ("12", "Capítulo 12", 904, 994, "llm")],
        "title": '"Digital Image Processing", 4th ed. (Rafael C. Gonzalez and Richard E. Woods, Pearson 2018)',
        "title_es": '"Digital Image Processing", 4.ª ed. (Rafael C. Gonzalez y Richard E. Woods)',
        "scanned": False,
        "ocr_text": False,
        "header_y": 45, "footer_y": 608,
        "body_min": 8.8,
        "cap_re": r"^\s*(FIGURE|TABLE)\s+(\d+\.\d+)\b",
        "cap_font": "Futura-CondensedBold",
        "side_captions": True,
        # bbox a mano: el recorte automatico de la Fig. 5.31 llegaba hasta el pie de pagina (texto del cuerpo)
        # 5.1: el recorte automatico cortaba los rotulos DEGRADATION/RESTORATION bajo el diagrama
        # 8.1 (p542): el recorte automatico solo tomaba las imagenes raster (b) y (c); el panel (a) es vectorial
        "fig_bbox": {319: {"5.1": [118, 500, 470, 600]}, 368: {"5.31": [145, 49, 485, 219]},
                     542: {"8.1": [49, 49, 497, 216]},
                     # 9.23 (p662): el recorte automatico omitia la fila superior de SEs B1..B8 con el rotulo "Origin"
                     662: {"9.23": [173, 47, 458, 358]},
                     # cap 10: 10.33/10.34 (p745/746) el automatico tomaba solo la franja de ejes de los histogramas;
                     # 10.53/10.54 (p781/782) solo las imagenes de arriba, sin los grafos (caption lateral)
                     745: {"10.33": [36, 309, 470, 562]}, 746: {"10.34": [62, 318, 485, 547]},
                     781: {"10.53": [164, 47, 437, 257]}, 782: {"10.54": [164, 47, 459, 379]},
                     # cap 11: 11.56 (p885) el automatico tomaba solo el rotulo "More octaves" (caption lateral)
                     885: {"11.56": [150, 66, 446, 298]},
                     # cap 12: 12.5 tomaba tambien la 12.6 y la 12.6 solo su vector; el resto perdia rotulos/salidas/paneles
                     # (12.17 tomaba solo (a); 12.20 sin x3; 12.22 sin y/x2; 12.23/12.28/12.29 sin la salida; 12.34 sin (a))
                     910: {"12.5": [185, 47, 442, 216], "12.6": [150, 222, 492, 376]}, 922: {"12.17": [128, 47, 500, 336]},
                     929: {"12.20": [190, 46, 406, 231]}, 935: {"12.22": [115, 430, 484, 603]}, 938: {"12.23": [200, 46, 430, 167]},
                     944: {"12.28": [187, 48, 445, 150]}, 945: {"12.29": [162, 50, 430, 181]}, 961: {"12.34": [36, 47, 478, 186]}},
        # figuras sin rotulo FIGURE (columna grafica de tablas, diagramas de problemas): recorte manual
        "extra_figs": {
            103: [("T2.3", [405, 265, 486, 612], "the 'Example' column of Table 2.3 (pictures of a transformed letter T)")],
            116: [("P2.14", [88, 288, 248, 372], "the two image subsets S1 and S2 (dashed boxes) of Problem 2.14, after item (c)")],
            200: [("P3.26", [92, 127, 242, 201], "the three images of Problem 3.26 (left column), right after item (a)"), ("P3.34", [320, 314, 472, 497], "the three blurred images (a),(b),(c) of Problem 3.34 (right column), before the sentence 'However, the bars have merged...'")],
            311: [("P4.21", [66, 417, 245, 509], "stripe image and its Fourier spectrum of Problem 4.21 (left column), before the sentence 'being two pixels wide...'")],
            394: [("P5.1", [110, 476, 236, 600], "test pattern (white bars on black) of Problem 5.1, after its Note paragraph")],
            396: [("P5.23", [114, 164, 227, 277], "black image with two thin white lines of Problem 5.23"), ("P5.29", [322, 459, 475, 602], "blurred heart image of Problem 5.29 with its courtesy line")],
            398: [("P5.41", [133, 243, 210, 321], "black image with single white pixel of Problem 5.41"), ("P5.42", [133, 370, 210, 448], "white disk with black disk of Problem 5.42")],
            460: [("P6.5", [68, 98, 272, 245], "three intensity-profile plots (Red, Green, Blue) of Problem 6.5, left column"), ("P6.6", [82, 321, 262, 453], "vertical color bars image with gray border of Problem 6.6, left column")],
            461: [("P6.13", [66, 53, 230, 217], "solid color squares image of Problem 6.13 (top of left column, belongs to Problem 6.13 from the previous page)"), ("P6.14", [56, 408, 231, 582], "Hue/Saturation/Intensity images of Problem 6.14, after item (c)")],
            462: [("P6.25", [106, 166, 238, 298], "500x500 image with Green/Red/Blue/Green squares of Problem 6.25")],
            526: [("T7.1", [168, 86, 387, 602], "the 'Scaling Function' and 'Wavelet Function' plot columns of Table 7.1")],
            198: [("P3.12", [320, 258, 462, 357], "the two plots p_r(r) and p_z(z) of Problem 3.12, right after its text")],
            117: [("P2.32", [286, 316, 490, 413], "Venn diagrams (a)*-(d) of Problem 2.32, right after its text")],
            694: [("P9.10", [70, 45, 262, 328], "cross-shaped set A and structuring elements B1-B4 of Problem 9.10, top of the left column")],
            695: [("P9.18", [76, 120, 236, 189], "grid image A and 3x3 SE B of Problem 9.18, after item (b)"),
                  ("P9.23", [316, 120, 451, 261], "black image with white rectangle and random dots (SE B lower right) of Problem 9.23, top of the right column"),
                  ("P9.26", [294, 472, 472, 596], "'UTK' image and T-shaped structuring element of Problem 9.26, after its text")],
            # cap 10: la Fig. 10.46 (p768) no la detecta layout (rotulo con caption debajo de una grilla 3x3); se recorta a mano
            768: [("10.46", [62, 47, 486, 410], "3x3 grid of weld X-ray images and histograms (a)-(i) of Figure 10.46")],
            # cap 11: p902 (problemas a dos columnas) imagenes sin rotulo de 11.38 y 11.39 (bbox de las imagenes raster)
            902: [("P11.38", [352, 284, 466, 364], "row of five bottles (imperfectly filled) of Problem 11.38, right column"),
                  ("P11.39", [352, 455, 466, 564], "gray image with air bubbles of Problem 11.39, right column")],
            806: [("P10.9", [83, 211, 258, 337], "two edge-model images with their horizontal profiles of Problem 10.9, left column"),
                  ("P10.14", [348, 389, 468, 509], "black image with a white m x n rectangle of Problem 10.14, right column")],
            810: [("P10.39", [108, 101, 234, 227], "gray image with white elongated objects of Problem 10.39, top of the left column"),
                  ("P10.42", [127, 519, 214, 606], "N x N image with a gray shape of Problem 10.42 (split and merge)"),
                  ("P10.49", [305, 553, 491, 599], "1-D intensity cross section (bar profile, x = 1..15) of Problem 10.49")],
            # cap 12: p993/p994 (problemas) diagrama de red del Problema 12.23 e imagen de elipses del 12.33, sin rotulo
            993: [("P12.23", [88, 273, 230, 370], "neural network diagram (3 inputs, 2 hidden, 2 outputs) of Problem 12.23, left column")],
            994: [("P12.33", [135, 385, 227, 474], "binary image of elliptical blobs of Problem 12.33, left column")],
        },
        "eq_re": r"^\((\d+-\d+)\)$", "eq_x0": 440,
        "indent": {"auto": True},
        "page_label": "header",
        "book_rules": r"""BOOK-SPECIFIC
- Omit the running header ("18  Chapter 1  Introduction" / "1.3  Examples of Fields that Use Digital Image Processing  25"),
  the page number, and the watermark "www.EBooksWorld.ir" at the bottom.
- Chapter opening page (big chapter number N, title, epigraph, "Preview", learning objectives, small decorative pictures):
  output "# Chapter N: <Title>"; the epigraph as a blockquote "> *<quote>*" and a line "> — <Author>";
  "Preview" and "Upon completion of this chapter, readers should:" as "#### <title>"; the objectives as a "- " list (one
  item per checkbox, reading the left column first then the right). Ignore the decorative pictures.
- Sections are printed in capitals "2.1 ELEMENTS OF VISUAL PERCEPTION": write them in Title Case:
  "## 2.1 Elements of Visual Perception". Subsection titles (bold, small caps or colour) "### <title>"; lower-level
  headings "#### <title>".
- Worked examples "EXAMPLE 3.2: <title>": a paragraph starting "**EXAMPLE 3.2:** **<title>**" followed by the example
  text as normal paragraphs; omit the small end-of-example square.
- End of chapter: "## Summary, References, and Further Reading" and "## Problems" (introductory note as a paragraph).
  Each problem is one paragraph starting with the bold number "**2.1** " (keep the "*" printed before problems with
  solutions: "**2.1** \* <text>"; sub-items (a), (b) as "- (a) ..." list items). Problems are printed in two columns:
  read the left column first, then the right one.
- Captions "FIGURE 2.6" (in a narrow left column or full-width under the figure): one paragraph "**Figure 2.6** <text>",
  marker [[FIG 2.6]] before it. OMIT the small sub-figure layout key printed above the caption ("a b / c d", "a / b").
  Table: "**Table 2.1** <text>" + pipe table. Small matrices / masks printed as number grids outside figures: LaTeX
  \begin{bmatrix} (or a pipe table if they are a table).
- Side notes in the narrow left column that are NOT captions (short explanatory notes in smaller type): blockquote
  "> **Note:** <text>" placed at the paragraph where they appear.
- The text layer has broken ligatures (fi, fl appear as garbage): take those words from the image.
- Notation: $f(x, y)$ italic; units and numbers like "250 ×" as printed; $F(u, v)$; $e^{-j2\pi(ux/M+vy/N)}$;
  convolution (filled star) $\bigstar$ and correlation (open star) $\star$. Equation numbers printed "(2-12)" ->
  \tag{2-12}.""",
        "glossary_extra": """digital image processing → procesamiento digital de imágenes | image → imagen | pixel → píxel | picture element → elemento de imagen | intensity → intensidad | gray level → nivel de gris
spatial domain → dominio espacial | spatial filtering → filtrado espacial | frequency domain → dominio de la frecuencia | histogram → histograma | histogram equalization → ecualización del histograma
image enhancement → realce de imágenes | image restoration → restauración de imágenes | image compression → compresión de imágenes | segmentation → segmentación | morphological processing → procesamiento morfológico
color image processing → procesamiento de imágenes en color | wavelets → wavelets (ondículas) | feature extraction → extracción de características | image pattern classification → clasificación de patrones en imágenes
computer vision → visión por computadora | image analysis → análisis de imágenes | electromagnetic (EM) spectrum → espectro electromagnético (EM) | gamma-ray imaging → imágenes por rayos gamma
X-ray → rayos X | ultraviolet / infrared → ultravioleta / infrarrojo | visible band → banda visible | microwave / radar → microondas / radar | radio band → banda de radio | magnetic resonance imaging (MRI) → resonancia magnética (MRI)
computerized axial tomography (CAT) → tomografía axial computarizada (CAT) | positron emission tomography (PET) → tomografía por emisión de positrones (PET) | angiogram / angiography → angiograma / angiografía
fluorescence microscopy → microscopía de fluorescencia | remote sensing → teledetección | multispectral → multiespectral | scanning electron microscope (SEM) → microscopio electrónico de barrido (SEM)
sensor → sensor | image acquisition → adquisición de imágenes | image sensing → captura (sensado) de imágenes | image display → visualización de imágenes | hardcopy → copia impresa | knowledge base → base de conocimiento
low-/mid-/high-level process → proceso de bajo / medio / alto nivel | Bartlane cable picture transmission system → sistema Bartlane de transmisión de imágenes por cable
visual perception → percepción visual | retina / cornea / lens / fovea → retina / córnea / cristalino / fóvea | cones / rods → conos / bastones | brightness adaptation → adaptación al brillo | Mach bands → bandas de Mach | simultaneous contrast → contraste simultáneo | optical illusion → ilusión óptica
luminance / radiance → luminancia / radiancia | sampling and quantization → muestreo y cuantización | spatial / intensity resolution → resolución espacial / de intensidad | dpi → dpi | false contouring → falso contorneado | image interpolation → interpolación de imágenes
nearest neighbor / bilinear / bicubic interpolation → interpolación por vecino más cercano / bilineal / bicúbica | neighbors of a pixel → vecinos de un píxel | adjacency → adyacencia | connectivity → conectividad | region / boundary → región / frontera (borde) | distance measures → medidas de distancia
elementwise / matrix operations → operaciones elemento a elemento / matriciales | linear / nonlinear operations → operaciones lineales / no lineales | arithmetic / set / logical operations → operaciones aritméticas / de conjuntos / lógicas | spatial operations → operaciones espaciales | affine transformation → transformación afín | image registration → registro de imágenes | tie points → puntos de control
image transform → transformada de imagen | forward / inverse transform kernel → núcleo de la transformada directa / inversa | probabilistic methods → métodos probabilísticos | random noise → ruido aleatorio
intensity transformation → transformación de intensidad | image negative → negativo de imagen | log / power-law (gamma) transformation → transformación logarítmica / de potencia (gamma) | contrast stretching → estiramiento de contraste | intensity-level slicing → segmentación por niveles de intensidad | bit-plane slicing → descomposición en planos de bits
histogram matching (specification) → coincidencia (especificación) de histogramas | local histogram processing → procesamiento local del histograma | spatial correlation / convolution → correlación / convolución espacial | smoothing (lowpass) filter → filtro de suavizado (pasabajos) | sharpening (highpass) filter → filtro de realce (pasaaltos)
box filter → filtro de caja | Gaussian kernel → kernel gaussiano | order-statistic (median) filter → filtro de estadísticos de orden (mediana) | Laplacian → laplaciano | unsharp masking / highboost filtering → máscara de desenfoque (unsharp masking) / filtrado highboost | gradient → gradiente
Fourier transform / series → transformada / serie de Fourier | discrete Fourier transform (DFT) → transformada discreta de Fourier (DFT) | fast Fourier transform (FFT) → transformada rápida de Fourier (FFT) | impulse / sifting property → impulso / propiedad de selección (sifting) | sampling theorem → teorema de muestreo | aliasing → aliasing | Nyquist rate → tasa de Nyquist
spectrum / phase angle / power spectrum → espectro / ángulo de fase / espectro de potencia | ideal / Butterworth / Gaussian lowpass filter → filtro pasabajos ideal / Butterworth / gaussiano | ringing → efecto de anillado (ringing) | homomorphic filtering → filtrado homomórfico | notch filter → filtro notch (de rechazo) | bandreject / bandpass → rechazabanda / pasabanda | zero padding → relleno con ceros
degradation function → función de degradación | noise model → modelo de ruido | probability density function (PDF) → función de densidad de probabilidad (PDF) | Gaussian / Rayleigh / Erlang (gamma) / exponential / uniform / salt-and-pepper noise → ruido gaussiano / de Rayleigh / de Erlang (gamma) / exponencial / uniforme / de sal y pimienta | periodic noise → ruido periódico
mean / adaptive / order-statistic filters → filtros de media / adaptativos / de estadísticos de orden | inverse filtering → filtrado inverso | Wiener filtering → filtrado de Wiener | constrained least squares filtering → filtrado por mínimos cuadrados restringidos | motion blur → desenfoque por movimiento | image reconstruction from projections → reconstrucción de imágenes a partir de proyecciones | Radon transform → transformada de Radon | backprojection → retroproyección | sinogram → sinograma
color fundamentals → fundamentos del color | primary / secondary colors → colores primarios / secundarios | hue / saturation / intensity → tono / saturación / intensidad | chromaticity diagram → diagrama de cromaticidad | tristimulus values → valores triestímulo | RGB / CMY(K) / HSI color model → modelo de color RGB / CMY(K) / HSI | full-color → a todo color
pseudocolor → pseudocolor | intensity slicing → segmentación por intensidad | color complements → complementos de color | color slicing → segmentación de color | tone and color corrections → correcciones de tono y color | color image smoothing / sharpening → suavizado / realce de imágenes en color | color edge detection → detección de bordes en color""",
        "margin_notes": False,
    },
    # ------------------------------------------------------------------------------------------------
    "DUDAHART": {
        "pdf": "DUDAHART.pdf",
        "work": "DUDAHART_traduccion",
        "units": [("01", "Capítulo 1", 14, 33, "llm"), ("02", "Capítulo 2", 38, 100, "llm"), ("03", "Capítulo 3", 106, 178, "llm"),
                  ("04", "Capítulo 4", 186, 254, "llm"), ("05", "Capítulo 5", 260, 327, "llm"), ("06", "Capítulo 6", 332, 403, "llm"),
                  ("07", "Capítulo 7", 410, 454, "llm"),
                  ("08", "Capítulo 8", 460, 523, "llm"),
                  ("09", "Capítulo 9", 530, 597, "llm"),
                  # cap 10 (ultimo): 604-688; fuera el indice del cap (689-692), la pag. vacia 693 y el Apendice A (694+)
                  ("10", "Capítulo 10", 604, 688, "llm")],
        "title": '"Pattern Classification", 2nd ed. (Richard O. Duda, Peter E. Hart, David G. Stork; Wiley 2001)',
        "title_es": '"Pattern Classification", 2.ª ed. (Richard O. Duda, Peter E. Hart y David G. Stork)',
        "scanned": True,
        "ocr_text": True,
        "page_offset": -11,                   # pagina impresa = indice + offset (verificado: idx16 -> p.5)
        # la numeracion impresa se reinicia en cada capitulo (cada capitulo empieza en p.3): offset por unidad
        "page_offsets": {"01": -11, "02": -35, "03": -103, "04": -183, "05": -257, "06": -329, "07": -407, "08": -457, "09": -527, "10": -601},
        # bbox a mano: el recorte automatico de la Fig. 3.5 incluia el recuadro "Algorithm 1" (ya transcrito)
        # 4.1 incluia las Ecs. (2)-(3) del cuerpo; 4.16 incluia la ultima linea del parrafo anterior
        "fig_bbox": {136: {"3.5": [94.88, 250, 385.51, 441.47]},
                     187: {"4.1": [160, 318, 455, 490]}, 211: {"4.16": [260, 232.5, 412, 335]},
                     # cap 8: el recorte automatico tomaba solo la mitad inferior de estos arboles (escaneo, trazo fino)
                     464: {"8.2": [104, 97, 452, 317]}, 490: {"8.12": [124, 304, 443, 528]},
                     495: {"8.15": [280, 258, 380, 390]},
                     # cap 9: 9.5 omitia el panel "truth" de arriba; 9.12 omitia el rotulo "evidence" del eje;
                     # 9.13 cortaba la cola izquierda de p(theta|h_i), la flecha Delta^0 theta y la theta del eje
                     548: {"9.5": [140, 89, 374, 534]}, 564: {"9.12": [196, 89, 348, 212]},
                     565: {"9.13": [238, 88.5, 464, 232]},
                     # cap 10: 10.15 incluia la linea "3" del sumatorio del epigrafe (y~418-428); 10.32 incluia el
                     # encabezado de pagina "10.14. LOW-DIMENSIONAL REPRESENTATIONS..." (y~80-89)
                     648: {"10.15": [208, 266, 358, 416]}, 666: {"10.32": [92, 112, 462, 220]}},
        # EX3.3 (p143): el encabezado de pagina "CHAPTER 3. MAXIMUM LIKELIHOOD..." atraviesa el diagrama por la
        # mitad (y~79.5-89), asi que no se puede excluir solo con el bbox: se blanquea esa franja y se redibujan
        # las dos flechas X->C y X->D que la cruzan (layout.crop_figures "fig_mask").
        # 7.7 (p421): el encabezado "STOCHASTIC METHODS" se mete a la derecha de la fila de salida; se blanquea lo que
        # cruza el rotulo alpha^o: se blanquea la franja a la derecha de la llave y se redibuja alpha^o.
        "fig_mask": {421: {"7.7": {"white": [[432, 70, 520, 78.5], [423.6, 78.5, 520, 90]],
                                   "lines": [[429.3, 78.0, 431.0, 80.5, 1.0], [431.0, 80.5, 433.2, 82.4, 1.0],
                                             [433.2, 82.4, 431.0, 84.5, 1.0], [431.0, 84.5, 429.6, 87.0, 1.0],
                                             [429.6, 87.0, 429.2, 90.5, 1.0]],
                                   "texts": [[435.5, 75.5, "α", 12, r"C:\Windows\Fonts\timesi.ttf"],
                                             [442.5, 72.0, "o", 8, r"C:\Windows\Fonts\timesi.ttf"]]}},
                     143: {"EX3.3": {"white": [[260, 79.5, 440, 89.2], [427.5, 89.2, 440, 112]],
                                     "lines": [[334.9, 79.0, 330.3, 89.8, 1.8], [353.1, 79.0, 357.4, 89.8, 1.8]],
                                     "polys": [[[330.5, 91.0], [334.3, 86.3], [329.6, 84.6]],
                                               [[358.2, 91.0], [359.3, 84.6], [354.4, 86.3]]]}}},
        "dpi_scan": 150,
        # figuras sin rotulo "Figure" (graficos dentro de los recuadros Example): recorte manual
        "extra_figs": {
            64: [("EX2.1", [166, 500, 336, 629], "plot inside Example 1, before the sentence 'The computed Bayes decision boundary...'")],
            73: [("EX2.3", [176, 503, 479, 629], "two 3-D plots inside Example 3, before the sentence 'The decision boundary for the Example...'")],
            121: [("EX3.1a", [258, 95, 424, 196], "posterior plot p(theta|D^n) of Example 1, at the top of the page, right before the sentence 'The posterior p(theta|D^n) for the model...'"), ("EX3.1b", [258, 320, 418, 430], "ML vs Bayes plot p(x|D), right before the sentence 'Given the full set of four points...'")],
            287: [("EX5.1", [245, 98, 378, 249], "scatter plot with decision boundary at the top of the page (pseudoinverse example), right before 'Four training points and the decision boundary...'")],
            309: [("EX5.2", [210, 97, 472, 218], "two XOR plots at the top of the page, right before 'The XOR problem in the original...'")],
            374: [("EX6.9", [166, 398, 372, 584], "contour plot of conjugate gradient descent, right before 'Conjugate gradient descent in a quadratic error landscape...'")],
            138: [("EX3.8", [190, 154, 342, 357], "EM iterations plot of Example 2 (ellipses 0-3 and red points), right before the sentence 'The four data points, one of which is missing...'")],
            143: [("EX3.3", [266, 0, 430, 112], "belief net diagram of Example 3 (fish), at the top of the page, right before the sentence 'A simple belief net for the fish example...'")],
            151: [("EX3.4", [204, 168, 452, 432], "HMM graph + trellis of Example 4, right before the paragraph 'The HMM (above) consists of four hidden states...'")],
            154: [("EX3.5", [140, 112, 382, 290], "HMM trellis with the red path (Example 5), right before the sentence 'The locally optimal path through the HMM trellis of Example 4.'")],
            # Fig. 7.7: el OCR no detecta el rotulo porque el encabezado de pagina atraviesa el diagrama; recorte manual
            421: [("7.7", [190, 30, 505, 280], "network diagram of Figure 7.7 (visible/hidden units)")],
            492: [("EX8.3", [72, 338, 560, 454], "two derivation trees of Example 3 (pronunciation of 639,014 and 2,953), between the rewrite rules and 'These two derivation trees show...'")],
            584: [("EX9.38", [160, 308, 384, 394], "three circle diagrams (P=1/3, P=1/4, P=1/2) of Problem 38 (Bertrand's chord paradox), before 'Explain why there is little or no reason...'")],
            # cap 10: dos graficas de p(theta|x1..xn) sin rotulo (Ejemplo 1, prior uniforme ancha/angosta)
            623: [("EX10.1", [216, 244, 427, 530], "two plots of p(theta|x_1,...,x_n) vs theta for n = 0..25 (wide and narrow uniform prior) of Example 1, right before 'In unsupervised Bayesian learning of the parameter theta...'")],
            471: [("EX8.1", [135, 298, 545, 640], "decision regions and trees of Example 1 (simple tree classifier), after the data table and before 'Training data and associated (unpruned) tree...'")],
        },
        "cap_re": r"^\s*Figure\s+(\d+\.\d+)\s*[:.]",
        "eq_re": r"^\((\d+)\)$",
        "page_label": "offset",
        "book_rules": r"""BOOK-SPECIFIC
- This is a SCANNED book: the "text layer" given to you is OCR output (may contain recognition errors, wrong symbols and
  broken math). The image is the source of truth; use the OCR only as a help for words.
- Omit the running header (italic "2.2. BAYESIAN DECISION THEORY - CONTINUOUS FEATURES   7" / "6   CHAPTER 2. ...") and
  page numbers. Chapter opening ("Chapter N" / title): output "# Chapter N: <Title>".
- Algorithm boxes ("Algorithm 1 (Basic gradient descent)" with numbered lines "1 begin initialize ...", "2 do ...",
  "end"): write them as
  :::algorithm
  **Algorithm 1** (Basic gradient descent)
  ---
  1 **begin initialize** $\mathbf{a}, \theta, \eta(\cdot), k \leftarrow 0$
  2   **do** $k \leftarrow k + 1$
  6 **end**
  :::
  keeping the printed line numbers, 2 extra spaces of indentation per nesting level, keywords in bold.
- End-of-chapter sections: "## Summary", "## Bibliographical and Historical Remarks", "## Problems",
  "## Computer exercises", "## Bibliography". In Problems / Computer exercises the small centred headings "Section 2.1"
  are "#### Section 2.1"; each problem is a numbered list item "1. <text>" with sub-items as nested "   - (a) ...".
  The small symbol printed before harder problems (⊕) is kept as "$\oplus$".
- Sections "## 1.1 <title>", subsections "### 1.3.1 <title>", deeper "#### <title>".
- Captions under the figures: "Figure 1.1: The objects ..." -> marker [[FIG 1.1]] then the paragraph "**Figure 1.1:** The objects ...".
- Margin notes (small capitals in the right margin, e.g. "DECISION THEORY", "FEATURE"): insert them INLINE at the start
  of the line where they appear as {{MARGIN: decision theory}} (lower case).
- Footnotes: as in the general rules ([^pPAGE-N]), the symbol/number printed may be * or a digit: use N = 1, 2 ... in order.
- Bibliography pages ("Bibliography"): "## Bibliography" and one paragraph per reference, numbered as printed "[1] ...".
  Keep authors, titles and venues exactly as printed (italics with *...*).
- Notation as printed: vectors bold ($\mathbf{x}$), states of nature $\omega_1$, $P(\omega_j)$, $p(\mathbf{x}|\omega_j)$,
  threshold $x^*$, $\boldsymbol{\mu}$, $\boldsymbol{\Sigma}$, expectation printed as script E $\mathcal{E}[\cdot]$,
  $\hat{\boldsymbol{\theta}}$, transpose printed as superscript t ($\mathbf{a}^t$). Equation numbers "(12)" -> \tag{12}.""",
        "glossary_extra": """pattern recognition → reconocimiento de patrones | pattern classification → clasificación de patrones | classifier → clasificador | category / class → categoría / clase
feature extraction → extracción de características | feature vector → vector de características | feature space → espacio de características | decision boundary → frontera de decisión
decision theory → teoría de la decisión | decision rule → regla de decisión | threshold → umbral | cost → costo | risk → riesgo | state of nature → estado de la naturaleza
preprocessing → preprocesamiento | segmentation → segmentación | sensing → sensado (captación) | transducer → transductor | invariance → invarianza | occlusion → oclusión
training samples → muestras de entrenamiento | novel pattern → patrón nuevo | template matching → comparación con plantillas (template matching) | syntactic pattern recognition → reconocimiento sintáctico de patrones
context → contexto | missing features → características faltantes | mereology → mereología | evidence pooling → combinación de evidencia | model selection → selección de modelo
computational complexity → complejidad computacional | learning and adaptation → aprendizaje y adaptación | sea bass / salmon → lubina (sea bass) / salmón | lightness → luminosidad | width → ancho
Bayesian decision theory → teoría bayesiana de la decisión | prior / posterior probability → probabilidad a priori / a posteriori | class-conditional probability density → densidad de probabilidad condicional a la clase | evidence → evidencia | loss function → función de pérdida | conditional risk → riesgo condicional | Bayes risk → riesgo de Bayes
minimum-error-rate classification → clasificación de tasa de error mínima | zero-one loss → pérdida cero-uno | likelihood ratio → razón de verosimilitud | minimax criterion → criterio minimax | Neyman-Pearson criterion → criterio de Neyman-Pearson | dichotomizer → dicotomizador
normal density → densidad normal | univariate / multivariate → univariada / multivariada | covariance matrix → matriz de covarianza | whitening transform → transformación de blanqueo | Mahalanobis distance → distancia de Mahalanobis | hyperquadric → hipercuádrica | linear machine → máquina lineal
error probabilities and integrals → probabilidades e integrales de error | Chernoff bound / Bhattacharyya bound → cota de Chernoff / cota de Bhattacharyya | signal detection theory → teoría de detección de señales | discriminability → discriminabilidad | receiver operating characteristic (ROC) → característica operativa del receptor (ROC) | hit / false alarm → acierto / falsa alarma
missing / noisy features → características faltantes / ruidosas | compound decision theory → teoría de la decisión compuesta | Bayesian belief network → red de creencias bayesiana | parameter estimation → estimación de parámetros | maximum-likelihood estimation → estimación por máxima verosimilitud | Bayesian estimation → estimación bayesiana | sufficient statistics → estadísticos suficientes
reproducing density → densidad reproductora | recursive Bayes learning → aprendizaje bayesiano recursivo | curse of dimensionality → maldición de la dimensionalidad | component analysis and discriminants → análisis de componentes y discriminantes | Fisher linear discriminant → discriminante lineal de Fisher | multiple discriminant analysis → análisis discriminante múltiple
expectation-maximization (EM) → esperanza-maximización (EM) | hidden Markov model (HMM) → modelo oculto de Markov (HMM) | forward / backward algorithm → algoritmo hacia adelante / hacia atrás | decoding → decodificación | Baum-Welch → Baum-Welch | first-order Markov → Markov de primer orden
nonparametric techniques → técnicas no paramétricas | density estimation → estimación de densidad | Parzen window → ventana de Parzen | probabilistic neural network (PNN) → red neuronal probabilística (PNN) | k-nearest-neighbor estimation → estimación por k vecinos más cercanos | nearest-neighbor rule → regla del vecino más cercano | Voronoi tessellation → teselación de Voronoi | metric → métrica | tangent distance → distancia tangente | fuzzy classification → clasificación difusa | reduced Coulomb energy (RCE) → energía de Coulomb reducida (RCE) | series expansion → desarrollo en serie
linear discriminant function → función discriminante lineal | hyperplane → hiperplano | augmented vector → vector aumentado | weight vector → vector de pesos | linearly separable → linealmente separable | margin → margen | perceptron criterion → criterio del perceptrón | batch / single-sample (fixed-increment) → por lotes / de una sola muestra (incremento fijo) | relaxation procedure → procedimiento de relajación
minimum squared-error (MSE) procedure → procedimiento de error cuadrático mínimo (MSE) | Widrow-Hoff (LMS) → Widrow-Hoff (LMS) | Ho-Kashyap procedure → procedimiento de Ho-Kashyap | linear programming → programación lineal | simplex algorithm → algoritmo símplex | support vector machine (SVM) → máquina de vectores de soporte (SVM) | multicategory generalization → generalización a múltiples categorías | Kesler's construction → construcción de Kesler
multilayer neural network → red neuronal multicapa | feedforward operation → operación hacia adelante | backpropagation algorithm → algoritmo de retropropagación | sensitivity → sensibilidad | stochastic / batch / on-line protocol → protocolo estocástico / por lotes / en línea | learning curves → curvas de aprendizaje | error surface → superficie de error | sigmoid → sigmoide
radial basis function (RBF) network → red de funciones de base radial (RBF) | special bases → bases especiales | regularization → regularización | pruning → poda | optimal brain damage / optimal brain surgeon → optimal brain damage / optimal brain surgeon | hints → pistas (hints) | weight initialization → inicialización de pesos | weight decay → decaimiento de pesos | hidden units → unidades ocultas | conjugate gradient → gradiente conjugado | Quickprop → Quickprop | cascade-correlation → cascade-correlation | neocognitron → neocognitrón""",
        "margin_notes": True,
    },
}

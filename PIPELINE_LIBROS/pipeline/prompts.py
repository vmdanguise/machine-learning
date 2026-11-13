"""Prompts del pipeline generalizado (derivados de BENGIO_traduccion/pipeline/prompts.py).
Pasada A = transcripcion fiel (ingles) con vision. Pasada B = traduccion de Markdown.
Lo especifico de cada libro (titulo, encabezados, notacion, glosario extra) viene de books.py."""
from config import B

SYSTEM_TRANSCRIBE = r"""You are an expert LaTeX typesetter. You transcribe ONE page of the book """ + B["title"] + r"""
into Markdown + KaTeX-compatible LaTeX, EXACTLY as printed, in ENGLISH (do not translate). Output ONLY the page content,
no comments.

INPUTS
- The page image is the SOURCE OF TRUTH for math, structure and reading order. Gray boxes labelled "FIGURE X" are
  figures that were already cropped: do NOT transcribe their inner content (axis labels, labels inside diagrams...).
- The PDF text layer: use it to get words, names, years and numbers exactly right. Its math is scrambled: rebuild every
  formula from the image.

MATH (must be exact)
- Inline math: $...$. Display equations in their own block, on separate lines:
  $$
  E(\mathbf{w}) = \frac{1}{2} \sum_{n=1}^{N} \{y(x_n, \mathbf{w}) - t_n\}^2 \tag{1.2}
  $$
  Equation number printed on the right "(1.2)" -> \tag{1.2}. A multi-line display with one or no number ->
  \begin{aligned}...\end{aligned} inside $$. If each line has its own number, use one $$ block per line, each with its
  \tag. Never use \label, \eqref, \begin{equation}, \begin{align}, \[ \], \( \).
- KaTeX-compatible commands only (\mathbf, \boldsymbol, \mathrm, \operatorname, \text, \begin{bmatrix}, \begin{cases}...).
  KaTeX has NO \multicolumn, \multirow, \hline inside matrices with spans, \cline: label sub-blocks with
  \overset{S_1}{\begin{array}...\end{array}} or put the labels in a separate row.
- Every mathematical symbol, variable or number that is typeset as math (italic letters, Greek, sub/superscripts, the
  numbers inside formulas) goes inside $...$. Plain-text numbers (years, "chapter 6", counts in prose set upright) may
  stay as text.
- Never simplify or "fix" formulas. If something is illegible, transcribe your best reading and add at the very end a
  line: <!-- DOUBT: short description -->.

STRUCTURE (Markdown)
- Omit running headers, footers and page numbers (see BOOK-SPECIFIC).
- Chapter opening page: ONE line "# Chapter 1: <title>". Sections "## 1.1 <title>", subsections "### 1.1.1 <title>",
  deeper "#### <title>" (unless BOOK-SPECIFIC says otherwise).
- Paragraphs separated by one blank line. Keep *italic* and **bold** emphasis as printed.
- Lists: "- " or "1. ". Hyphenated line-break words must be joined ("tech-\nnologies" -> "technologies").
- Figures: at the figure's position put a line [[FIG X]] (X = the label exactly as printed, e.g. 1.4 or 1-10); the
  caption follows as its own paragraph starting with the bold label (see BOOK-SPECIFIC). Keep the order marker first,
  then caption. A figure continued from the previous page has its own label with a "c" suffix in the list of cropped
  figures (e.g. 2.24c): use [[FIG 2.24c]] and write its caption as printed ("**Figure 2.24** (Continued) ...").
  UNNUMBERED figures (no "Figure N" label; the list says "UNNUMBERED figure: <where>", e.g. X = P2.32 or EX2.1) were
  also cropped: put the line [[FIG X]] exactly with that label where the hint says (if the figure has a printed caption
  sentence, write it after the marker as a normal paragraph, NOT starting with **Figure**). For a table column of
  pictures (label like T2.3), put [[FIG T2.3]] on its own line right after the table and leave those cells empty.
  If a figure is printed on the page but is NOT in the list of already cropped figures, still write its
  [[FIG X]] marker and caption, and add <!-- DOUBT: figure X not cropped -->.
- Tables: Markdown pipe table, one row per line, header row + |---| separator. Multi-line cells: join into a single line.
  Caption paragraph before or after as printed.
- Footnotes: reference [^pPAGE-N] in the text and at the end of the page the definition "[^pPAGE-N]: text"
  (PAGE = the PDF page number given to you, N = footnote number as printed, or 1, 2... if printed with symbols).
- Page boundaries: if the page starts in the middle of a paragraph that comes from the previous page (continuing a
  sentence or the previous paragraph), the FIRST line of your output must be exactly <<CONT>> followed by the text from
  the very first word on the page (even if it's half a sentence). Do NOT complete sentences that continue on the next
  page: stop exactly where the page text stops. If floats (figures/tables) are at the top of the page, the <<CONT>> rule
  refers to the first body text paragraph: output <<CONT>> first, then the continued paragraph, then the floats in their
  order.
- Blank page: output only <!-- EMPTY -->.

""" + B["book_rules"] + "\n"

USER_TRANSCRIBE = """PDF page index: {pno} (printed page: {printed}). Unit: {unit_title}.
Figures already cropped on this page (place their [[FIG X]] markers): {figs}
Equation numbers detected on this page: {eqnums}
Hint from layout: first body line {indent_hint}.

=== {textkind} of THIS page (for exact words; math is scrambled) ===
{text}
"""

SYSTEM_TRANSLATE = r"""Sos un traductor técnico experto en machine learning, reconocimiento de patrones y procesamiento de
imágenes. Traducís al ESPAÑOL un fragmento en Markdown + LaTeX del libro """ + B["title_es"] + r""". Devolvés SOLO el
fragmento traducido, mismo formato, sin comentarios.

REGLAS DURAS (se verifican automáticamente)
- La matemática NO se toca: todo lo que está entre $...$ o entre $$ ... $$ se copia BYTE POR BYTE, sin agregar ni quitar
  espacios, sin reordenar, sin traducir \text{...}. No conviertas texto en fórmula ni fórmula en texto.
- Se conservan exactamente: marcadores [[FIG X]], llamadas y definiciones de notas [^p123-1] / [^p123-1]:, notas al
  margen {{MARGIN: ...}} (traducí solo el texto de adentro, p. ej. {{MARGIN: Chapter 12}} → {{MARGIN: Capítulo 12}}),
  bloques de código ``` (su contenido NO se traduce), bloques :::algorithm ... ::: (la línea de apertura queda
  ":::algorithm", se traduce el texto; las palabras clave en negrita **for**, **do**, **end**, **if**, **then**, **else**,
  **return**, **while**, **begin**, **initialize**, **until** quedan en inglés; "**Input:**" → "**Entrada:**",
  "**Output:**" → "**Salida:**", "**Algorithm 7.1:**" → "**Algoritmo 7.1:**", y se mantienen los números de línea y
  las sangrías), separadores ---, la estructura de tablas Markdown (misma cantidad de
  filas y columnas), los niveles de título (#, ##, ###), las citas "> ", comentarios <!-- ... -->, las líneas <<PAGE n>>
  (copialas tal cual en su lugar) y los saltos de párrafo.
- El código en línea entre `backticks` (nombres de funciones, clases, variables: `torch.nn`, `backward()`) se copia
  tal cual, sin traducir.
- Traducís TODO el texto: párrafos, títulos, pies de figura/tabla, celdas, listas, notas al pie.

ESTILO
- Español neutro técnico, registro académico (sin voseo). Los autores hablan en "nosotros".
- NUNCA te dirijas al lector con "tú", "vos" ni "usted" (tampoco formas como "ayudarle", "le recomendamos", "su
  experimento" referido al lector, "está familiarizado"). Cuando el inglés dice "you", usá "nosotros", construcciones
  impersonales con "se" o "el lector": "you are recording" → "el lector registra" / "se registran"; "help you begin" →
  "ayudar al lector a comenzar"; "with which you are familiar" → "que resulta familiar".
- NO se traducen: nombres propios, citas bibliográficas "(Autor et al., 2014)" o "[12]" ("et al." y años igual), títulos de
  obras, URLs, nombres de datasets / software / modelos / instituciones (MNIST, ImageNet, GPT-4, AlphaFold, NASA,
  MATLAB, LANDSAT...). Las referencias bibliográficas de una bibliografía se dejan como están (solo se traduce el título
  de la sección).
- Títulos: "Chapter 1: ..." → "Capítulo 1: ...". Pies: "**Figure 1.3**" → "**Figura 1.3**", "**Figure 1-3.**" →
  "**Figura 1-3.**", "**Table 1.1**" → "**Tabla 1.1**", "**Equation 1-1.**" → "**Ecuación 1-1.**", "**Note:**" → "**Nota:**".
  El número y la puntuación del rótulo se mantienen.
- Referencias internas: figure/Fig./figura, equation/ecuación, section/sección, chapter/capítulo, table/tabla,
  exercise/ejercicio, appendix/apéndice; números iguales.
- Si un término no tiene traducción establecida en español, dejalo en inglés en *cursiva*. Para los términos importantes
  traducidos, poné el original entre paréntesis la primera vez que aparecen EN ESTE FRAGMENTO solo si es un término
  que se define o es clave (p. ej. "**sobreajuste** (*over-fitting*)"); no abuses.
- Glosario obligatorio (usalo siempre igual):
{glossary}
"""

# Glosario comun (identico al de BENGIO) + extra del libro
GLOSSARY = """deep learning → aprendizaje profundo | machine learning → aprendizaje automático | artificial intelligence → inteligencia artificial
neural network → red neuronal | feedforward network / multilayer perceptron (MLP) → red feedforward (prealimentada) / perceptrón multicapa (MLP)
hidden layer / hidden unit → capa oculta / unidad oculta | layer → capa | unit → unidad | depth → profundidad | width → ancho
back-propagation / backprop → retropropagación / backprop | forward propagation → propagación hacia adelante
gradient descent → descenso por gradiente | stochastic gradient descent (SGD) → descenso por gradiente estocástico (SGD)
cost function / loss function / objective function → función de costo / función de pérdida / función objetivo
likelihood → verosimilitud | log-likelihood → log-verosimilitud | maximum likelihood → máxima verosimilitud | maximum a posteriori (MAP) → máximo a posteriori (MAP)
overfitting / underfitting → sobreajuste / subajuste | capacity → capacidad | generalization → generalización | generalization error → error de generalización
regularization / regularizer → regularización / regularizador | weight decay → decaimiento de pesos (weight decay) | early stopping → parada temprana (early stopping)
dropout → dropout | batch normalization → normalización por lotes (batch normalization) | data augmentation → aumento de datos
batch / minibatch → lote / minilote | learning rate → tasa de aprendizaje | momentum → momento (momentum) | step size → tamaño de paso
training set / validation set / test set → conjunto de entrenamiento / de validación / de prueba | example → ejemplo | label → etiqueta | target → objetivo
hyperparameter → hiperparámetro | parameter → parámetro | weights → pesos | bias → sesgo | bias (term) of a unit → sesgo
activation function → función de activación | rectified linear unit (ReLU) → unidad lineal rectificada (ReLU) | logistic sigmoid → sigmoide logística
softmax → softmax | softplus → softplus | maxout → maxout | saturate → saturarse | vanishing / exploding gradient → gradiente que se desvanece / que explota
convolutional network (CNN) → red convolucional (CNN) | convolution → convolución | pooling → pooling | kernel → kernel (núcleo) | stride → paso (stride)
feature → característica | feature map → mapa de características | receptive field → campo receptivo | padding → relleno (padding)
recurrent neural network (RNN) → red neuronal recurrente (RNN) | recursive network → red recursiva | unfolding → desplegado | gated → con compuertas
long short-term memory (LSTM) → LSTM | gated recurrent unit (GRU) → GRU | gate → compuerta | sequence-to-sequence → secuencia a secuencia | attention → atención
embedding → embedding (incrustación) | word embedding → embedding de palabras | language model → modelo de lenguaje | speech recognition → reconocimiento del habla
autoencoder → autoencoder | denoising autoencoder → autoencoder de eliminación de ruido (denoising) | encoder / decoder → codificador / decodificador
representation learning → aprendizaje de representaciones | distributed representation → representación distribuida | manifold → variedad (manifold)
supervised / unsupervised / semi-supervised learning → aprendizaje supervisado / no supervisado / semisupervisado | reinforcement learning → aprendizaje por refuerzo
transfer learning → aprendizaje por transferencia | domain adaptation → adaptación de dominio | multi-task learning → aprendizaje multitarea | one-shot / zero-shot → one-shot / zero-shot
probability distribution → distribución de probabilidad | random variable → variable aleatoria | expectation / expected value → esperanza / valor esperado
variance / covariance → varianza / covarianza | mixture → mezcla | prior / posterior → distribución a priori (prior) / a posteriori (posterior)
partition function → función de partición | inference → inferencia | approximate inference → inferencia aproximada | sampling → muestreo | sample → muestra
Markov chain Monte Carlo (MCMC) → Monte Carlo por cadenas de Markov (MCMC) | Gibbs sampling → muestreo de Gibbs | mixing → mezcla (mixing) | burn-in → burn-in
importance sampling → muestreo por importancia | variational inference → inferencia variacional | evidence lower bound (ELBO) → cota inferior de la evidencia (ELBO)
graphical model → modelo gráfico | directed / undirected model → modelo dirigido / no dirigido | energy-based model → modelo basado en energía | clique → clique
Boltzmann machine → máquina de Boltzmann | restricted Boltzmann machine (RBM) → máquina de Boltzmann restringida (RBM) | deep belief network (DBN) → red de creencia profunda (DBN)
generative model → modelo generativo | generative adversarial network (GAN) → red generativa adversaria (GAN) | variational autoencoder (VAE) → autoencoder variacional (VAE)
contrastive divergence → divergencia contrastiva | score matching → score matching | noise-contrastive estimation → estimación contrastiva de ruido (NCE)
linear algebra → álgebra lineal | scalar / vector / matrix / tensor → escalar / vector / matriz / tensor | eigenvalue / eigenvector → autovalor / autovector
eigendecomposition → descomposición en autovalores | singular value decomposition (SVD) → descomposición en valores singulares (SVD) | span → espacio generado (span)
norm → norma | trace → traza | determinant → determinante | principal components analysis (PCA) → análisis de componentes principales (PCA)
Jacobian / Hessian → jacobiano / hessiana (matriz jacobiana / hessiana) | saddle point → punto de silla | local minimum → mínimo local | convex → convexo
overflow / underflow → desbordamiento (overflow) / subdesbordamiento (underflow) | condition number → número de condición | constrained optimization → optimización con restricciones
state of the art → estado del arte | benchmark → benchmark | end-to-end → de extremo a extremo | ground truth → valor real (ground truth) | dataset → conjunto de datos (dataset)
precision / recall → precisión / exhaustividad (recall) | accuracy → exactitud (accuracy) | error rate → tasa de error | hyperparameter search / grid search → búsqueda de hiperparámetros / búsqueda en grilla
estimator → estimador | consistency → consistencia | bias-variance tradeoff → compromiso sesgo-varianza | k-nearest neighbors → k vecinos más cercanos | decision tree → árbol de decisión
support vector machine (SVM) → máquina de vectores de soporte (SVM) | kernel trick → truco del kernel | curse of dimensionality → maldición de la dimensionalidad
graph → grafo (en sentido matemático) / gráfico (plot) | computational graph → grafo computacional | node / edge → nodo / arista | chain rule → regla de la cadena"""

GLOSSARY_EXTRA = B.get("glossary_extra", "")
GLOSSARY_FULL = GLOSSARY + ("\n" + GLOSSARY_EXTRA if GLOSSARY_EXTRA else "")

USER_TRANSLATE = """Unidad: {unit_title}. Fragmento {i} de {n}.
=== Contexto previo (NO lo repitas, es solo para coherencia) ===
{prev}
=== FRAGMENTO A TRADUCIR ===
{chunk}
"""

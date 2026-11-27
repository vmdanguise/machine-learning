**Asunto:** TP final de Machine Learning: detección de crisis epilépticas en EEG (síntesis)

Estimado profesor:

Le escribo para contarle en qué consiste mi trabajo final de Machine Learning y qué resultados obtuve.

**Un ejemplo de uso real**

Un chico con epilepsia queda internado varios días en una unidad de monitoreo, con electrodos de EEG conectados las 24 horas. Ahí se buscan dos cosas: registrar sus crisis para ajustar la medicación o evaluar una cirugía, y asistirlo enseguida cuando ocurren. Pero muchas crisis pasan de noche o duran apenas segundos, y nadie puede mirar la pantalla todo el tiempo.

El detector analiza la señal en ventanas de 4 segundos y, si reconoce el patrón de una crisis, avisa a la enfermería. En los pacientes de prueba, que el modelo nunca había visto, la red detectó 10 de cada 14 crisis, con una demora típica de unos 20 segundos y una falsa alarma cada 5 horas. A la mañana, el médico no tiene que revisar 24 horas de registro: va directo a los tramos marcados. Así son los registros de la base CHB-MIT que usé, tomados a pacientes pediátricos internados en el Boston Children's Hospital.

**Objetivo**

El trabajo busca detectar en forma automática crisis epilépticas en el electroencefalograma (EEG). Hoy un médico tiene que revisar a mano horas de registro para encontrar crisis que duran segundos. Un detector automático puede avisar en tiempo real o marcar los tramos que conviene revisar. El requisito es que encuentre la mayor cantidad posible de crisis con muy pocas falsas alarmas. Si no, el personal termina ignorándolo.

**Datos**

Uso dos bases públicas:
- **Bonn:** 500 segmentos de un canal, con 3 clases (sano, interictal, ictal).
- **CHB-MIT** (PhysioNet): 6 pacientes, 223 horas de registro continuo de 18 canales, con 34 crisis. Las crisis ocupan apenas el 0,37 % del tiempo, así que las clases están muy desbalanceadas.

**Qué hace el trabajo**

1. **Modelo de la señal y atributos:** a partir de un modelo de la crisis como descarga rítmica, uso la transformada de Fourier y el método de Welch para calcular la potencia por banda. De ese mismo modelo deduzco una calibración por paciente: restar la mediana de cada atributo.
2. **Modelos convexos (regresión logística y SVM):** verifico numéricamente la teoría de optimización. Muestro que en el caso convexo todos los puntos iniciales llegan al mismo óptimo global y que en una red neuronal chica no pasa lo mismo. También compruebo las condiciones KKT en el dual del SVM.
3. **Red convolucional sobre espectrogramas:** la entreno con seis optimizadores (SGD, Momentum, Nesterov, RMSprop, Adam y AdamW), tres tasas de aprendizaje y cinco semillas, y comparo los resultados con pruebas estadísticas.
4. **Evaluación clínica:** fijo el umbral de decisión con el lema de Neyman-Pearson para tener una tasa de falsas alarmas controlada. Mido los resultados por crisis detectada y por falsas alarmas por hora, siempre sobre pacientes que el modelo no vio.

**Resultados principales**

- **Bonn:** la regresión logística llega a 97,4 % de exactitud y el SVM con kernel RBF a 98,4 %.
- **Calibración por paciente:** es la mejora más grande del trabajo. Con la regresión logística en pacientes nuevos, el AUC sube de 0,80 a 0,93 y las falsas alarmas bajan de 3,3 a 1,2 por hora.
- **Optimizadores:** con la tasa elegida por validación, SGD resulta significativamente mejor. Pero si a todos se les da la tasa alta, SGD, RMSprop, Adam y AdamW quedan empatados (AUC entre 0,970 y 0,976). En este problema pesa más la tasa de aprendizaje que el algoritmo.
- **Red contra regresión logística:**
  - La red detecta 10 de 14 crisis con 0,19 falsas alarmas por hora, es decir, una cada 5 horas.
  - Con un umbral comparable, la regresión logística detecta 6 de 14 con 0,54 por hora.
  - La red además avisa antes, aunque su AUC es menor.
  - Conclusión: para un detector de crisis el AUC no es la métrica adecuada. Lo que importa es la sensibilidad con muy pocas falsas alarmas.

**Limitaciones**

- Trabajé con pocos pacientes: la evaluación final de la red se basa en 2 pacientes y 14 crisis.
- Usé un solo paciente de validación, y quedó saturado: no sirvió para elegir hiperparámetros.
- El experimento con la tasa alta lo diseñé después de mirar los resultados de prueba, así que esa conclusión es exploratoria.

Como trabajo futuro propongo validación cruzada por paciente para la red, sumar más pacientes y calibrar el umbral en línea.

El trabajo incluye el informe en LaTeX, cuatro notebooks (uno por etapa), los scripts de descarga, preprocesamiento y entrenamiento, y todos los resultados. Se puede reproducir completo con las instrucciones del README.

Quedo a disposición para cualquier consulta.

Saludos cordiales,
Vicente Matias Danguise
Maestría en Inteligencia Artificial, Universidad de Palermo

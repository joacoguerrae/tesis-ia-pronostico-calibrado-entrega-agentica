# Cantarelli, C. C., Davis, K., Pinto, J. K. & Turner, N. (2025). Reference class forecasting: promises, problems, and a research agenda moving forward. Production Planning & Control, 37(7), 691–709. DOI 10.1080/09537287.2025.2578708
**Estado de lectura:** leído completo desde https://dspace.lib.cranfield.ac.uk/server/api/core/bitstreams/076d9c29-659d-4bfd-9b1b-e0019ea9ad20/content (versión open access aceptada, CC BY-NC-ND; recibido 31/07/2025, aceptado 17/10/2025)
**Tipo:** revisión sistemática de literatura (61 artículos) + agenda de investigación · **Datos:** ninguno propio; sintetiza estudios ajenos (megaproyectos de infraestructura, energía, construcción, algo de IT) · **Objeto:** trabajo humano / método general
**Tiempo de lectura del original:** ~60 min · **Tiempo de lectura de este resumen:** ~8 min

## En una frase
Revisión crítica de 61 papers sobre Reference Class Forecasting (RCF) que concluye que el método funciona mejor que estimar "desde adentro" en proyectos grandes y tempranos, pero que su utilidad depende casi por completo de armar bien la clase de referencia, que los "uplifts" que salen son políticamente indigeribles, y que falta evidencia comparativa seria entre variantes híbridas.

## Por qué está en nuestra lista (qué decisión del proyecto toca)
Nuestro baseline "priors por categoría sin aprendizaje" y el modelo con priors por clase (10 clases = 5 tiers × 2 tamaños) *son* una forma de RCF: mirás la distribución de resultados de tareas parecidas y de ahí sacás el pronóstico. Este paper es la justificación bibliográfica de por qué esa idea tiene sentido, y sobre todo un catálogo de los problemas que vamos a tener: cómo definir la clase (demasiado ancha = mucha varianza; demasiado angosta = pocos datos), qué pasa cuando el proceso cambia y la clase deja de ser comparable (nuestra no estacionariedad entre versiones de agentes), y la advertencia de que la RCF "cruda" está evolucionando hacia híbridos bayesianos (que es exactamente lo que hacemos con pooling parcial). También toca OE5(a): la Proposición 3 pregunta cuánta variabilidad hay si distintos managers arman la clase de referencia, que es nuestro estudio de acuerdo entre etiquetadores en otro idioma.

## Resumen sección por sección

### 1. Orígenes de RCF
Arranca con el contexto de megaproyectos (≥ USD 1.000 millones) y los sobrecostos promedio que documentan Flyvbjerg y compañía: 157% Juegos Olímpicos, 96% represas, 73% proyectos de IT, 40% ferrocarriles; en plazo, 23% transporte, 74% hidroeléctricas, 45% represas. Flyvbjerg & Gardner (2023) reportan sobrecostos medios entre 1% y 238% según el tipo de proyecto (25 tipos).

La base teórica es la Prospect Theory de Kahneman y Tversky: la gente decide con "optimismo indebido" ignorando la evidencia distribucional del pasado. De ahí sale la *planning fallacy* (subestimar costo, tiempo y riesgo; sobreestimar beneficios), que se produce por mirar el proyecto "desde adentro" (inside view: sus detalles particulares) en vez de "desde afuera" (outside view: cómo les fue a proyectos parecidos). Flyvbjerg lo llevó al terreno de obra pública y atribuye los desvíos a tres causas: sesgo de optimismo, sesgo de unicidad ("nuestro proyecto es distinto") y tergiversación estratégica (mentir para conseguir la plata).

RCF es la respuesta prescriptiva: tomás la distribución empírica de desvíos de una clase de proyectos comparables y la usás como corrección. Reino Unido fue el primer gobierno europeo en hacerla obligatoria para transporte; Dinamarca después; Australia, Alemania, Noruega, Sudáfrica, Suecia, Suiza y Países Bajos la aplicaron caso por caso.

Los autores marcan que la ciencia no está cerrada: la corriente de Love e Ika sostiene que los desvíos se explican mejor por complejidad, incertidumbre y error de estimación que por sesgo sistemático, y que asumir sesgo es en sí un sesgo. Ika, Love y Pinto (2022) proponen que sesgo y error juntos explican mejor.

Las dos preguntas de investigación: (RQ1) cómo se compara RCF con métodos convencionales e híbridos y cómo se aplicó; (RQ2) qué fortalezas y problemas identifica la literatura.

### 2. Metodología
Revisión sistemática con análisis de contenido cualitativo, siguiendo los cuatro pasos de Mayring (2000): recolección, análisis descriptivo, selección de categorías, evaluación. Buscaron en Scopus y Web of Science con el término "reference class forecast*" (probaron alternativas más amplias y daban ruido), artículos y ponencias en inglés 2001–2025, más *snowballing* hacia atrás y adelante.

**Flujo de tamizado (Figura 1):**

| Paso | Cantidad |
|---|---|
| Scopus | 82 |
| Web of Science | 73 |
| Total inicial | 155 |
| Duplicados eliminados | 70 |
| Quedan tras deduplicar | 85 |
| Excluidos en primer tamizado (título/resumen) | 26 |
| Excluidos en segundo tamizado (texto completo) | 7 |
| Quedan | 52 |
| Sumados por snowballing | 10 |
| **Muestra final** | **61** |

**Tabla 1 – Criterios de exclusión:**

| Criterio | Descripción | Excluidos |
|---|---|---|
| Foco en RCF | Mencionan RCF al pasar, sin desarrollarla, aplicarla ni evaluarla | 23 |
| Alcance | RCF pero no relacionada con pronóstico | 3 |
| Tipo de documento | Sin acceso o duplicado de una versión de revista | 8 |

Ojo: la aritmética del texto (85 − 26 − 7 = 52; 52 + 10 = 62) no cierra exactamente con el 61 final, mientras que la Tabla 1 (85 − 34 = 51; 51 + 10 = 61) sí. Lo reporto tal como está; el número que el paper usa es 61.

Análisis descriptivo: 74% de los artículos son de 2015 en adelante (Figura 2, barras por año); 23 de los 61 salieron en revistas con más de una contribución, concentradas en gestión de proyectos (IJPM, PMJ), construcción/ingeniería y energía (Figura 3). Cinco categorías de codificación: RCF vs métodos convencionales, híbridos, aplicaciones prácticas, fortalezas, problemas.

### 3. Evaluación metodológica de RCF
**3.1 RCF vs métodos convencionales.** La mayoría de las comparaciones favorece a RCF: Chadee et al. (2023) en vivienda social; Bayram & Al-Jibouri (2016a) con 420 proyectos de construcción turcos; Batselier & Vanhoucke (2016, 2017) contra Earned Value Management y Monte Carlo en exactitud, estabilidad y oportunidad; Park (2021b) contra Monte Carlo en transporte UK/US. La excepción es Fridgeirsson (2016) en Islandia: si tu método actual ya anda bien, RCF no aporta. Bayram & Al-Jibouri (2016b, 2018) matizan: RCF gana en pre-diseño; con información detallada, regresión lineal simple y redes RBF ganan.

**3.2 Híbridos.** Acá está lo más relevante para nosotros. Bordley (2014) trata la clase de referencia como *prior* bayesiano (la distribución de arranque, antes de ver datos del proyecto) y la combina con un modelo específico: menor error y menor varianza que cada uno por separado. Zangeneh & McCabe (2022) usan redes bayesianas con la clase como prior actualizable. Kim & Reinschmidt (2011) actualizan durante la ejecución con datos de avance. Otros: kernel density adaptativo (Lordan-Perret et al. 2023), k-NN para elegir la clase (El Yamami et al. 2018, proyectos IT), gradient boosting sobre datos RCF (Natarajan 2022), *Similarity-Based Forecasting* que pondera por similitud en vez de peso igual (Lovallo, Clarke & Camerer 2012), *Weighted RCF* con pesos empíricos (Zani & Adey 2025), biclustering para armar clases (Garbuio & Gheno 2023), radio de giro como medida de similitud (Zarghami 2023). Servranckx, Vanhoucke & Aouam (2021), con 52 proyectos, muestran el trade-off central: más propiedades para definir la clase → más exactitud pero clase más chica y menos confiable. Allahaim, Liu & Kong (2016) encuentran que un modelo de contingencia basado en riesgo le gana a RCF P50 y P90.

**3.3 Aplicaciones.** Energía (Sovacool et al. 2014, 401 plantas en 57 países; Jenkins et al. 2022, 57 hidroeléctricas del Banco Mundial 1975–2015: RCF evitó proyectos malos pero también rechazó proyectos que hubieran sido buenos), transporte (Stuttgart 21; 30 puentes chinos; Flyvbjerg, Hon & Fok 2016 con 25 obras viales de Hong Kong contra 863 de benchmark), nuclear, eólica offshore, vivienda, petróleo y gas. Prater et al. (2017): fuera de ingeniería no hay validación estadística seria. Walczak & Majchrzak (2018): funciona en proyectos grandes y homogéneos, no en carteras heterogéneas de proyectos chicos.

La Tabla 2 del paper resume 28 estudios clave (fuente, método, hallazgo); no la transcribo entera pero los renglones más útiles para nosotros son Bordley (2014), Servranckx et al. (2021), Batselier & Vanhoucke (2016: RCF solo gana cuando la similitud es suficientemente alta), Walczak & Majchrzak (2018) y Themsen (2019: caso único longitudinal donde RCF no mejoró nada).

### 4. Fortalezas
(4.1) Mejora estimaciones en proyectos grandes, tempranos y no rutinarios: el desvío nace en el front-end, donde no hay detalle para hacer bottom-up. Limitaciones prácticas: empresas chicas con pocos tipos de proyecto, proyectos rutinarios, desvíos por cambios de alcance tardíos. Y una frase clave para nosotros: como los entornos cambian, la clase original puede dejar de ser comparable y los uplifts anteriores pierden vigencia. (4.2) Da una base empírica para contingencias, en vez del "porcentaje fijo según experiencia del estimador". (4.3) Es fácil de usar: pocos parámetros, un pronóstico fijo que da estabilidad; el costo está en juntar los datos. Los híbridos prometen pero "no hay evidencia concreta de su eficacia" y agravan la demanda de datos.

### 5. Problemas
(5.1) Los sesgos son colectivos y sociopolíticos: la evidencia de sesgo de optimismo en los estudios revisados es mixta, a veces aparece pesimismo; Themsen (2019) muestra con teoría del actor-red que la estimación es un efecto de red de actores interesados y que "des-sesgar" con una técnica es ingenuo. (5.2) Es difícil fijar uplifts razonables: para ferrocarriles, llegar a 50% de probabilidad de no pasarse exige +40%; bajar a 10% exige +68%. Ninguna agencia acepta eso, y un uplift de compromiso del 20–30% puede ser "lo peor de ambos mundos": insuficiente y encima mete holgura. Mitigar riesgos para "cortar la cola gorda" no tiene justificación estadística cuantificada. (5.3) Identificar la clase es lo más complejo: demasiado ancha no permite comparar, demasiado angosta no permite suavizar; tipos raros no tienen muestra; las empresas no comparten datos; la clase puede armarse con sesgo; Winch (2025a) pide medir la "unicidad" del proyecto y los autores proponen repensar los esquemas de clasificación con variables de complejidad estructural en vez de industria. (5.4) No sobrevender: RCF captura riesgo (lo modelable) pero no incertidumbre (unknown-unknowns), y es manipulable: si sabés que te van a aplicar uplift, bajás la estimación inicial.

### 6. Proposiciones y agenda
Las cinco proposiciones, en palabras:
1. **RCF es un corrector cuyo efecto depende de cómo lo usa la gente.** Hay una paradoja: corregir con un método calculado los sesgos que la gente metió usando otro método calculado. Los estimadores aprenden a "gamear" el uplift. Investigar cómo se crean las estimaciones iniciales, criterios de "matar" proyectos y la relación con mitigación de riesgos.
2. **La clave parece ser una "RCF mejorada" (híbrida).** Los híbridos dan mejores resultados pero la validación es con pocos proyectos y alcance angosto. Proponen meta-análisis de MAE/MAPE entre variantes y estudios de benchmarking controlado (backtesting retrospectivo con datos reales o simulación) para comparar variantes en condiciones idénticas y ver cómo priors, clustering y ponderación afectan la exactitud según contexto.
3. **La utilidad depende del proceso de selección de la clase de referencia.** Involucra juicio gerencial; pregunta empírica: ¿cuánta variabilidad hay si a distintos managers les pedís que armen la clase? ¿Se aprende con el tiempo? Los datos dan el "qué", no el "por qué".
4. **Falta evidencia de que RCF haga que los proyectos terminen dentro del presupuesto post-uplift.** El uplift puede inyectar holgura y generar problemas de control de alcance; hay que estudiar la dinámica post-uplift, incluso con experimentos controlados.
5. **La variedad de métodos para estudiar RCF es fortaleza y problema a la vez.** Casos únicos, longitudinales, modelado matemático: iluminan desde varios ángulos pero impiden el meta-análisis.

Recomendaciones para practicantes: entrenar en sesgos y razonamiento probabilístico, usar intervalos en vez de puntos, separar al equipo que estima del que aplica RCF, revisión independiente, pilotear híbridos antes de adoptarlos, criterios explícitos de inclusión/exclusión para la clase, y empezar a construir la base de datos de proyectos terminados.

### 7. Conclusiones
RCF pasó de técnica empírica no paramétrica (usás la distribución observada, sin asumir una forma) a componente dentro de modelos probabilísticos híbridos. La mayoría de las críticas actuales apuntan a implementación y gobernanza, no a la lógica central. Los datos mejores y más estructurados permiten aplicar RCF directo sobre líneas base y combinarla con modelos paramétricos.

## Los números que hay que recordar
- 61 artículos finales; 74% posteriores a 2015 (Sección 2.2, Figura 2).
- Sobrecostos medios: 157% Olímpicos, 96% represas, 73% IT, 40% ferrocarril; sobreplazos: 23% transporte, 74% hidro, 45% represas (Sección 1).
- Uplift ferroviario: +40% para P50, +68% para P90 (Sección 5.2, citando Flyvbjerg 2008).
- Servranckx et al. (2021), 52 proyectos: más propiedades → más exactitud pero menos confiabilidad (Sección 3.2, Tabla 2).
- Batselier & Vanhoucke (2016): RCF solo le gana a EVM y Monte Carlo cuando la similitud con la clase es suficientemente alta (Sección 5.3).
- Bordley (2014): clase de referencia como prior bayesiano → menor error y menor varianza que cada método solo (Sección 3.2).

## Limitaciones
**Declaradas:** búsqueda con un solo término; heterogeneidad de métodos impide meta-análisis; la evidencia de híbridos es de muestras chicas; el foco es costo, el plazo aparece solo de costado.
**Las nuestras:** casi todo es megaproyecto de infraestructura, con clases de decenas o cientos de proyectos y horizonte de años; nada se parece a tareas de horas o días. No hay ninguna medida probabilística de calibración (todo es exactitud del punto P50/P90); no hablan de cobertura, PIT ni CRPS. El detalle operativo del método está delegado a Lovallo, Cristofaro & Flyvbjerg (2023, p. 142). El leakage temporal (usar en la clase proyectos posteriores al pronóstico) no se discute como tal.

## Qué tomamos tal cual y qué hacemos distinto
**Tomamos:** (a) el encuadre outside view / inside view como justificación del baseline por categoría y del modelo con priors por clase; (b) el trade-off ancho/angosto de Servranckx et al. como argumento explícito para 10 clases y no 50, y para el pooling parcial (que es justamente la forma estadística de no elegir entre "todo junto" y "cada clase sola"); (c) la Proposición 2, que pide backtesting retrospectivo comparando variantes en condiciones idénticas, es literalmente nuestro diseño de evaluación con origen móvil; (d) la Proposición 3 como motivación de OE5(a): la variabilidad entre etiquetadores al asignar clase es un riesgo del método, no un detalle; (e) la advertencia de la Sección 4.1 sobre clases que dejan de ser comparables cuando cambia el entorno como motivación de OE5(b) (cuánta historia usar).
**Hacemos distinto:** nuestro objeto son agentes de IA, no humanos con incentivos para mentir, así que el problema 5.1 (sesgo sociopolítico, gaming del uplift) casi desaparece del lado del pronóstico; queda solo del lado de la estimación humana como baseline. Pronosticamos distribución completa y la evaluamos por calibración, no un uplift a P50/P90. No adoptamos ninguno de los híbridos sofisticados (kNN, GBRT, biclustering, WRCF): cada uno sería alcance nuevo y una justificación más que escribir; el pooling parcial ya es nuestro "híbrido" y alcanza para R1–R5. Si algún día se quiere ponderar por similitud (SBF/WRCF), eso va a R6–R8 y hay que decir qué sale.

## Si igual lo vas a abrir
Leé la Sección 2 (flujo y Tabla 1) para citar el método, la Tabla 2 completa (una página, muy útil para encontrar estudios comparativos), la 5.3 y las Proposiciones 2 y 3. Podés saltear la Sección 1 (contexto de megaproyectos), la 3.3 (aplicaciones por sector) y las recomendaciones para practicantes. Figuras 2 y 3 son solo distribuciones bibliométricas.

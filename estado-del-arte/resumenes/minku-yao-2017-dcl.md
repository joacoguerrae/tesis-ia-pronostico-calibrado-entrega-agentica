# Minku, L. L. & Yao, X. (2017). Which models of the past are relevant to the present? A software effort estimation approach to exploiting useful past models. Automated Software Engineering, 24(3), 499–542. DOI 10.1007/s10515-016-0209-7
**Estado de lectura:** leído desde https://minkull.github.io/publications/MINKUAUSE2016.pdf (preprint de autor). Aviso honesto: la herramienta de lectura devolvió el texto completo hasta la Sección 9 y el arranque de la Sección 10 (análisis de parámetros); el final de la 10, la Sección 11 (amenazas a la validez) y la 12 (conclusiones) no llegaron en tres pasadas. Lo que se dice de esas secciones está marcado como no verificado.
**Tipo:** propuesta de método + validación empírica (online learning, ablación, comparación con 6 métodos, 5 base learners, sensibilidad de parámetros) · **Datos:** ISBSG Release 10 (187 proyectos WC + 826 CC), Nasa60, Cocomo81, Nasa93 (repositorio PROMISE) · **Objeto:** trabajo humano (estimación de esfuerzo de software) / método general
**Tiempo de lectura del original:** ~90 min (44 páginas) · **Tiempo de lectura de este resumen:** ~9 min

## En una frase
Proponen DCL (Dynamic Cross-company Learning): un ensamble que mantiene varios modelos entrenados con datos "de otras empresas" más uno que aprende con los datos propios, y que va subiendo y bajando el peso de cada modelo según quién acertó en el último proyecto, de modo que en un entorno que cambia se apoya automáticamente en el modelo del pasado que mejor representa el presente; le gana a entrenar solo con datos propios en los cuatro datasets.

## Por qué está en nuestra lista (qué decisión del proyecto toca)
Es el paper de referencia para nuestra no estacionariedad: el proceso de desarrollo con agentes cambia entre versiones, y la pregunta "¿qué parte de la historia sigue siendo útil?" es exactamente OE5(b). Además, su protocolo de evaluación (los proyectos llegan uno por uno en orden cronológico, se entrena con lo disponible y se pronostican los siguientes) es un backtesting de origen móvil, el mismo que usamos, y su crítica a los splits aleatorios es el argumento contra el leakage que necesitamos citar. También sirve como ejemplo de un método que mantiene modelos "viejos" en vez de descartarlos, y de cómo se hace ablación y comparación contra baselines sin caer en sobreajuste de parámetros.

## Resumen sección por sección

### 1. Introducción
Estimación de esfuerzo de software (SEE): sobreestimar pierde contratos y desperdicia recursos; subestimar produce software malo, tardío o inconcluso. Las empresas viven en entornos no estacionarios (gente nueva, tecnologías, lenguajes, cambios de gestión), así que un modelo entrenado con el pasado puede ser útil o engañoso según el momento. Un trabajo previo de los mismos autores (Minku & Yao 2013) había mostrado que los modelos within-company (WC: datos propios) y cross-company (CC: datos de otras empresas) se turnan para ser el mejor según la época. Dos preguntas: **RQ1** ¿cómo saber qué modelo del pasado representa mejor los proyectos actuales? **RQ2** ¿esa información mejora la estimación? La contribución respecto a la versión de conferencia (PROMISE 2012) son las Secciones 6 a 10: validar que el mecanismo de pesos realmente identifica al mejor modelo y por qué, y compararlo con darle el mismo peso a todos.

### 2. Trabajo relacionado
La literatura previa encontraba que los modelos CC rinden igual o peor que los WC. El *relevancy filtering* (filtrar proyectos CC demasiado distintos a los propios por similitud de atributos) logra que CC empate con WC más seguido. Critican la evaluación con partición aleatoria porque entrena con proyectos que en un escenario real no habrían existido todavía en el momento de estimar (nuestro leakage). Los ensambles dinámicos de la literatura de aprendizaje online (Dynamic Weighted Majority, DWM) son el antecedente algorítmico.

### 3. DCL, el algoritmo paso a paso
Ingredientes: m modelos CC (uno por partición de datos ajenos), entrenados una sola vez antes de empezar y fijos; un modelo WC que se entrena con los proyectos propios a medida que llegan; dos factores de castigo β_c y β_w (entre 0 y 1); y un mecanismo de filtrado de respaldo con parámetros Q y T_start.

1. **Inicialización.** Cada modelo CC arranca con peso 1/m. El modelo WC arranca con peso 0 (todavía no tiene datos). Hasta que llega el primer proyecto propio, se puede pronosticar solo con los CC.
2. **Llega un proyecto propio terminado (x, y)**: x son sus atributos, y su esfuerzo real. Cada modelo predice el esfuerzo de x.
3. **Se elige un ganador**: el modelo con menor error absoluto |predicción − y|.
4. **Se castiga a los perdedores**: cada modelo que no ganó multiplica su peso por β (β_c si es CC, β_w si es WC). Por defecto β_c = β_w = 0,5, o sea, perder te reduce el peso a la mitad. El ganador conserva su peso.
5. **Si era el primer proyecto propio**, el peso del WC pasa de 0 a 1/(m+1).
6. **Normalización**: se dividen todos los pesos por su suma, así siguen sumando 1.
7. **Se entrena el modelo WC** con (x, y), reentrenándolo con todos los proyectos propios acumulados o de manera incremental según el algoritmo base.
8. **Pronóstico** para los proyectos siguientes: promedio ponderado de las predicciones de los m+1 modelos, con los pesos actuales.
9. **Filtrado (respaldo)**: una vez acumulados T_start = 15 proyectos propios, para cada nuevo proyecto se ignoran los modelos CC cuyos datos de entrenamiento tenían tamaños "demasiado chicos" respecto del proyecto a pronosticar: un modelo CC solo participa si el tamaño del proyecto es menor que el cuantil Q = 0,9 (el valor por debajo del cual está el 90% de los tamaños) de sus proyectos de entrenamiento. Los modelos filtrados no se borran, solo no votan en ese proyecto. La razón de esperar 15 proyectos es que antes el WC es inestable y conviene que los CC ayuden aunque sean imperfectos.

La intuición: un modelo que viene acertando mantiene peso alto; uno que viene fallando decae geométricamente; si el entorno cambia y otro modelo empieza a acertar, en pocos proyectos recupera el peso. Nunca se descarta nada, así que si el pasado vuelve a ser relevante, se lo puede volver a usar.

### 4. Datasets y protocolo temporal
**ISBSG Release 10** filtrado por calidad A/B, esfuerzo del equipo de desarrollo, sizing IFPUG 4+: 187 proyectos de una sola empresa (WC) y 826 de otras (CC). Cuatro atributos de entrada (tipo de desarrollo, tipo de lenguaje, plataforma, tamaño funcional); salida: esfuerzo en persona-horas; imputación de faltantes con k-NN. Tres variantes:
- **ISBSG2000**: 119 WC posteriores a 2000; 168 CC hasta fin de 2000.
- **ISBSG2001**: 69 WC posteriores a 2001; 224 CC hasta fin de 2001.
- **ISBSG**: 187 WC sin restricción; 826 CC incluyendo proyectos *posteriores* a los WC (simula que otras empresas están "más evolucionadas"; los autores lo declaran explícitamente).

Los CC se parten en 3 grupos por productividad (esfuerzo / tamaño), simulando "empresas" con distinta productividad (Tabla 1):

| Dataset | CC-0 | CC-1 | CC-2 |
|---|---|---|---|
| ISBSG2000 | [0,7; 5] n=57 | (5; 13] n=57 | (13; 155,7] n=55 |
| ISBSG2001 | [0,7; 6] n=72 | (6; 14] n=79 | (14; 155,7] n=73 |
| ISBSG | [0,3; 10] n=291 | (10; 20] n=250 | (20; 424,9] n=285 |
| Nasa60Coc81 (Coc81) | [0,7; 2,85] n=19 | (2,85; 6,6] n=20 | (6,6; 49] n=24 |

**Nasa60Coc81**: 60 proyectos NASA (WC, orden original preservado porque la cronología real se desconoce) y 63 de Cocomo81 (CC, ordenados por año). 16 atributos (15 cost drivers COCOMO + líneas de código); esfuerzo en persona-mes. **Nasa60Coc81Nasa93**: agrega Nasa93 (93 proyectos) como segunda partición CC; 55 proyectos se solapan con Nasa60, así que sirve solo como control de "verdad conocida" (DCL debería darle mucho peso a Nasa93) y no para concluir si CC ayuda.

**Protocolo**: en cada paso de tiempo llega un proyecto WC terminado, se actualiza el sistema y se pronostican los **siguientes 10** proyectos del flujo; la métrica de ese paso es el MAE (error absoluto promedio) sobre esos 10. Pasos de tiempo aproximados: ~100 (ISBSG2000), ~55 (ISBSG2001), ~160 (ISBSG), ~50 (Nasa). Los métodos deterministas corren una vez (el orden cronológico no se puede barajar).

### 5. Configuración experimental
Parámetros por defecto y sin ajuste: β_c = β_w = 0,5, T_start = 15, Q = 0,9 (argumento: en entornos no estacionarios el óptimo cambia y las empresas no tienen recursos para tunear). Base learner principal: árbol de regresión REPTree de Weka (mínimo 1 instancia por hoja, mínima proporción de varianza 0,0001). Métricas: MAE como principal porque es simétrica y no castiga proyectos grandes como hace el MRE; **SA** (Standardized Accuracy: cuánto mejor que adivinar al azar, en porcentaje: SA = (1 − MAE/MAE_random) × 100); **tamaño de efecto Δ** = (MAE_control − MAE_método) / desvío estándar del control, con la convención 0,2 chico, 0,5 mediano, 0,8 grande.

### 6. ¿DCL le da más peso a los modelos correctos? (RQ1)
Figura 2: el MAE de cada modelo individual sobre los siguientes 10 proyectos cambia mucho en el tiempo y los CC a veces le ganan al WC (en ISBSG, CC-RT0 y WC-RT compiten fuerte después del paso 50; en Nasa60Coc81, CC-RT1 es el mejor casi siempre). Figura 3: las trayectorias de pesos de DCL siguen esa competencia; en Nasa60Coc81Nasa93 le da el peso más alto al modelo de Nasa93 (el solapado), como se esperaba. Tabla 2 (Nasa60Coc81, pasos 25–45) muestra el límite: en los pasos 25–27 el WC gana en el proyecto actual (error 47, 2,4 y 1,2 contra 105/78/78 del CC-RT0) y sube de peso, pero sobre los *siguientes* diez el CC-RT0 era mejor. El peso se actualiza con el acierto en el proyecto actual, no con el futuro, así que ante cambios bruscos DCL reacciona con retraso. Proponen sumar detección de *concept drift* (cambio en la relación entre atributos y resultado) como trabajo futuro. Respuesta a RQ1: el mecanismo generalmente identifica al mejor modelo, con retrasos en transiciones abruptas.

### 7. Análisis de componentes (ablación)
Cuatro variantes: **DCL** (pesos + filtrado), **DCL-W** (solo pesos), **DCL-F** (solo filtrado, pesos iguales), **DCL-N** (ni pesos ni filtrado: promedio simple).

**Tabla 3 – MAE global (media ± desvío entre pasos de tiempo):**

| Dataset | DCL | DCL-W | DCL-F | DCL-N |
|---|---|---|---|---|
| ISBSG2000 | 2352,59 ± 925,84 | 2554,36 ± 1073,43 | 2641,08 ± 953,42 | 3521,61 ± 1632,34 |
| ISBSG2001 | 2873,11 ± 1235,93 | 2795,39 ± 1254,17 | 3417,44 ± 1648,90 | 3573,21 ± 1589,43 |
| ISBSG | 2805,56 ± 1468,20 | 2741,18 ± 1396,35 | 3041,07 ± 2140,21 | 5108,66 ± 2955,82 |
| Nasa60Coc81 | 205,83 ± 214,70 | 142,31 ± 122,64 | 303,28 ± 203,33 | 298,50 ± 196,10 |
| Nasa60Coc81Nasa93 | 109,82 ± 154,72 | 42,25 ± 45,42 | 241,75 ± 185,77 | 251,35 ± 192,75 |

SA (%): DCL 46,21 / 30,14 / 53,69 / 56,92 / 77,01; DCL-W 41,60 / 32,03 / 54,75 / 70,22 / 91,16; DCL-N 19,48 / 13,11 / 15,67 / 37,52 / 47,39 (mismo orden de datasets).

Test de Friedman (compara rankings de varios métodos sobre varios datasets): F_F = 27,25 > 3,49, p < 0,0001. Rankings promedio (Tabla 4): DCL-W 1,2; DCL 1,8; DCL-F 3,2; DCL-N 3,8. Post-hoc con corrección Holm-Bonferroni contra DCL-W: DCL p = 0,4624 (sin diferencia), DCL-F p = 0,0143, DCL-N p = 0,0015. Conclusión: los pesos dinámicos son lo esencial; el filtrado a veces ayuda (ISBSG2000) y a veces estorba, sin diferencia significativa global. Figura 4: aun así hay tramos donde DCL-N le gana a DCL (ISBSG alrededor de los pasos 37–45), que son oportunidades para mejorar el mecanismo.

### 8. Comparación con métodos existentes (RQ2)
Métodos: **RT** (árbol reentrenado en cada paso con todos los proyectos propios acumulados: el baseline WC), **CC-RT** (árbol con CC + WC juntos), **Relevancy Filtering** (RF, k = 10, 30 corridas) y **CC-RF**, **DWM** (ensamble dinámico de la literatura: agrega learner cuando el error supera 0,25·y, borra cuando el peso cae bajo 0,01) y **CC-DWM** (preentrenado en CC). Se excluye Nasa60Coc81Nasa93 por el solapamiento.

**Tabla 5 – MAE global:**

| Dataset | DCL | RT | CC-RT | RF | CC-RF | DWM | CC-DWM |
|---|---|---|---|---|---|---|---|
| ISBSG2000 | 2352,59 ± 925,84 | 2753,37 ± 1257,46 | 3271,01 ± 1887,27 | 2665,66 ± 1045,36 | 3092,01 ± 1345,41 | 3022,11 ± 1185,23 | 2906,75 ± 1076,84 |
| ISBSG2001 | 2873,11 ± 1235,93 | 3621,96 ± 1367,96 | 3417,17 ± 2070,06 | 3644,82 ± 1364,35 | 3630,93 ± 1403,04 | 3400,30 ± 1001,87 | 3336,35 ± 960,28 |
| ISBSG | 2805,56 ± 1468,20 | 3253,93 ± 2476,05 | 5244,59 ± 4047,20 | 3383,12 ± 2387,59 | 4484,34 ± 3060,12 | 3805,19 ± 2449,27 | 3812,13 ± 2457,67 |
| Nasa60Coc81 | 205,83 ± 214,70 | 319,46 ± 250,23 | 578,98 ± 665,27 | 325,40 ± 262,94 | 851,61 ± 1705,34 | 319,54 ± 303,82 | 384,04 ± 331,00 |

SA (%) en el mismo orden: DCL 46,21 / 30,14 / 53,69 / 56,92; RT 37,05 / 11,93 / 46,29 / 33,14; CC-RT 25,21 / 16,91 / 13,43 / **−21,18**; CC-RF 29,30 / 11,71 / 25,98 / **−78,24** (negativo = peor que adivinar). Δ contra random guess de DCL: 3,21 / 2,43 / 1,55 / 0,97, todos "grandes".

Friedman: F_F = 6,46 > 2,66, p = 0,0009. Rankings (Tabla 6): DCL 1,00 (primero en los 4 datasets); RT 3,00; DWM 3,75; RF 4,00; CC-DWM 4,00; CC-RT 6,00; CC-RF 6,25. Wilcoxon DCL vs RT por dataset: p = 0,0015; 0,0139; < 0,0001; 0,0074. Robustez a horizonte: pronosticando 3, 5 y 15 proyectos en vez de 10, DCL gana siempre en conteo; Wilcoxon global p = 0,00044. Figura 5: hay tramos de ~20 pasos donde DCL le gana claramente a RT, que en tiempo calendario son meses o años de estimaciones peores; DCL es peor que RT en los primeros ~15 pasos de ISBSG2001. Figura 6: tamaño de efecto en ventana deslizante (ancho 33/39/43/32 pasos), con períodos de Δ > 0,8 a favor de DCL en todos los datasets y también períodos negativos. Lección práctica: se puede usar datos ajenos para paliar la falta de datos propios.

### 9. Robustez al tipo de modelo base
Cinco base learners: k-NN con k = 1 (EBA), RT, bagging de 50 RT, perceptrón multicapa (9 nodos ocultos, 100 épocas) y RBF. Wilcoxon sobre los 20 pares (5 learners × 4 datasets): suma de rangos 196 vs 14, p = 0,00068 a favor de DCL sobre el WC correspondiente; excepciones: RBF en ISBSG2001 y EBA en Nasa60Coc81. Los tres mejores por dataset siempre son variantes DCL (Tabla 7; p. ej. ISBSG2000: DCL+MLP 2262,83, DCL+Bag 2293,03, DCL+RT 2352,59). Friedman entre combinaciones: p = 0,0288; rankings (Tabla 8): DCL+RT 2,0; DCL+Bag+RT 2,2; DCL+MLP 2,6; DCL+EBA 3,6; DCL+RBF 4,6. Recomendación: árboles o bagging de árboles.

### 10–12. Sensibilidad de parámetros, amenazas a la validez, conclusiones
Sección 10 (leída parcialmente): ANOVA factorial sobre β_w, β_c, Q y T_start con todas sus interacciones (Tabla 9); los cuatro factores y sus interacciones aparecen listados como significativos, o sea que el rendimiento depende de la combinación, no de un parámetro aislado. Los valores concretos de la grilla y la conclusión final de la sección no llegaron; el mensaje que sí queda claro del resto del paper es que los defaults sin tuneo alcanzan para los resultados reportados. **Secciones 11 y 12: no verificadas** (no se pudieron leer; no se inventa su contenido).

## Los números que hay que recordar
- DCL es el mejor en los 4 datasets contra 6 alternativas; ranking promedio 1,00 vs 3,00 del baseline WC (Tabla 6, Sección 8).
- MAE DCL vs RT: 2352,59 vs 2753,37 (ISBSG2000); 205,83 vs 319,46 (Nasa60Coc81) (Tabla 5).
- Ablación: pesos dinámicos son lo esencial; DCL vs DCL-W p = 0,4624; DCL-N (promedio simple) es lo peor, p = 0,0015 (Tabla 4, Sección 7).
- Defaults: β = 0,5, T_start = 15 proyectos, Q = 0,9; horizonte de evaluación = próximos 10 proyectos (Secciones 3 y 5).
- Usar CC "crudo" mezclado con WC puede ser peor que adivinar: SA = −21,18 (CC-RT) y −78,24 (CC-RF) en Nasa60Coc81 (Tabla 5).
- DCL rinde peor que RT en los primeros ~15 pasos de ISBSG2001 y hay retraso de adaptación en cambios bruscos (Figura 5, Tabla 2).

## Limitaciones
**Declaradas (en las secciones leídas):** retraso en enfatizar el modelo correcto ante cambios abruptos; el filtrado no siempre ayuda; el dataset ISBSG completo admite CC del futuro y Nasa60Coc81Nasa93 tiene solapamiento (ambos declarados y acotados); la cronología de Nasa60 es simulada; datos con imputación.
**Las nuestras:** es estimación puntual de esfuerzo (MAE), no pronóstico probabilístico: no hay intervalos, ni calibración, ni CRPS; los "modelos CC" son particiones por productividad de datos ajenos, un artificio de laboratorio; la unidad es proyecto de meses, no tarea de horas; el WC es una empresa; con 4 datasets el Friedman tiene poco poder; y la Sección 11 no se pudo leer, así que sus propias amenazas a la validez quedan pendientes.

## Qué tomamos tal cual y qué hacemos distinto
**Tomamos:** (a) el protocolo de evaluación online: un ítem por vez, orden cronológico, entrenar solo con lo que existía, pronosticar los siguientes k; es nuestro backtesting de origen móvil y la crítica a los splits aleatorios es la cita para la regla anti-leakage; (b) la idea central para OE5(b): no descartar la historia vieja sino ponderarla por su desempeño reciente, y el hallazgo de que un promedio ingenuo de todo (DCL-N) es lo peor; (c) la disciplina metodológica: ablación, defaults sin tunear, Friedman + post-hoc, tamaño de efecto además de p-valor, y mirar el desempeño a lo largo del tiempo y no solo el promedio global; (d) el uso de un horizonte fijo de evaluación (próximos 10) como plantilla para definir nuestro horizonte por origen.
**Hacemos distinto:** nosotros pronosticamos distribuciones y evaluamos cobertura, PIT y CRPS, así que la analogía con "peso por acierto puntual" habría que traducirla a puntaje probabilístico si algún día se implementa. **DCL como tal no está en el alcance comprometido**: implementarlo sería un método nuevo con su justificación y su ablación; para R1–R5 lo usamos como respaldo bibliográfico de que "cuánta historia usar" es una pregunta legítima y de cómo diseñar OE5(b) (comparar ventanas de historia con el mismo protocolo). Si se quisiera un ensamble ponderado por desempeño reciente para R6–R8, hay que decir qué sale a cambio. Nuestros "modelos del pasado" serían versiones anteriores del proceso de agentes (misma organización, distinta época), no otras empresas, lo cual de hecho es un caso más limpio que el de ISBSG.

## Si igual lo vas a abrir
Leé la Sección 3 (Algoritmo 1, con la Figura 1), la 4 (datasets y Tabla 1), la 7 (Tabla 3) y la 8 (Tablas 5 y 6, Figuras 5 y 6). La Sección 6 con la Tabla 2 vale por la explicación del retraso de adaptación. Podés saltear la 9 (base learners) y la 10 (ANOVA) salvo que vayas a implementar. Y si tenés el PDF, leé la 11 y la 12, que acá no llegaron.

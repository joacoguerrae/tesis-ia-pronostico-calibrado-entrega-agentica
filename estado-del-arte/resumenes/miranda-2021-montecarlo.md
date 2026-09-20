# Miranda, P., Faria, J. P., Correia, F. F., Fares, A., Graça, R. & Mendes Moreira, J. (2021). An Analysis of Monte Carlo Simulations for Forecasting Software Projects. Proceedings of the 36th Annual ACM Symposium on Applied Computing (SAC '21), 1550–1558. DOI 10.1145/3412841.3442030

**Estado de lectura:** leído completo desde el PDF en `tesis/bibliografia/` (9 páginas; es una impresión sin capa de texto, se leyó por OCR). Código de los autores: `github.com/pmiranda07/Promessa`.
**Tipo:** artículo revisado por pares (ACM SAC) · **Datos:** reales; Jira autoalojado de Fraunhofer Portugal, 71 proyectos, >12.000 historias, 2013–2020 · **Objeto:** trabajo humano, unidad = historia de usuario
**Tiempo de lectura del original:** ~40 min · **Tiempo de lectura de este resumen:** ~8 min

## En una frase
Aplican el Monte Carlo más simple posible —remuestrear tiempos históricos entre cierres de historias y sumarlos— para pronosticar fecha de entrega y esfuerzo en proyectos ágiles, obtienen 32% de error en fechas y 20% en esfuerzo contra 134% de los desarrolladores, y descubren de paso que usar demasiada historia empeora el pronóstico.

## Por qué está en nuestra lista (qué decisión del proyecto toca)
Por una razón distinta de la que figuraba en nuestra primera lectura desde el abstract: **este paper no es el precedente del motor de Rootstrap, es el precedente publicado de nuestro baseline 1 (conteo puro)**. Bootstrap de duraciones históricas sin categorías, sin grafo de dependencias y sin aprendizaje es exactamente el "todas las tareas son intercambiables", y ahora tiene DOI, datos reales y código público. Además emite intervalos al 95% y nunca mide su cobertura — y sus propias tablas permiten calcularla. Ese chequeo es la primera fila de nuestro boletín de calibración.

## Resumen sección por sección

### 1. Introducción
Los desarrolladores no estiman bien y eso afecta a toda la empresa. Hay resultados alentadores con Monte Carlo en la práctica, pero la técnica no está muy difundida en la industria y **cuesta encontrar trabajos académicos que estudien su aplicabilidad**; falta evidencia práctica de su exactitud. Dos objetivos: ver si Monte Carlo logra pronósticos exactos con poco esfuerzo del equipo, y entender cómo varía la exactitud con la cantidad de historia usada y con el horizonte pronosticado.

### 2. Trabajo relacionado
Adoptan la distinción de Keogh: una **estimación** es un valor único; un **pronóstico** es una predicción probabilística (un rango de valores o un valor con nivel de confianza asociado), y por su naturaleza probabilística suele ser más exacto y confiable. Definen dos métricas de flujo: **takt time** (el período entre la finalización de cada ítem; en manufactura, el ritmo de la línea) y **throughput** (cantidad de ítems completados en una ventana).

Las métricas de error que usan: RE = (Actual − Estimado)/Actual, MRE = |RE|, y **MMRE** = media de los MRE.

La Tabla 1 compara nueve métodos por tipo, facilidad de recolección de inputs, exactitud reportada, comprensibilidad y aplicabilidad en ágil: COCOMO, SLIM, Wideband Delphi, Planning Poker, Angel, **Monte Carlo**, SEER-SEM, SVM y redes bayesianas. Concluyen que los más prometedores son los métodos de machine learning y Monte Carlo, porque comparten facilidad de recolección de inputs, buena exactitud y aplicabilidad en ágil, y son inmunes a sesgos humanos por ser data-driven — **con la ventaja adicional para Monte Carlo de ser interpretable**, cosa que los de ML no siempre son.

### 3. El método
**3.1 El núcleo.** Y acá está lo importante para nosotros, por lo simple que es: una función recibe los datos históricos y la cantidad de historias a pronosticar; **selecciona al azar unos cuantos valores de esa historia y los suma** para simular el valor de todas las historias; repite; ordena el conjunto de valores resultante y **excluye los extremos según un intervalo de confianza (usan 95%)**. Devuelve media, mediana, optimista (límite inferior) y pesimista (superior). **La mediana es el pronóstico; el intervalo de confianza lo definen los valores optimista y pesimista.**

No hay categorías. No hay dependencias. No hay aprendizaje. Es bootstrap puro.

**3.2 Takt time.** La fecha final D se calcula sumando los M pronósticos, usando como insumo los N takt times históricos: los períodos entre las fechas de finalización de historias consecutivas, o sea el tiempo en que no se completó ninguna historia. Con eso se pronostica cuánto va a tardar un conjunto de historias.

**3.3 Esfuerzo.** Más complicado, porque el dataset no tenía el esfuerzo real. Lo reconstruyen: para cada historia, se cuentan las horas entre que pasó a "In Progress" y a "Done"; en cada hora se mira cuántas historias tenía asignadas ese desarrollador en paralelo, y el esfuerzo de esa hora se reparte dividiendo 1 por esa cantidad. **Supuestos explícitos: los desarrolladores trabajan 8 horas por día y reparten su tiempo en partes iguales entre las historias en curso.** No consideran días no laborables.

### 4. Salidas
Dos tipos: para una historia sola, un print con el pronóstico puntual y el intervalo (ejemplos del paper: "Point Forecast: 2:36:27, Interval Forecast: [0:06:19 – 1 día 21:32:09]"); para un conjunto, un gráfico con la historia (línea verde), el pronóstico mediano (azul) y las curvas optimista y pesimista, más las fechas de los sprints.

### 5. Evaluación

**5.1 Dataset.** Jira autoalojado de Fraunhofer Portugal, extraído por la API REST y anonimizado: **71 proyectos, ~120 usuarios, >12.000 historias, ~135.000 cambios de estado registrados en el changelog, ~150 sprints, 2013–2020**. Dieron preferencia a proyectos de 2018–2020 por ser más representativos del presente.

**5.2 Fecha de entrega.** **Toman el 50% de las historias de cada proyecto como entrenamiento y el 50% siguiente para validar.** Un solo corte, un solo origen. Repiten sobre **10 proyectos** (Tabla 2), reportando historia disponible, pronóstico, intervalo al 95%, entrega real y MMRE, todo en días restantes hasta la entrega:

| Historia | Pronóstico | Intervalo 95% | Entrega real | MMRE |
|---|---|---|---|---|
| 116 | 48,8 | [39,4 – 56,4] | 57,4 | 39% |
| 49 | 27,5 | [22,8 – 38,4] | 22,4 | 29% |
| 221 | 213,5 | [193,7 – 230,1] | 204,4 | 20% |
| 86 | 35,4 | [27,8 – 42,5] | 33,1 | 27% |
| 129 | 43,5 | [33,1 – 51,1] | 48,9 | 37% |
| 101 | 34,5 | [26,5 – 43,5] | 37,9 | 26% |
| 141 | 96,8 | [82,4 – 110,4] | 89,5 | 43% |
| 8 | 7,2 | [3,5 – 10,4] | 6,5 | 21% |
| 17 | 32,5 | [25,1 – 39,8] | 29,6 | 35% |
| 114 | 88,1 | [76,7 – 99,2] | 92,4 | 38% |

Promedio: **MMRE 32%**, rango 20%–43%. **Y el número que ellos no calculan: de los 10 intervalos al 95%, el valor real cayó adentro en 8.** (Se sale en la fila 1: 57,4 > 56,4; y en la fila 2: 22,4 < 22,8.)

**5.3 Cuánta historia y cuánto horizonte.** Barren todos los proyectos variando la cantidad de historias usadas como historia (5 a 70) y la cantidad a pronosticar. Hallazgos (Figura 7): con 5 o 10 historias el error es notoriamente mayor — en proyectos de menos de 15 historias el modelo es claramente menos exacto. **Y usar 60, 65 o 70 historias también aumenta el error**, cosa que atribuyen a "más ruido en el modelo". El óptimo en este contexto es **45 historias de historia para pronosticar 60**. Hay una mejora marcada al pronosticar 20 historias o más, y esperan que el error vuelva a subir con horizontes muy largos por acumulación de error o por cambios en el contexto del proyecto (composición del equipo, experiencia con tecnologías).

**5.4 Esfuerzo.** Sobre los **5 proyectos** que tenían estimaciones de los desarrolladores para todas las historias (Tabla 3):

| Historia | Pronóstico | Intervalo 95% | Esfuerzo real (aprox.) | Estimación del dev | MMRE modelo | MMRE dev |
|---|---|---|---|---|---|---|
| 101 | 306 h | [287 – 369] | 378 h | 1.100 h | 20% | 191% |
| 16 | 71 h | [55 – 94] | 68 h | 129 h | 11% | 89% |
| 12 | 95 h | [83 – 103] | 59 h | 87 h | 31% | 48% |
| 17 | 81 h | [70 – 93] | 87 h | 237 h | 12% | 172% |
| 14 | 69 h | [54 – 85] | 65 h | 177 h | 27% | 172% |

Media: **MMRE 20% del modelo contra 134% de los desarrolladores**. De estos 5 intervalos, el real cayó adentro en **3** (se sale en la fila 1: 378 > 369; y en la fila 3: 59 < 83).

**5.5 Limitaciones (las de ellos).** Un solo dataset y una sola organización, y les gustaría más proyectos de entornos empresariales distintos. No tenían tamaño de historia, experiencia del desarrollador ni tipo de proyecto, variables que hipotetizan importantes. Los supuestos del cálculo de esfuerzo (8 h/día, reparto parejo, solo el asignado trabaja en la historia) pueden no reflejar la realidad, y como el esfuerzo "real" se calcula con los mismos supuestos, **eso podría explicar la sobreestimación de los usuarios**. **MMRE es asimétrica** (las subestimaciones no pueden pasar de 100% y las sobreestimaciones no tienen límite) y problemática ante compensación de errores, y lo declaran citando a Shepperd et al. Los pronósticos a más de ~100 historias se degradan. Y no compararon contra otros métodos de la literatura.

### 6. Conclusiones
Monte Carlo sirve en la práctica para pronóstico de entrega y esfuerzo en proyectos ágiles después de unos sprints iniciales. Proponen como trabajo futuro un método de machine learning, y cierran diciendo que **este estudio sirve como baseline para evaluar otros métodos**, y que takt time y esfuerzo son dos buenas features de partida.

## Los números que hay que recordar
- **MMRE 32% en fecha de entrega sobre 10 proyectos** (rango 20%–43%), sin comparación humana (Tabla 2).
- **MMRE 20% en esfuerzo sobre 5 proyectos contra 134% de las estimaciones de los desarrolladores** (Tabla 3). **Ojo: son dos experimentos distintos; el "32% contra 134%" que circula mezcla los dos.**
- **De los 15 intervalos al 95% de las Tablas 2 y 3, el real cayó adentro en 11 (73%).** Número calculado por nosotros; ellos no lo reportan.
- El error mejora con **≥20 historias** de historia y **empeora con 60–70**; el óptimo es 45 para pronosticar 60 (Figura 7).
- Dataset: 71 proyectos, >12.000 historias, ~135.000 cambios de estado, 2013–2020 (Sección 5.1).
- Partición: **50% entrenamiento / 50% test por proyecto, un solo corte** (Secciones 5.2 y 5.4).

## Limitaciones
**Declaradas:** las de la Sección 5.5, arriba; son honestas y explícitas, incluida la crítica a su propia métrica.
**Nuestras:**
1. **La degradación con 60–70 historias la atribuyen a "más ruido", pero la explicación mucho más plausible es no estacionariedad:** la historia vieja describe un equipo y un proceso que ya cambiaron. Es evidencia a favor de la premisa de OE5(b), producida por un paper que no la reconoció como tal.
2. **El "45 es el óptimo" se eligió mirando el error sobre todos los proyectos**, o sea que ese hiperparámetro está ajustado en test.
3. Un solo corte 50/50 por proyecto **no es backtesting**: no hay origen móvil, así que no se ve cómo degrada el pronóstico con el tiempo.
4. Emiten intervalos y **no evalúan su cobertura**: la palabra calibración no aparece.
5. El takt time en proyectos con varios desarrolladores mezcla ritmo de entrega con paralelismo, y no lo discuten.
6. Llaman "confidence interval" a lo que es un intervalo de predicción (la distinción está en Jørgensen & Sjøberg 2003).

## Qué tomamos tal cual y qué hacemos distinto
**Tomamos:**
- **Es nuestro baseline 1, con pedigrí.** El bootstrap de duraciones históricas sin condicionar en nada es el conteo puro, y ahora tenemos DOI, datos reales, código público y un número de referencia (MMRE ≈32% en fechas) contra el cual dialogar. Que exista publicado hace mucho más difícil que alguien diga que el baseline es un hombre de paja.
- La unidad de análisis coincide (ítem de trabajo, no proyecto).
- **El barrido "cuánta historia × cuánto horizonte" de la Figura 7 es un experimento barato que conviene replicar tal cual** sobre nuestros datos: es OE5(b) en embrión, y tenerlo hecho en la misma forma que un paper publicado facilita la comparación.
- Hay que reportar una métrica puntual comparable (MMRE, aunque sea junto a algo mejor como MdAE o residuos absolutos) para poder dialogar con este número.

**Hacemos distinto, y son exactamente los tres diferenciales de la tesis:**
1. **Medir la cobertura de los intervalos que ellos emiten y no evalúan.** Sus propias tablas dan 11 de 15 para un 95% nominal. Con n = 15 no es concluyente, pero va en la dirección clásica: intervalos demasiado angostos. Ese chequeo es la primera fila de nuestro boletín.
2. **Origen móvil** en vez de un corte 50/50, y la elección de la ventana de historia hecha **fuera** de test.
3. Lo que el motor agrega por encima de esto —categorías, dependencias, aprendizaje— es exactamente lo que el torneo tiene que justificar. Si no le gana a este método, hay que decirlo.
- Detalle de vocabulario para la memoria: a sus intervalos llamarlos "de predicción", no "de confianza".

## Si igual lo vas a abrir
Leé la Sección 3.1 (el algoritmo, media página, es todo lo que hay), las Tablas 2 y 3 con sus columnas de intervalo, y la Figura 7 con su texto (Sección 5.3), que es la parte más original. La Sección 5.5 (limitaciones) es corta y honesta. Podés saltear la Sección 2 (Tabla 1 comparativa de métodos, útil solo si necesitás una tabla de panorama) y la Sección 4 (formatos de salida). El PDF es escaneado, así que no se puede buscar texto: ubicá las tablas por número de página.

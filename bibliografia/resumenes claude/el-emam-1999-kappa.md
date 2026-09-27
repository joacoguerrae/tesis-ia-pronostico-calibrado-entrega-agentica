# El Emam, K. (1999). Benchmarking Kappa: Interrater agreement in software process assessments. Empirical Software Engineering, 4(2), 113–133. DOI 10.1023/A:1009820201126
**Estado de lectura:** leído completo desde https://www.ehealthinformation.ca/web/default/files/wp-files/isern-98-02.pdf. Aclaración: lo leído es el reporte técnico ISERN-98-02 ("Benchmarking Kappa for Software Process Assessment Reliability Studies", Fraunhofer IESE, 14 páginas), versión previa del artículo de Empirical Software Engineering. Los números de página y la numeración de tablas corresponden al reporte, no a la revista; la versión publicada puede tener diferencias menores.
**Tipo:** estudio empírico metodológico (construcción de un benchmark normativo) · **Datos:** 70 instancias de proceso de los SPICE Trials (ISO/IEC 15504), 19 proyectos, 7 organizaciones europeas · **Objeto:** trabajo humano (evaluadores de procesos) / método general
**Tiempo de lectura del original:** ~30 min · **Tiempo de lectura de este resumen:** ~7 min

## En una frase
Como las escalas de interpretación de kappa que todos usan (Landis & Koch, Fleiss, Altman) vienen de medicina y ciencias sociales, El Emam construye una escala propia para evaluaciones de procesos de software a partir de los cuartiles de 70 valores reales de kappa, y propone: < 0,45 pobre, 0,45–0,62 moderado, 0,63–0,78 sustancial, > 0,78 excelente.

## Por qué está en nuestra lista (qué decisión del proyecto toca)
Toca de lleno OE5(a), el estudio de acuerdo entre etiquetadores que clasifican tareas ex ante en 5 tiers × 2 tamaños. Cuando reportemos un kappa vamos a tener que decir si es "bueno", y este paper es el antecedente de ingeniería de software para hacerlo, además de una advertencia: los umbrales de Landis & Koch son arbitrarios y de otro dominio, y el propio El Emam dice que el benchmark correcto depende de qué valores son alcanzables en la práctica en tu contexto. También nos sirve como modelo de diseño del estudio (grupos independientes, misma evidencia, sin discusión previa, consenso después) y como aviso de que el kappa simple trata las categorías como no ordenadas, cosa que para nuestros tiers ordinales no alcanza.

## Resumen sección por sección

### 1. Introducción (p. 2)
Las evaluaciones de proceso (SPICE / ISO/IEC 15504, CMM) producen puntajes que se usan para tomar decisiones de mejora y de selección de proveedores, así que importa que sean confiables. La confiabilidad que interesa acá es el **acuerdo entre evaluadores** (interrater agreement): cuánto coinciden evaluadores independientes al calificar las mismas prácticas. Los estudios previos usaban el kappa de Cohen y lo interpretaban con el benchmark de Landis & Koch, que no está basado en experiencia acumulada en ingeniería de software. El argumento: si en medicina "alta confiabilidad" es kappa > 0,8 pero casi ninguna evaluación de proceso llega a eso, el umbral es demasiado exigente en nuestro contexto; y también podría pasar lo contrario. Objetivo: un benchmark propio con datos de los SPICE Trials.

### 2. Background (p. 4–8)
**2.1 Esquema de calificación de ISO/IEC 15504.** Dos dimensiones: procesos (con sus prácticas base) y prácticas genéricas agrupadas en features comunes y niveles de capacidad. Cada práctica genérica de cada instancia de proceso (una ejecución concreta e identificable de un proceso, típicamente un proyecto) se califica en una escala de 4 puntos: **N** (no adecuada), **P** (parcialmente adecuada), **L** (en gran medida adecuada), **F** (totalmente adecuada). Los datos de un estudio de acuerdo se representan en una tabla de contingencia 4×4: filas = calificación del equipo 1, columnas = calificación del equipo 2, y en cada celda cuántas prácticas cayeron en esa combinación.

**2.2 Kappa.** Kappa mide el acuerdo observado descontando el que se esperaría por puro azar: κ = (P_o − P_e) / (1 − P_e), donde P_o es la proporción de calificaciones en las que los dos equipos coinciden (suma de la diagonal) y P_e es la proporción de coincidencias que habría si cada equipo calificara al azar respetando su propia frecuencia de uso de cada categoría (suma, por categoría, del producto de los marginales). κ = 1 es acuerdo total, 0 es lo que da el azar, negativo es peor que el azar (el mínimo depende de los marginales). Se usa el kappa de Cohen para dos calificadores, y las categorías se tratan como **nominales**, o sea sin orden: para el kappa simple, calificar N cuando el otro puso P es exactamente tan grave como calificar N cuando el otro puso F. El Emam menciona el kappa ponderado (que castiga menos los desacuerdos "cercanos") y lo descarta explícitamente porque no existe un esquema de pesos satisfactorio para 15504; lo deja para el futuro. No explica cómo se calculó kappa en el estudio con tres evaluadores.

**2.3 Benchmarks existentes.** Transcriptos tal cual:

Landis & Koch (1977) — los propios autores admiten que es arbitrario:

| Kappa | Fuerza del acuerdo |
|---|---|
| < 0,00 | Pobre |
| 0,00–0,20 | Leve |
| 0,21–0,40 | Regular |
| 0,41–0,60 | Moderado |
| 0,61–0,80 | Sustancial |
| 0,81–1,00 | Casi perfecto |

Altman (1991):

| Kappa | Fuerza del acuerdo |
|---|---|
| < 0,20 | Pobre |
| 0,21–0,40 | Regular |
| 0,41–0,60 | Moderado |
| 0,61–0,80 | Bueno |
| 0,81–1,00 | Muy bueno |

Fleiss (1981):

| Kappa | Fuerza del acuerdo |
|---|---|
| < 0,40 | Pobre |
| 0,40–0,75 | Intermedio a bueno |
| > 0,75 | Excelente |

**2.4 Cómo construir un benchmark.** Dos filosofías: *referenciado a criterio* (un umbral fijo con base teórica o económica: "por encima de X la decisión es suficientemente segura") y *referenciado a norma* (comparar tu valor con una muestra de referencia: "estás en el cuarto superior de lo que se ha logrado"). Como no hay base para un umbral absoluto de kappa, elige la norma. Usa percentiles 25, 50 y 75 (un percentil es el valor por debajo del cual cae ese porcentaje de la muestra): fácil de entender y sin asumir ninguna forma de distribución. El mismo enfoque ya se había usado para benchmarks de eficiencia de inspecciones.

### 3. Fuentes de datos (p. 9–10)
Cuatro estudios de acuerdo dentro de los SPICE Trials, todos con las mismas guías (Tabla 5 del reporte): el equipo evaluador se divide en k ≥ 2 grupos independientes; todos cumplen requisitos mínimos de competencia; todos ven exactamente la misma evidencia (mismas entrevistas, mismos documentos); si falta evidencia se recolecta y la ven todos; cada grupo califica la misma instancia de proceso por separado, sin discutir antes; después se juntan para armonizar un consenso. En tres estudios k = 2 con un evaluador por grupo; en uno k = 3, también con un evaluador por grupo. Total: 19 proyectos, 7 organizaciones europeas, 75 instancias de proceso. Se descartan 4 por datos "mal distribuidos" (todas las calificaciones en una sola celda, lo que hace que kappa no se pueda calcular) y 1 por ser un outlier causado por un sesgo extremo de uno de los evaluadores. Quedan **70** valores de kappa, uno por instancia de proceso (cada uno sale de la tabla 4×4 que junta todas las prácticas calificadas en esa instancia; el reporte no dice cuántas prácticas por instancia).

### 4. Resultados (p. 10–12)
La Figura 3 es un diagrama de caja de los 70 kappas, sin valores numéricos rotulados (no reporta media, desvío, mínimo ni máximo). El Emam explica la dispersión por diferencias entre procesos (algunos son más difíciles de calificar), por la capacidad del proceso (los de mayor capacidad se califican de manera más consistente) y por "un sinfín de otros factores".

**Cuartiles de los 70 kappas:**

| Percentil | Kappa |
|---|---|
| 25 (Q1) | 0,44 |
| 50 (mediana) | 0,62 |
| 75 (Q3) | 0,78 |

**Tabla 6 – Benchmark propuesto para evaluaciones de proceso de software:**

| Kappa | Fuerza del acuerdo |
|---|---|
| < 0,45 | Pobre (25% inferior) |
| 0,45–0,62 | Moderado (50% inferior) |
| 0,63–0,78 | Sustancial (50% superior) |
| > 0,78 | Excelente (25% superior) |

El corte en 0,45 en vez de 0,44 no se justifica en el texto; es redondeo de los bordes para que los rangos no se solapen. Guía de uso: una evaluación por debajo de 0,45 es "del peor tipo", indicio de que el método de evaluación falla y de que evaluadores y patrocinador deberían cambiarlo; una evaluación debería apuntar a al menos 0,63 (la mitad superior); las más confiables están en 0,79 o más. Comparación: el benchmark se parece mucho al de Fleiss (pobre < 0,40, excelente > 0,75) y es algo más exigente que Landis & Koch en el escalón "sustancial".

### 5. Conclusiones (p. 12)
Saltar de disciplina con un benchmark es cuestionable a priori; este reemplaza esa importación por datos propios de los SPICE Trials y permite decir si una evaluación nueva es buena o mala *comparada con las anteriores*. Queda para el futuro un benchmark distinto, basado en el impacto de la confiabilidad sobre las decisiones que se toman con los puntajes. La intención es revisar el benchmark a medida que los Trials acumulen datos.

## Los números que hay que recordar
- 70 kappas válidos de 75 instancias (4 descartadas por datos mal distribuidos, 1 outlier); 19 proyectos, 7 organizaciones (Sección 3).
- Cuartiles: 0,44 / 0,62 / 0,78 (Sección 4).
- Benchmark: < 0,45 pobre; 0,45–0,62 moderado; 0,63–0,78 sustancial; > 0,78 excelente (Tabla 6).
- Objetivo práctico: al menos 0,63 (mitad superior); "excelente" desde 0,79 (Sección 4).
- Landis & Koch: 0,41–0,60 moderado, 0,61–0,80 sustancial, > 0,80 casi perfecto; Fleiss: < 0,40 pobre, > 0,75 excelente (Sección 2.3).
- Escala de 4 categorías (N/P/L/F) tratada como nominal; kappa ponderado explícitamente fuera del alcance (Sección 2.2).

## Limitaciones
**Declaradas:** el benchmark representa solo lo logrado en los SPICE Trials hasta ese momento, no "todas las evaluaciones"; como se construyó con un evaluador por grupo, es un benchmark pesimista para equipos de dos o más personas (que deberían ser más consistentes), lo cual el autor presenta como ventaja porque lo hace bueno para detectar evaluaciones malas; no cubre kappa ponderado; se revisará con más datos.
**Las nuestras, y esta es la importante:** **el paper no cubre kappa ponderado ni ordinal.** La escala N/P/L/F es claramente ordinal y aun así el kappa se calcula como nominal; por lo tanto los cuartiles y los umbrales de la Tabla 6 valen para kappa de Cohen no ponderado, con 4 categorías, dos calificadores, en tablas 4×4. No son transferibles a un kappa ponderado cuadrático, a un kappa de Fleiss multi-calificador ni a otras cantidades de categorías (con 10 clases el azar coincide menos y kappa tiende a subir). No hay estadísticos descriptivos completos, no se discute el efecto de los marginales desbalanceados (la "paradoja de kappa": con prevalencias muy desiguales el acuerdo observado puede ser alto y kappa bajo), y no se dice cuántas prácticas entran en cada tabla, así que no sabemos la precisión de cada uno de los 70 valores. La muestra es 1998, un dominio (evaluación de procesos) y una región (Europa).

## Qué tomamos tal cual y qué hacemos distinto
**Tomamos:** (a) el argumento de que los umbrales de Landis & Koch son arbitrarios e importados, así que en OE5(a) vamos a reportar el kappa sin venderlo como "sustancial" por caer en 0,61–0,80, y citaremos ambas escalas dejando claro que ninguna es un criterio absoluto; (b) el diseño del estudio de acuerdo: misma información para cada etiquetador (la descripción de la tarea tal como existía ex ante, sin nada del resultado, para no meter leakage en la clasificación), calificación independiente sin hablar antes, consenso después; (c) la lógica normativa: si acumulamos varios kappas (por proyecto, por dimensión tier y tamaño), reportar su distribución en cuartiles es más informativo que un único número contra un umbral; (d) la práctica de excluir y explicar casos donde kappa no se puede calcular (todas las etiquetas en una celda), que con 100–300 tareas y 10 clases nos puede pasar en clases raras.
**Hacemos distinto:** nuestros tiers son ordinales, así que el kappa simple castiga igual confundir tier 2 con tier 3 que con tier 5, lo cual no refleja el daño real sobre los priors. Vamos a necesitar una medida que respete el orden (kappa ponderado con pesos lineales o cuadráticos, o alpha de Krippendorff ordinal), y para esa medida **este paper no da benchmark**; hay que buscarlo en otra referencia o presentarlo como comparación descriptiva sin escala de adjetivos. Además conviene separar el análisis en las dos dimensiones (5 tiers ordinal; 2 tamaños binario) en vez de una sola de 10 clases, porque el kappa de 10 categorías nominales no es comparable con nada de este paper. Todo esto es ya parte de OE5(a) y no suma alcance; lo que sí sumaría alcance sería construir nuestro propio benchmark normativo estilo El Emam con muchos kappas, y no lo vamos a hacer con tres etiquetadores y un puñado de proyectos. Y ojo con la unidad: acá cada kappa sale de un proceso con muchas prácticas calificadas; nosotros tenemos una tabla por par de etiquetadores con todas las tareas, o sea un kappa por par y por dimensión, no 70.

## Si igual lo vas a abrir
Mirá la Sección 2.2 (fórmula y la aclaración sobre kappa ponderado, dos párrafos), la Tabla 5 (guías del estudio de acuerdo, copiable como protocolo) y la Tabla 6 con el párrafo de interpretación. Los benchmarks de 2.3 están arriba transcriptos. La Figura 3 no aporta números. Podés saltear la 2.1 (arquitectura de 15504) salvo que necesites entender qué es una "instancia de proceso".

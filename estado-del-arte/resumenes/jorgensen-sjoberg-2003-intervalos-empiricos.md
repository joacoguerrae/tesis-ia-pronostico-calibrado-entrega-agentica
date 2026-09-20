# Jørgensen, M. & Sjøberg, D. I. K. (2003). An Effort Prediction Interval Approach Based on the Empirical Distribution of Previous Estimation Accuracy. Information and Software Technology, 45(3), 123–136. DOI 10.1016/S0950-5849(02)00188-X

**Estado de lectura:** leído completo desde el PDF en `tesis/bibliografia/SE.4.Joergensen.2003.b.pdf` (versión Simula, 18 páginas con apéndices).
**Tipo:** artículo revisado por pares; propuesta de método + dos evaluaciones empíricas · **Datos:** reales; 145 tareas de mantenimiento (dataset de Kitchenham, Pfleeger et al. 2002) + experimento con 13 profesionales sobre 15 tareas · **Objeto:** trabajo humano, unidad = **tarea**
**Tiempo de lectura del original:** ~60 min · **Tiempo de lectura de este resumen:** ~9 min

## En una frase
Proponen construir intervalos de predicción de esfuerzo tomando percentiles de la distribución empírica del error de estimación pasado, muestran sobre 145 tareas que es el método con mejor correspondencia entre confianza declarada y aciertos, y en un experimento encuentran que los intervalos que los profesionales declaran al 90% aciertan el **68%**.

## Por qué está en nuestra lista (qué decisión del proyecto toca)
Es **nuestro baseline 2** ("priors por categoría sin aprendizaje"), publicado, citable y de cinco líneas de código. La unidad de análisis coincide con la nuestra (tarea, no proyecto). Y da la cifra de sobreconfianza humana que usamos para justificar por qué el baseline de estimación humana no alcanza. Además —y esto es un regalo— los autores declaran como limitación propia justo el error metodológico que nosotros corregimos: usaron validación cruzada en vez del orden temporal real.

## Resumen sección por sección

### 1. Introducción
Un intervalo de predicción (PI) de esfuerzo es un mínimo, un máximo y un nivel de confianza. Empiezan distinguiendo algo que se confunde todo el tiempo: **un intervalo de predicción se refiere a la incertidumbre de una estimación; un intervalo de confianza se refiere a la incertidumbre de los parámetros de un modelo**. En una nota al pie fulminan un paper previo (Angelis & Stamelos 2000) por haber comparado el intervalo de confianza de la media de un modelo de regresión contra el intervalo de predicción de un método de analogía, y aclaran que al reanalizar los datos los dos rinden parecido.

Revisan lo poco que hay: bootstrap, regresión, y reglas de dedo como la de la NASA SEL, que transcribo porque es una tabla linda para citar:

| Punto de estimación | Intervalo de predicción |
|---|---|
| Fin de definición y especificación de requisitos | [Est/2,0 ; Est×2,0] |
| Fin de análisis de requisitos | [Est/1,75 ; Est×1,75] |
| Fin de diseño preliminar | [Est/1,40 ; Est×1,40] |
| Fin de diseño detallado | [Est/1,25 ; Est×1,25] |
| Fin de implementación | [Est/1,10 ; Est×1,10] |
| Fin de pruebas de sistema | [Est/1,05 ; Est×1,05] |

Su diagnóstico: el bootstrap y la regresión son difíciles de entender para practicantes; las reglas de dedo no se adaptan a la organización. Falta algo simple que se ajuste a los datos propios.

### 2. El método, paso a paso
Cuatro pasos: (1) elegir una medida de exactitud que permita separar sesgo de dispersión; (2) encontrar un conjunto de proyectos con **la misma incertidumbre esperada** que el proyecto a estimar; (3) mirar la distribución de exactitud de esos proyectos y decidir cómo calcular el PI; (4) fijar el nivel de confianza y calcular.

**2.1 La medida: BRE (Balanced Relative Error).**

```
BRE = (Act − Est) / Act    si Act ≤ Est     (sobreestimaste)
BRE = (Act − Est) / Est    si Act >  Est     (subestimaste)
```

O sea: **el denominador es el menor de los dos**. Positivo si subestimaste. ¿Por qué no MRE (= |Act−Est|/Act)? Porque MRE no permite separar sesgo de dispersión, y porque es asimétrica: **por más que subestimes, el MRE' no puede pasar de 1, mientras que las sobreestimaciones no tienen límite**. Con BRE, estimar tres veces de más y tres veces de menos dan la misma desviación desde cero (−2 y +2). La media del BRE se interpreta como el **sesgo**; su desvío estándar, como la **dispersión**.

Advierten de un problema que a nosotros nos aplica de lleno: cuando la especificación es vaga, **hasta una estimación mala se vuelve exacta porque funciona como objetivo** ("self-fulfilling"); en ese caso la exactitud medida no mide incertidumbre sino flexibilidad del producto.

**2.2 Selección de proyectos.** Acá está la idea fina y es fácil de pasar por alto: hay que agrupar por **expectativa de exactitud similar**, no por parecido en tamaño o tipo. Y lo dicen explícito: *las variables importantes para la incertidumbre de una estimación pueden ser distintas de las importantes para calcularla*.

**2.3 y 2.4 Cálculo.** Dos variantes.
- *Paramétrica:* si los BRE son normales, `μ ± t(1−conf, n−1)·σ·√(1 + 1/n)`. Con el dataset de 145 tareas (σ = 0,51, μ = −0,10, t = 1,655) da un intervalo BRE de **[−0,94; 0,74]** al 90%. Si no se puede asumir normalidad, usan Chebyshev; y si además la distribución es unimodal y simétrica, la cota mejora a `1 − 1/(2,25k²)`, con lo cual ±2 desvíos cubren al menos 89%.
- *Empírica:* se ordenan los BRE y se toman los percentiles (1−conf)/2 y (1+conf)/2. Para 90%: percentil 5 y percentil 95. Sobre las mismas 145 tareas da **[−0,76; 0,51]**, más angosto que el paramétrico.

Después se mapea de vuelta a horas con la reformulación del BRE:

```
Act = Est / (1 − BRE)   si BRE ≤ 0
Act = Est × (1 + BRE)   si BRE > 0
```

**Ejemplo del paper:** Est = 100 horas, BRE_min = −0,5, BRE_max = 1,5 → PI = **[67; 250] horas**. El intervalo queda **asimétrico alrededor del punto**, que es la propiedad deseable, y refleja el sesgo histórico.

Una consecuencia que discuten y que vale la pena tener presente: si el sesgo histórico es fuerte, **la estimación puntual puede quedar fuera de su propio intervalo**. Cuando eso pasa hay que decidir si el sesgo sigue vigente; si no, se ajusta la media del BRE a 0. Esa posibilidad de ajuste manual del sesgo la presentan como ventaja sobre los métodos más sofisticados: sin ella, uno asume que la organización nunca aprendió de sus errores.

**3.1 Métricas de evaluación.** **HitRate** = proporción de casos donde el real cae dentro del PI. **PIWidth** = (máximo − mínimo) / estimación puntual; reportan la **mediana**, no la media, para que unos pocos intervalos gigantes no dominen.

### 3.2 Aplicabilidad sobre 145 tareas
Parten el dataset en 4 clusters cruzando método de estimación (juicio experto vs herramientas/procesos estructurados) × tamaño (chico < 260 puntos función):

| Cluster | Método | Tamaño | N | Media BRE | Desvío BRE | Media MRE |
|---|---|---|---|---|---|---|
| 1 | Juicio experto | Chico | 56 | −0,13 | 0,44 | 0,27 |
| 2 | Juicio experto | Grande | 49 | −0,07 | 0,63 | 0,25 |
| 3 | Herramientas/proceso | Chico | 16 | −0,21 | 0,32 | 0,30 |
| 4 | Herramientas/proceso | Grande | 24 | 0,00 | 0,47 | 0,21 |

Observación que hacen y que nos sirve: **el MRE medio es parecido en los cuatro clusters, pero las razones del error son distintas** — los chicos se sobreestiman sistemáticamente (sesgo), los grandes tienen más componente aleatoria (dispersión). Eso es justo lo que el BRE permite ver y el MRE no.

Resultados (Tabla 3), con validación cruzada dentro del cluster:

| Enfoque | Confianza teórica | HitRate | PIWidth mediana | Veredicto de ellos |
|---|---|---|---|---|
| PARAM 1 (normal) | 60% | 81% | 0,59 | PIs inexactos |
| PARAM 1 | 90% | 94% | 1,09 | PIs exactos |
| PARAM 2 (Chebyshev) | >56% | 85% | 0,68 | Cota OK |
| PARAM 2 | >89% | 94% | 1,27 | Cota OK |
| **EMP (empírico)** | **60%** | **58%** | **0,30** | Muy exactos |
| **EMP** | **90%** | **85%** | **0,82** | Exactos |

EMP es el único con cobertura cerca de la nominal y con intervalos mucho más angostos. Explican por qué PARAM 1 falla: tres de los cuatro clusters tienen distribuciones de BRE mucho más picudas que la normal (cluster 2: curtosis 21; cluster 4: curtosis 0,3), y efectivamente el cluster 2 da 88% de cobertura al 60% nominal mientras el 4 da 67% (Tabla 4).

### 3.3 Experimento contra juicio humano y regresión
13 profesionales (media 4,6 años de experiencia, 6 con experiencia como líderes de proyecto) estimaron 10 tareas reales de otra organización, con **feedback del esfuerzo real después de cada una**, y a mitad de camino se les recordó explícitamente que 9 de cada 10 intervalos al 90% deberían contener el real. Usaron en promedio 43 minutos, unos 4–5 por tarea. Se evalúa sobre las tareas 11–15.

| Enfoque | Confianza | HitRate medio | PIWidth mediana | MRE mediana |
|---|---|---|---|---|
| Juicio humano (HJ) | 90% | **68%** | 1,3 | 0,50 |
| EMP sobre estimaciones HJ | 90% | 82% | 2,8 | 0,50 |
| EMP sobre HJ | 73% | 68% | 1,7 | 0,50 |
| Regresión pura (PURE-REG) | 90% | 80% | **6,0** | 0,31 |
| EMP sobre estimaciones de regresión | 90% | 80% | 1,6 | 0,31 |

Tres lecturas que ellos destacan: (a) pese al entrenamiento y al feedback, la sobreconfianza persiste (68% para un 90% declarado); (b) a igualdad de cobertura (68%), el humano usa la información de incertidumbre **más eficientemente** que EMP (ancho 1,3 vs 1,7); (c) la regresión pura produce intervalos absurdos — PIWidth 6,0 significa que para una estimación de 100 horas el intervalo es [17; 600] — y el híbrido EMP-REG logra la misma cobertura con ancho 1,6, casi cuatro veces más angosto.

En 3.3.2 dan las razones de la sobreconfianza: dificultad de interpretar qué significa 90% sin datos históricos; agendas ocultas (querer parecer competente); **los jefes prefieren intervalos angostos porque les simplifica la planificación**; y la estimación puntual actúa como ancla. Reportan además cifras de un trabajo previo (Jørgensen, Teigen et al. 2002): **35% de hit rate en proyectos industriales** (sin nivel de confianza declarado) y 62% al 90% en proyectos de estudiantes.

En 3.3.3 explican por qué la regresión falla con n chico: los intervalos de regresión asumen error insesgado, homocedástico, independiente y normal; con pocos datos y un modelo flojo, un solo error grande ensancha todo. Dan un caso concreto: para la tarea 14, el modelo de regresión sugirió un mínimo que implicaba una productividad **cinco veces mayor que la máxima observada**.

### 4. Conclusiones
El trade-off central es entre **exactitud** (correspondencia confianza–cobertura) y **eficiencia** (usar bien la información de incertidumbre). Los profesionales son eficientes pero sobreconfiados; los métodos formales, lo contrario. Su apuesta: entrenar a los profesionales en el método EMP.

## Los números que hay que recordar
- **68% de cobertura para intervalos declarados al 90%** por 13 profesionales, con entrenamiento y feedback (Tabla 5). La cifra del baseline humano.
- Sobre 145 tareas: EMP da **85% al 90% nominal con PIWidth 0,82**, contra 94% y 1,09 del paramétrico (Tabla 3).
- El ejemplo canónico del método: Est = 100 h, BRE [−0,5; 1,5] → PI **[67; 250] h**, asimétrico (Sección 2.4).
- Regresión pura: **PIWidth 6,0** (o sea [17; 600] para una estimación de 100 h) contra 1,6 del híbrido (Tabla 5).
- Clusters de 16 y 24 tareas: los percentiles 5 y 95 salen de ahí (Tabla 2).
- Trabajo previo citado: **35% de hit rate en proyectos industriales** (Jørgensen, Teigen et al. 2002) — **ojo, es otra referencia, no este paper ni el de 2004**.

## Limitaciones
**Declaradas:** muestra de conveniencia, y por eso **no hacen tests de significancia y lo dicen**; la regresión se evaluó sobre 5 puntos; los participantes no conocían las aplicaciones ni a los desarrolladores; el problema de las estimaciones auto-cumplidas; y la más importante para nosotros: **usaron cross-validation dentro del cluster en vez de la secuencia temporal real, y admiten que lo correcto habría sido usar el orden real, pero no tenían esa información**.
**Nuestras:** con clusters de 16 y 24 tareas, estimar el percentil 5 es esencialmente reportar el mínimo observado. Asumen que la distribución del error no cambia con el tiempo: no hay ventanas, ni ponderación por recencia, ni detección de drift. Y todo el método depende de que **exista una estimación puntual previa** como ancla.

## Qué tomamos tal cual y qué hacemos distinto
**Tomamos:** el método es nuestro baseline 2, y con respaldo publicado — agrupar por categoría, distribución empírica del error, percentiles, aplicar a la estimación puntual. Eso lo blinda de la crítica de que el baseline es un hombre de paja. La unidad de análisis (tarea) coincide. **PIWidth = (max−min)/Est reportado como mediana** es una métrica de sharpness normalizada, barata y muy fácil de explicar en la defensa: buen complemento legible al CRPS. La forma de reportar —tabla de (método × nivel de confianza) → (hit rate, ancho mediano)— es casi nuestra tabla de cobertura. Y el BRE merece considerarse: si medimos error relativo de duración, evita el sesgo del MRE que premia sobreestimar.

**Hacemos distinto:**
1. **El leakage que ellos declaran como limitación, nosotros lo resolvemos.** Backtesting de origen móvil en lugar de cross-validation. Es una mejora metodológica explícita sobre una referencia publicada y conviene escribirla así en la memoria: es un argumento fuerte y gratis.
2. Hit rate + ancho no distingue un modelo bien calibrado de uno que compensa errores en distintas partes de la distribución. Por eso agregamos PIT y CRPS.
3. Con celdas chicas hay que evitar los cuantiles extremos (o suavizar, o hacer bootstrap, o encoger hacia el pool global) — que es exactamente el argumento del pooling parcial.
4. **Ojo con una dependencia:** EMP necesita una estimación puntual previa. Si la telemetría de Rootstrap no trae una estimación por tarea, hay que anclarlo a la mediana del propio modelo, y ahí deja de ser un baseline limpio "sin aprendizaje". **Esto es una pregunta concreta para el export.**
5. La advertencia de las estimaciones auto-cumplidas aplica fuerte: vale la pena chequear en la telemetría si las duraciones se agolpan alrededor de los valores estimados.

## Si igual lo vas a abrir
Leé la Sección 2 entera (son 5 páginas y contienen el método completo, con las fórmulas F1 y F6 que hay que implementar), la Tabla 2 (los clusters), la Tabla 3 y la Tabla 5. La Sección 3.3.2 (por qué la gente es sobreconfiada) es corta y muy citable. Podés saltear 3.3.3 (teoría de intervalos de regresión) salvo que quieras usar regresión, y los apéndices con los datos de las 15 tareas.

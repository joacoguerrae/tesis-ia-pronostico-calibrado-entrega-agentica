# Sigweni, B., Shepperd, M. & Turchi, T. (2016). Realistic Assessment of Software Effort Estimation Models. Proceedings of EASE 2016 (20th International Conference on Evaluation and Assessment in Software Engineering), Limerick. DOI 10.1145/2915970.2916005

**Estado de lectura:** leído completo desde el PDF en `tesis/bibliografia/Sigweni, Shepperd & Turchi (2016), EASE.pdf` (6 páginas).
**Tipo:** artículo corto revisado por pares; experimento metodológico · **Datos:** reales; Desharnais (77 proyectos) y Finnish (406 proyectos), 477 predicciones por técnica · **Objeto:** trabajo humano, unidad = proyecto
**Tiempo de lectura del original:** ~25 min · **Tiempo de lectura de este resumen:** ~6 min

## En una frase
Comparan la validación cruzada leave-one-out contra una validación cronológica que hace crecer el conjunto de entrenamiento proyecto a proyecto, sobre los mismos datos y los mismos modelos, y muestran que la cronológica da errores entre 14% y 48% más altos — o sea que la validación tradicional es **sistemáticamente optimista** — y que en un dataset llega a cambiar qué modelo parece mejor.

## Por qué está en nuestra lista (qué decisión del proyecto toca)
Es **la** cita para justificar el backtesting de origen móvil dentro de ingeniería de software empírica, con números y p-valores, sin tener que ir a la literatura de forecasting general. Justifica OE3 y la regla anti-leakage del proyecto. Y trae de regalo un experimento barato y replicable que podemos hacer nosotros: correr las dos validaciones y publicar la brecha.

## Resumen sección por sección

### 1. Introducción
El problema: la práctica habitual de evaluar modelos de estimación de esfuerzo usa todos los datos con alguna estrategia de holdout, y eso choca con la realidad de un dataset que **crece a medida que los proyectos terminan**. Repasan los dos esquemas dominantes: **k-fold** (los datos se parten al azar en k pliegues, cada uno se reserva por turno) y **LOOCV** (caso especial con k = n, o sea un pliegue por caso; es determinista, y por eso lo eligen como representante). Y proponen el nombre del esquema realista: **GOAT** (*grow one at a time*), donde el conjunto de entrenamiento crece con el tiempo y el siguiente proyecto es el caso de test.

Lo dicen sin vueltas: es evidente que ninguno de los dos esquemas tradicionales aproxima bien la situación real.

### 2. Trabajo relacionado
Repasan a Kohavi (sesgo y varianza en k-fold vs bootstrap) e Isaksson et al. (LOOCV es poco confiable con muestras chicas, porque el solapamiento entre entrenamiento y test hace perder independencia). Marcan que esos trabajos son sobre clasificadores, mientras que el problema de estimación de esfuerzo es de predicción de valores reales, y que los proyectos empiezan y terminan en momentos distintos, así que **conviene pensar los datos como una pseudo-serie temporal**.

En la literatura de costos de software: Lefley & Shepperd y Sentas et al. ordenaron los datos cronológicamente pero no estudiaron si eso cambiaba los resultados. Lokan & Mendes se hicieron la pregunta y **concluyeron que no hacía diferencia**. MacDonell & Shepperd sí encontraron diferencias significativas entre LOOCV y GOAT, pero con solo 16 proyectos. O sea: la evidencia previa está dividida, y por eso vale revisitarla.

### 3. Diseño experimental
Diseño factorial 2×3: esquema de validación × técnica de ponderación de features. Un detalle metodológico que vale la pena copiar: usaron **protocolo de análisis ciego** — los experimentos los corrió BS, los resultados crudos los cegó TT y los analizó MS, para limitar el sesgo de análisis.

- **Esquemas:** LOOCV y GOAT.
- **Técnicas** (tres variantes de estimación por analogía en la herramienta archANGEL): **CBR** (todos los features pesan igual, el baseline), **FSS** (pesos binarios 0 o 1, selección de features) y **FSW** (pesos continuos no negativos). Aclaran que la elección es arbitraria: no les interesa cuál es mejor, solo necesitan vehículos para comparar los dos esquemas de validación.
- **Métrica:** **residuos absolutos**. Descartan MMRE explícitamente por el comportamiento asimétrico de cualquier z-score, citando a Kitchenham et al. y a Shepperd & MacDonell.

**Datasets (Tabla 1):**

| Dataset | Casos | Features | Esfuerzo mín. | máx. | media | mediana |
|---|---|---|---|---|---|---|
| Desharnais | 77 | 9 | 546 | 23.940 | 5.046,31 | 3.542 |
| Finnish | 406 | 44 | 55 | 63.694 | 5.031,00 | 2.500 |

Desharnais: 81 proyectos originales de casas de software canadienses en 3 entornos, menos 4 con valores faltantes. Finnish: 408 de la consultora STTF Ltd., menos 2 con esfuerzo cero (<1% del total). No removieron outliers en ninguno.

**Cómo arman GOAT.** Ordenan cronológicamente por fecha de finalización: Desharnais ya trae el campo `YearFin`; para Finnish tuvieron que sumar la duración en meses a `DATESTART` y construir un campo `EndDate` usado **solo para ordenar**, no como feature. Los empates de fecha se ordenaron al azar. Después: se toman los primeros 4 casos (ventana de 3 más el objetivo), se predice el cuarto; cuando termina, entra a la base y se predice el quinto; y así. Salen **74 bases de casos en Desharnais y 403 en Finnish: 477 predicciones** por técnica.

Descartan explícitamente las ventanas móviles con un argumento que conviene citar: **las consideran una técnica de modelado (elegir no usar todos los datos disponibles), no un método de validación.**

### 4. Resultados

**Tabla 2 — Desharnais:**

| Esquema | Media residuo abs. | Desvío | Mediana |
|---|---|---|---|
| GOAT | 2.455,8 | 2.912,3 | 1.576,4 |
| LOOCV | 2.159,7 | 2.547,8 | 1.357,2 |

**Tabla 3 — Finnish:**

| Esquema | Media residuo abs. | Desvío | Mediana |
|---|---|---|---|
| GOAT | 3.919,9 | 6.388,2 | 1.923,3 |
| LOOCV | 2.646,1 | 4.174,8 | 1.359,4 |

Calculando sobre esos números: en Desharnais la validación cronológica da **13,7% más de error medio y 16,1% más de mediana**; en Finnish, **48,1% y 41,5%**. Y en los dos casos **la varianza también crece con GOAT**, lo que sugiere que el desempeño real es menos estable de lo que implica LOOCV.

**Tabla 4 — ANOVA robusto de dos vías de Wilcox** (recorte 0,2 de las medias, con bootstrap; diseño within-within, o sea medidas repetidas):

| Factor | Dataset | p |
|---|---|---|
| Esquema de validación | Desharnais | 0,047 |
| Técnica de ponderación | Desharnais | ≈0 |
| Interacción | Desharnais | 0,666 |
| Esquema de validación | Finnish | ≈0 |
| Técnica de ponderación | Finnish | ≈0 |
| **Interacción** | **Finnish** | **0,046** |

El dato decisivo es la interacción significativa en Finnish: **el esquema de validación puede cambiar el ranking entre modelos, no solo el nivel de error.** En Desharnais no aparece, así que el propio paper concluye que "a veces pasa y a veces no".

### 5. Discusión y conclusiones
La respuesta a sus dos preguntas es sí: el esquema afecta las comparaciones, y las diferencias **no son simétricas** — LOOCV está sesgado respecto de GOAT y hace que los predictores parezcan más efectivos en el laboratorio que en el campo. Sus resultados coinciden con MacDonell & Shepperd y contradicen a Lokan & Mendes, y de ahí sacan el argumento que más me gusta del paper: **si a veces importa y a veces no, y no se puede saber a priori cuándo, la única respuesta racional es usar siempre el enfoque temporal.**

Cierran con una frase que vale para nosotros: si el objetivo es investigación con impacto en la práctica profesional, hacen falta razones convincentes para **no** tratar los datos como una serie temporal.

Trabajo futuro que ellos mismos listan: extender a k-fold, replicar con otros datasets y modelos, y **asegurar que un proyecto objetivo solo use datos disponibles al momento de su comienzo**.

## Los números que hay que recordar
- **Desharnais: GOAT 2.455,8 vs LOOCV 2.159,7 de media (13,7% más); medianas 1.576,4 vs 1.357,2 (16,1% más)** (Tabla 2).
- **Finnish: GOAT 3.919,9 vs LOOCV 2.646,1 (48,1% más); medianas 1.923,3 vs 1.359,4 (41,5% más)** (Tabla 3).
- Significancia del esquema: **p = 0,047 (Desharnais), p ≈ 0 (Finnish)**; interacción esquema × técnica **p = 0,046 en Finnish** (Tabla 4).
- 477 predicciones por técnica (74 bases en Desharnais + 403 en Finnish); ventana inicial de 3 casos (Sección 3.5).
- La varianza crece con GOAT en los dos datasets (desvíos 2.912 vs 2.548 y 6.388 vs 4.175).

## Limitaciones
**Declaradas:** solo dos datasets y tres modelos; comparan contra LOOCV y no contra k-fold en general; no implementaron ventanas móviles porque las consideran modelado y no validación.
**Nuestras:** la más importante es que **GOAT ordena por fecha de finalización**, así que un proyecto entra al entrenamiento cuando termina — pero el pronóstico del objetivo se hace conceptualmente al inicio, y entre medio el conocimiento disponible cambió. Es leakage residual, y los propios autores lo listan como trabajo futuro. Además: rompen los empates de fecha al azar sin reportar sensibilidad a la semilla; la ventana inicial de 3 casos es arbitraria y no justificada; y el `EndDate` de Finnish está reconstruido sumando duración a la fecha de inicio, o sea que el orden cronológico es aproximado.

## Qué tomamos tal cual y qué hacemos distinto
**Tomamos:**
1. Es la cita para el backtesting de origen móvil **dentro del dominio**. No hace falta apoyarse solo en la literatura de forecasting general: existe evidencia en ingeniería de software empírica, con p-valores.
2. **El diseño es copiable casi gratis:** mismo dato, mismos modelos, dos esquemas de validación, y reportar la brecha. Los modelos ya van a estar construidos; correr una vez una validación aleatoria junto al backtest móvil y **publicar la diferencia** es honesto, barato, y es un candidato a resultado publicable aun si el modelo probabilístico no le gana a los baselines.
3. El rechazo de MMRE por asimetría y el uso de residuos absolutos, para el componente puntual de nuestra evaluación.
4. El protocolo de análisis ciego (quien corre no es quien analiza) — con tres personas en el equipo, es factible y nos blinda contra el sesgo de análisis en R4.

**Hacemos distinto:**
1. Su unidad es el proyecto; la nuestra es la tarea. Eso nos da más observaciones, pero introduce **dependencia jerárquica** (tareas anidadas en proyectos) que ellos no enfrentan: el corte del backtest tiene que ser por **tiempo**, no por proyecto, o tareas hermanas se filtran entre sí.
2. Ellos evalúan estimación **puntual** con residuos absolutos; nosotros evaluamos **distribuciones** con PIT, cobertura y CRPS. Traducida a nuestro marco, la brecha LOOCV-vs-cronológico se vuelve una **brecha de calibración**: la hipótesis natural es que la validación aleatoria no solo baje el error puntual sino que haga parecer los intervalos mejor calibrados de lo que están. **Ese sería un resultado nuevo y nuestro.**
3. Corregimos el leakage residual que ellos dejan abierto: el corte es el **momento del pronóstico** (cuando la tarea entra al backlog o arranca), no el de finalización, y una tarea entra al entrenamiento solo cuando su desenlace ya era observable en ese momento. Es más estricto que GOAT y es defendible **citándolos a ellos**, porque lo listan como su propio trabajo futuro.
4. Su distinción "ventana móvil es modelado, no validación" nos ordena el alcance: OE5(b) es una pregunta de **modelado**, separada del diseño de evaluación. Conviene mantener esa separación en la memoria.

## Si igual lo vas a abrir
Son 6 páginas, se lee entero en 25 minutos. Si querés ir al grano: Sección 3.5 (cómo construyen GOAT, con la Figura 1) y las Tablas 2, 3 y 4. La Sección 5 es una página y es la que da los argumentos citables. Podés saltear la 3.2 (las tres técnicas de ponderación, que los propios autores dicen que son arbitrarias).

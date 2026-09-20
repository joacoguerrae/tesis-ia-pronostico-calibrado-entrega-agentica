# Jørgensen, M., Welde, M. & Halkjelsvik, T. (2023). Evaluation of Probabilistic Project Cost Estimates. IEEE Transactions on Engineering Management, 70(10), 3481–3496. DOI 10.1109/TEM.2021.3067050
**Estado de lectura:** leído completo desde https://www.ntnu.no/documents/1261860271/1262022437/Evaluation+of+Probabilistic+Project+Cost+Estimates.pdf/fe7703af-c96a-55bd-55a1-6885121fd7ca?t=1636128630571 (versión aceptada, 16 páginas; volumen/número/páginas verificados en Crossref: online 2021, en volumen 2023). Aclaración: la lectura fue por extractor en bloques; los números aparecieron consistentes en pasadas independientes, pero la numeración exacta de las tablas IV y V puede ser una reconstrucción — están marcadas.
**Tipo:** artículo metodológico (guías de evaluación) + estudio empírico retrospectivo, revisado por pares · **Datos:** 69 proyectos públicos noruegos grandes (>≈75 M EUR) con estimaciones probabilísticas de costo en la etapa QA2 y costo final real · **Objeto:** trabajo humano / método general de evaluación
**Tiempo de lectura del original:** ~50 min · **Tiempo de lectura de este resumen:** ~8 min

## En una frase
Si no definís qué punto de la distribución es tu "estimación" y no usás una métrica que se minimice justo en ese punto, la evaluación castiga a los buenos estimadores; y para intervalos y distribuciones no alcanza con calibración: hay que medir también si los intervalos distinguen entre proyectos más y menos inciertos.

## Por qué está en nuestra lista (qué decisión del proyecto toca)
Es el precedente metodológico más cercano a nuestro boletín de calibración: evalúa estimaciones probabilísticas reales con **hit rate, PIT con histograma, ancho relativo de intervalo y CRPS**, la misma batería que declaramos en OE3. Toca tres decisiones: (1) qué cuantiles pedirle al modelo y con qué pérdida evaluarlos (P50 con error absoluto o log-error; cuantiles altos por cobertura/pinball, nunca por MAPE); (2) el diseño del baseline "conteo puro": el paper construye exactamente ese contrafáctico —un estimador que aplica la misma incertidumbre global a todos los casos— y muestra que **puede ganar en calibración y CRPS sin ser informativo**; (3) cómo reportar: calibración e informatividad por separado, y sesgo por período, no solo agregado.

## Resumen sección por sección

### I. Introducción
El problema de partida: la literatura de sobrecostos usa "estimación" sin decir si es la moda, la mediana o la media de una distribución, y después mide con "alguna" métrica. Citan la idea de Gneiting de que pedir un punto sin especificar cuál y luego puntuarlo con una función cualquiera no tiene sentido. Proponen un marco probabilístico: la estimación se define como un punto de la distribución (PX = percentil X, con X% de probabilidad de que el costo real quede por debajo), un intervalo (PIX = intervalo de dos lados que contiene el real con X% de probabilidad) o la distribución completa.

### II. Guías para evaluar estimaciones
**II.A Marco probabilístico.** La Fig. 1 muestra una lognormal hipotética con moda ≈21, mediana (P50) ≈27, media ≈31 y P85 ≈62 M EUR, para ilustrar que en distribuciones asimétricas esos puntos difieren mucho.

**II.B Estimaciones puntuales.** Criterio de "match": la función de pérdida implícita en la métrica debe minimizarse cuando la estimación es exactamente el punto pedido. (Una función de pérdida es la regla que dice cuánto "duele" cada error; cada métrica de error promedio implica una.) Tabla I (error, sin signo): error absoluto medio y mediano → matchean con la media; error absoluto en logaritmo, medio o mediano → matchean con P50. Tabla II (sesgo, con signo): error medio y error relativo medio → media; log-error medio, error relativo mediano, log-error mediano → P50. Resultado contraintuitivo (nota 4 / apéndice): el error relativo absoluto medio (MARE) para una lognormal como la de la Fig. 1 se minimiza en el percentil 69,1, más alto que la media, así que **premia estimaciones infladas**. Y si evaluás P50 perfectos con el error relativo medio, aparece un "sobrecosto" espurio de ≈13% que es puro artefacto de la métrica.

**II.C Intervalos y distribuciones.** Dos dimensiones: calibración (la proporción de reales que caen dentro coincide con la probabilidad declarada) e informatividad (los intervalos varían entre proyectos y esa variación refleja la incertidumbre real). El argumento se arma con tres estimadores de P85 que salen igual de calibrados: A conoce el riesgo de cada proyecto y ajusta la contingencia caso a caso; B ("orientado a la incertidumbre global") multiplica todos los P50 por un factor fijo (≈1,3 en el ejemplo); C hace lo mismo pero agregando ruido aleatorio al factor. Los tres muestran 85% de cobertura; solo A es informativo. Tabla III: medidas de calibración — hit rate (cobertura), PIT (para cada proyecto, en qué percentil de la distribución estimada cayó el costo real; si la distribución es correcta, esos valores se reparten uniforme entre 0 y 1) e histograma PIT; de informatividad — ancho relativo (ancho del intervalo dividido por la estimación puntual) y correlación entre ancho relativo y error absoluto; y CRPS como medida combinada (un score que mide la distancia entre toda la distribución pronosticada y el valor real; menor es mejor).

### III. Aplicación: proyectos públicos noruegos
**III.A Proyectos.** 69 proyectos (35 rutas, 8 ferrocarril, 14 edificios, 7 sistemas de información, 5 compras) sometidos al esquema de aseguramiento de calidad QA2 (Fig. 2), externo, de ≈6,5 meses de duración, antes de la aprobación parlamentaria y antes de licitar. Estimaciones P10/P50/P85/P90/media obtenidas por juicio experto (mín/probable/máx por ítem) agregadas por Monte Carlo. Unos 7% de los proyectos se cancelaron tras QA2 (posible sesgo de supervivencia favorable). Promedio de 7 años entre estimación y cierre, por lo que indexaron costos con índices sectoriales: ≈27% de aumento medio (≈3% anual); sin indexar, los "sobrecostos" serían mucho mayores y no interpretables.

**III.B Error y sesgo del P50.** Se evalúa solo el P50 (el P85 como punto exigiría una pérdida que pena 5,7 veces más el sobrecosto que el subcosto: 0,85/0,15). Log-error medio absoluto = 15%; la Fig. 3 muestra que P50 perfectos con una distribución donde el 67% de los reales cae entre 80% y 120% de la estimación ya producen ese 15%, o sea que el error refleja incertidumbre, no incompetencia. Error relativo mediano = 4%, log-error mediano = 4%, no distinguible de cero (test de Wilcoxon de rangos con signo, p = 0,52; test no paramétrico de si la mediana de las diferencias es cero). Benchmarks de la literatura: 21% de sobrecosto mediano y 20–45% en estudios tipo Flyvbjerg. Fig. 4: cola más larga hacia subcostos; error absoluto medio 18% en subcostos vs 12% en sobrecostos; máximo sobrecosto 37% (31% en log). Fig. 5 y 6: por período de inicio, 2001–03 subcosto medio 16%, 2010–12 sobrecosto 8%, intermedio ≈0 — **el sesgo agregado bajo esconde sesgos opuestos que se cancelan.**

**III.C Calibración e informatividad.** Tabla (reconstruida como "Tabla V"):

| Medida | Estimaciones reales | Estimador hipotético "global" |
|---|---|---|
| Hit rate P10 (esperado 10%) | 19% | 13% |
| Hit rate P50 (esperado 50%) | 42% (p = 0,23) | 48% |
| Hit rate P85 (esperado 85%) | 75% | 90% |
| Hit rate P90 (esperado 90%) | 80% | 93% |
| Correlación ancho relativo vs. \|log-error\| | −0,02 | 0 (por construcción) |
| Ancho relativo medio del PI80 | 0,29 | 0,49 |
| Contingencia media P50→P85 | 13% | 26% |
| CRPS mediano | 109 | 88 (p < 0,001) |

Fig. 7 (histograma PIT): exceso en ambos extremos → distribuciones demasiado angostas. Fig. 8 (dispersión ancho relativo vs. error absoluto con suavizado): nube plana, correlación −0,02: los intervalos no distinguen proyectos más inciertos. El estimador hipotético ajusta una sola distribución del log-error a todos los proyectos (≈ normal con media 0,05 y desvío 0,20) y la aplica idéntica: **gana en cobertura y en CRPS, pero necesita el doble de contingencia y es inútil para priorizar proyectos riesgosos.**

### IV. Implicancias y limitaciones
Recomiendan: log-error absoluto medio para precisión de P50 y error relativo mediano para sesgo; para otros percentiles, evaluar solo por calibración/informatividad; reportar tendencias temporales; reportar calibración e informatividad por separado y no un combinado con pesos ocultos. Limitaciones declaradas: no dicen cómo producir estimaciones; evitan funciones de pérdida "verdaderas" porque son difíciles de formalizar; el marco es difícil de entender para practicantes (anécdota de un CEO que leyó un 100% de cobertura del P85 como buena gestión, cuando indica sobreestimación sistemática).

### V. Conclusión y Apéndice
Reafirman el criterio de match y la dupla calibración + informatividad. El apéndice deriva que el error medio se minimiza con la media, el error relativo medio también con la media, y el error relativo mediano con la mediana.

## Los números que hay que recordar
- 69 proyectos; 42% de cobertura del P50 (esperado 50%, p = 0,23) y 75% del P85 (esperado 85%) — Sección III.C.
- Correlación −0,02 entre ancho relativo del intervalo y error absoluto: intervalos no informativos — Fig. 8.
- El estimador "una sola distribución para todos" mejora CRPS mediano de 109 a 88 (p < 0,001) y cobertura P85 de 75% a 90%, pero duplica la contingencia (13% → 26%) — III.C.
- MARE se minimiza en el percentil 69,1 de una lognormal (μ = 3,3, σ = 0,5); evaluar P50 con error relativo medio genera ≈13% de sobrecosto espurio — nota 4 / apéndice.
- Sesgo mediano 4% (p = 0,52) que oculta −16% en 2001–03 y +8% en 2010–12 — Fig. 5.

## Limitaciones
**Declaradas:** proyectos comparables, misma etapa de estimación, alcance estable, solo proyectos terminados; ≈7% de cancelaciones post-QA2 (supervivencia); indexación necesaria.
**Nuestras:** (1) n = 69 y ningún test formal de uniformidad del PIT ni bandas — el histograma se interpreta "a ojo"; (2) CRPS calculado ajustando lognormales a P50/P90/media, o sea que evalúa una distribución reconstruida, no la del estimador; (3) las 69 observaciones son cuasi-independientes (proyectos distintos), no una serie con origen móvil como la nuestra; (4) no tratan datos discretos ni átomos; (5) es costo de infraestructura, no duración de software.

## Qué tomamos tal cual y qué hacemos distinto
**Tomamos:** el criterio de match (nuestro P50 se evalúa con error absoluto o log-error absoluto, nunca con MAPE/MRE); reportar cobertura por cuantil + PIT + una medida de informatividad (correlación ancho-vs-error, o ancho medio) por separado del CRPS; el contrafáctico "estimador global" como baseline explícito — es literalmente nuestro baseline de conteo puro, y el paper anticipa el resultado: puede empatar o ganar en CRPS siendo inútil para distinguir tareas. **Eso legitima que un empate sea hallazgo**, y nos da la métrica para desempatar: la correlación entre ancho y error. La lección de tendencia temporal (Fig. 5) la traducimos a reportar calibración por ventana de backtest.
**Hacemos distinto:** unidad = tarea y horizonte corto (días/horas), con duraciones enteras y átomos → PIT no-randomizado (Czado et al.) en vez de PIT clásico; origen móvil con PIT correlacionados → tests con varianza robusta (Knüppel) o bandas conjuntas (Rossi–Sekhposyan) en lugar del histograma sin bandas; comparaciones con Diebold–Mariano sobre diferenciales de CRPS/pinball; y la "estimación humana" entra como tercer comparador con la misma batería. Ojo con la cita: Crossref lo lista en el volumen 70(10) de 2023 con DOI de 2021; citar 2023.

## Si igual lo vas a abrir
Sección II.C.1 (los tres estimadores) y III.C.1 (el hipotético) son el corazón; Tablas I–III para copiar el vocabulario; Fig. 7 y 8; nota al pie 4 y el apéndice para la matemática del match. Saltear III.A (contexto noruego) salvo el detalle de la indexación.

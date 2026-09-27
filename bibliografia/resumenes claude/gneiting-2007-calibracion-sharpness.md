# Gneiting, T., Balabdaoui, F. & Raftery, A. E. (2007). Probabilistic forecasts, calibration and sharpness. Journal of the Royal Statistical Society: Series B, 69(2), 243–268. DOI 10.1111/j.1467-9868.2007.00587.x

**Estado de lectura:** leído completo desde el PDF en `tesis/bibliografia/Gneiting2007jrssb.pdf` (26 páginas; recibido mayo 2005, revisión final octubre 2006).
**Tipo:** artículo teórico-metodológico revisado por pares, con estudio de simulación y caso real · **Datos:** simulación con T = 10.000; caso real con 5.136 pronósticos de velocidad de viento · **Objeto:** método general, sin dominio
**Tiempo de lectura del original:** ~2 h (denso) · **Tiempo de lectura de este resumen:** ~10 min

## En una frase
Establece que un pronóstico probabilístico se evalúa con el paradigma de **maximizar la sharpness sujeto a calibración**, y demuestra con una simulación que la cobertura y el histograma PIT **no alcanzan para rankear modelos**: cuatro pronosticadores de calidad muy distinta producen coberturas e histogramas casi idénticos, y lo que los separa es el ancho de los intervalos y el CRPS.

## Por qué está en nuestra lista (qué decisión del proyecto toca)
Es la fuente primaria de casi todo lo que declaramos en OE3: PIT, calibración vs sharpness, y el uso de reglas de puntuación propias. Pero además tiene un resultado que **cambia el diseño de nuestro torneo (R4)**: si evaluáramos solo por cobertura, el baseline de conteo puro empataría con el modelo completo y concluiríamos que las categorías no sirven. Eso hay que dejarlo escrito antes de correr nada. También trae la limitación técnica que nos va a morder: todo el marco supone distribuciones continuas.

## Resumen sección por sección

### 1. Introducción y el contraejemplo que ordena todo
Arranca con el marco: en cada instante *t* la naturaleza elige una distribución **G_t** (el proceso que realmente genera los datos) y el pronosticador elige una distribución predictiva **F_t**. El resultado observado x_t es un sorteo de G_t. Si F_t = G_t para todo t, tenemos el **pronosticador ideal**. Siguiendo el principio prequencial de Dawid, los pronósticos se juzgan solo con los pares (F_t, x_t), sin importar de dónde salieron.

La herramienta tradicional es el **PIT** (*probability integral transform*): p_t = F_t(x_t), o sea en qué percentil de tu distribución pronosticada cayó el valor real. Si el pronóstico es ideal y F_t es continua, los p_t se distribuyen uniformes.

Y acá viene el golpe. Retomando un ejemplo de Hamill (2001), montan una simulación con cuatro pronosticadores (Tabla 1). La naturaleza sortea μ_t ~ N(0,1) y genera G_t = N(μ_t, 1):
- **Ideal:** F_t = N(μ_t, 1).
- **Climatológico:** F_t = N(0, 2), siempre la misma distribución sin condicionar en nada.
- **Desenfocado:** mezcla al 50% de N(μ_t,1) y N(μ_t+τ_t,1) con τ_t = ±1 — o sea, sesgo distribucional.
- **El de Hamill:** reparte la tarea entre tres estudiantes sesgados.

10.000 repeticiones. **Los cuatro histogramas PIT salen esencialmente uniformes** (Figura 1, con 20 bins). El PIT no distingue al ideal de sus competidores, y sin embargo, como señalan Diebold et al., el ideal es preferido por todos los usuarios sea cual sea su función de pérdida.

### 2. Los tres modos de calibración
Definen tres nociones y demuestran que son **lógicamente independientes** (Tabla 2: ocurren las ocho combinaciones posibles).

- **Calibración probabilística** (la que nos importa): el promedio de G_t(F_t⁻¹(p)) converge a p para todo p. En criollo: cuando declarás el cuantil 80%, la realidad tiene que caer por debajo el 80% de las veces. Es exactamente la cobertura de cuantiles, y es equivalente a que los PIT sean uniformes (Teorema 2).
- **Calibración de excedencia:** el promedio de G_t⁻¹(F_t(x)) converge a x. Es la versión "por umbral" en vez de "por cuantil": fijás un valor x (por ejemplo 60 días), mirás qué probabilidad le asigna tu pronóstico, y buscás qué umbral real correspondería a esa probabilidad; en promedio tiene que darte x de vuelta. **Los propios autores no le encuentran análogo muestral**, o sea que no es diagnosticable con datos.
- **Calibración marginal:** el promedio de las CDF pronosticadas converge al promedio de las reales. Es la condición "de climatología": si apilás todos tus pronósticos y los comparás con la distribución empírica de todo lo observado, tienen que coincidir. Es débil: el pronosticador climatológico la cumple perfecto y no sirve para nada.

Los ejemplos 1–6 construyen un pronosticador para cada combinación. El **climatológico** (ejemplo 2) es probabilísticamente y marginalmente calibrado pero no de excedencia; el **desenfocado** (ejemplo 3) es probabilísticamente calibrado y nada más.

### 2.4 El principio de sharpness (que es una conjetura)
Proponen el paradigma operativo: **maximizar la sharpness sujeto a calibración**. La sharpness es cuán concentrada está la distribución, y es propiedad **solo del pronóstico**, no mira los datos. La conjetura es que "ser el pronosticador ideal" y "maximizar sharpness sujeto a calibración" son equivalentes. **No lo pueden probar** y lo dicen: dan contraejemplos donde un pronosticador cumple la condición finita de calibración probabilística (o de excedencia) y aun así es *más* angosto que el ideal. El Teorema 1 rescata un caso: para pronósticos climatológicos vale una cota inferior de varianza. Y cierran admitiendo que no saben si un pronosticador no climatológico puede estar calibrado probabilística y marginalmente y ser más sharp que el ideal.

### 3. Herramientas de diagnóstico
**3.1 PIT.** Recomiendan **10 o 20 bins**. La lectura de las formas —y esto es lo que vamos a usar todas las semanas:

| Forma del histograma | Qué significa |
|---|---|
| Plano | Calibrado |
| **Joroba** (masa al medio) | Distribuciones **sobredispersas**: intervalos demasiado anchos en promedio |
| **Forma de U** (masa en los extremos) | Distribuciones **demasiado angostas** |
| **Triangular / rampa** | Distribuciones **sesgadas** |

Notan que la cobertura de los intervalos centrales es **información redundante**: se lee del histograma PIT como el área de los 10 y 18 bins centrales. Advierten que los tests formales de uniformidad se complican con estructuras de dependencia, y que en series temporales los PIT de pronósticos a k pasos son a lo sumo (k−1)-dependientes, cosa que se chequea con autocorrelogramas de los momentos del PIT.

**3.2 Calibración marginal.** Se evalúa comparando la CDF predictiva promedio contra la CDF empírica de las observaciones (Teorema 3).

**3.3 Sharpness.** Resúmenes numéricos y gráficos del **ancho de los intervalos de predicción**. Cuando hay heterocedasticidad condicional el promedio no alcanza y proponen box plots: el "diagrama de sharpness".

**3.4 Reglas de puntuación propias.** Una regla es **propia** si la pérdida esperada se minimiza cuando declarás la distribución que realmente creés; o sea, no se puede hacer trampa. Mencionan tres:
- **Score logarítmico:** propio, pero poco robusto.
- **CRPS:** `crps(F,x) = ∫ {F(y) − 1(y ≥ x)}² dy`. Tienen la representación equivalente e intuitiva `E_F|X − x| − ½·E_F|X − X′|`: el error absoluto esperado de tu distribución respecto del dato, menos media penalización por ser difuso. Propiedades que destacan: es propio, robusto, **se reporta en las mismas unidades que la observación**, y **generaliza el error absoluto, al que se reduce si el pronóstico es un punto**.
- **Brier score** por umbral: muestran que el **CRPS es la integral del Brier sobre todos los umbrales**.

**No mencionan** pinball / quantile loss ni interval score. Si usamos pinball, la cita tiene que ser otra.

### 4. Caso real: viento en Stateline
Velocidad media horaria del viento en el Stateline wind energy centre (frontera Oregon–Washington), pronósticos a 2 horas, **5.136 casos**. Tres métodos: persistencia, autorregresivo y RST (regime-switching space-time). *Nota: las Tablas 8 y 9 encabezan "March–November 2003" pero listan siete meses, mayo a noviembre, y el texto de sharpness dice "May–November 2003"; la discrepancia está en el paper.*

Coberturas (Tabla 6, nominal 50%/90%): persistencia 50,9/89,2; autorregresivo 55,6/90,4; RST 51,2/88,4. **Todas aceptables.** El histograma PIT del autorregresivo sale con joroba (sobredisperso).

Anchos promedio (Tabla 7, m/s): persistencia 2,63/7,51; autorregresivo 2,74/6,55; **RST 2,20/5,31** — el RST es ~20% más angosto que el autorregresivo.

CRPS global (Tabla 8, m/s): persistencia 1,20; autorregresivo 1,12; **RST 0,97**. MAE (Tabla 9): 1,61 / 1,53 / **1,34**. El RST gana en los siete meses; bajo la nula de empate eso pasa con probabilidad (1/2)⁷ = **1/128**. Remiten a Diebold & Mariano para tests formales y advierten que hay que cuidar las dependencias en los diferenciales.

### 5. Discusión
Si tuvieran que reducir todo a una recomendación: **evaluar sharpness, sobre todo cuando el objetivo es rankear**. Repasan cinco estudios comparativos previos que evaluaron solo por calibración y desempeño puntual, y sostienen que ese tipo de trabajo exige sharpness de rutina.

## Los números que hay que recordar
- **Coberturas de los cuatro pronosticadores simulados: 51,2 / 51,3 / 50,1 / 50,9 al 50% nominal, y 90,0 / 90,7 / 90,1 / 89,5 al 90%** (Tabla 3). Prácticamente idénticas: la cobertura no los distingue.
- **Anchos al 90%: ideal 3,29; Hamill 3,62; desenfocado 3,68; climatológico 4,65** (Tabla 4). Acá sí se separan.
- **CRPS: ideal 0,56; Hamill 0,61; desenfocado 0,63; climatológico 0,78.** LogS: 1,41 / 1,52 / 1,53 / 1,75 (Tabla 5).
- Caso real: **CRPS 0,97 del RST contra 1,20 de persistencia**; anchos 5,31 vs 7,51; gana los 7 meses, p = 1/128 (Tablas 7–8).
- Recomiendan **10 o 20 bins** para el histograma PIT (Sección 3.1); las figuras usan 20 con T = 10.000.

## Limitaciones
**Declaradas:** el principio de sharpness es una conjetura que no pueden probar, y dan contraejemplos donde la calibración finita no impide ser más sharp que el ideal; la calibración de excedencia no tiene análogo muestral; los tests formales de uniformidad se complican con dependencia.
**Nuestras, y una es grave:** (1) **Todo el marco supone que F_t y G_t son continuas y estrictamente crecientes en R. No tratan distribuciones discretas ni átomos, y no mencionan PIT randomizado.** Si medimos duraciones en días u horas enteras, o hay tareas que cierran el mismo día, el PIT no va a dar uniforme aunque el modelo sea perfecto. (2) Leen el PIT con T = 10.000 y 5.136 casos; con 100–300 tareas el histograma es ruido y hace falta bandas o un test, decidido de antemano. (3) No hay censura: toda observación se realiza. (4) El diagnóstico es visual y no da criterio de cuánta desviación de la uniformidad es tolerable.

## Qué tomamos tal cual y qué hacemos distinto
**Tomamos:** el paradigma completo, y con él **la estructura de la tabla de resultados de la tesis**: una tabla de cobertura, una de ancho, una de scores, con una fila por modelo — es literalmente el layout de las Tablas 3, 4 y 5. La lectura diagnóstica del PIT (U = angosto, joroba = ancho, rampa = sesgado). El CRPS reportado en días y comparado contra el MAE del baseline puntual — es el número que va al resumen, y el hecho de que el CRPS se reduzca al error absoluto es lo que hace posible el torneo entre un modelo distribucional y uno que da una fecha sola. Y el detalle de que la cobertura es redundante con el PIT: conviene reportar las dos igual, porque la cobertura se lee más fácil.

**Hacemos distinto, y son tres cosas concretas:**
1. **El resultado de la simulación es una advertencia directa sobre R4.** Nuestro baseline de conteo puro es un pronosticador climatológico: va a estar bien calibrado, con PIT plano, y no por eso es bueno. La cobertura sola no lo va a descartar; lo van a descartar la sharpness y el CRPS. **El protocolo pre-especificado tiene que decir que el ranking se hace por CRPS y ancho, con la calibración como filtro previo y no como criterio de ranking.**
2. **Los átomos son problema nuestro y no de ellos.** Hace falta PIT no-randomizado o randomizado, y la cita para eso no es este paper (ver la sección de pendientes de `00_ESTADO_DEL_ARTE.md`).
3. **n chico.** Con 100–300 tareas y menos por ventana de backtest, el histograma visual no alcanza: hay que decidir de antemano bandas de confianza o un test robusto a la correlación entre PITs sucesivos, que el origen móvil introduce y que ellos mismos advierten que rompe los tests formales.

## Si igual lo vas a abrir
Leé la Sección 1 entera (el contraejemplo de los cuatro pronosticadores es el corazón del paper y son 3 páginas), la Sección 3 completa (herramientas), y las Tablas 3, 4 y 5 juntas. De la Sección 2 alcanza con la Definición 1 y la Tabla 2; los ejemplos 4, 5 y 6 y las demostraciones se pueden saltear. La Sección 4 (caso del viento) leela en diagonal mirando Tablas 6–9, que son la plantilla de cómo reportar. El Apéndice A (demostraciones) no hace falta.

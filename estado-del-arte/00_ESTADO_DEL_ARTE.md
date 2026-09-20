# ESTADO DEL ARTE — Mapa, orden de lectura y resúmenes

*Tesis: Pronóstico calibrado de entrega agéntica. Maestría en IA, Universidad ORT Uruguay.*
*Equipo: Joaquín Guerra, Germán Pazos, Ramiro Sanes. Relevamiento cerrado el 18 de setiembre de 2026.*

---

## Empezá por acá

Esta carpeta tiene **12 resúmenes que reemplazan la lectura de los papers**. Están escritos sección por sección, con las tablas transcriptas y los números exactos, para que no tengas que abrir el original salvo que algo te haga ruido. Cada uno termina con "qué tomamos tal cual y qué hacemos distinto", que es la parte que se convierte en texto de la memoria.

> **El estado del arte completo son ~100 minutos de lectura de resúmenes** en lugar de ~9 horas de papers. El orden está en la §3.

| Archivo | Qué es |
|---|---|
| `00_ESTADO_DEL_ARTE.md` | Este documento: el mapa, el ranking y el camino de lectura |
| `resumenes/*.md` | Un resumen por paper, 12 en total |
| `LITERATURA.md` (en la carpeta de arriba) | El relevamiento amplio: ~100 candidatos con triage. Sigue siendo la fuente para "¿existe algo sobre X?" |
| `INTRODUCCION.md` (en la carpeta de arriba) | Los conceptos de probabilidad explicados desde cero. Si no te suena "PIT" o "sharpness", **leelo antes que esto** |

**Cómo se hizo.** Se partió de las 17 referencias del anteproyecto entregado, se leyó a texto completo todo lo accesible, y se expandió la búsqueda en tres frentes nuevos (§5). Toda entrada tiene una URL que se abrió efectivamente. Lo que no se pudo leer está marcado como tal y no se resumió: **no hay ninguna ficha escrita desde un abstract**.

**Estado de acceso, con honestidad:**

| | Cuántos |
|---|---|
| Leídos a texto completo, con resumen | **12** |
| Verificados pero no conseguidos (sin resumen) | **3** — Jørgensen 2019, Batselier & Vanhoucke 2016, Lokan & Mendes 2017 |
| Verificados a nivel metadatos, para citar como contexto | ~45 (en `LITERATURA.md` y §5 de acá) |

---

## 1. El estado del arte en una página

Nuestro problema vive en el cruce de **cinco líneas de investigación que casi no se citan entre sí**. Esa es la razón de que el hueco exista: no es que alguien intentó y falló, es que las piezas están en comunidades distintas.

```
     (A) ESTIMACIÓN DE SOFTWARE          (B) EVALUACIÓN DE PRONÓSTICOS
         Décadas de literatura.              PROBABILÍSTICOS
         Monte Carlo sobre históricos,       Calibración, sharpness, PIT, CRPS.
         reference classes, analogía.        Meteorología y econometría.
         Casi todo mide error PUNTUAL.       Casi nada aplicado a software.
              │                                        │
              │   Jørgensen es el único puente         │
              │   (intervalos y calibración en SE)     │
              └───────────────┬────────────────────────┘
                              ▼
                    ◆ ACÁ ESTÁ NUESTRA TESIS ◆
                              ▲
              ┌───────────────┴────────────────────────┐
              │                                        │
     (C) VALIDACIÓN TEMPORAL              (D) MEDICIÓN EMPÍRICA DE
         Y NO ESTACIONARIEDAD                 AGENTES DE IA
         Origen móvil, ventanas,              Explotó en 2026 (AIDev y MSR).
         leakage, concept drift.              Mide productividad, adopción,
         Resultados contradictorios.          intervención. NO mide entrega
                                              ni calibra nada distribucional.
                              
     (E) RECLASES / TAXONOMÍAS: cómo se arma una clase de referencia y si dos
         personas la arman igual. Todo a nivel megaproyecto, nada a nivel tarea.
```

**Lo que cada línea ya resolvió, y que no conviene presentar como nuestro:**

- **(A)** El motor. Simular un proyecto sorteando duraciones históricas está resuelto desde hace décadas y validado empíricamente al menos una vez (Miranda et al. 2021, MMRE 32%).
- **(B)** El criterio de evaluación. "Maximizar sharpness sujeto a calibración" es de Gneiting, Balabdaoui & Raftery (2007), y las métricas (PIT, CRPS, pinball) están definidas, implementadas y con software.
- **(C)** El argumento de que hay que validar respetando el tiempo (Sigweni et al. 2016, con p-valores y dentro de ingeniería de software).
- **(D)** La descripción de cómo trabajan los agentes y cuánto interviene un humano (Kumar et al. 2025; toda la línea AIDev).
- **(E)** La crítica a las clases de referencia y el trade-off ancho/angosto (Cantarelli et al. 2025).

**Lo que nadie hizo, y es el aporte:** aplicar (B) a (A) sobre datos de (D), con la disciplina de (C) y las clases de (E). Los detalles en §6.

**Las tres cosas que cambiaron con esta lectura** respecto de lo que creíamos hace dos semanas:

1. **Miranda et al. no es el precedente de nuestro motor: es el precedente de nuestro baseline 1.** Su método es bootstrap sin categorías ni dependencias, o sea el conteo puro. Eso es una buena noticia — el baseline tiene DOI y datos reales, y se vuelve difícil de acusar de hombre de paja — y una mala: lo que el motor de Rootstrap agrega por encima sigue sin validación publicada.
2. **La cobertura sola no rankea modelos.** Gneiting et al. demuestran con una simulación que cuatro pronosticadores de calidad muy distinta dan coberturas e histogramas PIT casi idénticos. Nuestro baseline de conteo puro va a estar bien calibrado. Si el protocolo de R4 rankea por cobertura, concluiríamos que las categorías no sirven, y sería falso.
3. **Hay un problema técnico abierto en R3 que no teníamos identificado:** todo el marco de PIT supone distribuciones continuas. Con duraciones en días enteros, el PIT no da uniforme aunque el modelo sea perfecto. Hay solución publicada (§5.2) pero hay que decidirla antes de implementar.

---

## 2. Ranking: qué leer y por qué

Los tres ejes del triage: **CERCANÍA** (A = agentes, A/H = asistido, H = humano, G = general) · **FUNCIÓN** (MÉTODO / BASELINE / ANTECEDENTE / CONTEXTO) · **SOLIDEZ** (PR = revisado por pares, PP = preprint, GRIS; datos reales/simulados; n).

### P1 — leer completo; cambian decisiones de diseño

| # | Fuente | Cerc. | Función | Solidez | Resumen | Por qué |
|---|---|---|---|---|---|---|
| 1 | **Gneiting, Balabdaoui & Raftery (2007)**, JRSS-B 69(2) | G | MÉTODO | PR; simulación T=10.000 + 5.136 casos reales | ✅ | El criterio de evaluación completo, y la demostración de que cobertura y PIT no rankean. Define R3 y corrige R4. |
| 2 | **Jørgensen & Sjøberg (2003)**, IST 45(3) | H | BASELINE | PR; 145 tareas + 13 profesionales | ✅ | Es nuestro baseline 2, publicado. Unidad = tarea. Y la cifra de sobreconfianza humana (68% para 90% nominal). |
| 3 | **Miranda et al. (2021)**, ACM SAC | H | BASELINE | PR; 71 proyectos, >12.000 historias | ✅ | Es nuestro baseline 1, publicado. MMRE 32%. Emite intervalos y nunca mide su cobertura: ahí empieza nuestro trabajo. |
| 4 | **Sigweni, Shepperd & Turchi (2016)**, EASE | H | MÉTODO | PR; 477 predicciones | ✅ | La cita para el origen móvil dentro de SE. Y un experimento replicable casi gratis. |
| 5 | **Rootstrap (2026)**, whitepaper | A | ANTEC. | GRIS; sin datos | ✅ | Define el objeto de estudio. Su última frase es el enunciado de nuestra tesis. |
| 6 | **Jørgensen, Welde & Halkjelsvik (2023)**, IEEE TEM 70(10) | H | MÉTODO | PR; 69 proyectos | ✅ | **El precedente metodológico más cercano**: usa hit rate + PIT + ancho + CRPS sobre estimaciones reales. Y construye nuestro mismo contrafáctico de baseline. |
| 7 | **Cantarelli et al. (2025)**, Prod. Planning & Control 37(7) | H | ANTEC. | PR; SLR de 61 artículos | ✅ | El trade-off ancho/angosto de las clases de referencia, que es nuestro problema con 10 celdas. Justifica el pooling parcial. |
| 8 | **El Emam (1999)**, EMSE 4(2) | H | MÉTODO | PR; 70 kappas, 19 proyectos | ✅ | Fija el criterio de éxito de OE5(a). **Con una trampa: sus umbrales son para kappa nominal y nuestros tiers son ordinales.** |
| 9 | **Kumar et al. (2025)**, ASE | A/H | ANTEC. | PR; 19 devs, 33 issues | ✅ | El estudio de campo de referencia sobre colaboración humano-agente. Declara explícitamente que **no midió duraciones**. |
| 10 | **Li, Zhang & Hassan (2026)**, AIDev, MSR | A | MÉTODO (datos) | PP; 932.791 PRs | ✅ | El plan B. El resumen contesta si permite reconstruir (momento del pronóstico, desenlace): **sí, pero cambiando de pregunta.** |
| 11 | **Dao et al. (2026)**, MSR Mining Challenge | A | ANTEC. | PR (declarado); 33.707 PRs | ✅ | Lo más cercano a pronosticar trabajo de agentes. Su curva de calibración es el mínimo que hay que superar. |
| 12 | **Minku & Yao (2017)**, Automated SE 24(3) | H | MÉTODO (concepto) | PR; 5 datasets | ✅ | El encuadre de OE5(b): no descartar la historia vieja, ponderarla. Y su ablación nos ahorra una rama entera del árbol de decisiones. |
| 13 | **Czado, Gneiting & Held (2009)**, Biometrics 65(4) | G | MÉTODO | PR | ⛔ pendiente | **Resuelve el PIT con datos discretos**, que es el hueco técnico abierto de R3. Prioridad de lectura alta cuando toque diseñar el boletín. |
| 14 | **Verenich et al. (2019)**, ACM TIST 10(4) | H | ANTEC. | PR; 16 logs, 16 métodos | ⛔ pendiente | 16 métodos de "tiempo restante" y **ninguno produce intervalos ni distribuciones**. Es nuestro argumento de hueco más limpio para tareas en curso. |

### P2 — leer secciones; hacen falta para justificar

| Fuente | Función | Para qué exactamente |
|---|---|---|
| Gneiting & Raftery (2007), JASA 102(477) | MÉTODO | La fuente de CRPS y pinball. Leer solo las secciones de esos dos scores. |
| Gneiting et al. (2023), *Model diagnostics and forecast evaluation for quantiles*, Annual Review of Statistics 10, DOI 10.1146/annurev-statistics-032921-020240 | MÉTODO | **El tutorial moderno y abierto (CC-BY), y sobre cuantiles, que es lo que nosotros reportamos.** Mejor punto de entrada que los papers de densidades. |
| Knüppel (2015), JBES 33(2) · o Rossi & Sekhposyan (2019), J. Econometrics 208(2) | MÉTODO | Tests de uniformidad del PIT **robustos a n chico y a PITs correlacionados**, que es exactamente nuestra situación con origen móvil. Elegir uno. |
| Diebold (2015), JBES 33(1) + Harvey, Leybourne & Newbold (1997), IJF 13(2) | MÉTODO | Cómo testear que una diferencia de CRPS entre dos modelos es significativa, con corrección de muestra chica. Necesario para que el torneo de R4 concluya algo. |
| Jordan, Krüger & Lerch (2019), JSS 90(12), `scoringRules` | MÉTODO | Implementación de CRPS, incluidas distribuciones discretas y muestras. Ahorra escribir código. |
| Jørgensen (2019), IST 115 | MÉTODO | El criterio en el vocabulario de SE, en 4 páginas. **A un clic y todavía no lo bajamos.** |
| Lokan & Mendes (2017), EMSE 22(2) | ANTEC. | El resultado negativo sobre ventanas móviles que sostiene cómo planteamos OE5(b). **No conseguido.** |
| Batselier & Vanhoucke (2016), PMJ 47(5) | BASELINE | La única comparación empírica RCF vs Monte Carlo. **No conseguido.** |
| Haider et al. (2020), JMLR 21(85) | MÉTODO | **D-calibration**: cómo mantener el PIT cuando hay observaciones censuradas (tareas en curso). |
| Klein & Moeschberger (2003), cap. 2 | MÉTODO | La fórmula de la distribución residual T \| T > s, para re-pronosticar una tarea ya empezada. |
| Amiri Elyasi et al. (2025), BPM 2025 | ANTEC. | Intervalos **calibrados** de tiempo restante, con recalibración por longitud de prefijo. Lo más cercano que existe a nuestra evaluación, en otro dominio. |
| El-Ramly (2026), ACEM, arXiv:2608.02582 | ANTEC. | **El competidor nominal más cercano**: "modelo de estimación de costo para ingeniería agéntica". Determinístico, sin datos, y pide calibración empírica futura. Citarlo para marcar la diferencia. |
| Shepperd & MacDonell (2012), IST 54(8) | MÉTODO | Siempre contra un baseline trivial, con tamaño de efecto. Deprecia MMRE. |
| Tawosi, Moussa & Sarro (2023), IEEE TSE 49(4) | BASELINE | La mediana por clase es un baseline muy difícil de vencer. Respalda la nota metodológica del anteproyecto. |
| Colin & Vanhoucke (2016), JCEM 142(1) | ANTEC. | Validación empírica de lognormal para duraciones de actividades, 1.881 actividades reales. |
| Bai et al. (2026), arXiv:2604.22750 | CONTEXTO | Predicción ex ante de consumo de tokens en tareas agénticas: variabilidad de 30×, autopredicción con correlación 0,39. |
| Garikaparthi (2026), arXiv:2604.00010 | CONTEXTO | Los LLM sobreestiman su propia duración 4–7×. Argumento de por qué el pronóstico tiene que ser externo al agente. |
| Kaddour et al. (2026), arXiv:2602.06948 | CONTEXTO | Sobreconfianza agéntica: 22% de éxito real contra 77% autopredicho. Calibración, pero de probabilidad de éxito. |

### P3 — citar sin leer completo

Flyvbjerg (2006) y Flyvbjerg (2008) para el origen de RCF · Lovallo & Kahneman (2003) para la "outside view" · Love & Ahiaga-Dagbui (2018) como contrapeso · Fischhoff (1975) para el sesgo retrospectivo · Herzig, Just & Zeller (2013) para "las etiquetas del tracker no son confiables" · Hayes & Krippendorff (2007) para alpha ordinal · Lokan & Mendes (2009) y Amasaki & Lokan (2015) para la línea de ventanas · Gama et al. (2014) para el vocabulario de concept drift · Menzies et al. (2017) para "resultados negativos son resultados" · Vacanti (2015) y Magennis (2011) para la práctica de la industria · Little (2006) y Trietsch et al. (2012) para lognormalidad de duraciones · Choetkiertikul et al. (2017) y Weiss et al. (2007) para predicción a nivel issue · Robbes et al. (2026), Popescu et al. (2026) y He et al. (2026) para adopción y efectos de agentes · Anthropic (2026) *Measuring AI agent autonomy* y OpenAI/Johnston et al. (2026) para magnitudes de producción · METR (2026) para por qué los benchmarks no son proyectos.

La lista completa con DOIs está en `LITERATURA.md`.

---

## 3. El camino de lectura

Pensado para vos: fuerte en producto y datos, sin la estadística de pronóstico fresca. **Lineal, de corrido, ~100 minutos si leés los resúmenes.** Cada etapa dice qué pregunta te tiene que quedar contestada; si al terminar no la podés contestar, volvé antes de seguir.

### Etapa 0 · Antes de nada (30 min)
**`INTRODUCCION.md`**, de corrido. Es el documento que explica distribución, cuantil, Monte Carlo, calibración, PIT, CRPS y leakage con ejemplos numéricos corridos. Todo lo que sigue lo da por sabido.

### Etapa 1 · Qué estamos evaluando exactamente (22 min)
| | |
|---|---|
| **Rootstrap** (8 min) | Releelo ahora aunque ya lo conozcas. Ahora vas a leer la §5 con otros ojos. |
| **Gneiting, Balabdaoui & Raftery** (10 min) | El paper más importante de la lista. |
| *Pregunta que te tiene que quedar contestada* | **¿Por qué la cobertura sola no alcanza para rankear modelos?** Si podés explicarle a Germán el ejemplo de los cuatro pronosticadores, seguí. |

### Etapa 2 · Contra qué comparamos (16 min)
| | |
|---|---|
| **Miranda et al.** (8 min) | Nuestro baseline 1. |
| **Jørgensen & Sjøberg** (9 min) | Nuestro baseline 2. |
| *Pregunta* | **¿Qué le agrega el motor de Rootstrap a estos dos métodos, y cómo lo demostramos?** Y una concreta: ¿el baseline 2 necesita una estimación puntual previa que nosotros tengamos? |

### Etapa 3 · Cómo se valida sin hacer trampa (6 min)
| | |
|---|---|
| **Sigweni et al.** (6 min) | Corto. |
| *Pregunta* | **¿En qué exactamente somos más estrictos que ellos?** (Respuesta en la ficha: el corte es el momento del pronóstico, no el de finalización.) |

### Etapa 4 · El precedente más cercano (8 min)
| | |
|---|---|
| **Jørgensen, Welde & Halkjelsvik** (8 min) | Ya usa nuestra batería completa, sobre costo de infraestructura. |
| *Pregunta* | **¿Por qué su "estimador global" gana en CRPS y sin embargo es inútil?** Esa respuesta es la que justifica que reportemos informatividad además de calibración. |

### Etapa 5 · Las clases y su fragilidad (15 min)
| | |
|---|---|
| **Cantarelli et al.** (8 min) | El trade-off ancho/angosto. |
| **El Emam** (7 min) | El umbral de acuerdo. |
| *Pregunta* | **Con 10 celdas sobre 100–300 tareas, ¿cuántas van a tener menos de 5 casos, y qué hacemos con esas?** Y: ¿tratamos los tiers como ordinales o nominales? Hay que decidirlo antes de correr OE5(a). |

### Etapa 6 · El tiempo que pasa (9 min)
| | |
|---|---|
| **Minku & Yao** (9 min) | Es el más largo; se puede leer en diagonal saltando las tablas de base learners. |
| *Pregunta* | **¿OE5(b) es "confirmar que las ventanas ayudan" o "medir cuánta historia conviene"?** (Es lo segundo, y la hipótesis nula es que no importa.) |

### Etapa 7 · Dónde está el hueco (21 min)
| | |
|---|---|
| **Kumar et al.** (7 min) | Cómo se trabaja realmente con agentes. |
| **AIDev** (7 min) | El plan B, y qué le falta. |
| **Dao et al.** (7 min) | Lo más cercano a pronosticar trabajo agéntico. |
| *Pregunta* | **Si mañana se cae el acuerdo con Rootstrap, ¿qué pregunta podríamos contestar con AIDev y cuál no?** |

### Etapa 8 · No ahora: cuando toque diseñar R3 (F2, noviembre)
No leas esto todavía. Va acá para que sepas que existe y no lo descubras tarde:
- **Czado, Gneiting & Held (2009)** — PIT con datos discretos.
- **Knüppel (2015)** o **Rossi & Sekhposyan (2019)** — test de calibración con n chico y PITs correlacionados.
- **Diebold (2015)** + **Harvey et al. (1997)** — significancia de diferencias de CRPS.
- **Gneiting et al. (2023)**, Annual Review — el tutorial de cuantiles, abierto.
- Si hay tareas en curso al momento del pronóstico: **Haider et al. (2020)** y **Klein & Moeschberger** cap. 2.

**Regla de trabajo, y es la que más tiempo les va a ahorrar:** después de cada etapa, escribí 1–2 páginas de prosa. Las fichas te dan el esqueleto; la prosa que conecta es tuya y es lo que va a la memoria. Si leés las ocho etapas y no escribís nada, en marzo releés todo.

---

## 4. Reparto sugerido, si lo dividen entre los tres

Las etapas 0 a 2 las leen los tres (es el tronco común, ~70 min). Después:

| Persona | Bloque | Qué escribe |
|---|---|---|
| Joaco | Etapas 1 y 4 + Etapa 8 | La sección de evaluación y calibración de la memoria. Es el diferencial de la tesis. |
| Germán | Etapas 2 y 3 | La sección de baselines y el diseño del torneo (R4). |
| Ramiro | Etapas 5, 6 y 7 | Clases de referencia y OE5(a); no estacionariedad y OE5(b); el estado del arte de agentes. |

---

## 5. Lo nuevo del barrido de setiembre 2026

Tres frentes que no estaban en el relevamiento anterior. Todo verificado con URL abierta; ninguno leído a texto completo salvo donde se indica.

### 5.1 Agentes de código, marzo–setiembre 2026

Se revisaron los programas de **FSE 2026 (Industry) e ICSE 2026 (workshop AGENT)**: ninguno de los papers aceptados trata estimación, pronóstico ni calibración de trabajo agéntico.

Lo que sí apareció, y conviene incorporar al argumento:

- **La predicción ex ante de recursos existe, pero es de tokens o de éxito, no de tiempo — y es mala.** Bai et al. (arXiv:2604.22750): variabilidad de 30× en consumo de tokens dentro de la misma tarea, y la autopredicción del agente antes de ejecutar alcanza correlación 0,39. Garikaparthi (arXiv:2604.00010, workshop ICLR 2026): los LLM sobreestiman la duración de sus propias tareas 4–7×, y en setting agéntico 5–10×. Kaddour et al. (arXiv:2602.06948): agentes con 22% de éxito real predicen 77%. **Los tres refuerzan el hueco: el agente no es un estimador confiable de sí mismo, hace falta un modelo externo con telemetría.**
- **"Calibración de agentes" ya existe como término, pero para probabilidad de éxito binaria**, en benchmarks, con AUROC y ECE: Kaddour et al.; Li et al. (arXiv:2608.29685, EMNLP 2026); Grotov & Malykh (arXiv:2609.05274, EMNLP Industry); Mammen et al. (arXiv:2609.09448). **Nadie calibra una distribución de duración o de fecha.** Hay que enunciar el hueco con esa precisión, porque decir "nadie calibra nada sobre agentes" es falso y verificable.
- **El competidor nominal:** El-Ramly (2026), *ACEM: A Cost Estimation Model for Agentic Software Engineering*, arXiv:2608.02582. Modelo tipo COCOMO con tres dimensiones (tokens, esfuerzo humano en el loop, infraestructura). **Sin datos, determinístico, estima costo y no tiempo, y el propio autor pide "calibración empírica futura".** Es la cita obligada para posicionarse: ellos proponen la fórmula, nosotros el sistema que aprende de telemetría y se autoevalúa.
- **Magnitudes nuevas de producción.** OpenAI/Johnston et al. (arXiv:2606.26959): la fracción de usuarios de Codex con tareas de ≥8 h de tiempo humano estimado pasó de 2,1% a 25,6% entre diciembre 2025 y mayo 2026; el empleado mediano de OpenAI tenía 2,5 h/día de turnos de agente. Anthropic (feb 2026, *Measuring AI agent autonomy in practice*): duración mediana de turno ~45 s estable, p99,9 pasó de <25 min a >45 min en cuatro meses; las interrupciones humanas **suben** con la experiencia del usuario (5% → 9% de turnos).
- **Datasets alternativos a AIDev:** SWE-chat (arXiv:2604.20779), 6.000 sesiones reales, 63k prompts, 355k tool calls; y AgenticFlict (arXiv:2604.03551), 142k PRs con 27,67% de conflictos de merge. **Ninguno tiene duración de tarea con etiqueta de proyecto/cliente ni escalaciones formales.**

**Conclusión del frente 1: el hueco sigue abierto.** No apareció nada que pronostique fechas de entrega ni que evalúe calibración de distribuciones sobre trabajo ejecutado por agentes.

### 5.2 El problema técnico de R3: PIT discreto y n chico

Este frente se abrió porque la lectura de Gneiting et al. reveló una limitación que nos afecta: **su marco supone distribuciones continuas.** Con duraciones en días u horas enteras, o con tareas que cierran el mismo día, el PIT no da uniforme aunque el modelo sea perfecto, y el histograma va a mostrar bandas falsas que leeríamos como mala calibración.

Hay solución publicada:

| Problema | Solución | Referencia (abierta) |
|---|---|---|
| Duraciones discretas / átomos | **PIT no-randomizado**: en vez de un número por observación, una función lineal por tramos entre F(x−1) y F(x), promediada sobre las n observaciones. Recomiendan 10 o 20 bins. | **Czado, Gneiting & Held (2009)**, Biometrics 65(4), DOI 10.1111/j.1541-0420.2009.01191.x. Versión abierta: tech report UW #518. Implementado en `scoringutils` (R), opción `nonrandom` |
| Fundamento formal del PIT randomizado con átomos | z = (1−U)·F(x−) + U·F(x) es U(0,1) bajo el modelo verdadero | **Brockwell (2007)**, Stat. & Prob. Letters 77(14); abierto en PMC. También Gneiting & Ranjan (2013), EJS 7, Def. 2.6–2.7 |
| n chico + PITs correlacionados por el origen móvil | Test de momentos brutos del PIT con varianza de largo plazo (HAC). Tamaño contenido incluso con T = 50 | **Knüppel (2015)**, JBES 33(2); abierto como Bundesbank DP |
| Ídem, alternativa gráfica | KS y Cramér–von Mises sobre la CDF empírica del PIT con **bandas conjuntas** y bootstrap por bloques; reemplaza el histograma con bins | **Rossi & Sekhposyan (2019)**, J. Econometrics 208(2); abierto en CREI |
| ¿La diferencia de CRPS entre dos modelos es significativa? | Diebold–Mariano sobre diferenciales de score, con la corrección de muestra chica de Harvey–Leybourne–Newbold | **Diebold (2015)**, JBES 33(1), abierto en UPenn; **Harvey et al. (1997)**, IJF 13(2) |
| Implementación | CRPS cerrado para muchas familias, incluidas discretas; `crps_sample` para muestras | **Jordan, Krüger & Lerch (2019)**, JSS 90(12), abierto |
| Tutorial moderno, y sobre cuantiles | Calibración incondicional vs condicional, diagramas de confiabilidad isotónicos, scores consistentes | **Gneiting et al. (2023)**, Annual Review of Statistics 10, CC-BY |

**Lo mínimo defendible para R1–R5:** PIT no-randomizado (Czado et al.) + un test robusto (Knüppel o Rossi–Sekhposyan) + Diebold–Mariano con corrección HLN. Son tres citas y ningún método nuevo: es evaluación, no modelado. Todo lo demás (diagramas CORP, tests de score de Wei & Held) es deseable y suma justificación.

### 5.3 Tareas en curso: censura y tiempo restante

Frente abierto porque al momento de cada pronóstico va a haber tareas empezadas y no terminadas. Si las descartamos, sesgamos hacia tareas cortas.

- **Lo mínimo:** tratarlas como censuradas por la derecha en el entrenamiento, y pronosticarlas con la **distribución residual** T | T > s de la misma familia ya ajustada. Referencias: **Klein & Moeschberger (2003)** cap. 2 para la fórmula, y `lifelines` en Python tiene el parámetro `conditional_after` que lo implementa directo. Costo bibliográfico bajo: no es método nuevo, es una operación sobre el modelo que ya tenemos.
- **Para evaluar con censura:** **Integrated Brier Score con IPCW** (Graf et al. 1999, la referencia canónica, implementada en scikit-survival y mlr3proba) y **D-calibration** (Haider et al. 2020, JMLR 21(85), abierto) — que es literalmente nuestro histograma PIT con una regla para repartir la masa de los censurados. **Aviso importante y de leakage:** la estimación de la distribución de censura para los pesos IPCW debe hacerse **solo con datos anteriores al origen** de cada corte del backtesting.
- **El argumento de hueco más limpio:** **Verenich et al. (2019)**, ACM TIST 10(4) (arXiv:1805.02896, abierto), comparan 16 métodos de predicción de tiempo restante sobre 16 logs reales, midiendo MAE. **Ninguno de los 16 produce intervalos ni distribuciones**, y el paper ni siquiera lo plantea como trabajo futuro. Es la evidencia de que el pronóstico distribucional de trabajo en curso es contribución.
- **Lo más cercano que existe:** **Amiri Elyasi, van der Aa & Stuckenschmidt (2025)**, BPM 2025 (PDF abierto en eprints de Viena): intervalos de tiempo restante con recalibración isotónica **por longitud de prefijo** y calibración medida como área de miscalibración (0,03–0,11 contra 0,11–0,47 de MC-dropout). Es process mining, no software, pero legitima la idea entera.
- **Cuidado con el alcance:** un modelo de tiempo restante con features dinámicas es un **segundo modelo** con su propia justificación y evaluación. Eso es R6–R8, no R1–R5.

---

## 6. Los huecos: el argumento de aporte

Reescrito después de leer los textos completos. Cada punto dice qué se buscó, qué es lo más cercano, y qué queda vacío.

**6.1 Pronóstico de fechas de entrega para trabajo ejecutado por agentes. No existe.** Lo más cercano es predecir esfuerzo de revisión (Dao et al.) o tiempo hasta merge (Pansuriya et al.) de PRs agénticos individuales en open source, como clasificación o regresión puntual — y con el resultado explícito de que el tiempo es difícil de predecir con información de creación. Nada a nivel proyecto, nada con grafo de dependencias, nada con horizonte de fecha. El único trabajo que plantea el problema de estimar cuando la IA hace el trabajo (El-Ramly, ACEM) es conceptual, determinístico y sin datos.

**6.2 Evaluación de calibración de pronósticos de entrega de software.** Hay que separar dos cosas que se llaman igual, y ser preciso porque la versión tajante es falsa:
- **Calibración de una probabilidad binaria** sobre trabajo agéntico: **sí existe**. Dao et al. publican una curva de calibración (aunque sin métrica numérica), y toda la línea de "agentic uncertainty" de 2026 calibra probabilidad de éxito con AUROC y ECE.
- **Calibración de una distribución predictiva sobre una duración o una fecha, en software:** **no encontramos ninguno**, con agentes ni sin ellos. La línea MSR reporta precision/recall/MAE; la línea Jørgensen mide hit rate de intervalos humanos pero no reglas de puntuación propias; Miranda et al. emiten intervalos al 95% y **nunca reportan su cobertura** (que en sus propias tablas da 11 de 15). Lo más cercano en cualquier dominio es Jørgensen, Welde & Halkjelsvik, que **sí** usa hit rate + PIT + ancho + CRPS — pero sobre **costo de infraestructura pública**, no sobre software ni sobre fechas.

  → La frase para la memoria es: *"sobre entrega de software no encontramos evaluación de calibración de distribuciones predictivas"*, no *"nadie evalúa calibración"*.

**6.3 Monte Carlo sobre throughput sin validación de calibración.** La práctica que la industria usa (Vacanti, Magennis) no tiene evaluación de calibración publicada. Miranda et al. es lo único con datos reales y mide solo error puntual. Y ojo con el encuadre: ese paper valida el *bootstrap sin condicionar*, que es nuestro baseline 1, **no** un motor con categorías y dependencias como el del whitepaper. Eso sigue sin validación publicada.

**6.4 Confiabilidad entre evaluadores para categorías de complejidad o tamaño de tareas.** Hay acuerdo entre anotadores para *tipo* de issue (Herzig et al., Izadi et al.) y umbrales de kappa para evaluaciones de proceso (El Emam), pero ningún estudio que reporte kappa o alpha para asignar tiers de complejidad o tallas a tareas de software. Sobre T-shirt sizing solo aparece literatura de herramientas. OE5(a) tiene bastante de inédito, y **un acuerdo bajo sería un hallazgo sobre la taxonomía**, independiente del pronóstico.

**6.5 Ventanas móviles a nivel tarea, en una organización, con cambios de proceso identificados.** Toda la línea Lokan/Mendes/Amasaki/Minku trabaja a nivel proyecto sobre datasets multi-organización, con el tiempo como continuo y sin variable explícita de versión de proceso. Nuestro caso (unidad tarea, drift abrupto y fechado por sello de procedencia) no tiene antecedente directo. **Dato nuevo de esta lectura:** Miranda et al. encuentran que el error *empeora* con 60–70 historias de historia y lo atribuyen a "ruido"; la explicación más plausible es no estacionariedad. Es evidencia a favor de la premisa de OE5(b) producida por un paper que no la reconoció.

**6.6 RCF a nivel tarea con clases chicas y pooling.** RCF es siempre a nivel proyecto o megaproyecto. En SE lo más parecido es la estimación por analogía y la mediana por clase como baseline, y ninguna de las dos literaturas cita a la otra. Presentar el prior por clase de referencia como puente entre ambas es un aporte de encuadre barato.

**6.7 Distribución de duración de tareas de agentes en proyectos reales.** Solo hay distribuciones a nivel sesión de asistente (Liu et al., Anthropic), tiempo hasta merge de PRs en open source (línea AIDev, contaminado por el 28,3% de merges en menos de un minuto), y duraciones de trayectorias en benchmarks. **No existe un dataset publicado con duración por tarea de proyectos comerciales ejecutados por agentes, con QA, escalaciones y latencia de cliente.** La caracterización descriptiva de esas distribuciones ya es un resultado por sí misma.

**6.8 Horas de intervención humana por tarea.** Solo proxies: frecuencia de intervención (Khelifi et al.: ~52% de PRs agénticos), tipos de intervención, turnos humanos por tarea (Anthropic: −33% en seis meses), interrupciones (5–9% de turnos). **Y el punto se refuerza con la lectura completa de Kumar et al.: el estudio de campo de referencia declara explícitamente que no analizó duraciones**, para no sesgar hacia participantes que repetían acciones en intervalos cortos. O sea que el trabajo más citado del tema no tiene una sola cifra de tiempo. METR documenta además que medir tiempo humano con agentes concurrentes es metodológicamente frágil en experimentos — lo cual es un argumento a favor de la telemetría observacional.

**6.9 Pronóstico distribucional de trabajo en curso.** Verenich et al. comparan 16 métodos de tiempo restante y ninguno produce intervalos. Amiri Elyasi et al. (2025) es la primera excepción que encontramos, y es de este año y en otro dominio.

**6.10 Sesgo de la literatura, que conviene declarar.** Casi toda la evidencia empírica sobre agentes autónomos sale de un solo dataset (AIDev) y de open source. Ninguno de los trabajos vistos tiene latencia de decisiones del cliente, escalaciones formales ni versión de proceso. Es a la vez una limitación del plan B y el argumento de por qué los datos de una consultora con clientes son distintos.

---

## 7. Pendientes de verificación

Nada de esta sección está afirmado como hecho.

**Lo que hay que conseguir**
- **Jørgensen (2019), IST 115.** A un clic: `https://nva.sikt.no/registration/019e68dcd4d6-54916087-4631-424c-bfad-5aa97ff22339`, archivo `.doc` con licencia CC-BY. Cuatro páginas. **Sin excusa.**
- **Lokan & Mendes (2017), EMSE 22(2).** Springer de pago. Es el del resultado negativo sobre ventanas móviles y sostiene cómo planteamos OE5(b). Vía: acceso institucional de ORT a Springer, o escribirle a Chris Lokan (UNSW Canberra).
- **Batselier & Vanhoucke (2016), PMJ 47(5).** SAGE de pago; Ghent lo tiene restringido; el PDF que OR-AS tenía público dio 404. Vía: acceso institucional a SAGE, o pedírselo a los autores.
- **Czado, Gneiting & Held (2009).** La versión de Biometrics es cerrada; hay tech report UW #518 abierto. Conseguir antes de F2.

**Cifras y citas a confirmar antes de escribir**
- **La cifra de sobreconfianza.** Hay tres números distintos circulando y son de trabajos distintos: **68%** (Jørgensen & Sjøberg 2003, verificado en su Tabla 5, 13 profesionales con feedback); **35%** en proyectos industriales y **62%** en estudiantes, ambos citados por J&S como provenientes de *Jørgensen, Teigen et al. 2002* — que **no es** la referencia [11] del anteproyecto (Jørgensen, Teigen & Moløkken 2004, JSS). Antes de escribir cualquiera de las tres, ubicar de qué estudio sale. La de 2004 sigue sin leerse.
- **Umbral de acuerdo para escalas ordinales.** El Emam deriva sus cuartiles para **kappa no ponderado, nominal**, y explícitamente no cubre kappa ponderado. Nuestros tiers son ordinales. Hay que decidir y declarar antes de correr OE5(a): o nominal y aplican esos umbrales, o kappa ponderado / alpha de Krippendorff ordinal y **hace falta otra fuente para el umbral, que todavía no tenemos**.
- **AIDev: versión y licencia.** El paper describe 932.791 PRs (corte 1/8/2025, cinco agentes); la ficha de Hugging Face hoy muestra 2.743.854 PRs y seis agentes. El paper **no declara licencia**; la ficha dice CC-BY-4.0. Si se usa, fijar versión y fecha de corte explícitamente. Y el paper **no explica cómo identifica los PRs agénticos**: eso está en el paper compañero arXiv:2507.15003, pendiente de leer.
- **Verificar AIDev de primera mano.** Confirmar que `pr_timeline` permite reconstruir, por PR, el par (momento del pronóstico, momento del desenlace) utilizable para backtesting. De eso depende si el plan B es real. **Tarea acotada; conviene hacerla antes de diciembre.**
- **Aceptaciones declaradas y no verificadas:** Kumar et al. (ASE 2025), AIDev y Dao et al. (MSR 2026) declaran aceptación en arXiv o en el encabezado del HTML, no cruzada contra el programa. El DOI de ACM de AIDev (10.1145/3793302.3797249) **no resuelve**. Lo mismo para varios del frente 1 (Li et al. EMNLP, Grotov & Malykh EMNLP Industry, Rabanser et al. ICML).
- **El Emam se leyó en la versión de reporte técnico** (ISERN-98-02, Fraunhofer IESE), no en la publicada en EMSE. Los umbrales coinciden con los que se citan universalmente, pero si se cita el paper de 1999 conviene cotejar.
- **Minku & Yao: secciones 11 y 12 no se pudieron leer** (amenazas a la validez y conclusiones). El resumen lo dice.
- **Jørgensen, Welde & Halkjelsvik:** Crossref lo lista en IEEE TEM 70(10), 2023, con DOI de 2021; la copia abierta de NTNU es de 2021. **Citar 2023.** Y la numeración de sus Tablas IV y V en el resumen puede ser una reconstrucción del extractor.
- **Citas de tercer nivel dentro de Cantarelli et al.** (Zarghami 2023, Zani & Adey 2025, Servranckx et al. 2021, Lovallo et al. 2012, Chadee et al. 2023, Park 2021, Fridgeirsson 2016): se reportan porque ellos las reportan. **Ninguna fue leída ni verificada.**
- **Miranda et al.: la cobertura de 11/15 la calculamos nosotros** a partir de sus Tablas 2 y 3. Con n = 15 no es estadísticamente concluyente y hay que presentarla como observación, no como resultado.

**Preguntas para el export de Rootstrap** (salieron de la lectura, y condicionan el diseño)
1. ¿Existe una **estimación puntual por tarea** en la telemetría? Sin ella, el baseline 2 (Jørgensen & Sjøberg) no aplica tal cual y hay que anclarlo a la mediana del modelo, con lo que deja de ser un baseline limpio "sin aprendizaje".
2. ¿Las duraciones vienen en **unidades enteras** (días, horas) o con resolución fina? De eso depende si necesitamos PIT no-randomizado.
3. ¿Hay tareas **en curso** al momento de cada corte histórico, y con qué frecuencia? De eso depende si entra censura al alcance comprometido.
4. ¿Se registran **horas** de intervención humana, o solo eventos? Determina si R6 es viable.
5. ¿Las duraciones se agolpan alrededor de los valores estimados? (El problema de las estimaciones auto-cumplidas que advierten Jørgensen & Sjøberg.)

---

## 8. Qué NO leer

Para que el tiempo rinda, también conviene decir qué descartamos y por qué:

- **Benchmarks de agentes** (SWE-bench, SWE-Lancer, HCAST, SWE-Marathon): miden capacidad en tareas autocontenidas, no entrega en proyectos. METR mismo publicó una nota enumerando por qué su "horizonte temporal" no es un pronóstico. Citar como contexto, no leer.
- **La mayor parte de la línea AIDev** (una docena de papers de MSR 2026 sobre merge, rechazo, conflictos, auto-merge, agentes revisores): todos analizan PRs agénticos en open source y ninguno agrega nada a AIDev + Dao para nuestro problema. Están listados en `LITERATURA.md` por si hay que citar "la literatura AIDev" en bloque.
- **Los híbridos sofisticados de RCF** (kNN para elegir la clase, gradient boosting, biclustering, weighted RCF): cada uno sería alcance nuevo con justificación nueva. El pooling parcial ya es nuestro híbrido.
- **DCL de Minku & Yao como implementación**: entra como fundamento del problema y precedente de evaluación online, no como algo a construir.
- **RCTs de productividad pre-agentes** (Peng et al. 2023, Google 2024): superados por Cui et al. 2026 (Management Science, 4.867 devs) si hace falta una cifra.

---

*Documento cerrado el 18/9/2026. Las tres referencias no conseguidas y los cinco puntos del §7 son lo que hay que resolver antes de que arranque F2 en noviembre.*

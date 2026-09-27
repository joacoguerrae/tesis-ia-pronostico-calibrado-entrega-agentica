# Dao, S. D. M., Huynh, T. K., Nguyen, L. P. Q., Pham, P. H., Tran, C. N., Nguyen, D. H. D. & Truong, B. T. (2026). Early-Stage Prediction of Review Effort in AI-Generated Pull Requests. MSR 2026 Mining Challenge. arXiv:2601.00753 · DOI 10.1145/3793302.3793609

**Estado de lectura:** leído completo desde https://arxiv.org/html/2601.00753v2 (v2, 27/1/2026).
**Tipo:** paper corto (5 páginas, 4 figuras) del Mining Challenge de MSR 2026. Aceptación **declarada por los autores** en el campo Comments de arXiv y en el encabezado del HTML con DOI de ACM; no verificada contra el programa. · **Datos:** AIDev v1.0, 33.707 PRs agénticos en 2.807 repos con >100 estrellas. · **Objeto:** agentes **autónomos** (Codex, Copilot, Devin, Claude) que abren PRs; predicción con features disponibles al momento de creación.
**Tiempo de lectura del original:** ~15 min · **Tiempo de lectura de este resumen:** ~7 min

## En una frase
Con features estructurales disponibles al abrir el PR (líneas agregadas/borradas, archivos tocados, entropía, largo de la descripción, si tiene plan explícito), un LightGBM predice qué PRs agénticos van a caer en el 20% de mayor esfuerzo de revisión con AUC 0,96 en split temporal y 0,83 en split por repos disjuntos, y de paso describen dos regímenes: 28,3% de PRs que se mergean en menos de un minuto y una minoría que el agente abandona cuando le piden cambios.

## Por qué está en nuestra lista (qué decisión del proyecto toca)
Es el paper más parecido a lo que queremos hacer con el plan B: predicción **en el momento de creación** de una unidad agéntica, con cuidado explícito de leakage y con varios esquemas de validación, incluido uno temporal. Muestra qué features tempranas funcionan sobre AIDev, qué tan fuerte es el "tamaño" como predictor, y deja un ejemplo de curva de calibración que hay que mirar con lupa porque es el único componente de calibración de su evaluación. Su métrica (esfuerzo de revisión) es además un proxy de "intervención humana", nuestra variable deseable.

## Resumen sección por sección

### Introducción
El cuello de botella con agentes ya no es generar código sino que el mantenedor humano gestione el ida y vuelta. Introducen "agentic ghosting": el agente abre un PR, le piden cambios, y nunca vuelve. Dos preguntas: RQ1, si el esfuerzo de revisión se puede predecir al crear el PR solo con señales estructurales; RQ2, qué comportamientos correlacionan con el ghosting. Contribuciones: operacionalizar el ghosting, un modelo "Circuit Breaker" (nombre del patrón de resiliencia: cortar antes de que el daño se propague) con AUC 0,96, y evidencia de que los cambios grandes, multi-componente y sin plan son los que rompen la interacción.

### Trabajo relacionado
Se diferencian de la literatura de Modern Code Review en que estudian PRs de agentes (no deterministas, a diferencia de bots tipo Dependabot) y en que cambian la variable objetivo: en vez de latencia hasta el merge, que según literatura previa correlaciona poco con el tamaño, usan esfuerzo (volumen de comentarios y reviews), que sí correlaciona.

### Metodología
- **Datos:** AIDev v1.0, 33.707 PRs, 2.807 repos. Identificación de agentes por metadatos (`type='Bot'`) más nombres de agentes generativos, excluyendo bots deterministas; auditoría manual con **94% de precisión**. Desglose (Tabla 2): Codex 21.799, Copilot 5.017, Devin 4.827, Claude 3.5 523. Suman 32.166, no 33.707; **la diferencia no se explica en el texto** (no mencionan a Cursor).
- **Variables objetivo (Tabla 1):**

| Objetivo | Definición |
|---|---|
| High Cost | Top 20% de PRs por Effort Score = suma de reviews + comentarios (incluyendo bots), umbral fijado en el set de entrenamiento |
| True Ghosting | PR rechazado (cerrado sin merge) Y con feedback humano Y sin commit posterior en más de 14 días |

  Robustez: recalculando sin mensajes de bots, 99% de las etiquetas coinciden. Variar el umbral de inactividad entre 7 y 30 días casi no cambia las etiquetas. La Figura 1 (ECDF, la curva acumulada de "qué fracción cerró antes de X días desde el feedback") justifica los 14 días.
- **Features:** 35 en total, en dos momentos. **T0 (creación):** complejidad (adiciones, borrados, archivos, entropía —cuán dispersos están los cambios entre archivos—), intención (largo del cuerpo, `has_plan`: flag por regex que busca "plan:" o "steps:", validado con 91% de precisión), contexto (lenguaje, agente, tipos de archivo, si toca tests, si toca CI/config). **T1 (pre-review):** agrega estado de CI y comentarios de bots. El paper no enumera las 35 una por una ni define formalmente la entropía.
- **Leakage:** el Circuit Breaker usa solo T0; T1 se excluye explícitamente porque ocurre después de la creación. Correlación de Pearson tamaño-esfuerzo ≈0,6.
- **Modelo y validación:** LightGBM (hiperparámetros no reportados; nada sobre semillas ni desbalance). Baselines: TF-IDF sobre descripción, tokens de paths, CodeBERT, solo-tamaño con log(cambios totales), y un ensemble apilado. Esquemas: **split temporal** (cronológico 80/20; no dicen por qué campo ordenan ni las fechas de corte), **repo-disjunto**, **leave-one-agent-out**, y **evaluación dentro de cuartiles de tamaño**. Métricas: AUC con IC 95% por bootstrap (cantidad de remuestreos no reportada), PR-AUC, Precision@20% y curva de calibración.

Antes de seguir: **AUC** es la probabilidad de que el modelo le asigne mayor puntaje a un PR caro elegido al azar que a uno barato elegido al azar; 0,5 es tirar la moneda, 1 es orden perfecto. **PR-AUC** es lo mismo sobre precisión y recall, y castiga más cuando la clase positiva es rara (acá, 20%). **Precision@20%** es qué fracción de los PRs del top 20% son realmente caros.

### Resultados RQ1: predictibilidad del esfuerzo

| Modelo | Features | Split | AUC | PR-AUC |
|---|---|---|---|---|
| TF-IDF (descripción) | texto | repo-disjunto | 0,57 | — |
| Tokens de paths | texto | repo-disjunto | 0,75 | — |
| CodeBERT | embeddings | repo-disjunto | 0,52 | — |
| Solo tamaño | log(cambios) | repo-disjunto | 0,65 | — |
| LightGBM | T0 | temporal | 0,9571 | 0,8812 |
| Solo tamaño | log(cambios) | temporal | 0,9330 | 0,8700 |
| LightGBM | T0 | repo-disjunto | 0,8345 | 0,8719 |
| Ensemble apilado | T0 | repo-disjunto | 0,8342 | 0,8747 |

Lectura: la semántica del texto no ayuda; la estructura sí. **Pero mirá la diferencia entre solo-tamaño y el modelo completo en split temporal: 0,933 vs 0,957. Casi todo el AUC temporal es tamaño.** En repo-disjunto la brecha es mayor (0,65 vs 0,83), o sea que el resto de las features aportan sobre todo para generalizar a repos nuevos.

Tabla 4 (AUC dentro de cuartiles de tamaño): pequeño <51 LOC, n=1.699, AUC 0,96; mediano 51–124, n=1.666, 0,88; grande 124–324, n=1.682, 0,82; XL >324, n=1.680, 0,88. Tabla 5 (Precision@20% dentro de cuartil, solo-tamaño vs completo): pequeño 0,009 → 0,035; mediano 0,069 → 0,144; grande 0,329 → 0,504 (+17,5 pp).

**Figura 2:** (a) curva de utilidad top-K: revisando el 20% mejor rankeado capturan **~69%** de los PRs de alto esfuerzo. **(b) curva de calibración:** el texto solo dice que hay "alineación cercana" con la diagonal. **No** reportan número de bins, Brier, ECE, ni en qué split está calculada, ni si hubo recalibración. Una curva de calibración —que compara "de los PRs a los que les dijiste 30%, ¿qué fracción fue realmente cara?"— con un solo panel y sin números es evidencia débil; para nuestro estándar (cobertura, PIT, CRPS) no alcanza, y hay que decirlo así en la tesis.

### Resultados RQ2: ghosting

| Agente | PRs | Merge instantáneo (<1 min) | Ghosting (sobre rechazados con feedback) |
|---|---|---|---|
| Codex | 21.799 | 42,9% | 10,0% |
| Claude 3.5 | 523 | 2,9% | 3,1% |
| Devin | 4.827 | 1,0% | 0,9% |
| GitHub Copilot | 5.017 | 0,1% | 2,3% |

Global: **28,3% de merges instantáneos**; del 71,7% restante que entra en revisión, 68,7% termina aceptado; entre los 2.364 PRs rechazados con feedback humano, **3,8% son ghosting**. Figura 3: los merges instantáneos tienen mediana de 68 cambios vs 104 en los normales, y tocan config crítica en 7,1% vs 18,4%. Figura 4: el riesgo sube con cambios multi-componente sin plan; tocar CI solo no sube el riesgo una vez controlados los confusores.

### Robustez, amenazas y conclusión
Leave-one-agent-out y splits cronológicos mantienen AUC >0,95 (eso se refiere a los esquemas temporal y por agente, no al repo-disjunto de 0,83). SHAP: dominan adiciones, largo del cuerpo y cambios totales; `has_plan` es predictor negativo fuerte de ghosting. Amenazas declaradas: la métrica incluye bots (mitigado), claims correlacionales, recall de `has_plan` desconocido, PRs abandonados sin cierre no se capturan, ruido residual en identificación de agentes, necesidad de reentrenar. Paquete de replicación: https://zenodo.org/records/17993901.

## Los números que hay que recordar
- **AUC 0,9571 temporal / 0,8345 repo-disjunto** para LightGBM con T0 (Tabla 3).
- **Solo tamaño: 0,9330 temporal / 0,65 repo-disjunto** — casi todo el poder predictivo temporal es tamaño (Tabla 3).
- **28,3% de merges en <1 min**; Codex 42,9% vs Copilot 0,1% (Tabla 2).
- **Ghosting 3,8%** sobre 2.364 rechazados con feedback; Codex 10,0%, Devin 0,9% (Tabla 2).
- **69% de los PRs caros capturados revisando el 20%** (Figura 2a).
- **94%** precisión al identificar agentes; **91%** en `has_plan`; **99%** acuerdo de etiquetas sin bots.

## Limitaciones
**Declaradas:** las de su sección de amenazas (arriba).
**Nuestras:** calibración afirmada, no medida (sin bins, sin Brier/ECE, sin decir en qué split) — no sirve como evidencia de que un modelo sobre AIDev esté calibrado. El objetivo es un **ranking binario** (top 20%), no una distribución sobre una cantidad continua, y el umbral depende del mix de agentes. La suma de agentes no cuadra con el total (32.166 vs 33.707), sin explicación. El split temporal es 80/20 una sola vez: **no es backtesting de origen móvil**, así que no sabemos cómo degrada con el tiempo ni cuánto pesa la mezcla cambiante de agentes. Hiperparámetros, semillas y manejo de desbalance no reportados. Y "esfuerzo" cuenta mensajes, no horas humanas; mide revisión OSS, no una consultora con cliente.

## Qué tomamos tal cual y qué hacemos distinto
**Tomamos:** la disciplina de separar features **T0 (creación)** de **T1 (post-creación)** y excluir T1 — es nuestra misma regla anti-leakage, con precedente citable. El menú de features tempranas que funcionan sobre AIDev, y el hallazgo de que el tamaño domina: **cualquier baseline nuestro tiene que incluir un modelo "solo tamaño"** para no vendernos una mejora que no existe. La validación **repo-disjunta** como análogo de "proyecto nuevo": con ~10 proyectos, un leave-one-project-out es lo natural, y este paper da precedente de que la generalización entre repos cae bastante (0,96 → 0,83). La estratificación por régimen: si usamos AIDev, los PRs de <1 minuto son un régimen aparte y hay que excluirlos o modelarlos separado, porque distorsionan cualquier distribución de tiempo hasta desenlace. Y el esfuerzo de revisión como proxy ordinal de intervención humana en el plan B.
**Hacemos distinto:** nuestro objetivo es una **distribución de la fecha de entrega**, no una clase binaria; la evaluación es cobertura, PIT y CRPS, no AUC. La curva de calibración de este paper es el mínimo que hay que superar: reportar bins, conteos por bin y una métrica numérica, en cada origen del backtesting. Backtesting de **origen móvil** en vez de un corte 80/20 único. Y si el plan B se activa, decir explícitamente que estamos cambiando de pregunta (tiempo hasta merge de un PR agéntico en OSS) y no fingir equivalencia. Replicar su modelo no está en R1–R5; lo que sí entra es reutilizar sus features y su esquema anti-leakage.

## Si igual lo vas a abrir
Andá directo a la Tabla 1 (definiciones), la Tabla 3 (AUC por esquema) y la Figura 2b (calibración) para ver con tus ojos lo poco que hay; después la Tabla 2 (regímenes por agente). Leé la sección de amenazas, es honesta y corta. Salteá related work e implicancias éticas. Si vas a replicar algo, lo que importa está en el paquete de Zenodo.

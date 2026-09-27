# Kumar, A., Bajpai, Y., Gulwani, S., Soares, G. & Murphy-Hill, E. (2025). Why AI Agents Still Need You: Findings from Developer-Agent Collaborations in the Wild. ASE 2025. arXiv:2506.12347

**Estado de lectura:** leído completo desde https://arxiv.org/html/2506.12347v3 (más https://arxiv.org/abs/2506.12347v3 para metadatos). Ojo: el render HTML de v3 muestra como título "Sharp Tools: How Developers Wield Agentic AI in Real Software Engineering Tasks"; el título de la referencia ("Why AI Agents Still Need You…") es el que figura en el listado de arXiv. Es el mismo paper (mismos autores, mismos números), pero conviene citar con el título del listado y anotar el alias.
**Tipo:** estudio empírico observacional (sesiones de laboratorio con desarrolladores reales sobre issues reales). Aceptación en ASE'25 **declarada por los autores** en el campo "Comments" de arXiv; no verificada contra el programa. · **Datos:** 19 desarrolladores de Microsoft, 33 issues abiertos de repos públicos de dos organizaciones de GitHub de la empresa, 269 prompts, grabaciones de pantalla/audio, cuestionarios pre y post. · **Objeto:** agente **asistido** dentro del IDE (Cursor Agent v0.47 con Claude 3.5 Sonnet), con humano en el loop. No es benchmark ni agente autónomo.
**Tiempo de lectura del original:** ~45 min · **Tiempo de lectura de este resumen:** ~7 min

## En una frase
Observaron a 19 desarrolladores profesionales resolviendo 33 issues reales con un agente de IDE y encontraron que apenas la mitad terminó bien, que quienes iban de a pasos y aportaban conocimiento propio del repo tuvieron mucho más éxito (83% vs 38%), y que las fallas principales fueron de comunicación (acciones no pedidas, verbosidad, sicofancia, sobreconfianza) y de debugging/testing, más que de generación de código.

## Por qué está en nuestra lista (qué decisión del proyecto toca)
Toca directamente la variable "intervención humana" (deseable, R6–R8) y la modelización de las iteraciones de QA/escalaciones. El paper da evidencia de **por qué** una tarea ejecutada por agente no se resuelve sola: el humano interviene para dar contexto experto, corregir, debuggear y testear. Eso justifica que en nuestra telemetría la duración dependa de cuántas rondas humano-agente hubo, y que "horas de intervención humana" sea un predictor plausible. También sirve para argumentar en la introducción que los benchmarks autónomos (SWE-bench y compañía) no describen cómo se entrega software con agentes en una consultora.

## Resumen sección por sección

### Introducción y preguntas de investigación
Parten de que los agentes de ingeniería de software se evalúan casi siempre en modo autónomo (SWE-bench, LiveCodeBench, SWE-Lancer), pero en la práctica se usan con un humano al lado. Tres preguntas: RQ1, cómo colaboran los desarrolladores con el agente para cerrar issues abiertos; RQ2, cuáles son las barreras de comunicación; RQ3, qué factores explican el éxito. Se presentan como el primer estudio empírico de colaboración desarrollador-agente sobre issues reales.

### Método
- **Agente:** Cursor Agent (v0.47, Claude 3.5 Sonnet), elegido tras revisar VSCode Agent Mode, Windsurf Cascade, Cline y Amazon Q, porque incorpora solo los archivos abiertos y la posición del cursor como contexto.
- **Participantes:** 19 empleados de Microsoft que ya habían contribuido a los repos elegidos. Repos con >50 archivos fuente, >500 estrellas y mantenimiento activo. Demografía (Tabla I): 6 SWE I/II, 7 senior, 5 principal/manager, 1 consultor; experiencia desde 0–2 años (1) hasta ≥16 (5); 14 hombres, 5 mujeres; 10 en EE.UU., 2 India, 2 Kenia, 2 Israel, 2 Alemania, 1 China. Solo 3 habían usado Cursor antes; 18 de 19 habían usado Copilot Chat.
- **Sesiones:** ~60 min cada una, con instrucción explícita de usar el agente para todo. 33 issues en total.
- **Codificación:** dos libros de códigos. Uno de acciones del participante (adaptado de la taxonomía CUPS); otro de trayectoria del chat. Kappa de Cohen —medida de cuánto coinciden dos anotadores más allá del azar, donde 1 es acuerdo perfecto— de **0,92 y 0,89**.
- **Resultado por issue:** éxito completo (10), éxito de parche (6: conformes con el código pero faltaba configuración o tests), incompleto (10), sin progreso (2), abandonado (1). Cuatro issues se descartaron por razones externas, así que el 55% se calcula sobre 29 válidos (16/29).
- Member checking al final. No usaron estadística inferencial por el tamaño de muestra; todo descriptivo.

### RQ1: cómo colaboran
Dos estrategias de delegación:

| Estrategia | Prompts prom. por issue | Éxito | Leen código a mano |
|---|---|---|---|
| One-shot (pegan el issue entero y piden la solución) | 7,0 | 38% (6/16) | 60% (9/15) |
| Incremental (parten en sub-tareas, un prompt por paso) | 11,0 | 83% (15/18) | 83% (15/18) |

Tipos de pedido sobre los 269 prompts (no excluyentes): 50% cambios de código, 27% explicaciones del codebase, 16% correr tests, 11% explicar un cambio. Promedio general: 8,2 prompts por issue; features 11,2 vs bugs 6,3.

Conocimiento que aportan: distinguen **contextual** (lo que está en el issue o en logs) de **experto** (convenciones e implementación que no se ven en el código). El experto aparece en 49% de los prompts que piden código nuevo y en 65% de los que piden refinar. Sube con familiaridad con el repo (70% con ≥10 commits en 4 meses vs 48%) y con experiencia previa en Cursor (81%).

Trabajo manual: debuggearon/testearon a mano en 21 de 33 issues; escribieron código a mano en 14, y en 10 de esos 14 solo editaron lo que propuso el agente.

Revisión de salidas: siguieron la ejecución en vivo en 84% de los prompts; revisaron el diff en 67% de las respuestas con código; leyeron explicaciones tras 39% de las respuestas. Los que ya usaban Cursor leían explicaciones solo en 18% (vs 35%). En el cuestionario post (Figura 5), "explicaciones detalladas" quedó como la feature menos importante.

Manejo de errores: 52% de los prompts de código fueron refinamientos; rechazaron cambios solo el 10% de las veces; usaron checkpoint para volver atrás en 15% de los issues; frenaron al agente en 11% de los prompts.

### RQ2: barreras de comunicación
1. **Falta de conocimiento tácito:** el agente no captura lo que el dev sabe por experiencia.
2. **Acciones no pedidas:** en 38% de los prompts que no pedían código, igual cambió código; en 10% de los que no pedían ejecutar, corrió comandos de terminal. Con comandos de terminal, la probabilidad de que el humano lo frenara era 61% vs 21%. Un participante abandonó el issue porque el agente le rompió el entorno.
3. **Sincronía:** trabajar en paralelo genera conflictos.
4. **Verbosidad:** cinco participantes se quejaron de respuestas largas.
5. **Sicofancia:** si le decís "está mal" revierte sin discutir, y eso erosiona la confianza.
6. **Sobreconfianza:** nunca duda aunque esté errado. Frenaron al agente en 39% de las respuestas con más de 3 acciones vs 9% con ≤3.
7. **Sugerencias de seguimiento inútiles:** aparecen en 62% de las respuestas pero solo 7% de los prompts siguientes las retoman.
8. **Debugging y testing:** el agente es flojo para localizar bugs y lidiar con comandos de entorno; el 64% de intervención manual en verificación es una respuesta forzada, no una elección.

### RQ3: factores de éxito
| Factor | Con | Sin |
|---|---|---|
| Estrategia incremental | 83% | 38% (one-shot) |
| Aporte de conocimiento experto | 64% (14/22) | 29% (2/7) |
| Escribir código a mano | 79% (11/14) | 33% (5/15) |
| Debuggear/testear a mano | 53% (10/19) | 60% (6/10) |
| Experiencia previa con Cursor | 75% (3/4) | 52% (13/25) |

Issues exitosos: más prompts (10,3 vs 7,1); los que no pidieron ningún refinamiento tuvieron 30% de éxito. Por tipo: UI 100% (5/5), refactors 67% (2/3), features 50% (4/8), bugs no-UI 38% (5/13). Por lenguaje: C# 100% (3/3), TypeScript 63%, C++ 50%, Python 44%, Java 0% (0/1); concluyen que el lenguaje no discrimina, a diferencia de los benchmarks autónomos.

### Discusión, amenazas y conclusión
Implicancias de diseño: calibrar el alcance de lo que hacen, juntar información antes de proponer el fix, discutir en serio en vez de dar la razón. Amenazas: todos de una empresa con cultura pro-IA; N chico sin inferencia; mayoría sin experiencia previa (captura uso temprano); efecto observador; instrucción de usar IA para todo; herramienta y modelo de principios de 2025.

## Los números que hay que recordar
- **55% de éxito** (16/29 issues válidos).
- **83% vs 38%**: incremental vs one-shot; 11,0 vs 7,0 prompts por issue (RQ1/RQ3).
- **64% vs 29%**: con vs sin aporte de conocimiento experto (RQ3).
- **Debugging/testing manual en 21 de 33 issues (64%)** y no correlaciona con éxito (53% vs 60%) — limitación del agente.
- **38%** de acciones de código no solicitadas; **10%** de comandos de terminal no pedidos; frenado 61% vs 21% cuando hay terminal.
- **κ = 0,92 / 0,89** en los libros de códigos.

## Limitaciones
**Declaradas:** una sola empresa, N=19/33, uso temprano de la herramienta, observador, instrucción forzada de usar IA, snapshot de Cursor 0.47 + Claude 3.5 Sonnet.
**Nuestras:** (a) sesiones de 60 minutos, no tareas de días: **no dice nada de duración calendario ni de latencias de cliente**; de hecho los autores declaran explícitamente que no analizaron duraciones, para no sesgar hacia participantes que repetían acciones en intervalos cortos. (b) Es un agente de IDE con humano al lado, no un pipeline agéntico de consultora; la intensidad de intervención humana acá es casi total por diseño. (c) Ningún número tiene intervalo de confianza; los porcentajes con denominadores de 3 o 4 son anecdóticos. (d) El desenlace "éxito" es la satisfacción del participante, no un merge ni una entrega al cliente. (e) Discrepancia de título entre versiones de arXiv.

## Qué tomamos tal cual y qué hacemos distinto
**Tomamos:** la idea de que la carga de una tarea agéntica se explica más por rondas de refinamiento y por verificación humana que por generación de código — respalda medir **iteraciones de QA** y **escalaciones** como covariables (R1–R5, sin sumar alcance). La distinción contextual vs experto como forma de pensar qué información existía al momento del pronóstico: el contexto del ticket está en t0; el conocimiento experto aparece durante la ejecución y no se puede usar como predictor en t0 sin leakage. La evidencia de que la partición incremental mejora el resultado: si la consultora versiona su proceso, la **versión del proceso** es una covariable con respaldo bibliográfico. Y el argumento para la introducción de que SWE-bench y afines no representan el trabajo real.
**Hacemos distinto:** nosotros no medimos éxito binario en una sesión; pronosticamos **fecha de entrega** con distribución calibrada y evaluamos con cobertura, PIT y CRPS. Para "horas de intervención humana" (R6–R8) el paper sugiere qué contar (prompts de refinamiento, código a mano, debugging manual, frenadas), pero eso es exactamente lo que hay que sacar del camino crítico: registrar si la telemetría lo trae, no diseñar instrumentación nueva. AIDev como plan B no captura nada de esto (no hay sesiones de IDE ni prompts), así que esta variable existiría solo con la consultora.

## Si igual lo vas a abrir
Leé completa la sección RQ3 (tablas de éxito por estrategia, conocimiento experto y tipo de issue) y la lista de barreras de RQ2. La Tabla I (demografía) solo si necesitás describir la muestra. Salteá las Tablas II y III (libros de códigos) y el detalle de los cuestionarios salvo que quieras discutir diseño de agentes.

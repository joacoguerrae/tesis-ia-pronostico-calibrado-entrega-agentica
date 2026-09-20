# Tesis — Pronóstico calibrado de entrega agéntica
## Nota de contexto y decisiones

*Documento vivo. Última actualización: setiembre 2026.*
*Objetivo: que cualquier sesión nueva entienda el proyecto y, sobre todo, **por qué** es así y no de otra manera.*

---

## 1. Qué es el proyecto en una frase

Un sistema de pronóstico probabilístico para entrega de software desarrollada con agentes de IA que **se autoevalúa**: dada la telemetría histórica y el plan de un proyecto nuevo, produce la distribución de fechas de finalización y el boletín de calibración que dice cuánto creerle a esa distribución.

**Pregunta de tesis:** ¿se puede pronosticar de forma calibrada la entrega ejecutada por agentes, y qué aporta cada capa del modelo sobre baselines simples?

**El diferencial no es el motor de pronóstico** (eso es conocido desde hace décadas) **sino la capa de evaluación**: medir si el "P80" del sistema significa realmente 80%.

---

## 2. Contexto institucional

- **Maestría en IA**, Facultad de Ingeniería, Universidad ORT Uruguay. Segundo año.
- **Vía producto**, no investigación. Decisión firme del equipo.
- **Equipo:** Joaquín Guerra, Germán Pazos, Ramiro Sanes.
- **Tutora:** referente académica que revisa el anteproyecto.
- **Matías:** referente de la maestría consultado sobre viabilidad de opciones.
- **Socio externo:** Rootstrap (empresa de desarrollo de software). Aporta la telemetría. **No hay insider en la empresa** — la relación es externa, todo acuerdo tiene que estar por escrito.

**Fechas:** anteproyecto ~mediados de setiembre 2026. Entrega final abril 2027.
**Dedicación parcial** — ninguno de los tres tiene esto como ocupación principal.

---

## 3. Decisiones tomadas y por qué

**Vía producto, no investigación.** El entregable es un sistema que corre, con un usuario real y una decisión comercial detrás (cotizar a precio fijo). La investigación queda *adentro* del producto, no al costado.

**La unidad primaria de análisis es la tarea/capability, no el proyecto.** Hay ~10 proyectos históricos. Con n=10 no se puede validar calibración a nivel proyecto (sacar entre 6 y 10 aciertos de 10 es estadísticamente indistinguible). A nivel tarea hay del orden de 100–300 observaciones, y ahí sí se hace estadística. El nivel proyecto se reporta como demostración (leave-one-project-out), no como validación.

**Alcance en dos niveles.** Comprometidos (R1–R5) y deseables (R6–R8). Los comprometidos no dependen de terceros más allá del export inicial.

**Punto de control go/no-go en diciembre 2026.** Si los datos no sostienen el torneo a nivel tarea, se recorta el alcance y se declara. Está escrito en el anteproyecto — es el seguro contractual del equipo.

**Un resultado desfavorable es un resultado.** Si el modelo está mal calibrado, o si los baselines simples le empatan al modelo completo, eso es un hallazgo publicable y contraintuitivo, no un fracaso. El diseño está armado para dar información en cualquier dirección.

**No fijar métodos prematuramente.** Corrección explícita de la tutora: en el anteproyecto no se declaran decisiones técnicas (Montecarlo, deep learning), se declara qué hay que decidir y con qué criterios. Cada método fijado ahora es deuda de justificación bibliográfica después.

**No se replica el delivery system de Rootstrap.** Eso ya existe y es de ellos. La tesis es la capa de evaluación más la salida que a su método le falta (horas de intervención humana).

**El proyecto es la línea de Rootstrap, sin plan B.** Se evaluaron y descartaron alternativas del lado médico (evaluador de razonamiento clínico con referente en Pediatría; modelos sobre encuestas públicas ENDIS/ENNAJ). No hay proyecto alternativo en reserva. Consecuencia directa: el acuerdo escrito con Rootstrap y el dataset público AIDev como respaldo de datos pasan de deseables a **críticos**.

---

## 4. Alcance

**Comprometidos**
- R1. Esquema canónico de telemetría + pipeline de ingesta sobre datos reales.
- R2. Motor de pronóstico v1 operativo (distribuciones y cuantiles).
- R3. Boletín de calibración automático sobre el histórico (backtesting con origen móvil).
- R4. Comparación contra ≥2 baselines, con diseño congelado antes de ver resultados.
- R5. Informe final con los hallazgos, cualquiera sea su dirección.

**Deseables**
- R6. Distribución de horas de intervención humana como segunda variable pronosticada.
- R7. El segundo estudio empírico de OE5 (el no priorizado).
- R8. Proyección viva sobre un proyecto en curso.

**Los dos estudios de OE5** (se prioriza uno, el otro queda deseable):
- (a) Confiabilidad entre evaluadores del etiquetado de categorías de tarea.
- (b) Cuánta historia usar cuando el proceso cambia entre versiones (ventanas móviles, ponderación por recencia).

**Fuera de alcance:** frailties compartidas, dependencias ocultas muestreadas, replicar el motor completo del whitepaper.

---

## 5. Baselines del torneo (pre-especificados)

1. **Conteo puro** — todas las tareas intercambiables, sin categorías. *Es el que más cuesta ganarle y el que hay que reportar sí o sí.*
2. **Priors por categoría sin aprendizaje** — la tabla de referencia sin actualización bayesiana.
3. **Estimación humana**, donde exista registro.

---

## 6. Riesgos vivos

| Riesgo | Mitigación |
|---|---|
| Dependencia de Rootstrap para los datos | Esquema canónico que desacopla el sistema de la fuente; dataset público AIDev como alternativa para correr el mismo diseño |
| El histórico no tiene categorías asignadas *antes* de ejecutarse | Etiquetado a ciegas (solo la spec, nunca el resultado) por 2+ personas; el ejercicio habilita el estudio OE5(a) |
| No estacionariedad: el proceso cambia entre versiones del loop | Segmentación por versión de proceso; estudio OE5(b); reportar el efecto en vez de suponerlo nulo |
| Dedicación parcial | Alcance en dos niveles; go/no-go en diciembre |
| **Leakage** en el backtesting | En cada paso el modelo solo puede usar información que existía en ese momento. Es el error más común y más difícil de detectar |

---

## 7. Pendientes

- [ ] **Mail de Rootstrap** con: alcance del acceso (telemetría cruda vs export curado), permiso de publicar **incluidos resultados desfavorables**, condiciones de anonimización, e **interlocutor con nombre y apellido**. — *Bloqueante.*
- [ ] Confirmar si el whitepaper de Rootstrap puede citarse públicamente o anexarse a la memoria.
- [ ] Confirmar si la telemetría guarda **el texto/descripción de las tareas** o solo los resultados. Si solo resultados, se cae el pronóstico condicional y hay que volver al conteo.
- [ ] Confirmar desde cuándo se congelan etiquetas ex ante en producción, y cuántas versiones de proceso cruzan los ~10 proyectos.
- [ ] Verificar DOIs y datos editoriales de todas las referencias.
- [ ] Confirmar si la cátedra pide correos institucionales.

---

## 8. Glosario

- **Capability / tarea** — unidad de trabajo del delivery system. Unidad primaria de análisis del proyecto.
- **Calibración** — que las probabilidades correspondan a frecuencias reales: de todo lo declarado P80, ~80% debe caer antes de esa fecha.
- **Sharpness** — qué tan angosto es el intervalo. Se evalúa *sujeto a* calibración: un rango angosto sin calibración es precisión falsa.
- **Backtesting con origen móvil** — entrenar con lo anterior a un punto, pronosticar lo siguiente, avanzar el punto y repetir. Nunca usar información posterior al origen.
- **Cobertura de cuantiles** — contar en qué porcentaje el resultado real cayó antes de cada cuantil declarado.
- **PIT** — en qué percentil de la distribución cayó cada resultado real; deberían repartirse uniformemente.
- **CRPS** — puntaje único de toda la distribución; penaliza estar lejos y ser innecesariamente ancho. Permite el torneo entre modelos.
- **Ground Truth** (en el vocabulario de Rootstrap) — **no** es el sentido de ML. Es la especificación completa y autoritativa del software a construir.
- **No estacionariedad** — el proceso cambia con el tiempo, así que el historial viejo describe un proceso que ya no existe.

---

## 9. Referencias base

Todas requieren verificación de DOI antes de la entrega.

1. Miranda & Faria (2021), *An analysis of Monte Carlo simulations for forecasting software projects*, ACM SAC '21. — **Precedente directo y baseline numérico.**
2. Batselier & Vanhoucke (2016), Project Management Journal 47(5). — Reference class forecasting evaluado empíricamente.
3. Jørgensen, Teigen & Moløkken (2004), JSS 70(1–2). — **Baseline humano publicado:** los intervalos de 90% contienen el real solo 60–70% de las veces.
4. Jørgensen, *Evaluating probabilistic software development effort estimates: Maximizing informativeness subject to calibration*. — **La metodología de evaluación del proyecto.**
5. Gneiting & Raftery (2007), JASA 102(477). — Reglas de puntuación propias.
6. Lokan & Mendes (2009), ESEM. — Ventanas móviles.
7. Amasaki & Lokan, replicated study, EMSE. — Ventanas ponderadas.
8. Kumar et al. (2025), *Why AI agents still need you*, ASE 2025, arXiv:2506.12347. — Colaboración humano-agente; n chico, nivel IDE. **El hueco está acá.**
9. AIDev, arXiv:2602.09185. — Dataset público de agentes en GitHub. **Plan B de datos.**
10. Flyvbjerg (2006), Project Management Journal 37(3).
11. Vacanti (2015), *Actionable Agile Metrics for Predictability*.
12. Rootstrap (2026), *Estimations: about to be solved*. Whitepaper. — Fuente primaria del socio.

---

## 10. Convenciones de trabajo

- Todo en español rioplatense informal.
- Preguntar antes de producir entregables largos.
- Nada de datos personales ni información identificable de clientes en el repositorio ni en las conversaciones.
- Los experimentos se congelan antes de correrse: el diseño de evaluación se escribe primero, se corre después.

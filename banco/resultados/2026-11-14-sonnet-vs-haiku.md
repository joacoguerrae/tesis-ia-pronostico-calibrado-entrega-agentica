# Primera comparación A vs B en el banco: Sonnet 5.5 vs Haiku 5.5

14/11/2026 · Joaquín Guerra · Exportado del doc compartido "Primera comparación A vs B en el banco" (el gráfico de efectos no se incluye; los mismos números están en los facts de abajo).

## Qué se corrió

El experimento `a-vs-b-haiku` corrió 80 veces sin problemas: 8 tareas (T01 a T08) × 5 repeticiones × 2 versiones, con A y B intercaladas al azar (semilla 1114). Corrió en la máquina de Joaco (WSL, Claude Code 2.1.312) y costó USD 5,78.

| Versión | Configuración | Archivo |
| --- | --- | --- |
| A | Claude Code en modo bare con Sonnet 5.5 y la plantilla básica | `banco/versiones/A.json` |
| B | Igual a A, cambiando solo el modelo a Haiku 5.5 | `banco/versiones/B.json` |

Las 80 corridas terminaron con `success`. Ninguna llegó a un tope de costo, turnos o tiempo, y ninguna tocó el banco.

Promedio por corrida:

| Versión | Éxito | Costo (USD) | Duración (s) | Pasos | Tokens de entrada | Tokens de salida |
| --- | --- | --- | --- | --- | --- | --- |
| A | 100 % | 0,127 | 57,4 | 7,1 | 86.972 | 7.938 |
| B | 100 % | 0,017 | 106,0 | 13,1 | 320.761 | 20.847 |

Los números de A coinciden con el piloto de Germán en otra máquina (USD 0,130 y 52 s por corrida): el banco se reproduce entre máquinas. La duración sale un poco más alta acá, y por eso nunca hay que mezclar máquinas dentro de una misma comparación.

## Resultado

El sistema produjo su primer trade-off real: Haiku cuesta 88 % menos, pero tarda 72 % más, da 83 % más pasos y usa el triple de tokens de entrada, con el mismo éxito.

Todas las diferencias tienen intervalos lejos de cero. Lo que escribió el generador, tal cual:

```text
- La tasa de éxito es equivalente entre A y B: la diferencia queda dentro de ±5 puntos (IC 90 %: de +0,0 a +0,0 puntos; 8 tareas).
- De A a B, el costo baja 88 % (IC 95 %: de -90 a -85 %; 8 tareas).
- De A a B, los tokens de entrada suben 238 % (IC 95 %: de +176 a +315 %; 8 tareas).
- De A a B, los tokens de salida suben 141 % (IC 95 %: de +96 a +194 %; 8 tareas).
- De A a B, los pasos suben 83 % (IC 95 %: de +63 a +105 %; 8 tareas).
- De A a B, la duración sube 72 % (IC 95 %: de +43 a +105 %; 8 tareas).
```

## Cómo leer los números del generador

La tabla de facts del generador tiene tres columnas que necesitan traducción:

- **`efecto`** está en escala logarítmica. Para pasarlo a porcentaje: e^efecto − 1. En el costo, e^(−2,09) = 0,12, o sea, B cuesta el 12 % de A: baja 88 %.
- **`ic_inf` / `ic_sup`** es el rango donde está el efecto real con 95 % de confianza. Todos los rangos de esta comparación están lejos de cero, así que ninguna diferencia es casualidad.
- **`q`** es la probabilidad de que la diferencia sea azar, corregida por estar mirando 6 métricas a la vez (Benjamini-Hochberg). Todas dan prácticamente 0.

Por qué tiene sentido que B sea más barata aunque use 3,4 veces más tokens de entrada: cada token de Haiku 5.5 cuesta unas 20 veces menos que uno de Sonnet 5.5 (USD 0,10 contra 2 por millón de entrada, USD 0,50 contra 10 por millón de salida). Haiku da más vueltas, 13 pasos contra 7, y por eso tarda más, pero cada vuelta es muy barata.

## Lo que no cierra

1. **El fact de éxito es engañoso.** Dice "equivalente, ±5 puntos, IC de 0 a 0", pero eso no se demostró: las 80 corridas pasaron todos los tests y no hubo variación para medir. El generador debería decir algo como "sin variación: todas las corridas resolvieron todas las tareas" en vez de declarar equivalencia. Es un arreglo chico en `generador.py`, pero es un error de lógica que hay que hablar con Germán.
2. **Las tareas son demasiado fáciles, y ahora hay evidencia.** Ni siquiera Haiku falló una. Mientras sea así, la tesis no puede decir nada sobre calidad, solo sobre eficiencia. Pasar a tareas más difíciles es lo más urgente del banco.
3. **Esto no valida el generador.** Los efectos son enormes (−88 %, +72 %) y cualquier método los detectaría. Sirve como control: muestra que el flujo entero anda de punta a punta y que el sistema ve lo que esperábamos. La validación de verdad, la de efectos chicos, sigue siendo la de DeepSWE.
4. **El costo es una estimación de Claude Code, no lo facturado.** Siguen pendientes dos chequeos: si la versión 2.1.312 usa el precio nuevo de lectura de caché de Sonnet 5.5 (que bajó de USD 0,20 a 0,10 por millón el 7 de octubre de 2026) y si aplica el recargo de Haiku 5.5 para prompts de más de 100 mil tokens. Si usa el precio viejo, el costo de A queda inflado y el fact exagera el ahorro de B. Se puede verificar recalculando con los tokens de cada llamada, que quedaron guardados.

## Tareas más difíciles: T09 a T11

Las tres tareas nuevas tampoco distinguen versiones: Sonnet 5.5 y Haiku 5.5 las resolvieron en las 30 corridas.

Cada una prueba un tipo de dificultad distinto: diagnóstico de un bug plantado, concurrencia entre procesos y lógica de calendario. Todas tienen tests que hacen fallar los arreglos a medias. Se corrieron 5 veces por tarea con cada versión, en dos experimentos separados (`calibracion-t09-t11` y `calibracion-t09-t11-b`).

| Tarea | Éxito A (Sonnet 5.5) | Éxito B (Haiku 5.5) | Duración A (s) | Duración B (s) |
| --- | --- | --- | --- | --- |
| T09 horarios corridos | 5/5 | 5/5 | 33–42 | 64–71 |
| T10 reservas simultáneas | 5/5 | 5/5 | 43–49 | 80–109 |
| T11 clases recurrentes | 5/5 | 5/5 | 85–112 | 199–256 |

Contando la comparación de las 8 tareas originales, son 11 tareas y unas 110 corridas sin una sola falla. En este banco, el éxito está saturado incluso para Haiku: no distingue versiones, y la eficiencia sí. La propuesta es usar el éxito como control de que la calidad no empeora y centrar la evaluación en los trade-offs de eficiencia.

Las duraciones de la tabla son solo descriptivas. Las dos calibraciones corrieron una después de la otra, sin intercalar A y B, y en ese caso el generador da falsas alarmas: 44 % en la validación de Germán.

## Siguientes pasos posibles

- [x] Compartir con Germán y Ramiro: subir las corridas de `a-vs-b-haiku` al repo en una rama, con este resumen.
- [ ] Arreglar el fact de éxito sin variación en `generador.py`.
- [ ] Verificar el costo recalculando desde los tokens de cada llamada con la tarifa vigente.
- [x] Diseñar tareas más difíciles (T09 en adelante) para que el éxito distinga versiones. Hechas T09 a T11 (pull request #3). Tampoco distinguen versiones.
- [ ] Decidir con Germán y Ramiro si el éxito pasa a ser un control de calidad y la evaluación se centra en la eficiencia.

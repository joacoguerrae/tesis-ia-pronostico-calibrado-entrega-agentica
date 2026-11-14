# Notas del banco

## Prueba ciega (3/11/2026)

Para comprobar que cada pedido alcanza para resolver su tarea, se le dio a un agente general (Claude Opus 5.5, una corrida por tarea) solo la app y el `pedido.md`. No vio los tests de aceptación ni la solución. Las cinco tareas de entonces, T01 a T05, pasaron todos sus tests ocultos en 1,5 a 3,5 minutos cada una. Eso indica que los tests no piden nada que el pedido no diga.

La prueba mostró una ambigüedad en T02. El pedido decía que no había que romper las versiones viejas de la app, pero con la paginación esas versiones reciben solo la primera página. Se aclaró en el pedido que eso está aceptado.

T06 a T08 se sumaron el 9/11 para tener tareas más grandes y alguna que dependa de un sistema externo.

## Corridas de humo (12 y 13/11/2026)

La primera corrida de T01 usó el Claude Code instalado en la máquina, la versión 2.1.258. Pasó los 11 tests en 46 segundos y costó 0,32 dólares. La telemetría y las trazas llegaron completas. Aparecieron dos problemas:

- Al agente le negaron un comando de Python con heredoc, entendió que tenía prohibida toda la terminal y no corrió los tests. La plantilla ahora dice qué comandos puede usar.
- Esa versión no reconoce el modelo Sonnet 5.5 y su estimación de costo no es confiable. El banco pasó a usar su propia versión fija, la 2.1.312, la misma que usa Rootshift en el laboratorio.

La segunda corrida, ya con los dos cambios, corrió los tests, pasó los 11 en 36 segundos y costó 0,09 dólares.

Las dos quedaron en `corridas/humo-2.1.258/` y `corridas/humo/`.

## Piloto (13/11/2026)

Se corrieron las 8 tareas 6 veces cada una con la versión A: Claude Code 2.1.312 con Sonnet 5.5. El resumen completo está en `generador/resultados/piloto_piloto-8-tareas.txt`.

Las 48 corridas terminaron bien, con telemetría y trazas, y ninguna llegó a un tope ni tocó el banco. Costaron 6,23 dólares en total. T01 a T05 rondan los 0,09 dólares y los 35 segundos por corrida, y T06 a T08, entre 0,15 y 0,23 dólares y entre 1 y 1,5 minutos.

Las 8 tareas se resolvieron en todas las corridas. Con este agente, el éxito no distingue versiones, y hacen falta tareas más difíciles para que lo haga.

El ruido entre corridas de una misma tarea es menor que en DeepSWE en todas las métricas continuas:

| Métrica | Banco | DeepSWE (mediana) |
|---|---|---|
| Costo | 0,107 | 0,203 |
| Tokens de entrada | 0,220 | 0,268 |
| Tokens de salida | 0,117 | 0,138 |
| Pasos | 0,148 | 0,173 |
| Duración | 0,094 | 0,232 |

Son desvíos en escala logarítmica. Con 15 tareas y 5 corridas por versión (150 corridas, unos 19 dólares por comparación), el generador detectaría en el 80 % de los casos cambios de 7 % a 12 % en el costo y de 6 % a 13 % en la duración. El rango va de un efecto parejo entre tareas a uno que varía entre tareas como en DeepSWE.

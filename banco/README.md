# Banco de tareas

Tareas propias para correr dos versiones de un agente muchas veces sobre lo mismo y comparar su telemetría. Cada tarea es un pedido sobre Pulso, una API ficticia de reservas de clases de un gimnasio, y trae tests de aceptación que el agente no ve. Una corrida es un éxito si pasan todos.

Las pruebas que se hicieron con el banco y sus resultados están en [NOTAS.md](NOTAS.md).

## Estructura

- `app/`: Pulso en su estado inicial (FastAPI y SQLite, con 11 tests propios). Cada corrida arranca de una copia limpia.
- `tareas/Txx/pedido.md`: el pedido que recibe el agente.
- `tareas/Txx/inicial/`: si existe, archivos que se ponen encima de la app antes de la corrida, por ejemplo un bug plantado. Entran en el commit inicial, así el diff de la corrida muestra solo lo que hizo el agente.
- `tareas/Txx/aceptacion/`: los tests de aceptación. Se copian al repo de la corrida recién al evaluar.
- `tareas/Txx/solucion/`: una solución de referencia, para comprobar que los tests están bien.
- `tareas/_comun/`: fixtures compartidas por los tests de aceptación.
- `herramientas/corredor.py`: corre un experimento y guarda cada corrida.
- `herramientas/evaluar.py`: evalúa una corrida con los tests de su tarea.
- `herramientas/verificar.py`: comprueba que cada tarea falla sobre la app base y pasa con su solución.
- `experimentos/`, `versiones/` y `plantillas/`: qué se corre, con qué configuración del agente y con qué texto alrededor del pedido.

## Tareas

| Tarea | Clase | Qué pide | Dónde se puede equivocar el agente | Tests |
|---|---|---|---|---|
| T01 | C2-S | Cancelar una reserva y devolver el crédito según la anticipación | Las 2 horas justas, la clase ya empezada, reservas de otro socio | 11 |
| T02 | C1-S | Filtrar clases por día, instructor y lugar, de a páginas | El día en hora de Montevideo, el formato de la respuesta, el total en un header | 12 |
| T03 | C1-S | CSV con la ocupación de las clases de un período | El redondeo de los ,5, las comillas del CSV, el límite de 31 días | 12 |
| T04 | C1-S | Registro de socios con plan, créditos y token | La normalización y la validación del email, los duplicados | 13 |
| T05 | C2-S | Recordatorio de la clase en las 24 horas previas, una vez por reserva | La ventana inclusiva, no repetir recordatorios | 11 |
| T06 | C2-L | Lista de espera, con cancelación y ampliación de cupo desde recepción | El orden de llegada, saltear al que no tiene créditos, varios lugares a la vez, no asignar después del inicio | 16 |
| T07 | C3-L | Compra de créditos con una pasarela de pagos externa: pago, webhook y conciliación | No confiar en el webhook, la idempotencia, el 502 que deja la compra pendiente, que una falla no corte la conciliación | 16 |
| T08 | C3-S | Plan corporativo validado contra un servicio de beneficios externo | El piso de créditos, el email codificado en la URL, el 503 sin cambios, que una falla no corte la revalidación | 14 |
| T09 | C2-S | Diagnosticar y arreglar horarios corridos, a partir de reportes de socios (bug plantado en `inicial/`) | Arreglar el síntoma y no la causa, no migrar las clases ya guardadas, correr dos veces la migración, las fechas viejas sin zona | 13 |
| T10 | C2-S | Que las reservas respeten cupo, créditos y reservas repetidas con pedidos simultáneos de varios procesos | Un candado que solo sirve dentro de un proceso, el correo dentro de la transacción (base bloqueada), los 500 por base ocupada | 9 |
| T11 | C2-L | Series semanales: crear, cambiar de una clase en adelante y cancelar una clase | El día de la semana en hora de Montevideo, los días de cierre, la base vieja sin las columnas nuevas, rechazar el cambio entero | 37 |

T09 a T11 se armaron para que fallen más seguido: cada una prueba un tipo de dificultad distinto (diagnóstico, concurrencia y lógica de calendario). Su dificultad todavía no está medida; ver NOTAS.md.

La clase sigue la taxonomía de capabilities de Rootshift, nivel por tamaño. C1 es un solo flujo, C2 tiene reglas y estado propios, y C3 depende de un sistema externo que es la fuente de verdad. La clasificación es tentativa hasta tener el documento de la taxonomía. En T07 y T08, los tests reemplazan el sistema externo por un servidor falso en `127.0.0.1`.

## Instalación

```
python3.11 -m venv .venv
.venv/bin/pip install -r app/requirements.txt
npm install
.venv/bin/python herramientas/verificar.py
```

`npm install` deja Claude Code en la versión fijada en `package.json`, que el corredor usa por defecto. Así las corridas no dependen de la versión instalada en cada máquina.

## Correr un experimento

```
# probar el corredor sin gastar, con un Claude Code falso
.venv/bin/python herramientas/corredor.py experimentos/prueba.json --claude ".venv/bin/python herramientas/pruebas/claude_falso.py"

# ver el orden de las corridas
.venv/bin/python herramientas/corredor.py experimentos/piloto-8-tareas.json --plan

# correr de verdad
export ANTHROPIC_API_KEY=...
.venv/bin/python herramientas/corredor.py experimentos/humo.json
.venv/bin/python herramientas/corredor.py experimentos/piloto-8-tareas.json
```

El corredor arma una ronda por repetición. Dentro de cada ronda, ordena al azar todas las combinaciones de tarea y versión, así las versiones quedan intercaladas en el tiempo. El orden depende de la semilla del experimento.

En cada corrida, copia la app a un repo temporal fuera del banco y lanza `claude -p --bare` con el pedido. Al terminar evalúa el resultado con los tests de aceptación. Todo queda en `corridas/<experimento>/<id>/`:

- `corrida.json`: qué se corrió, cuándo, con qué versión de Claude Code y cómo terminó;
- `stream.jsonl`: la salida de Claude Code;
- `otel.jsonl` y `trazas.jsonl`: los eventos de telemetría y los tramos de la traza;
- `cambios.patch` y `evaluacion.json`: el diff del agente y el resultado de los tests.

Si el corredor se corta, al volver a lanzarlo sigue desde la corrida que faltaba.

Cada corrida recibe su propio id de traza por `TRACEPARENT`. Claude Code lo usa en todos sus eventos y tramos, y así se cruzan con la corrida.

Cada archivo de `versiones/` define el modelo, el esfuerzo, la plantilla del pedido, los permisos y los topes de costo, turnos y tiempo. Para armar una versión B se copia `A.json` y se cambia una sola cosa. Los topes de A (3 dólares, 100 turnos, 20 minutos) existen para cortar corridas trabadas: en el piloto ninguna llegó a tocarlos. Una corrida cortada por un tope se evalúa igual que las demás.

El corredor usa solo la clave de `ANTHROPIC_API_KEY`. En modo `--bare`, Claude Code no lee `~/.claude`, así que no toma otras claves, CLAUDE.md, hooks ni servidores MCP de la máquina. Si una corrida usó otra clave, el corredor se corta.

`generador/claude_code.py` pasa las corridas al formato del generador, y `generador/piloto.py` resume un piloto.

## Pendiente

- Llegar a 15 tareas, con tareas más difíciles. En el piloto, las 8 se resolvieron en todas las corridas, también con Haiku 5.5.
- Medir la dificultad de T09 a T11 con `experimentos/calibracion-t09-t11.json` y quedarse con las que A resuelve entre el 20 % y el 80 % de las veces.
- Confirmar la clasificación con el documento de la taxonomía de Rootshift.

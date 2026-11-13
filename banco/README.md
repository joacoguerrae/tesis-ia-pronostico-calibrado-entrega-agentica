# Banco de tareas

Tareas propias para correr dos versiones de un agente muchas veces sobre lo mismo y comparar su telemetría. Cada tarea es un pedido sobre Pulso, una app ficticia de reservas de clases de un gimnasio, y trae tests de aceptación que el agente no ve. La corrida cuenta como éxito si pasan todos.

## Estructura

- `app/`: Pulso en su estado inicial (API en FastAPI con SQLite, 11 tests propios). Cada corrida arranca de una copia limpia de este estado.
- `tareas/Txx/pedido.md`: lo que recibe el agente. Con Claude Code va como prompt. Con Rootshift va como capability en el Ground Truth, con su contexto, historia de usuario y reglas de negocio.
- `tareas/Txx/aceptacion/`: tests de aceptación. Se copian al repo recién al evaluar y se borran después.
- `tareas/Txx/solucion/`: solución de referencia, con los archivos que cambian respecto de `app/`. Sirve para comprobar que los tests están bien. El agente tampoco la ve.
- `tareas/_comun/`: fixtures que comparten los tests de aceptación. Usan solo lo que la app base ya tiene.
- `herramientas/evaluar.py`: corre los tests de aceptación de una tarea sobre un repo y devuelve cuántos pasaron.
- `herramientas/verificar.py`: comprueba que cada tarea falla sobre la app base, pasa con la solución de referencia y no rompe los tests propios.

## Tareas

La clase es nuestra clasificación tentativa con la taxonomía v3 de Rootshift, tal como la pasó el ORT Bot (no tenemos el documento). El tier va de C1 a C5:
- C1: un solo flujo, como un CRUD, un listado o la cuenta propia;
- C2: reglas y estado propios, "exactamente una vez" y caminos de falla;
- C3: un sistema externo es la fuente de verdad.

El tamaño es S o L.

| Tarea | Clase | Qué pide | Dónde se puede equivocar el agente | Tests |
|---|---|---|---|---|
| T01 | C2-S | Cancelar una reserva y devolver el crédito según la anticipación | Las 2 horas justas, la clase ya empezada, reservas de otro socio | 11 |
| T02 | C1-S | Filtrar clases por día, instructor y lugar, de a páginas | El día en hora de Montevideo, no romper el formato de la respuesta, el total en un header | 12 |
| T03 | C1-S | CSV con la ocupación de las clases de un período | El redondeo de los ,5, las comillas del CSV, el límite de 31 días | 12 |
| T04 | C1-S | Registro de socios con plan, créditos y token | La normalización y la validación del email, los duplicados | 13 |
| T05 | C2-S | Recordatorio de la clase en las 24 horas previas, una vez por reserva | La ventana inclusiva, no repetir recordatorios | 11 |
| T06 | C2-L | Lista de espera, con cancelación y ampliación de cupo desde recepción y asignación automática de los lugares que se liberan | El orden de llegada, saltear al que no tiene créditos, varios lugares a la vez, no asignar después del inicio, el crédito al cancelar, el cupo mínimo | 16 |
| T07 | C3-L | Compra de packs de créditos con Cobrá, una pasarela de pagos externa: creación del pago, webhook y conciliación | No confiar en el cuerpo del webhook, la idempotencia, el 502 que deja la compra pendiente, la búsqueda por referencia, que una falla no corte la conciliación, los 30 minutos | 16 |
| T08 | C3-S | Plan corporativo validado contra el servicio de beneficios de cada empresa, con revalidación diaria | El piso de créditos (no es una suma), el email codificado en el path, el 503 sin cambios, distinguir empleado y empresa desconocidos, que una falla no corte la revalidación | 14 |

T06 a T08 se sumaron el 9/11/2026 para tener tareas más grandes y difíciles, y alguna C3. Sus tests usan servidores falsos en `127.0.0.1` para el sistema externo, que viven en la carpeta `aceptacion/` de cada tarea. Todavía no pasaron por la prueba ciega: la va a reemplazar el piloto.

## Cómo se usa

```
python3.11 -m venv .venv
.venv/bin/pip install -r app/requirements.txt
npm install    # Claude Code 2.1.312, la versión fija para las corridas
.venv/bin/python herramientas/verificar.py
.venv/bin/python herramientas/evaluar.py T01-cancelar-reserva /ruta/al/repo
```

`evaluar.py` devuelve un JSON con la cantidad de tests, los que pasaron, los que fallaron y si la corrida fue un éxito.

## Corredor de experimentos

`herramientas/corredor.py` corre un experimento de `experimentos/`, que define las tareas, las versiones de `versiones/` y la cantidad de repeticiones. Arma una ronda por repetición y, dentro de cada ronda, pone todas las combinaciones de tarea y versión en orden al azar, así las versiones quedan intercaladas en el tiempo. El plan sale siempre igual porque usa la semilla del experimento.

En cada corrida, el corredor:

1. copia la app a un repo nuevo fuera del banco, para que el agente no pueda llegar a los tests;
2. lanza `claude -p` en modo `--bare` con el pedido armado según la plantilla de la versión, y con el modelo, los permisos, el presupuesto, el tope de turnos y el límite de tiempo de la versión;
3. guarda la salida stream-json y la telemetría de Claude Code: los eventos (un `api_request` por llamada al modelo y un `tool_result` por uso de herramienta) y los tramos de la traza, que están en beta (`claude_code.interaction`, con un `claude_code.llm_request` y un `claude_code.tool` por llamada);
4. guarda el diff que dejó el agente y lo evalúa con los tests de aceptación.

Todo queda en `corridas/<experimento>/<id>/`. Si el corredor se corta, al volver a lanzarlo sigue desde la corrida que faltaba.

**Trazas.** Cada corrida recibe un id de traza propio por `TRACEPARENT`. En modo `-p`, Claude Code cuelga de ahí su traza y pone ese id en cada evento, así los eventos y los tramos se cruzan con la corrida. `corrida.json` guarda el id (`traza_id`), cuántos tramos llegaron y cuántos traen otro id, que debería ser cero.

**Versiones.** Cada versión es un JSON con el modelo, el esfuerzo, la plantilla del pedido, un agregado opcional al prompt de sistema, las herramientas, los permisos, el presupuesto por corrida, el tope de turnos y el límite de tiempo. Para armar una versión B se copia `A.json` y se cambia una sola cosa.

La versión A tiene 3 dólares, 100 turnos y 20 minutos por corrida. Son topes para cortar corridas trabadas o en bucle, no para apurar al agente, y quedan a confirmar con el piloto. Una corrida cortada por un tope cuenta igual: se evalúa con los tests como cualquier otra y entra con lo que gastó hasta ahí. El motivo queda en `resultado` (por ejemplo, `error_max_turns`) y en `termino`.

**Credenciales.** El corredor usa solo `ANTHROPIC_API_KEY`. En modo `--bare`, Claude Code no lee `~/.claude`, así que no toma otra clave configurada en la máquina, ni CLAUDE.md, hooks, plugins o servidores MCP. Si una corrida igual usó otra clave, el corredor se corta.

**Lectura.** `generador/claude_code.py` pasa las corridas al formato común del generador. Además devuelve una tabla por llamada al modelo y otra por uso de herramienta, con el id de la corrida.

```
# probar sin gastar, con un Claude Code falso
.venv/bin/python herramientas/corredor.py experimentos/prueba.json --claude ".venv/bin/python herramientas/pruebas/claude_falso.py"

# ver el orden del piloto
.venv/bin/python herramientas/corredor.py experimentos/piloto.json --plan

# una corrida real y después el piloto (50 corridas)
export ANTHROPIC_API_KEY=...
.venv/bin/python herramientas/corredor.py experimentos/humo.json
.venv/bin/python herramientas/corredor.py experimentos/piloto.json
```

La versión de Claude Code queda fijada en `package.json` y el corredor la usa por defecto (`node_modules/.bin/claude`), así no depende de la que tenga instalada cada máquina.

Con el Claude Code real hay que comprobar cuatro cosas, y la corrida de `humo` sirve para eso:

- que en modo `--bare` mande la telemetría;
- que lleguen los tramos de la traza con el id de la corrida (`tramos_otel` mayor que cero y `tramos_de_otra_traza` en cero);
- que el resultado traiga los campos que lee el adaptador;
- que con estos permisos el agente pueda correr los tests.

## Piloto (13/11/2026)

Se corrieron las 8 tareas 6 veces cada una con la versión A (`experimentos/piloto-8-tareas.json`, Claude Code 2.1.312 y Sonnet 5.5). El resumen completo está en `generador/resultados/piloto_piloto-8-tareas.txt` y las corridas, en `corridas/piloto-8-tareas/`.

- **Controles.** Las 48 corridas terminaron bien. Todas mandaron telemetría y trazas, y ninguna tocó el banco.
- **Costo y tiempo.** 6,23 dólares en total: 0,13 por corrida en promedio (0,09 en T01 a T05 y de 0,15 a 0,23 en T06 a T08). Cada corrida tarda unos 52 segundos.
- **Éxito.** Las 8 tareas se resolvieron en todas las corridas. Con este agente el éxito no distingue versiones: hacen falta tareas más difíciles, con éxito entre 20 % y 80 %, o declararlo como límite.
- **Ruido entre corridas.** Es menor que en DeepSWE en todas las métricas continuas. El desvío en escala log es 0,107 en costo (DeepSWE: 0,203), 0,094 en duración (0,232), 0,117 en tokens de salida (0,138), 0,148 en pasos (0,173) y 0,220 en tokens de entrada (0,268).
- **Qué se puede detectar.** Con 15 tareas y 5 corridas por versión (150 corridas, unos 19 dólares por comparación), el generador detectaría en el 80 % de los casos cambios de 7 % a 12 % en el costo, de 8 % a 11 % en los tokens de salida y de 6 % a 13 % en la duración. Cada rango va del efecto parejo entre tareas al variable.

## Primera corrida de humo (12/11/2026)

Se corrió T01 una vez con el Claude Code de la máquina (2.1.258), con la versión A:
- **Resultado:** pasó los 11 tests ocultos en 46 segundos, por 0,32 dólares y en 9 turnos.
- **Controles:** usó la clave de ANTHROPIC_API_KEY. Llegaron 25 eventos y 29 tramos de traza, todos con el id de la corrida. No tocó el banco.

Salieron dos problemas, que se corrigieron antes del piloto:
- **No corrió los tests.** Le negaron un comando de Python con heredoc y entendió que tenía prohibida toda la terminal. La plantilla ahora dice qué comandos puede usar.
- **Esa versión no reconoce el modelo Sonnet 5.5** (avisa `unrecognized_model`), así que su costo estimado puede no ser exacto. El banco ahora usa su propia versión fija, la 2.1.312, la misma que usa Rootshift en el lab.

La corrida quedó en `corridas/humo-2.1.258/`.

## Prueba ciega (3/11/2026)

Para comprobar que cada pedido alcanza para resolver su tarea, se le dio a un agente general (Claude Opus 5.5, una corrida por tarea) solo la app y el `pedido.md`, sin los tests de aceptación ni la solución. Las cinco tareas pasaron todos sus tests ocultos, cada una en 1,5 a 3,5 minutos. Eso indica que los tests no piden nada que el pedido no diga. También indica que, para un modelo de ese nivel, estas tareas pueden ser fáciles: si el piloto muestra que se resuelven siempre, el éxito no va a distinguir versiones y habrá que sumar tareas más difíciles.

La prueba sacó a la luz una ambigüedad en T02: el pedido decía que no había que romper las versiones viejas de la app, pero con la paginación esas versiones reciben solo la primera página. Se aclaró en el pedido que eso está aceptado.

## Pendiente

- Confirmar la clasificación con el documento de la taxonomía (`docs/classifying-capabilities.md` de Rootshift) cuando Anthony dé acceso.
- Llegar a 15 tareas con tareas más difíciles, porque en el piloto todas se resolvieron siempre. Pueden salir del benchmark público.

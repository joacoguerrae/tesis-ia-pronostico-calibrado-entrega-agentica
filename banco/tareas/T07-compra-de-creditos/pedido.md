# Compra de créditos con Cobrá

## Contexto

Hoy los créditos se compran en recepción: el socio paga en el mostrador y alguien se los suma a mano. Queremos que el socio compre packs de créditos desde la app y los pague online con Cobrá, la pasarela de pagos que la empresa ya usa para las cuotas.

El pago se hace en la página de Cobrá, fuera de Pulso. Pulso se entera del resultado por un webhook y, como los webhooks a veces se pierden, también por una conciliación que un proceso programado llama cada 10 minutos. Cobrá es la fuente de verdad: Pulso nunca da un pago por aprobado sin preguntarle a Cobrá.

## Historia de usuario

Como socio, quiero comprar un pack de créditos desde la app y pagarlo online, para no tener que pasar por recepción.

## Reglas de negocio

El catálogo es fijo:

| Pack | Créditos | Precio |
|---|---|---|
| `pack-4` | 4 | $U 1200 |
| `pack-8` | 8 | $U 2200 |

**Compra**

1. `POST /compras` recibe el pack. Si falta o no está en el catálogo, la respuesta es 422 y no se crea nada: ni la compra ni el pago.
2. La compra se guarda en Pulso como `pendiente` antes de llamar a Cobrá. Su referencia es `pulso-compra-{id}`, con el id de la compra. Después se crea el pago en Cobrá por el precio del pack, en pesos uruguayos (`UYU`), con esa referencia y con el header `Idempotency-Key` igual a la referencia. La respuesta es 201 y trae la `url_pago` que devuelve Cobrá, adonde la app manda al socio a pagar. Los créditos se suman recién cuando el pago queda aprobado.
3. Si Cobrá falla al crear el pago, la respuesta es 502. La compra no se borra ni se rechaza: queda `pendiente` y sin pago, porque Cobrá pudo haber creado el pago aunque la respuesta no haya llegado. Nunca se crea otro pago para esa compra: la conciliación lo busca por la referencia (regla 9).

**Estado del pago**

4. Cuando Pulso averigua el estado de un pago, sea por el webhook o por la conciliación, lo aplica a la compra así:
   - `aprobado`: la compra pasa a `aprobada`, se le suman al socio los créditos del pack y se le manda un correo con el asunto `Compra de créditos aprobada`. El cuerpo es libre.
   - `rechazado`: la compra pasa a `rechazada`. No se suman créditos ni se manda correo.
   - `pendiente`: no cambia nada.
5. Una compra `aprobada` o `rechazada` ya no cambia. Los créditos y el correo van una sola vez por compra, aunque el webhook llegue repetido o la conciliación vuelva a ver el mismo pago.

**Webhook**

6. Cobrá llama a `POST /webhooks/pagos` cada vez que cambia el estado de un pago, a veces más de una vez por el mismo cambio. La ruta no pide autenticación, así que cualquiera la puede llamar: del cuerpo solo se usa `pago_id`. Pulso consulta ese pago en Cobrá y usa el estado y la referencia que devuelve Cobrá. El `estado` que viene en el cuerpo se ignora.
7. La compra se busca por la referencia del pago, no por el id del pago. Así funciona también con una compra que quedó sin pago por la regla 3: en ese caso, se le guarda el pago, con su id y su `url_pago`.
8. Si Cobrá no conoce el pago, o si la referencia del pago no es de ninguna compra, la respuesta es 404. Si Cobrá falla, la respuesta es 503 y no cambia nada, para que Cobrá vuelva a mandar el webhook más tarde.

**Conciliación**

9. `POST /admin/conciliar-pagos` es un endpoint de administración: sin una `X-Admin-Key` válida la respuesta es 401. Revisa todas las compras pendientes, de todos los socios. Si la compra tiene pago, lo consulta por id. Si no tiene, lo busca por la referencia y, si lo encuentra, le guarda el pago a la compra. Después aplica el estado como dice la regla 4.
10. Si la búsqueda por referencia no encuentra ningún pago y la compra se creó hace 30 minutos o más, el pago nunca se creó: la compra pasa a `rechazada`. Si se creó hace menos, queda pendiente, porque el pago todavía puede estar creándose.
11. Si Cobrá falla con una compra, esa compra queda pendiente y la conciliación sigue con las demás. Que Cobrá falle no es lo mismo que no encontrar el pago: una búsqueda que falla nunca rechaza la compra.
12. La respuesta dice cómo quedaron las compras que estaban pendientes cuando empezó la llamada: cuántas pasaron a aprobadas, cuántas a rechazadas y cuántas siguen pendientes. Las que ya estaban aprobadas o rechazadas no se cuentan.

**Listado**

13. `GET /compras` devuelve las compras del socio, de la más nueva a la más vieja. Muestra lo que Pulso tiene guardado, sin consultar a Cobrá.

## Contrato de la API

### Pulso

`POST /compras`, con el token del socio:

```json
{"pack": "pack-4"}
```

Respuesta 201:

```json
{"id": 17, "pack": "pack-4", "creditos": 4, "monto": 1200, "estado": "pendiente", "creada": "2026-11-10T15:00:00+00:00", "url_pago": "https://pagar.cobra.uy/pag_8f3k2"}
```

Errores: 401 sin un token válido, 422 si el pack no es válido y 502 si Cobrá falla.

`GET /compras`, con el token del socio. Respuesta 200: una lista de compras con el mismo formato. `estado` es `pendiente`, `aprobada` o `rechazada`, y `url_pago` es `null` mientras la compra no tenga pago.

`POST /webhooks/pagos`, sin autenticación. Cobrá manda:

```json
{"pago_id": "pag_8f3k2", "estado": "aprobado"}
```

Respuesta 200, con el estado de la compra después de procesar el aviso:

```json
{"compra_id": 17, "estado": "aprobada"}
```

Errores: 404 si Cobrá no conoce el pago o el pago no es de ninguna compra, 422 si falta `pago_id` y 503 si Cobrá falla.

`POST /admin/conciliar-pagos`, con `X-Admin-Key` y sin cuerpo. Respuesta 200:

```json
{"aprobadas": 2, "rechazadas": 1, "pendientes": 4}
```

### Cobrá

- La URL base sale de la variable `PULSO_PAGOS_URL`, sin barra al final, y las rutas van a continuación. Por ejemplo, con `https://api.cobra.uy/v1`, el pago se crea con `POST https://api.cobra.uy/v1/pagos`.
- Todos los pedidos llevan el header `X-Cobra-Clave` con el valor de la variable `PULSO_PAGOS_CLAVE`. Sin una clave válida, Cobrá responde 401.
- Las dos variables se leen cuando se usan, igual que `PULSO_ADMIN_KEY`, no al importar el módulo.
- Para llamar a Cobrá se usa `httpx`, que ya está en `requirements.txt`. No se agregan dependencias.
- Cobrá falla cuando no contesta (conexión rechazada o más de 5 segundos sin respuesta) o cuando contesta con un código que no está en este contrato para esa ruta, por ejemplo un 500 o un 401.

Un pago tiene este formato en todas las respuestas de Cobrá:

```json
{"id": "pag_8f3k2", "estado": "pendiente", "monto": 1200, "moneda": "UYU", "referencia": "pulso-compra-17", "url_pago": "https://pagar.cobra.uy/pag_8f3k2"}
```

`estado` es `pendiente`, `aprobado` o `rechazado`, y los dos últimos son definitivos. Cobrá pasa a `rechazado` los pagos que no se completan en 24 horas.

`POST /pagos`, con el header `Idempotency-Key`, que es obligatorio:

```json
{"monto": 1200, "moneda": "UYU", "referencia": "pulso-compra-17"}
```

`monto` es un entero, en pesos. Respuesta 201 con el pago nuevo. Si ya existe un pago creado con esa `Idempotency-Key`, Cobrá no crea otro y responde 200 con el que ya existía. Si falta un dato o el header, responde 422.

`GET /pagos/{id}`: 200 con el pago, o 404 si no existe.

`GET /pagos?referencia=pulso-compra-17`: 200 con los pagos que tienen esa referencia. Si la referencia siempre va como `Idempotency-Key`, hay uno como mucho:

```json
{"pagos": [{"id": "pag_8f3k2", "estado": "aprobado", "monto": 1200, "moneda": "UYU", "referencia": "pulso-compra-17", "url_pago": "https://pagar.cobra.uy/pag_8f3k2"}]}
```

Si no hay ninguno, la respuesta es `{"pagos": []}`.

## Fuera de alcance

- Devoluciones y cancelación de compras.
- Reintentar el pago de una compra rechazada o sin pago: el socio hace otra compra.
- Verificar una firma en el webhook. Por eso se le consulta el pago a Cobrá.
- El proceso que llama a la conciliación cada 10 minutos.
- Vencimiento de los créditos comprados.

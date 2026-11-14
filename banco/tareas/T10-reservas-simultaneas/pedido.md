# Reservas simultáneas

## Contexto

Las clases de la semana se publican los domingos a las 20:00 y en los primeros minutos llegan cientos de reservas a la vez. En producción, la API corre con 4 procesos de uvicorn sobre la misma base SQLite, y cada proceso atiende varios pedidos al mismo tiempo.

El domingo pasado, recepción encontró:

- clases con más reservas confirmadas que lugares;
- socios con créditos negativos;
- socios con dos reservas confirmadas para la misma clase, porque tocaron dos veces el botón de reservar;
- confirmaciones repetidas en la bandeja de correos.

Probando de a un pedido por vez, todo anda bien.

## Historia de usuario

Como socio, quiero que mi reserva valga aunque muchos reserven al mismo tiempo, y que nadie reserve un lugar que no existe.

## Reglas de negocio

`POST /reservas` mantiene las reglas y las respuestas de hoy, pero se tienen que cumplir siempre, aunque lleguen muchos pedidos a la vez desde varios procesos:

1. Una clase nunca tiene más reservas confirmadas que su cupo.
2. Los créditos de un socio nunca quedan negativos, y cada reserva confirmada descuenta exactamente un crédito.
3. Un socio tiene como mucho una reserva confirmada por clase.
4. Cada reserva confirmada genera exactamente un correo de confirmación.
5. Un pedido rechazado no deja rastro: no crea reserva, no descuenta créditos y no manda correo. Responde 409 con el mismo `detail` que hoy:
   - `La clase no tiene lugar`
   - `No te quedan créditos`
   - `Ya tenés una reserva para esta clase`
6. Ningún pedido termina en un error del servidor por culpa de la simultaneidad. Si la base está ocupada, el pedido espera su turno, y si gana un lugar recibe 201 como siempre.

## Restricciones

- La base sigue siendo SQLite y no se agregan dependencias.
- La app va a seguir corriendo con varios procesos.

## Fuera de alcance

- Cancelaciones y lista de espera.
- Limitar la cantidad de pedidos por socio.

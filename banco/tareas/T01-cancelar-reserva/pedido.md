# Cancelar una reserva

## Contexto

Hoy un socio que reserva una clase no tiene forma de bajarse: el lugar queda ocupado y el crédito se pierde. Recepción recibe muchos pedidos por WhatsApp para cancelar a mano.

## Historia de usuario

Como socio, quiero cancelar una reserva para liberar mi lugar y, si aviso con tiempo, recuperar el crédito.

## Reglas de negocio

1. Solo el dueño puede cancelar su reserva. Si la reserva no existe o es de otro socio, la respuesta es 404.
2. Una reserva que ya está cancelada no se puede volver a cancelar: 409.
3. Cuando la clase ya empezó (la hora actual es igual o posterior al inicio), no se puede cancelar: 409.
4. Si se cancela con 2 horas o más de anticipación, se devuelve el crédito. Con menos de 2 horas se cancela igual, pero el crédito no se devuelve.
5. La reserva cancelada no se borra: queda con estado `cancelada` y sigue apareciendo en `GET /reservas`.
6. El lugar se libera: vuelve a contar en `lugares_libres` y otro socio lo puede reservar. El mismo socio también puede volver a reservar esa clase.

## Contrato de la API

`POST /reservas/{id}/cancelar`, con el token del socio y sin cuerpo.

Respuesta 200:

```json
{"id": 12, "clase_id": 3, "estado": "cancelada", "creada": "2026-11-10T15:00:00+00:00", "credito_devuelto": true}
```

## Fuera de alcance

- Correos de aviso de cancelación.
- Cancelaciones hechas por el gimnasio.

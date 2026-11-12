# Recordatorio de la clase reservada

## Contexto

Muchos socios reservan y después se olvidan, y las clases quedan con lugares vacíos que otros querían. Queremos mandar un recordatorio el día antes.

## Historia de usuario

Como socio, quiero recibir un correo que me recuerde la clase que reservé, para no olvidarme de ir.

## Reglas de negocio

1. Un proceso programado llama cada 15 minutos a `POST /admin/recordatorios`. Es un endpoint de administración: sin una `X-Admin-Key` válida la respuesta es 401.
2. Cada llamada manda un recordatorio por cada reserva confirmada cuya clase empieza en las próximas 24 horas: después de la hora actual y hasta 24 horas después, inclusive.
3. Cada reserva recibe como máximo un recordatorio, aunque el proceso se llame muchas veces o la reserva se haya hecho cuando ya faltaban menos de 24 horas.
4. Las reservas que no están confirmadas (por ejemplo, las que canceló recepción) no reciben recordatorio.
5. El correo va al email del socio con el asunto `Recordatorio: {clase} el {fecha y hora}`, con la fecha y la hora en el formato de `correo.fecha_y_hora()`. Por ejemplo: `Recordatorio: Yoga el 11/11 a las 18:30`. El cuerpo es libre, pero tiene que nombrar al instructor.
6. La respuesta dice cuántos recordatorios se mandaron en esa llamada.

## Contrato de la API

`POST /admin/recordatorios`, con `X-Admin-Key` y sin cuerpo.

Respuesta 200:

```json
{"enviados": 3}
```

## Fuera de alcance

- Notificaciones push o por WhatsApp.
- Que el socio elija si quiere recibir recordatorios.

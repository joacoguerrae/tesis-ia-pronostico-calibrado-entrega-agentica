# Lista de espera para clases llenas

## Contexto

Las clases de la tarde se llenan en minutos. Cuando alguien avisa que no va, recepción llama uno por uno a los socios que habían preguntado, con una lista en papel, y muchas veces el lugar queda vacío. Además, recepción no puede cancelar reservas ni ampliar el cupo de una clase desde el panel: se lo pide a sistemas, que lo cambia a mano en la base.

## Historia de usuario

Como socio, quiero anotarme en la lista de espera de una clase llena para quedarme con el primer lugar que se libere, sin tener que estar pendiente.

Como recepcionista, quiero cancelar reservas y ampliar el cupo de una clase desde el panel, y que los lugares que se liberan pasen solos a la lista de espera.

## Reglas de negocio

### Lista de espera

1. Cada clase tiene su lista de espera. El socio se anota con `POST /clases/{id}/espera`, ve su posición con `GET /clases/{id}/espera` y se baja con `DELETE /clases/{id}/espera`. Los tres piden el token del socio: sin un token válido, la respuesta es 401. Si la clase no existe, 404.
2. Solo se puede anotar en una clase llena. La respuesta es 409, y el socio no queda anotado, si:
   - la clase tiene lugar (en ese caso tiene que reservar directo);
   - ya tiene una reserva confirmada para esa clase;
   - ya está en la lista;
   - la clase ya empezó, es decir, la hora actual es igual o posterior al inicio;
   - no le quedan créditos.
3. Anotarse no es reservar: no descuenta créditos ni crea una reserva confirmada. El crédito se descuenta recién cuando el socio recibe un lugar.
4. La lista va por orden de llegada. El primero tiene la posición 1, y la posición cuenta solo a los que siguen anotados: cuando alguien de adelante sale de la lista (porque se bajó, porque recibió un lugar o porque se lo salteó por la regla 11), los de atrás avanzan. Si un socio se baja y se vuelve a anotar, queda último.
5. `GET` y `DELETE` responden 404 si el socio no está en la lista de esa clase.

### Panel de recepción

6. Recepción cancela una reserva con `POST /admin/reservas/{id}/cancelar`. La reserva no se borra: queda con estado `cancelada` y el socio la sigue viendo en `GET /reservas`. Al socio se le devuelve el crédito siempre, falte lo que falte para la clase, aunque ya haya empezado. Si la reserva no existe, 404. Si ya estaba cancelada, 409, y no se devuelve otro crédito ni se libera otro lugar.
7. Recepción cambia el cupo de una clase con `PATCH /admin/clases/{id}`. Por ahora solo se puede cambiar `cupo`, que es obligatorio y tiene que ser un entero mayor que 0: si falta o no es válido, 422. El cupo no puede quedar por debajo de las reservas confirmadas que ya tiene la clase: en ese caso la respuesta es 409 y la clase queda como estaba. Igual a las confirmadas sí se puede. Si la clase no existe, 404.
8. Los dos endpoints de recepción son de administración: sin una `X-Admin-Key` válida la respuesta es 401 y no se cambia nada.

### Lugares que se liberan

9. Se libera un lugar cada vez que recepción cancela una reserva confirmada. Ampliar el cupo en k libera k lugares de una vez. Cada lugar liberado pasa en el momento al primero de la lista, dentro de la misma operación: cuando vuelve la respuesta de la cancelación o del cambio de cupo, el lugar ya está asignado.
10. El socio que recibe el lugar:
    - queda con una reserva confirmada para la clase, que ve en `GET /reservas`;
    - se le descuenta un crédito, como en cualquier reserva;
    - sale de la lista de espera;
    - recibe un correo con el asunto `Se liberó un lugar: {clase} el {fecha y hora}`, con la fecha y la hora en el formato de `correo.fecha_y_hora()`. Por ejemplo: `Se liberó un lugar: Spinning el 12/11 a las 19:00`. Este correo reemplaza al de `Reserva confirmada`, que en este caso no se manda. El cuerpo es libre.
11. Si al primero de la lista no le quedan créditos en ese momento, se lo saca de la lista sin reserva, recibe un correo con el asunto `No pudimos darte el lugar: {clase} el {fecha y hora}`, en el mismo formato, y el lugar pasa al siguiente. Si ya tiene una reserva confirmada para esa clase, se lo saca de la lista sin otra reserva ni correo, y el lugar también pasa al siguiente. Se sigue así hasta que no quedan lugares libres o la lista queda vacía.
12. Si la clase ya empezó (la hora actual es igual o posterior al inicio), no se asigna ningún lugar: la cancelación y el cambio de cupo se hacen igual, pero los lugares quedan libres y la lista no cambia.
13. Ninguna operación puede dejar a un socio con dos reservas confirmadas para la misma clase, ni a una clase con más reservas confirmadas que cupo.

## Contrato de la API

### Socio, con `Authorization: Bearer <token>`

`POST /clases/{id}/espera`, sin cuerpo. Respuesta 201:

```json
{"clase_id": 3, "posicion": 4}
```

`GET /clases/{id}/espera`: respuesta 200, con el mismo formato.

`DELETE /clases/{id}/espera`: respuesta 204, sin cuerpo.

### Recepción, con `X-Admin-Key`

`POST /admin/reservas/{id}/cancelar`, sin cuerpo. Respuesta 200, con la reserva en el formato de `GET /reservas`:

```json
{"id": 12, "clase_id": 3, "estado": "cancelada", "creada": "2026-11-09T22:10:00+00:00"}
```

`PATCH /admin/clases/{id}`, con el cupo nuevo:

```json
{"cupo": 25}
```

Respuesta 200, con la clase en el formato de `GET /clases/{id}` y los lugares ya asignados a la lista de espera:

```json
{"id": 3, "nombre": "Spinning", "instructor": "Leo", "inicio": "2026-11-12T22:00:00+00:00", "duracion_min": 45, "cupo": 25, "lugares_libres": 0}
```

## Fuera de alcance

- Que el socio cancele su propia reserva desde la app.
- Correos al anotarse o al bajarse de la lista, y al socio al que recepción le cancela la reserva.
- Cambiar otros datos de la clase.
- Mostrar en `GET /clases` cuántos socios hay en la lista de espera.
- Ofrecer el lugar con un plazo para aceptarlo: se asigna directo.

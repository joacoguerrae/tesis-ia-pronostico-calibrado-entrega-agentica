# Clases recurrentes

## Contexto

Hoy recepción carga las clases una por una: "Yoga los martes a las 19:00" son 50 cargas por año, y cuando un instructor cambia de horario hay que editar cada clase a mano. Queremos cargar series semanales, cambiarlas desde una fecha en adelante y cancelar una clase suelta cuando hace falta.

## Historia de usuario

Como recepcionista, quiero cargar una clase semanal una sola vez y poder cambiarla o cancelar una fecha sin tocar las demás.

## Reglas de negocio

Todas las horas y fechas de este pedido son de Montevideo. Las fechas de las clases se guardan y se devuelven en UTC, como dice el README.

**Clases**

1. Las clases tienen dos datos nuevos, que aparecen en todas las respuestas que devuelven clases: `serie_id`, el id de la serie a la que pertenecen, o `null` si se cargaron sueltas; y `estado`, que es `programada` o `cancelada`. Las clases que ya existen y las que se cargan con `POST /admin/clases` son `programada` y tienen `serie_id` en `null`.

**Crear una serie**

2. `POST /admin/series` crea la serie y una clase por cada semana: una por cada fecha entre `desde` y `hasta`, las dos incluidas, que caiga en el `dia` de la serie, a la `hora` de la serie.
3. `dia` es uno de `lunes`, `martes`, `miércoles`, `jueves`, `viernes`, `sábado` o `domingo`, escrito así. `hora` va como `HH:MM`, de `00:00` a `23:59`.
4. No se crean clases en los días que el gimnasio cierra: 25/12/2026, 1/1/2027, 8/2/2027, 9/2/2027, 25/3/2027, 26/3/2027 y 1/5/2027. Esas semanas la serie no tiene clase.
5. Tampoco se crean clases cuyo inicio ya pasó, o sea, que empiezan en este momento o antes.
6. La respuesta es 422, y no se crea nada, si falta un dato o si tiene un valor inválido: `dia` o `hora` fuera de lo que dice la regla 3, `nombre` o `instructor` vacíos, `duracion_min` o `cupo` menores que 1, `hasta` anterior a `desde`, o más de 366 días entre `desde` y `hasta`. Una serie que no genera ninguna clase es válida.

**Cambiar una serie de una clase en adelante**

7. `PATCH /admin/series/{id}` recibe `desde_clase_id` y uno o más de `hora`, `instructor` y `cupo`. Cambia la clase `desde_clase_id` y todas las clases de la serie que empiezan después de ella. Las anteriores no cambian. La serie pasa a tener los datos nuevos.
8. Las clases canceladas no cambian y siguen canceladas.
9. Un cambio de `hora` mueve cada clase a esa hora del mismo día. La clase conserva su `id` y sus reservas, y cada socio con una reserva confirmada recibe un correo con el asunto `Cambio de horario: {nombre} el {fecha y hora nuevas}`, por ejemplo `Cambio de horario: Yoga el 17/11 a las 20:00`. El cuerpo es libre. Cambiar el `instructor` o el `cupo` no manda correos.
10. El cambio entero se rechaza con 409, y no cambia ninguna clase, si:
    - la clase `desde_clase_id` ya empezó;
    - con la hora nueva, alguna clase quedaría empezando en este momento o antes;
    - con el cupo nuevo, alguna clase quedaría con más reservas confirmadas que lugares.
11. La respuesta es 404 si la serie no existe o si `desde_clase_id` no es una clase de esa serie, y 422 si no viene ningún cambio o si un valor es inválido según las reglas 3 y 6.

**Cancelar una clase**

12. `POST /admin/clases/{id}/cancelar` cancela una clase, sea de una serie o suelta. La clase pasa a `cancelada`: ya no aparece en `GET /clases`, pero `GET /clases/{id}` la sigue mostrando, y no se puede reservar (409 con el `detail` `La clase está cancelada`).
13. Cada reserva confirmada de esa clase pasa a `cancelada`, el socio recupera el crédito y recibe un correo con el asunto `Clase cancelada: {nombre} el {fecha y hora}`, por ejemplo `Clase cancelada: Yoga el 17/11 a las 19:00`. El cuerpo es libre.
14. La respuesta es 409 si la clase ya está cancelada o ya empezó, y 404 si no existe.

## Contrato de la API

Todos los endpoints de este pedido son de administración: sin una `X-Admin-Key` válida la respuesta es 401.

`POST /admin/series`:

```json
{"nombre": "Yoga", "instructor": "Sofía", "dia": "martes", "hora": "19:00", "duracion_min": 60, "cupo": 15, "desde": "2026-11-10", "hasta": "2026-12-31"}
```

Respuesta 201, con las clases ordenadas por inicio:

```json
{"id": 3, "nombre": "Yoga", "instructor": "Sofía", "dia": "martes", "hora": "19:00", "duracion_min": 60, "cupo": 15, "desde": "2026-11-10", "hasta": "2026-12-31",
 "clases": [{"id": 41, "nombre": "Yoga", "instructor": "Sofía", "inicio": "2026-11-10T22:00:00+00:00", "duracion_min": 60, "cupo": 15, "lugares_libres": 15, "serie_id": 3, "estado": "programada"}]}
```

`GET /admin/series/{id}`: 200 con el mismo formato, con todas las clases de la serie, también las canceladas. 404 si no existe.

`PATCH /admin/series/{id}`:

```json
{"desde_clase_id": 43, "hora": "20:00", "instructor": "Leo"}
```

Respuesta 200 con la serie como en `GET /admin/series/{id}`.

`POST /admin/clases/{id}/cancelar`, sin cuerpo. Respuesta 200 con la clase, como en `GET /clases/{id}`.

## Fuera de alcance

- Borrar una serie entera o cambiar su día de la semana.
- Agregar clases a una serie después de creada o extender su `hasta`.
- Lista de espera.

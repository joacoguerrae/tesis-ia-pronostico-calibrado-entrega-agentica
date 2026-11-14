# Horarios de clases corridos

## Contexto

Desde el lunes 2/11, recepción recibe quejas sobre los horarios de algunas clases. Ese día empezó a usarse la versión nueva del panel de administración, el que usa el personal para cargar las clases. No todas las clases tienen problemas: las que se cargaron antes andan bien.

Estos son tres reportes que llegaron esta semana. Todas las horas son de Montevideo:

1. "La clase de Funcional del jueves 12/11 es a las 19:00, pero a las 16:00 desapareció de la app y, cuando quise reservarla, me dijo que ya había empezado."
2. "Reservé el Funcional del 12/11 y el correo de confirmación dice que es a las 16:00. Fui a las 16:00 y no había nadie."
3. "En la lista de clases del jueves, la de Spinning de las 21:00 aparece antes que la de Yoga de las 20:00."

Funcional y Spinning se cargaron con el panel nuevo; Yoga, la semana anterior. El horario real de las tres es el que dicen los socios: Funcional a las 19:00, Yoga a las 20:00 y Spinning a las 21:00.

## Historia de usuario

Como socio, quiero ver, reservar y recibir los avisos de cada clase con su horario real, para no perderme ninguna.

## Qué tiene que quedar

1. Encontrá la causa y arreglala. No alcanza con que desaparezcan los tres síntomas de arriba: todo lo que dependa de la misma causa tiene que quedar bien.
2. Las clases se ven, se ordenan, se pueden reservar hasta su hora de inicio y aparecen en los correos con su horario real. Tiene que funcionar igual para las que se cargan de ahora en más y para las que ya están en la base.
3. `POST /admin/clases` acepta la hora de inicio con cualquier desfase horario: `Z`, `+00:00`, `-03:00` o cualquier otro. Todas las fechas se guardan y se devuelven como dice el README: en UTC y en ISO 8601, con el formato `2026-11-12T22:00:00+00:00`.
4. La base de producción ya tiene clases cargadas de tres formas distintas, y todas tienen que quedar guardadas en el formato del punto 3:
   - las de antes de setiembre se guardaron sin zona horaria (`2026-08-20T22:00:00`), y esa hora está en UTC;
   - las que se cargaron entre setiembre y el 1/11 están bien (`2026-10-15T22:00:00+00:00`);
   - las del panel nuevo quedaron guardadas con el desfase que mandó el panel (`2026-11-12T19:00:00-03:00`), y esa hora es correcta para ese desfase.
5. Ninguna clase puede cambiar su horario real. Funcional sigue siendo el jueves 12/11 a las 19:00 de Montevideo, o sea, `2026-11-12T22:00:00+00:00`.
6. Otros procesos de la empresa leen la tabla `clases` directamente de la base. Por eso lo que queda guardado tiene que estar bien, no solo lo que devuelve la API.
7. Nadie va a correr un script a mano: las clases ya cargadas se tienen que arreglar solas cuando arranca la versión nueva de la app, o sea, al llamar a `crear_app()`. La app se reinicia seguido, así que arrancarla otra vez no puede volver a mover ninguna clase.
8. Las clases conservan su `id`, porque las reservas apuntan a ellas.

## Fuera de alcance

- Cambiar el panel de administración: es otro sistema y va a seguir mandando la hora con el desfase de Montevideo.
- Avisar por correo a los socios afectados.

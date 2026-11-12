# Pulso

API de reservas de clases de Pulso, una cadena de gimnasios de Montevideo. Los socios ven las clases (yoga, spinning, funcional…), las reservan con créditos de su plan y reciben un correo de confirmación. El personal del gimnasio carga las clases desde un panel de administración.

## Cómo correrlo

```
pip install -r requirements.txt
python -m pytest
```

## Estructura

- `pulso/main.py`: la API (FastAPI). `crear_app()` arma la aplicación e inicializa la base.
- `pulso/db.py`: acceso a SQLite. La ruta de la base sale de la variable `PULSO_DB`.
- `pulso/reloj.py`: hora actual de la app.
- `pulso/correo.py`: bandeja de salida de correos.
- `tests/`: tests de la API con pytest.

## Convenciones

- La hora actual se toma siempre de `reloj.ahora()`, nunca de `datetime.now()`. Los tests la fijan con `reloj.fijar()`.
- Las fechas se guardan y se devuelven en UTC, en ISO 8601. Lo que ve el socio (correos, reportes, filtros por día) va en hora de Montevideo, que es UTC−3 todo el año: `reloj.MONTEVIDEO`.
- Los socios se identifican con `Authorization: Bearer <token>`. Los endpoints de administración están bajo `/admin` y piden el header `X-Admin-Key`, que se compara con la variable `PULSO_ADMIN_KEY`.
- Los errores se devuelven con `HTTPException` y el mensaje en `detail`: 401 sin credenciales válidas, 404 si no existe el recurso o no es del socio, 409 si una regla de negocio no permite la operación y 422 si los datos no son válidos.
- Los correos no se mandan directo: se guardan con `correo.enviar()`, y las fechas del texto van con `correo.fecha_y_hora()`.
- Las funciones de `db.py` que ya existen no cambian de nombre ni de firma, porque las usan otros procesos de la empresa. Se pueden agregar funciones y columnas nuevas.

## Endpoints

| Método | Ruta | Qué hace |
|---|---|---|
| GET | `/clases` | Clases que todavía no empezaron, ordenadas por inicio, con `lugares_libres`. |
| GET | `/clases/{id}` | Una clase. |
| POST | `/admin/clases` | Crea una clase (admin). |
| POST | `/reservas` | Reserva una clase: descuenta un crédito y manda el correo de confirmación. |
| GET | `/reservas` | Reservas del socio, ordenadas por el inicio de la clase. |
| GET | `/yo` | Datos del socio y créditos que le quedan. |

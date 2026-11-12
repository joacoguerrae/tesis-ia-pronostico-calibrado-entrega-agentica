# Exportar la ocupación de las clases

## Contexto

Todos los meses la gerencia arma una planilla con la ocupación de cada clase para decidir horarios e instructores. Hoy la copian a mano del panel.

## Historia de usuario

Como gerente, quiero bajar un CSV con la ocupación de las clases de un período para abrirlo en Excel.

## Reglas de negocio

1. Es un endpoint de administración: sin una `X-Admin-Key` válida la respuesta es 401.
2. `desde` y `hasta` son obligatorios, con formato `YYYY-MM-DD`, y los dos extremos se incluyen. Filtran por el día en que empieza la clase, en hora de Montevideo. Entran las clases pasadas y las futuras.
3. Si falta una fecha, si tiene otro formato, si `desde` es posterior a `hasta` o si el período tiene más de 31 días contando los dos extremos, la respuesta es 422. Por ejemplo, del 1/10 al 31/10 se acepta, y del 1/10 al 1/11 (32 días) no.
4. La respuesta es `text/csv; charset=utf-8`, separada por comas. La primera fila es el encabezado: `fecha,hora,clase,instructor,cupo,confirmadas,ocupacion_pct`.
5. Hay una fila por clase, ordenadas por el inicio y, si empatan, por id.
6. `fecha` va como `YYYY-MM-DD` y `hora` como `HH:MM`, las dos en hora de Montevideo.
7. `confirmadas` cuenta las reservas confirmadas. Las canceladas no cuentan.
8. `ocupacion_pct` es confirmadas / cupo × 100, redondeado al entero más cercano, y los ,5 redondean para arriba: 12,5 da 13.
9. Si un texto tiene comas o comillas, va entre comillas dobles y las comillas internas se duplican, como pide el CSV estándar (RFC 4180).
10. Si no hay clases en el período, el archivo trae solo el encabezado.

## Contrato de la API

`GET /admin/ocupacion.csv?desde=2026-11-01&hasta=2026-11-30`, con `X-Admin-Key`.

```
fecha,hora,clase,instructor,cupo,confirmadas,ocupacion_pct
2026-11-03,07:00,Spinning,Leo,20,15,75
2026-11-03,19:30,"Yoga, nivel 1",Sofía,12,12,100
```

## Fuera de alcance

- Otros formatos (Excel, PDF).
- Totales por instructor o por sede.

# Filtrar y paginar las clases

## Contexto

La app móvil muestra la grilla de clases. Con las tres sedes nuevas hay cientos de clases, la lista tarda en cargar y los socios piden buscar por día y por instructor.

## Historia de usuario

Como socio, quiero filtrar las clases por día, por instructor y por lugar disponible, y verlas de a páginas.

## Reglas de negocio

1. `GET /clases` acepta los parámetros opcionales `desde`, `hasta`, `instructor`, `con_lugar`, `pagina` y `por_pagina`.
2. `desde` y `hasta` son fechas `YYYY-MM-DD` y filtran por el día en que empieza la clase, en hora de Montevideo. Los dos extremos se incluyen y se pueden usar por separado.
3. `instructor` filtra por el nombre exacto del instructor, sin distinguir mayúsculas de minúsculas.
4. `con_lugar=true` deja solo las clases con `lugares_libres` mayor que cero. Con `con_lugar=false`, o sin el parámetro, no se filtra.
5. Las clases que ya empezaron nunca se listan, igual que ahora.
6. `pagina` empieza en 1 y por defecto es 1. `por_pagina` va de 1 a 50 y por defecto es 20. Fuera de esos rangos la respuesta es 422. Una página más allá del final devuelve una lista vacía.
7. El orden es el de ahora: por inicio y, si empatan, por id.
8. La respuesta sigue siendo una lista de clases con el formato de hoy, para no romper las versiones viejas de la app. Esas versiones van a recibir solo la primera página, y eso está aceptado. El total de clases que cumplen los filtros, antes de paginar, va en el header `X-Total`.
9. Si una fecha no tiene el formato `YYYY-MM-DD`, o si `desde` es posterior a `hasta`, la respuesta es 422.

## Contrato de la API

`GET /clases?desde=2026-11-12&hasta=2026-11-14&instructor=leo&con_lugar=true&pagina=2&por_pagina=10`

Respuesta 200 con el header `X-Total: 23` y una lista de hasta 10 clases.

## Fuera de alcance

- Filtrar por sede o por tipo de clase.
- Cambios en `GET /clases/{id}`.

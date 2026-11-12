# Plan corporativo por convenio

## Contexto

Pulso firmó convenios con algunas empresas: sus empleados pueden tener el plan corporativo. Quién es empleado activo de cada empresa no lo sabemos nosotros: lo publica cada empresa en el servicio de beneficios de un proveedor externo. Hoy recepción pide un recibo de sueldo y cambia el plan a mano, y nadie se entera cuando alguien deja la empresa.

## Historia de usuario

Como socio que trabaja en una empresa con convenio, quiero activar el plan corporativo desde la app, para tener más créditos sin pasar por recepción.

## Reglas de negocio

1. `POST /convenio` lo usa el socio con su token (sin token válido, 401) y recibe `empresa`, el código de la empresa en el servicio de beneficios. Si falta `empresa` o viene vacío, la respuesta es 422.
2. El servicio de beneficios es la fuente de verdad. Pulso no guarda una lista de empleados ni lo deduce por su cuenta (por ejemplo, por el dominio del email): le pregunta al servicio en cada activación y en cada revalidación. Lo que sí guarda es con qué empresa activó el plan cada socio, para revalidarlo después.
3. El email va al servicio en minúsculas, aunque el socio lo tenga guardado con mayúsculas, y codificado entero en el path. Ojo: el servicio decodifica el path como un formulario, así que un `+` sin codificar le llega como espacio. Por ejemplo, `Ana.Perez+Gym@Example.com` va como `ana.perez%2Bgym%40example.com`.
4. Si el servicio dice que es empleado activo, el plan pasa a `corporativo` y los créditos suben a un piso de 12: si tenía menos de 12 quedan en 12, y si tenía 12 o más no cambian. No se suman 12 a los que tenía.
5. Al activar el plan, el socio recibe un correo con el asunto `Ya tenés el plan corporativo`. El cuerpo es libre.
6. Si el socio ya tiene el plan corporativo, con esa empresa o con otra, la respuesta es 409 y no cambia nada: no se vuelven a dar créditos ni se manda otro correo. Un socio que volvió a `basico` por la revalidación puede activarlo de nuevo, con las mismas reglas.
7. Si el servicio dice que no es empleado activo (`"activo": false`) o que no lo conoce, la respuesta es 409 y no cambia nada.
8. Si el servicio dice que la empresa no existe, la respuesta es 404 y no cambia nada.
9. Si el servicio falla, la respuesta es 503 y no cambia nada. Cuenta como falla que no se pueda conectar, que no conteste en 3 segundos o que conteste algo que no está en el contrato de abajo: un 5xx, un 401 porque la clave está mal, etc.
10. Un proceso programado llama una vez por día a `POST /admin/revalidar-convenios`. Es un endpoint de administración: sin una `X-Admin-Key` válida, la respuesta es 401. Consulta al servicio por cada socio con plan corporativo, con la empresa con la que lo activó:
    - si sigue siendo empleado activo, no se le cambia nada, tampoco los créditos;
    - si ya no es empleado activo, si el servicio no lo conoce o si la empresa ya no existe, vuelve al plan `basico`, conserva los créditos que tenga y recibe un correo con el asunto `Se terminó tu plan corporativo`;
    - si el servicio falla para ese socio (como en la regla 9), el socio queda como estaba y se sigue con los demás.
11. La revalidación responde 200 aunque el servicio haya fallado para algunos socios o para todos, y dice cuántos siguen con el plan corporativo, cuántos bajaron a `basico` y cuántos no se pudieron revisar.
12. Hay dos claves y no se mezclan. `X-Admin-Key` protege los endpoints de `/admin`, como siempre. La clave del servicio de beneficios sale de `PULSO_BENEFICIOS_CLAVE` y va en el header `X-Api-Key` de cada consulta. La URL base del servicio sale de `PULSO_BENEFICIOS_URL`. Las dos variables se leen del entorno cada vez que se consulta al servicio, como pasa con `PULSO_ADMIN_KEY`.

## Contrato de la API

### Pulso

`POST /convenio`, con el token del socio:

```json
{"empresa": "acme"}
```

Respuesta 200:

```json
{"plan": "corporativo", "empresa": "acme", "creditos": 12}
```

Si no se puede activar, responde 401, 404, 409, 422 o 503, según las reglas de arriba.

`POST /admin/revalidar-convenios`, con `X-Admin-Key` y sin cuerpo.

Respuesta 200:

```json
{"siguen": 2, "bajaron": 1, "sin_revisar": 1}
```

`GET /yo` ya devuelve `plan` y `creditos`, y no cambia.

### Servicio de beneficios

`GET {PULSO_BENEFICIOS_URL}/empresas/{empresa}/empleados/{email}`, con el header `X-Api-Key`. La URL base no lleva barra al final. Por ejemplo:

```
GET https://beneficios.example.com/empresas/acme/empleados/ana.perez%2Bgym%40example.com
X-Api-Key: <PULSO_BENEFICIOS_CLAVE>
```

| Respuesta | Qué significa |
|---|---|
| 200 `{"activo": true}` | Es empleado activo de la empresa. |
| 200 `{"activo": false}` | Es empleado, pero no está activo (licencia, baja en trámite…). |
| 404 `{"error": "empleado_desconocido"}` | La empresa existe, pero no conoce ese email. |
| 404 `{"error": "empresa_desconocida"}` | No hay ninguna empresa con ese código. |
| 401 `{"error": "clave_invalida"}` | Falta la clave o no es válida. |

Cuando tiene problemas, puede responder un 5xx, que no siempre trae JSON, o directamente no responder.

## Fuera de alcance

- Que el socio dé de baja el plan corporativo por su cuenta.
- Reintentos cuando el servicio falla: el socio prueba más tarde, y a los corporativos los revisa la revalidación del día siguiente.
- Que un socio tenga convenio con más de una empresa a la vez.

# Alta de socios desde la app

## Contexto

Hoy los socios los da de alta recepción. Queremos que cualquiera se pueda registrar desde la app y empezar a reservar enseguida.

## Historia de usuario

Como persona interesada en el gimnasio, quiero registrarme en la app con mi nombre, mi email y un plan, para empezar a reservar clases.

## Reglas de negocio

1. `POST /socios` no pide autenticación y recibe `nombre`, `email` y `plan`.
2. Al `nombre` se le sacan los espacios del principio y del final. Después de eso tiene que tener entre 2 y 80 caracteres.
3. Al `email` se le sacan los espacios de los extremos y se pasa a minúsculas antes de validarlo y de guardarlo. Es válido si no tiene espacios, tiene exactamente una `@`, hay algo antes de la `@` y después viene un dominio con al menos un punto, que no puede estar ni al principio ni al final del dominio.
4. `plan` es `basico` o `premium`. Los créditos iniciales son 8 para `basico` y 20 para `premium`.
5. Si ya existe un socio con ese email, la respuesta es 409.
6. Si falta un dato o alguno no es válido, la respuesta es 422.
7. Al registrarse, el socio recibe un correo con el asunto `Te damos la bienvenida a Pulso`.
8. La respuesta trae el token con el que el socio se autentica después (`Authorization: Bearer`). Tiene que ser distinto para cada socio, imposible de adivinar y de al menos 32 caracteres.

## Contrato de la API

`POST /socios`

```json
{"nombre": "Ana Pérez", "email": "Ana.Perez@Example.com", "plan": "premium"}
```

Respuesta 201, con el nombre y el email ya normalizados:

```json
{"id": 7, "nombre": "Ana Pérez", "email": "ana.perez@example.com", "plan": "premium", "creditos": 20, "token": "…"}
```

## Fuera de alcance

- Verificar el email con un enlace.
- Contraseñas y login: por ahora el socio usa el token que recibe al registrarse.

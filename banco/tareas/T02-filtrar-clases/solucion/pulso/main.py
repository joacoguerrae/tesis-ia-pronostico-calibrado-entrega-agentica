import os
from datetime import date

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Query, Response
from pydantic import AwareDatetime, BaseModel, Field

from pulso import correo, db, reloj

router = APIRouter()


def socio_actual(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(401, 'Falta el token')
    socio = db.socio_por_token(authorization.removeprefix('Bearer '))
    if socio is None:
        raise HTTPException(401, 'Token inválido')
    return socio


def admin(x_admin_key: str | None = Header(default=None)):
    if not x_admin_key or x_admin_key != os.environ.get('PULSO_ADMIN_KEY'):
        raise HTTPException(401, 'Clave de administración inválida')


def ver_clase(clase):
    return dict(clase, lugares_libres=clase['cupo'] - db.confirmadas(clase['id']))


def ver_reserva(reserva):
    return {k: reserva[k] for k in ('id', 'clase_id', 'estado', 'creada')}


@router.get('/clases')
def listar_clases(response: Response, desde: date | None = None, hasta: date | None = None,
                  instructor: str | None = None, con_lugar: bool = False,
                  pagina: int = Query(1, ge=1), por_pagina: int = Query(20, ge=1, le=50)):
    if desde and hasta and desde > hasta:
        raise HTTPException(422, 'desde es posterior a hasta')
    ahora = reloj.ahora()
    elegidas = []
    for c in db.clases():
        inicio = db.a_fecha(c['inicio'])
        dia = inicio.astimezone(reloj.MONTEVIDEO).date()
        if inicio <= ahora or (desde and dia < desde) or (hasta and dia > hasta):
            continue
        if instructor and c['instructor'].lower() != instructor.lower():
            continue
        clase = ver_clase(c)
        if con_lugar and clase['lugares_libres'] <= 0:
            continue
        elegidas.append(clase)
    response.headers['X-Total'] = str(len(elegidas))
    return elegidas[(pagina - 1) * por_pagina:pagina * por_pagina]


@router.get('/clases/{clase_id}')
def obtener_clase(clase_id: int):
    clase = db.clase(clase_id)
    if clase is None:
        raise HTTPException(404, 'No existe la clase')
    return ver_clase(clase)


class NuevaClase(BaseModel):
    nombre: str = Field(min_length=1)
    instructor: str = Field(min_length=1)
    inicio: AwareDatetime
    duracion_min: int = Field(gt=0)
    cupo: int = Field(gt=0)


@router.post('/admin/clases', status_code=201, dependencies=[Depends(admin)])
def crear_clase(datos: NuevaClase):
    return ver_clase(db.crear_clase(**datos.model_dump()))


class NuevaReserva(BaseModel):
    clase_id: int


@router.post('/reservas', status_code=201)
def reservar(datos: NuevaReserva, socio=Depends(socio_actual)):
    clase = db.clase(datos.clase_id)
    if clase is None:
        raise HTTPException(404, 'No existe la clase')
    inicio = db.a_fecha(clase['inicio'])
    if inicio <= reloj.ahora():
        raise HTTPException(409, 'La clase ya empezó')
    if any(r['clase_id'] == clase['id'] and r['estado'] == 'confirmada' for r in db.reservas_de(socio['id'])):
        raise HTTPException(409, 'Ya tenés una reserva para esta clase')
    if db.confirmadas(clase['id']) >= clase['cupo']:
        raise HTTPException(409, 'La clase no tiene lugar')
    if socio['creditos'] < 1:
        raise HTTPException(409, 'No te quedan créditos')
    reserva = db.crear_reserva(socio['id'], clase['id'], reloj.ahora())
    db.sumar_creditos(socio['id'], -1)
    correo.enviar(socio['email'], f"Reserva confirmada: {clase['nombre']} el {correo.fecha_y_hora(inicio)}",
                  f"Hola {socio['nombre']}, te esperamos en {clase['nombre']} con {clase['instructor']}.")
    return ver_reserva(reserva)


@router.get('/reservas')
def mis_reservas(socio=Depends(socio_actual)):
    return [ver_reserva(r) for r in db.reservas_de(socio['id'])]


@router.get('/yo')
def yo(socio=Depends(socio_actual)):
    return {k: socio[k] for k in ('id', 'nombre', 'email', 'plan', 'creditos')}


def crear_app():
    db.inicializar()
    app = FastAPI(title='Pulso')
    app.include_router(router)
    return app

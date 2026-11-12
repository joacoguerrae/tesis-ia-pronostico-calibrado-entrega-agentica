import csv
import io
import math
import os
from datetime import date
from fractions import Fraction

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Response
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
def listar_clases():
    ahora = reloj.ahora()
    return [ver_clase(c) for c in db.clases() if db.a_fecha(c['inicio']) > ahora]


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


@router.get('/admin/ocupacion.csv', dependencies=[Depends(admin)])
def exportar_ocupacion(desde: date, hasta: date):
    if desde > hasta or (hasta - desde).days + 1 > 31:
        raise HTTPException(422, 'Período inválido')
    salida = io.StringIO()
    escritor = csv.writer(salida)
    escritor.writerow(['fecha', 'hora', 'clase', 'instructor', 'cupo', 'confirmadas', 'ocupacion_pct'])
    for c in db.clases():
        inicio = db.a_fecha(c['inicio']).astimezone(reloj.MONTEVIDEO)
        if not desde <= inicio.date() <= hasta:
            continue
        n = db.confirmadas(c['id'])
        pct = math.floor(Fraction(100 * n, c['cupo']) + Fraction(1, 2))
        escritor.writerow([f'{inicio:%Y-%m-%d}', f'{inicio:%H:%M}', c['nombre'], c['instructor'], c['cupo'], n, pct])
    return Response(salida.getvalue(), media_type='text/csv; charset=utf-8')


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

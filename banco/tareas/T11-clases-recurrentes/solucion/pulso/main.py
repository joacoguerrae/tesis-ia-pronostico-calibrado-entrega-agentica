import os
from datetime import date, datetime
from typing import Literal

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException
from pydantic import AwareDatetime, BaseModel, Field, model_validator

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
    return [ver_clase(c) for c in db.clases()
            if c['estado'] == 'programada' and db.a_fecha(c['inicio']) > ahora]


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
    if clase['estado'] == 'cancelada':
        raise HTTPException(409, 'La clase está cancelada')
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


DIAS = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
CIERRES = {date(2026, 12, 25), date(2027, 1, 1), date(2027, 2, 8), date(2027, 2, 9), date(2027, 3, 25),
           date(2027, 3, 26), date(2027, 5, 1)}
HORA = r'^([01][0-9]|2[0-3]):[0-5][0-9]$'


def en_montevideo(dia, hora):
    h, m = map(int, hora.split(':'))
    return datetime(dia.year, dia.month, dia.day, h, m, tzinfo=reloj.MONTEVIDEO)


class NuevaSerie(BaseModel):
    nombre: str = Field(min_length=1)
    instructor: str = Field(min_length=1)
    dia: Literal['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
    hora: str = Field(pattern=HORA)
    duracion_min: int = Field(gt=0)
    cupo: int = Field(gt=0)
    desde: date
    hasta: date

    @model_validator(mode='after')
    def rango(self):
        if self.hasta < self.desde:
            raise ValueError('hasta es anterior a desde')
        if (self.hasta - self.desde).days > 366:
            raise ValueError('la serie dura más de 366 días')
        return self


def ver_serie(serie):
    clases = [ver_clase(c) for c in db.clases_de_serie(serie['id'])]
    return dict(serie, clases=clases)


@router.post('/admin/series', status_code=201, dependencies=[Depends(admin)])
def crear_serie(datos: NuevaSerie):
    ahora = reloj.ahora()
    dia_semana = DIAS.index(datos.dia)
    inicios = []
    for n in range((datos.hasta - datos.desde).days + 1):
        dia = date.fromordinal(datos.desde.toordinal() + n)
        if dia.weekday() == dia_semana and dia not in CIERRES:
            inicio = en_montevideo(dia, datos.hora)
            if inicio > ahora:
                inicios.append(inicio)
    valores = dict(datos.model_dump(), desde=datos.desde.isoformat(), hasta=datos.hasta.isoformat())
    return ver_serie(db.crear_serie(valores, inicios))


@router.get('/admin/series/{serie_id}', dependencies=[Depends(admin)])
def obtener_serie(serie_id: int):
    serie = db.serie(serie_id)
    if serie is None:
        raise HTTPException(404, 'No existe la serie')
    return ver_serie(serie)


class CambioDeSerie(BaseModel):
    desde_clase_id: int
    hora: str | None = Field(default=None, pattern=HORA)
    instructor: str | None = Field(default=None, min_length=1)
    cupo: int | None = Field(default=None, gt=0)

    @model_validator(mode='after')
    def algun_cambio(self):
        if self.hora is None and self.instructor is None and self.cupo is None:
            raise ValueError('no hay ningún cambio')
        return self


@router.patch('/admin/series/{serie_id}', dependencies=[Depends(admin)])
def cambiar_serie(serie_id: int, datos: CambioDeSerie):
    serie = db.serie(serie_id)
    if serie is None:
        raise HTTPException(404, 'No existe la serie')
    desde = db.clase(datos.desde_clase_id)
    if desde is None or desde['serie_id'] != serie_id:
        raise HTTPException(404, 'La clase no es de esta serie')
    ahora = reloj.ahora()
    if db.a_fecha(desde['inicio']) <= ahora:
        raise HTTPException(409, 'La clase ya empezó')
    inicio_desde = db.a_fecha(desde['inicio'])
    afectadas = [c for c in db.clases_de_serie(serie_id)
                 if c['estado'] == 'programada'
                 and (c['id'] == desde['id'] or db.a_fecha(c['inicio']) > inicio_desde)]
    cambios = {c['id']: {} for c in afectadas}
    movidas = []
    for c in afectadas:
        if datos.hora is not None:
            dia = db.a_fecha(c['inicio']).astimezone(reloj.MONTEVIDEO).date()
            nuevo = en_montevideo(dia, datos.hora)
            if nuevo <= ahora:
                raise HTTPException(409, 'Una clase quedaría empezando en el pasado')
            if db.a_texto(nuevo) != c['inicio']:
                cambios[c['id']]['inicio'] = db.a_texto(nuevo)
                movidas.append((c, nuevo))
        if datos.instructor is not None:
            cambios[c['id']]['instructor'] = datos.instructor
        if datos.cupo is not None:
            if db.confirmadas(c['id']) > datos.cupo:
                raise HTTPException(409, 'Una clase tiene más reservas que el cupo nuevo')
            cambios[c['id']]['cupo'] = datos.cupo
    de_la_serie = {k: v for k, v in (('hora', datos.hora), ('instructor', datos.instructor), ('cupo', datos.cupo))
                   if v is not None}
    db.cambiar_serie(serie_id, de_la_serie, cambios)
    for c, nuevo in movidas:
        for r in db.reservas_confirmadas_de_clase(c['id']):
            correo.enviar(r['email'], f"Cambio de horario: {c['nombre']} el {correo.fecha_y_hora(nuevo)}",
                          f"Hola {r['socio_nombre']}, {c['nombre']} pasa a ser el {correo.fecha_y_hora(nuevo)}.")
    return ver_serie(db.serie(serie_id))


@router.post('/admin/clases/{clase_id}/cancelar', dependencies=[Depends(admin)])
def cancelar_clase(clase_id: int):
    clase = db.clase(clase_id)
    if clase is None:
        raise HTTPException(404, 'No existe la clase')
    if clase['estado'] == 'cancelada':
        raise HTTPException(409, 'La clase ya está cancelada')
    inicio = db.a_fecha(clase['inicio'])
    if inicio <= reloj.ahora():
        raise HTTPException(409, 'La clase ya empezó')
    for r in db.cancelar_clase(clase_id):
        correo.enviar(r['email'], f"Clase cancelada: {clase['nombre']} el {correo.fecha_y_hora(inicio)}",
                      f"Hola {r['socio_nombre']}, se canceló {clase['nombre']}. Te devolvimos el crédito.")
    return ver_clase(db.clase(clase_id))


def crear_app():
    db.inicializar()
    app = FastAPI(title='Pulso')
    app.include_router(router)
    return app

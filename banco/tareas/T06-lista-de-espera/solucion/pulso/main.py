import os

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


def buscar_clase(clase_id):
    clase = db.clase(clase_id)
    if clase is None:
        raise HTTPException(404, 'No existe la clase')
    return clase


def ya_empezo(clase):
    return db.a_fecha(clase['inicio']) <= reloj.ahora()


def asignar_lugares(clase_id):
    """Da los lugares libres de la clase a los primeros de la lista de espera."""
    clase = db.clase(clase_id)
    if ya_empezo(clase):
        return
    cuando = correo.fecha_y_hora(db.a_fecha(clase['inicio']))
    for anotado in db.lista_de_espera(clase_id):
        if db.confirmadas(clase_id) >= clase['cupo']:
            break
        socio = db.socio(anotado['socio_id'])
        db.sacar_de_espera(socio['id'], clase_id)
        if db.tiene_reserva(socio['id'], clase_id):
            continue
        if socio['creditos'] < 1:
            correo.enviar(socio['email'], f"No pudimos darte el lugar: {clase['nombre']} el {cuando}",
                          f"Hola {socio['nombre']}, se liberó un lugar en {clase['nombre']}, pero no te quedan "
                          f"créditos. Te sacamos de la lista de espera.")
            continue
        db.crear_reserva(socio['id'], clase_id, reloj.ahora())
        db.sumar_creditos(socio['id'], -1)
        correo.enviar(socio['email'], f"Se liberó un lugar: {clase['nombre']} el {cuando}",
                      f"Hola {socio['nombre']}, ya tenés tu lugar en {clase['nombre']} con {clase['instructor']}. "
                      f"Usamos un crédito de tu plan.")


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


class CambioDeClase(BaseModel):
    cupo: int = Field(gt=0)


@router.patch('/admin/clases/{clase_id}', dependencies=[Depends(admin)])
def cambiar_clase(clase_id: int, datos: CambioDeClase):
    buscar_clase(clase_id)
    if datos.cupo < db.confirmadas(clase_id):
        raise HTTPException(409, 'El cupo no puede quedar por debajo de las reservas confirmadas')
    db.cambiar_cupo(clase_id, datos.cupo)
    asignar_lugares(clase_id)
    return ver_clase(db.clase(clase_id))


@router.post('/admin/reservas/{reserva_id}/cancelar', dependencies=[Depends(admin)])
def cancelar_reserva(reserva_id: int):
    reserva = db.reserva(reserva_id)
    if reserva is None:
        raise HTTPException(404, 'No existe la reserva')
    if not db.cancelar_reserva(reserva_id):
        raise HTTPException(409, 'La reserva ya está cancelada')
    db.sumar_creditos(reserva['socio_id'], 1)
    asignar_lugares(reserva['clase_id'])
    return ver_reserva(db.reserva(reserva_id))


def ver_espera(socio, clase_id):
    posicion = db.posicion_en_espera(socio['id'], clase_id)
    if posicion is None:
        raise HTTPException(404, 'No estás en la lista de espera')
    return {'clase_id': clase_id, 'posicion': posicion}


@router.post('/clases/{clase_id}/espera', status_code=201)
def anotarse(clase_id: int, socio=Depends(socio_actual)):
    clase = buscar_clase(clase_id)
    if ya_empezo(clase):
        raise HTTPException(409, 'La clase ya empezó')
    if db.tiene_reserva(socio['id'], clase_id):
        raise HTTPException(409, 'Ya tenés una reserva para esta clase')
    if db.posicion_en_espera(socio['id'], clase_id) is not None:
        raise HTTPException(409, 'Ya estás en la lista de espera')
    if db.confirmadas(clase_id) < clase['cupo']:
        raise HTTPException(409, 'La clase tiene lugar: reservala directo')
    if socio['creditos'] < 1:
        raise HTTPException(409, 'No te quedan créditos')
    db.anotar_en_espera(socio['id'], clase_id, reloj.ahora())
    return ver_espera(socio, clase_id)


@router.get('/clases/{clase_id}/espera')
def mi_lugar_en_espera(clase_id: int, socio=Depends(socio_actual)):
    buscar_clase(clase_id)
    return ver_espera(socio, clase_id)


@router.delete('/clases/{clase_id}/espera', status_code=204)
def bajarse(clase_id: int, socio=Depends(socio_actual)):
    buscar_clase(clase_id)
    if not db.sacar_de_espera(socio['id'], clase_id):
        raise HTTPException(404, 'No estás en la lista de espera')
    return Response(status_code=204)


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

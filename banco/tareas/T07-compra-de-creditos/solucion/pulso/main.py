import os
import re
from datetime import timedelta

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException
from pydantic import AwareDatetime, BaseModel, Field

from pulso import correo, db, pagos, reloj

router = APIRouter()

PACKS = {'pack-4': {'creditos': 4, 'monto': 1200}, 'pack-8': {'creditos': 8, 'monto': 2200}}
MONEDA = 'UYU'
ASUNTO_COMPRA_APROBADA = 'Compra de créditos aprobada'
# Una compra sin pago se da por rechazada si a los 30 minutos Cobrá no tiene ningún pago con su referencia.
ESPERA_SIN_PAGO = timedelta(minutes=30)


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


def ver_compra(compra):
    return {k: compra[k] for k in ('id', 'pack', 'creditos', 'monto', 'estado', 'creada', 'url_pago')}


def referencia(compra):
    return f"pulso-compra-{compra['id']}"


def compra_de_referencia(texto):
    encontrada = re.fullmatch(r'pulso-compra-(\d+)', texto or '')
    return db.compra(int(encontrada.group(1))) if encontrada else None


def aplicar_pago(compra, pago):
    """Aplica a la compra el estado que tiene el pago en Cobrá. Devuelve la compra actualizada."""
    if compra['pago_id'] is None:
        db.guardar_pago(compra['id'], pago['id'], pago.get('url_pago'))
    if pago['estado'] == 'aprobado' and db.aprobar_compra(compra['id']):
        socio = db.socio(compra['socio_id'])
        correo.enviar(socio['email'], ASUNTO_COMPRA_APROBADA,
                      f"Hola {socio['nombre']}, sumamos {compra['creditos']} créditos a tu cuenta. "
                      f"Ahora tenés {socio['creditos']}.")
    elif pago['estado'] == 'rechazado':
        db.rechazar_compra(compra['id'])
    return db.compra(compra['id'])


class NuevaCompra(BaseModel):
    pack: str


@router.post('/compras', status_code=201)
def comprar(datos: NuevaCompra, socio=Depends(socio_actual)):
    pack = PACKS.get(datos.pack)
    if pack is None:
        raise HTTPException(422, 'No existe ese pack')
    compra = db.crear_compra(socio['id'], datos.pack, pack['creditos'], pack['monto'], reloj.ahora())
    try:
        pago = pagos.crear_pago(pack['monto'], MONEDA, referencia(compra))
    except pagos.FallaDeCobra:
        # El pago pudo haberse creado igual: la compra queda pendiente y la conciliación lo busca por referencia.
        raise HTTPException(502, 'No pudimos iniciar el pago. Probá de nuevo en unos minutos.')
    db.guardar_pago(compra['id'], pago['id'], pago['url_pago'])
    return ver_compra(db.compra(compra['id']))


@router.get('/compras')
def mis_compras(socio=Depends(socio_actual)):
    return [ver_compra(c) for c in db.compras_de(socio['id'])]


class AvisoDePago(BaseModel):
    pago_id: str = Field(min_length=1)


@router.post('/webhooks/pagos')
def aviso_de_pago(aviso: AvisoDePago):
    # El webhook no viene firmado: del cuerpo solo se usa el id, y el estado se le pregunta a Cobrá.
    try:
        pago = pagos.consultar_pago(aviso.pago_id)
    except pagos.FallaDeCobra:
        raise HTTPException(503, 'Cobrá no responde')
    compra = compra_de_referencia(pago.get('referencia')) if pago else None
    if compra is None:
        raise HTTPException(404, 'No existe el pago')
    compra = aplicar_pago(compra, pago)
    return {'compra_id': compra['id'], 'estado': compra['estado']}


@router.post('/admin/conciliar-pagos', dependencies=[Depends(admin)])
def conciliar_pagos():
    ahora = reloj.ahora()
    cuenta = {'aprobada': 0, 'rechazada': 0, 'pendiente': 0}
    for compra in db.compras_pendientes():
        try:
            if compra['pago_id']:
                pago = pagos.consultar_pago(compra['pago_id'])
            else:
                pago = pagos.buscar_pago(referencia(compra))
        except pagos.FallaDeCobra:
            cuenta['pendiente'] += 1
            continue
        if pago is not None:
            compra = aplicar_pago(compra, pago)
        elif compra['pago_id'] is None and ahora - db.a_fecha(compra['creada']) >= ESPERA_SIN_PAGO:
            db.rechazar_compra(compra['id'])
            compra = db.compra(compra['id'])
        cuenta[compra['estado']] += 1
    return {'aprobadas': cuenta['aprobada'], 'rechazadas': cuenta['rechazada'], 'pendientes': cuenta['pendiente']}


def crear_app():
    db.inicializar()
    app = FastAPI(title='Pulso')
    app.include_router(router)
    return app

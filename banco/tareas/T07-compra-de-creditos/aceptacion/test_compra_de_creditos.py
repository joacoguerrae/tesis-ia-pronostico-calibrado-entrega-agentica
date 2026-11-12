from datetime import timedelta

import pytest

from apoyo import ADMIN, AHORA, auth
from cobra_falso import CobraFalso
from pulso import db, reloj

CLAVE_COBRA = 'clave-de-cobra'
ASUNTO = 'Compra de créditos aprobada'
CAMPOS = ('id', 'pack', 'creditos', 'monto', 'estado', 'creada', 'url_pago')


@pytest.fixture(autouse=True)
def cobra(monkeypatch):
    falso = CobraFalso(CLAVE_COBRA)
    monkeypatch.setenv('PULSO_PAGOS_URL', falso.url)
    monkeypatch.setenv('PULSO_PAGOS_CLAVE', CLAVE_COBRA)
    yield falso
    falso.apagar()


def ver(compra):
    return {k: compra[k] for k in CAMPOS}


def comprar(cliente, socio, pack='pack-4'):
    r = cliente.post('/compras', json={'pack': pack}, headers=auth(socio))
    assert r.status_code == 201, r.text
    return ver(r.json())


def intentar_comprar(cliente, socio, pack='pack-4'):
    return cliente.post('/compras', json={'pack': pack}, headers=auth(socio)).status_code


def compras(cliente, socio):
    r = cliente.get('/compras', headers=auth(socio))
    assert r.status_code == 200, r.text
    return [ver(c) for c in r.json()]


def referencia(compra):
    return f"pulso-compra-{compra['id']}"


def avisar(cliente, pago_id, estado='aprobado'):
    return cliente.post('/webhooks/pagos', json={'pago_id': pago_id, 'estado': estado})


def conciliar(cliente):
    r = cliente.post('/admin/conciliar-pagos', headers=ADMIN)
    assert r.status_code == 200, r.text
    return {k: r.json()[k] for k in ('aprobadas', 'rechazadas', 'pendientes')}


def conteo(aprobadas, rechazadas, pendientes):
    return {'aprobadas': aprobadas, 'rechazadas': rechazadas, 'pendientes': pendientes}


def creditos(cliente, socio):
    return cliente.get('/yo', headers=auth(socio)).json()['creditos']


def aprobaciones():
    return [c for c in db.correos() if c['asunto'] == ASUNTO]


def test_pack_que_no_esta_en_el_catalogo_da_422(cliente, socio, cobra):
    assert intentar_comprar(cliente, socio, 'pack-5') == 422
    assert cliente.post('/compras', json={}, headers=auth(socio)).status_code == 422
    assert compras(cliente, socio) == []
    assert cobra.creaciones() == []


def test_la_compra_queda_pendiente_con_la_url_de_pago(cliente, socio, cobra):
    compra = comprar(cliente, socio, 'pack-4')
    pago = cobra.pago_de(referencia(compra))
    assert pago is not None
    assert compra == {'id': compra['id'], 'pack': 'pack-4', 'creditos': 4, 'monto': 1200, 'estado': 'pendiente',
                      'creada': '2026-11-10T15:00:00+00:00', 'url_pago': pago['url_pago']}
    assert compras(cliente, socio) == [compra]
    assert creditos(cliente, socio) == 8
    assert aprobaciones() == []


def test_crea_el_pago_con_la_clave_y_la_idempotency_key(cliente, socio, cobra):
    compra = comprar(cliente, socio, 'pack-8')
    [pedido] = cobra.creaciones()
    assert pedido['ruta'] == '/v1/pagos'
    assert {k: pedido['cuerpo'].get(k) for k in ('monto', 'moneda', 'referencia')} == \
        {'monto': 2200, 'moneda': 'UYU', 'referencia': f"pulso-compra-{compra['id']}"}
    assert pedido['headers'].get('x-cobra-clave') == CLAVE_COBRA
    assert pedido['headers'].get('idempotency-key') == f"pulso-compra-{compra['id']}"


def test_si_cobra_falla_al_crear_el_pago_da_502_y_la_compra_queda_pendiente(cliente, socio, cobra):
    cobra.caido = True
    assert intentar_comprar(cliente, socio, 'pack-4') == 502
    cobra.apagar()
    assert intentar_comprar(cliente, socio, 'pack-8') == 502
    assert [(c['pack'], c['estado'], c['url_pago']) for c in compras(cliente, socio)] == \
        [('pack-8', 'pendiente', None), ('pack-4', 'pendiente', None)]
    assert creditos(cliente, socio) == 8


def test_webhook_aprobado_suma_los_creditos_y_manda_el_correo(cliente, socio, cobra):
    compra = comprar(cliente, socio, 'pack-4')
    pago_id = cobra.poner_estado(referencia(compra), 'aprobado')
    r = avisar(cliente, pago_id)
    assert r.status_code == 200
    assert (r.json()['compra_id'], r.json()['estado']) == (compra['id'], 'aprobada')
    assert creditos(cliente, socio) == 12
    assert compras(cliente, socio)[0]['estado'] == 'aprobada'
    [enviado] = aprobaciones()
    assert enviado['para'] == 'ana@example.com'


def test_webhook_no_usa_lo_que_dice_el_cuerpo(cliente, socio, cobra):
    compra = comprar(cliente, socio, 'pack-4')
    pago_id = cobra.pago_de(referencia(compra))['id']
    r = avisar(cliente, pago_id, 'aprobado')
    assert r.status_code == 200
    assert r.json()['estado'] == 'pendiente'
    assert avisar(cliente, 'pag_inventado', 'aprobado').status_code == 404
    ajeno = cobra.agregar_pago('pulso-compra-999', estado='aprobado')
    assert avisar(cliente, ajeno, 'aprobado').status_code == 404
    assert compras(cliente, socio)[0]['estado'] == 'pendiente'
    assert creditos(cliente, socio) == 8
    assert aprobaciones() == []


def test_webhook_rechazado_marca_la_compra_sin_sumar_creditos(cliente, socio, cobra):
    compra = comprar(cliente, socio, 'pack-8')
    pago_id = cobra.poner_estado(referencia(compra), 'rechazado')
    antes = db.correos()
    r = avisar(cliente, pago_id, 'rechazado')
    assert r.status_code == 200
    assert r.json()['estado'] == 'rechazada'
    assert compras(cliente, socio)[0]['estado'] == 'rechazada'
    assert creditos(cliente, socio) == 8
    assert db.correos() == antes


def test_cada_compra_suma_sus_creditos_una_sola_vez(cliente, socio, cobra):
    primera = comprar(cliente, socio, 'pack-8')
    segunda = comprar(cliente, socio, 'pack-4')
    pago_primera = cobra.poner_estado(referencia(primera), 'aprobado')
    for _ in range(3):
        assert avisar(cliente, pago_primera).status_code == 200
    pago_segunda = cobra.poner_estado(referencia(segunda), 'aprobado')
    assert conciliar(cliente) == conteo(1, 0, 0)
    r = avisar(cliente, pago_segunda)
    assert r.status_code == 200
    assert r.json()['estado'] == 'aprobada'
    assert conciliar(cliente) == conteo(0, 0, 0)
    assert creditos(cliente, socio) == 8 + 8 + 4
    assert len(aprobaciones()) == 2


def test_webhook_da_503_si_cobra_falla(cliente, socio, cobra):
    compra = comprar(cliente, socio, 'pack-4')
    pago_id = cobra.poner_estado(referencia(compra), 'aprobado')
    antes = db.correos()
    cobra.caido = True
    assert avisar(cliente, pago_id).status_code == 503
    cobra.apagar()
    assert avisar(cliente, pago_id).status_code == 503
    assert compras(cliente, socio)[0]['estado'] == 'pendiente'
    assert creditos(cliente, socio) == 8
    assert db.correos() == antes


def test_webhook_encuentra_la_compra_que_quedo_sin_pago(cliente, socio, cobra):
    cobra.crear_y_caer = True
    assert intentar_comprar(cliente, socio, 'pack-4') == 502
    cobra.caido = False
    [pago] = cobra.pagos()
    cobra.poner_estado(pago['referencia'], 'aprobado')
    r = avisar(cliente, pago['id'])
    assert r.status_code == 200
    assert r.json()['estado'] == 'aprobada'
    [compra] = compras(cliente, socio)
    assert (compra['estado'], compra['url_pago']) == ('aprobada', pago['url_pago'])
    assert pago['referencia'] == referencia(compra)
    assert creditos(cliente, socio) == 12


def test_conciliar_pide_clave_de_admin(cliente, socio, cobra):
    compra = comprar(cliente, socio, 'pack-4')
    cobra.poner_estado(referencia(compra), 'aprobado')
    assert cliente.post('/admin/conciliar-pagos').status_code == 401
    assert cliente.post('/admin/conciliar-pagos', headers={'X-Admin-Key': 'otra'}).status_code == 401
    assert compras(cliente, socio)[0]['estado'] == 'pendiente'
    assert creditos(cliente, socio) == 8


def test_la_conciliacion_aplica_el_estado_de_cobra_a_las_compras_de_todos(cliente, socio, otro, cobra):
    a = comprar(cliente, socio, 'pack-4')
    b = comprar(cliente, otro, 'pack-8')
    c = comprar(cliente, socio, 'pack-8')
    comprar(cliente, otro, 'pack-4')
    cobra.poner_estado(referencia(a), 'aprobado')
    cobra.poner_estado(referencia(b), 'aprobado')
    cobra.poner_estado(referencia(c), 'rechazado')
    assert conciliar(cliente) == conteo(2, 1, 1)
    assert [x['estado'] for x in compras(cliente, socio)] == ['rechazada', 'aprobada']
    assert [x['estado'] for x in compras(cliente, otro)] == ['pendiente', 'aprobada']
    assert (creditos(cliente, socio), creditos(cliente, otro)) == (12, 16)
    assert sorted(x['para'] for x in aprobaciones()) == ['ana@example.com', 'juan@example.com']


def test_la_conciliacion_busca_por_referencia_la_compra_que_quedo_sin_pago(cliente, socio, cobra):
    cobra.crear_y_caer = True
    assert intentar_comprar(cliente, socio, 'pack-4') == 502
    cobra.caido = False
    [pago] = cobra.pagos()
    assert conciliar(cliente) == conteo(0, 0, 1)
    [compra] = compras(cliente, socio)
    assert (compra['estado'], compra['url_pago']) == ('pendiente', pago['url_pago'])
    cobra.poner_estado(pago['referencia'], 'aprobado')
    assert conciliar(cliente) == conteo(1, 0, 0)
    assert creditos(cliente, socio) == 12
    assert len(cobra.pagos()) == 1


def test_la_compra_sin_pago_se_rechaza_a_los_30_minutos(cliente, socio, cobra):
    cobra.caido = True
    assert intentar_comprar(cliente, socio, 'pack-4') == 502
    cobra.caido = False
    reloj.fijar(AHORA + timedelta(minutes=29, seconds=59))
    assert conciliar(cliente) == conteo(0, 0, 1)
    reloj.fijar(AHORA + timedelta(minutes=30))
    cobra.caido = True
    assert conciliar(cliente) == conteo(0, 0, 1)
    cobra.caido = False
    assert conciliar(cliente) == conteo(0, 1, 0)
    assert compras(cliente, socio)[0]['estado'] == 'rechazada'
    assert cobra.pagos() == []
    assert creditos(cliente, socio) == 8


def test_una_falla_de_cobra_no_frena_la_conciliacion(cliente, socio, cobra):
    a, b, c = (comprar(cliente, socio, 'pack-4') for _ in range(3))
    for compra in (a, b, c):
        cobra.poner_estado(referencia(compra), 'aprobado')
    cobra.fallar_con(cobra.pago_de(referencia(b))['id'])
    assert conciliar(cliente) == conteo(2, 0, 1)
    assert [x['estado'] for x in compras(cliente, socio)] == ['aprobada', 'pendiente', 'aprobada']
    assert creditos(cliente, socio) == 16
    cobra.no_fallar_mas()
    assert conciliar(cliente) == conteo(1, 0, 0)
    assert creditos(cliente, socio) == 20


def test_lista_solo_las_compras_del_socio(cliente, socio, otro, cobra):
    primera = comprar(cliente, socio, 'pack-4')
    comprar(cliente, otro, 'pack-8')
    segunda = comprar(cliente, socio, 'pack-8')
    assert compras(cliente, socio) == [segunda, primera]
    assert [c['pack'] for c in compras(cliente, otro)] == ['pack-8']
    assert cliente.get('/compras').status_code == 401
    assert cliente.post('/compras', json={'pack': 'pack-4'}).status_code == 401

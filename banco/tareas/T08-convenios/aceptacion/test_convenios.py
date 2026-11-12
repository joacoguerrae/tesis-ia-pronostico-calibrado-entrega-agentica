import pytest

from apoyo import ADMIN, auth
from beneficios_falso import CLAVE, ServicioBeneficios
from pulso import db

ALTA = 'Ya tenés el plan corporativo'
BAJA = 'Se terminó tu plan corporativo'


@pytest.fixture(autouse=True)
def beneficios(monkeypatch):
    servicio = ServicioBeneficios()
    monkeypatch.setenv('PULSO_BENEFICIOS_URL', servicio.url)
    monkeypatch.setenv('PULSO_BENEFICIOS_CLAVE', CLAVE)
    for variable in ('NO_PROXY', 'no_proxy'):
        monkeypatch.setenv(variable, '127.0.0.1,localhost')
    yield servicio
    servicio.apagar()


def activar(cliente, socio, empresa='acme'):
    return cliente.post('/convenio', json={'empresa': empresa}, headers=auth(socio))


def revalidar(cliente):
    r = cliente.post('/admin/revalidar-convenios', headers=ADMIN)
    assert r.status_code == 200
    return r.json()


def plan_y_creditos(cliente, socio):
    yo = cliente.get('/yo', headers=auth(socio)).json()
    return yo['plan'], yo['creditos']


def correos(asunto):
    return sorted(c['para'] for c in db.correos() if c['asunto'] == asunto)


def test_activar_pide_token_y_empresa(cliente, socio, beneficios):
    beneficios.empleado('acme', 'ana@example.com')
    assert cliente.post('/convenio', json={'empresa': 'acme'}).status_code == 401
    otro_token = {'Authorization': 'Bearer otro'}
    assert cliente.post('/convenio', json={'empresa': 'acme'}, headers=otro_token).status_code == 401
    assert cliente.post('/convenio', json={}, headers=auth(socio)).status_code == 422
    assert cliente.post('/convenio', json={'empresa': ''}, headers=auth(socio)).status_code == 422
    assert plan_y_creditos(cliente, socio) == ('basico', 8)


def test_empleado_activo_pasa_a_corporativo(cliente, socio, beneficios):
    beneficios.empleado('acme', 'ana@example.com')
    r = activar(cliente, socio)
    assert r.status_code == 200
    assert {k: r.json()[k] for k in ('plan', 'empresa', 'creditos')} == {
        'plan': 'corporativo', 'empresa': 'acme', 'creditos': 12}
    assert plan_y_creditos(cliente, socio) == ('corporativo', 12)
    [pedido] = beneficios.pedidos
    assert (pedido.metodo, pedido.empresa, pedido.email) == ('GET', 'acme', 'ana@example.com')


def test_los_creditos_suben_hasta_12_sin_sumarse(cliente, beneficios):
    for creditos, esperados in ((0, 12), (11, 12), (12, 12), (15, 15), (30, 30)):
        socio = db.crear_socio(f'Socio {creditos}', f'socio{creditos}@example.com', creditos=creditos)
        beneficios.empleado('acme', socio['email'])
        r = activar(cliente, socio)
        assert r.status_code == 200
        assert r.json()['creditos'] == esperados, creditos
        assert plan_y_creditos(cliente, socio) == ('corporativo', esperados), creditos


def test_correo_al_activar(cliente, socio, beneficios):
    beneficios.empleado('acme', 'ana@example.com')
    assert activar(cliente, socio).status_code == 200
    [enviado] = db.correos()
    assert enviado['para'] == 'ana@example.com'
    assert enviado['asunto'] == ALTA


def test_activar_dos_veces_da_409_sin_cambios(cliente, socio, beneficios):
    beneficios.empleado('acme', 'ana@example.com')
    beneficios.empleado('globex', 'ana@example.com')
    assert activar(cliente, socio).status_code == 200
    db.sumar_creditos(socio['id'], -3)
    assert activar(cliente, socio).status_code == 409
    assert activar(cliente, socio, 'globex').status_code == 409
    assert plan_y_creditos(cliente, socio) == ('corporativo', 9)
    assert correos(ALTA) == ['ana@example.com']


def test_si_no_es_empleado_activo_da_409_sin_cambios(cliente, socio, otro, beneficios):
    beneficios.empleado('acme', 'ana@example.com', activo=False)
    assert activar(cliente, socio).status_code == 409
    assert activar(cliente, otro).status_code == 409
    assert plan_y_creditos(cliente, socio) == ('basico', 8)
    assert plan_y_creditos(cliente, otro) == ('basico', 8)
    assert db.correos() == []


def test_empresa_inexistente_da_404_sin_cambios(cliente, socio, beneficios):
    beneficios.empleado('acme', 'ana@example.com')
    assert activar(cliente, socio, 'initech').status_code == 404
    assert [(p.empresa, p.email) for p in beneficios.pedidos] == [('initech', 'ana@example.com')]
    assert plan_y_creditos(cliente, socio) == ('basico', 8)
    assert db.correos() == []


def test_si_el_servicio_responde_con_error_da_503_sin_cambios(cliente, socio, beneficios, monkeypatch):
    beneficios.empleado('acme', 'ana@example.com')
    for codigo in (500, 502, 503):
        beneficios.fallar(codigo)
        assert activar(cliente, socio).status_code == 503, codigo
    beneficios.fallar(None)
    monkeypatch.setenv('PULSO_BENEFICIOS_CLAVE', 'clave-vieja')
    assert activar(cliente, socio).status_code == 503
    assert plan_y_creditos(cliente, socio) == ('basico', 8)
    assert db.correos() == []


def test_si_el_servicio_no_esta_da_503_sin_cambios(cliente, socio, beneficios):
    beneficios.empleado('acme', 'ana@example.com')
    beneficios.apagar()
    assert activar(cliente, socio).status_code == 503
    assert plan_y_creditos(cliente, socio) == ('basico', 8)
    assert db.correos() == []


def test_el_email_va_en_minusculas_y_codificado(cliente, beneficios):
    socio = db.crear_socio('Ana Pérez', 'Ana.Perez+Gym@Example.com')
    beneficios.empleado('acme', 'ana.perez+gym@example.com')
    assert activar(cliente, socio).status_code == 200
    assert beneficios.pedidos[-1].email == 'ana.perez+gym@example.com'
    assert revalidar(cliente) == {'siguen': 1, 'bajaron': 0, 'sin_revisar': 0}
    assert beneficios.pedidos[-1].email == 'ana.perez+gym@example.com'


def test_el_servicio_es_la_fuente_de_verdad(cliente, socio, beneficios):
    beneficios.empleado('acme', 'ana@example.com', activo=False)
    assert activar(cliente, socio).status_code == 409
    beneficios.empleado('acme', 'ana@example.com', activo=True)
    assert activar(cliente, socio).status_code == 200
    beneficios.empleado('acme', 'ana@example.com', activo=False)
    assert revalidar(cliente) == {'siguen': 0, 'bajaron': 1, 'sin_revisar': 0}
    assert plan_y_creditos(cliente, socio) == ('basico', 12)
    beneficios.empleado('acme', 'ana@example.com', activo=True)
    assert activar(cliente, socio).status_code == 200
    assert plan_y_creditos(cliente, socio) == ('corporativo', 12)


def test_cada_clave_va_a_su_lugar(cliente, socio, beneficios):
    beneficios.empleado('acme', 'ana@example.com')
    assert activar(cliente, socio).status_code == 200
    for headers in ({}, {'X-Admin-Key': 'otra'}, {'X-Admin-Key': CLAVE}):
        assert cliente.post('/admin/revalidar-convenios', headers=headers).status_code == 401, headers
    assert len(beneficios.pedidos) == 1
    assert revalidar(cliente) == {'siguen': 1, 'bajaron': 0, 'sin_revisar': 0}
    assert [p.clave for p in beneficios.pedidos] == [CLAVE, CLAVE]


def test_revalidar_baja_a_los_que_ya_no_son_empleados(cliente, socio, otro, beneficios):
    lucia = db.crear_socio('Lucía Díaz', 'lucia@example.com', creditos=15)
    pedro = db.crear_socio('Pedro Ríos', 'pedro@example.com')
    marta = db.crear_socio('Marta Sosa', 'marta@example.com')
    for s, empresa in ((socio, 'acme'), (otro, 'acme'), (lucia, 'globex'), (pedro, 'acme')):
        beneficios.empleado(empresa, s['email'])
        assert activar(cliente, s, empresa).status_code == 200
    db.sumar_creditos(socio['id'], -1)
    db.sumar_creditos(pedro['id'], -1)
    beneficios.empleado('acme', 'ana@example.com', activo=False)
    beneficios.olvidar('acme', 'juan@example.com')
    beneficios.cerrar('globex')
    assert revalidar(cliente) == {'siguen': 1, 'bajaron': 3, 'sin_revisar': 0}
    assert plan_y_creditos(cliente, socio) == ('basico', 11)
    assert plan_y_creditos(cliente, otro) == ('basico', 12)
    assert plan_y_creditos(cliente, lucia) == ('basico', 15)
    assert plan_y_creditos(cliente, pedro) == ('corporativo', 11)
    assert plan_y_creditos(cliente, marta) == ('basico', 8)
    assert correos(BAJA) == ['ana@example.com', 'juan@example.com', 'lucia@example.com']


def test_una_falla_no_frena_la_revalidacion(cliente, socio, otro, beneficios):
    lucia = db.crear_socio('Lucía Díaz', 'lucia@example.com')
    for s in (socio, otro, lucia):
        beneficios.empleado('acme', s['email'])
        assert activar(cliente, s).status_code == 200
    beneficios.fallar(500, email='juan@example.com')
    beneficios.empleado('acme', 'lucia@example.com', activo=False)
    assert revalidar(cliente) == {'siguen': 1, 'bajaron': 1, 'sin_revisar': 1}
    assert plan_y_creditos(cliente, otro) == ('corporativo', 12)
    assert plan_y_creditos(cliente, lucia) == ('basico', 12)
    beneficios.apagar()
    assert revalidar(cliente) == {'siguen': 0, 'bajaron': 0, 'sin_revisar': 2}
    assert plan_y_creditos(cliente, socio) == ('corporativo', 12)
    assert plan_y_creditos(cliente, otro) == ('corporativo', 12)
    assert correos(BAJA) == ['lucia@example.com']

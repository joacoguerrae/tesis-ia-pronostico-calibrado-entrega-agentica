from datetime import timedelta

from conftest import ADMIN, AHORA, auth
from pulso import db


def test_lista_solo_clases_futuras_en_orden(cliente):
    db.crear_clase('Spinning', 'Leo', AHORA + timedelta(hours=5))
    db.crear_clase('Yoga', 'Sofía', AHORA + timedelta(hours=2))
    db.crear_clase('Funcional', 'Leo', AHORA - timedelta(hours=1))
    r = cliente.get('/clases')
    assert r.status_code == 200
    assert [c['nombre'] for c in r.json()] == ['Yoga', 'Spinning']
    assert r.json()[0]['lugares_libres'] == 20


def test_clase_inexistente(cliente):
    assert cliente.get('/clases/99').status_code == 404


def test_admin_crea_clase(cliente):
    datos = {'nombre': 'Pilates', 'instructor': 'Marta', 'inicio': '2026-11-12T21:00:00Z', 'duracion_min': 45, 'cupo': 10}
    r = cliente.post('/admin/clases', json=datos, headers=ADMIN)
    assert r.status_code == 201
    assert r.json()['inicio'] == '2026-11-12T21:00:00+00:00'
    assert cliente.post('/admin/clases', json=datos).status_code == 401
    assert cliente.post('/admin/clases', json=datos, headers={'X-Admin-Key': 'otra'}).status_code == 401


def test_admin_rechaza_fecha_sin_zona(cliente):
    datos = {'nombre': 'Pilates', 'instructor': 'Marta', 'inicio': '2026-11-12T21:00:00', 'duracion_min': 45, 'cupo': 10}
    assert cliente.post('/admin/clases', json=datos, headers=ADMIN).status_code == 422


def test_reservar_descuenta_credito_y_manda_correo(cliente, socio):
    clase = db.crear_clase('Yoga', 'Sofía', AHORA + timedelta(hours=6, minutes=30))
    r = cliente.post('/reservas', json={'clase_id': clase['id']}, headers=auth(socio))
    assert r.status_code == 201
    assert r.json()['estado'] == 'confirmada'
    assert cliente.get('/yo', headers=auth(socio)).json()['creditos'] == 7
    assert cliente.get(f"/clases/{clase['id']}").json()['lugares_libres'] == 19
    [enviado] = db.correos()
    assert enviado['para'] == 'ana@example.com'
    assert enviado['asunto'] == 'Reserva confirmada: Yoga el 10/11 a las 18:30'


def test_reservar_sin_token(cliente):
    assert cliente.post('/reservas', json={'clase_id': 1}).status_code == 401


def test_no_reserva_dos_veces(cliente, socio):
    clase = db.crear_clase('Yoga', 'Sofía', AHORA + timedelta(hours=2))
    assert cliente.post('/reservas', json={'clase_id': clase['id']}, headers=auth(socio)).status_code == 201
    assert cliente.post('/reservas', json={'clase_id': clase['id']}, headers=auth(socio)).status_code == 409


def test_no_reserva_clase_llena(cliente, socio):
    clase = db.crear_clase('Yoga', 'Sofía', AHORA + timedelta(hours=2), cupo=1)
    otro = db.crear_socio('Juan Gómez', 'juan@example.com')
    db.crear_reserva(otro['id'], clase['id'], AHORA)
    assert cliente.post('/reservas', json={'clase_id': clase['id']}, headers=auth(socio)).status_code == 409


def test_no_reserva_clase_empezada(cliente, socio):
    clase = db.crear_clase('Yoga', 'Sofía', AHORA - timedelta(minutes=5))
    assert cliente.post('/reservas', json={'clase_id': clase['id']}, headers=auth(socio)).status_code == 409


def test_no_reserva_sin_creditos(cliente):
    socio = db.crear_socio('Ana Pérez', 'ana@example.com', creditos=0)
    clase = db.crear_clase('Yoga', 'Sofía', AHORA + timedelta(hours=2))
    assert cliente.post('/reservas', json={'clase_id': clase['id']}, headers=auth(socio)).status_code == 409


def test_mis_reservas_en_orden_de_clase(cliente, socio):
    tarde = db.crear_clase('Spinning', 'Leo', AHORA + timedelta(days=2))
    temprano = db.crear_clase('Yoga', 'Sofía', AHORA + timedelta(days=1))
    for clase in (tarde, temprano):
        cliente.post('/reservas', json={'clase_id': clase['id']}, headers=auth(socio))
    r = cliente.get('/reservas', headers=auth(socio))
    assert [x['clase_id'] for x in r.json()] == [temprano['id'], tarde['id']]

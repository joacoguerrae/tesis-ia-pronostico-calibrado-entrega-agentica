from datetime import timedelta

from apoyo import AHORA, auth
from pulso import db, reloj


def reservar(cliente, socio, clase):
    r = cliente.post('/reservas', json={'clase_id': clase['id']}, headers=auth(socio))
    assert r.status_code == 201
    return r.json()


def cancelar(cliente, socio, reserva_id):
    return cliente.post(f'/reservas/{reserva_id}/cancelar', headers=auth(socio))


def creditos(cliente, socio):
    return cliente.get('/yo', headers=auth(socio)).json()['creditos']


def test_con_anticipacion_devuelve_el_credito(cliente, socio):
    clase = db.crear_clase('Yoga', 'Sofía', AHORA + timedelta(hours=5))
    reserva = reservar(cliente, socio, clase)
    r = cancelar(cliente, socio, reserva['id'])
    assert r.status_code == 200
    assert r.json()['estado'] == 'cancelada'
    assert r.json()['credito_devuelto'] is True
    assert creditos(cliente, socio) == 8


def test_respuesta_trae_los_campos_de_la_reserva(cliente, socio):
    clase = db.crear_clase('Yoga', 'Sofía', AHORA + timedelta(hours=5))
    reserva = reservar(cliente, socio, clase)
    cuerpo = cancelar(cliente, socio, reserva['id']).json()
    assert cuerpo['id'] == reserva['id']
    assert cuerpo['clase_id'] == clase['id']
    assert cuerpo['creada'] == reserva['creada']


def test_con_dos_horas_justas_devuelve_el_credito(cliente, socio):
    clase = db.crear_clase('Yoga', 'Sofía', AHORA + timedelta(hours=2))
    reserva = reservar(cliente, socio, clase)
    assert cancelar(cliente, socio, reserva['id']).json()['credito_devuelto'] is True
    assert creditos(cliente, socio) == 8


def test_con_menos_de_dos_horas_no_devuelve_el_credito(cliente, socio):
    clase = db.crear_clase('Yoga', 'Sofía', AHORA + timedelta(hours=1, minutes=59))
    reserva = reservar(cliente, socio, clase)
    r = cancelar(cliente, socio, reserva['id'])
    assert r.status_code == 200
    assert r.json()['estado'] == 'cancelada'
    assert r.json()['credito_devuelto'] is False
    assert creditos(cliente, socio) == 7


def test_no_cancela_una_clase_que_ya_empezo(cliente, socio):
    clase = db.crear_clase('Yoga', 'Sofía', AHORA + timedelta(hours=1))
    reserva = reservar(cliente, socio, clase)
    reloj.fijar(AHORA + timedelta(hours=1))
    assert cancelar(cliente, socio, reserva['id']).status_code == 409
    reloj.fijar(AHORA + timedelta(hours=1, minutes=10))
    assert cancelar(cliente, socio, reserva['id']).status_code == 409
    assert db.reserva(reserva['id'])['estado'] == 'confirmada'


def test_no_cancela_dos_veces(cliente, socio):
    clase = db.crear_clase('Yoga', 'Sofía', AHORA + timedelta(hours=5))
    reserva = reservar(cliente, socio, clase)
    assert cancelar(cliente, socio, reserva['id']).status_code == 200
    assert cancelar(cliente, socio, reserva['id']).status_code == 409
    assert creditos(cliente, socio) == 8


def test_reserva_de_otro_o_inexistente(cliente, socio, otro):
    clase = db.crear_clase('Yoga', 'Sofía', AHORA + timedelta(hours=5))
    reserva = reservar(cliente, otro, clase)
    assert cancelar(cliente, socio, reserva['id']).status_code == 404
    assert cancelar(cliente, socio, 999).status_code == 404
    assert db.reserva(reserva['id'])['estado'] == 'confirmada'


def test_sin_token(cliente, socio):
    clase = db.crear_clase('Yoga', 'Sofía', AHORA + timedelta(hours=5))
    reserva = reservar(cliente, socio, clase)
    assert cliente.post(f"/reservas/{reserva['id']}/cancelar").status_code == 401


def test_libera_el_lugar_para_otro_socio(cliente, socio, otro):
    clase = db.crear_clase('Yoga', 'Sofía', AHORA + timedelta(hours=5), cupo=1)
    reserva = reservar(cliente, socio, clase)
    assert cliente.get(f"/clases/{clase['id']}").json()['lugares_libres'] == 0
    cancelar(cliente, socio, reserva['id'])
    assert cliente.get(f"/clases/{clase['id']}").json()['lugares_libres'] == 1
    assert cliente.post('/reservas', json={'clase_id': clase['id']}, headers=auth(otro)).status_code == 201


def test_puede_volver_a_reservar_la_misma_clase(cliente, socio):
    clase = db.crear_clase('Yoga', 'Sofía', AHORA + timedelta(hours=5))
    reserva = reservar(cliente, socio, clase)
    cancelar(cliente, socio, reserva['id'])
    assert cliente.post('/reservas', json={'clase_id': clase['id']}, headers=auth(socio)).status_code == 201


def test_sigue_apareciendo_en_mis_reservas(cliente, socio):
    clase = db.crear_clase('Yoga', 'Sofía', AHORA + timedelta(hours=5))
    reserva = reservar(cliente, socio, clase)
    cancelar(cliente, socio, reserva['id'])
    mias = cliente.get('/reservas', headers=auth(socio)).json()
    assert [(x['id'], x['estado']) for x in mias] == [(reserva['id'], 'cancelada')]

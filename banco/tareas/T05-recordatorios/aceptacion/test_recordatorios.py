from datetime import timedelta

from apoyo import ADMIN, AHORA
from pulso import db, reloj


def recordar(cliente):
    r = cliente.post('/admin/recordatorios', headers=ADMIN)
    assert r.status_code == 200
    return r.json()['enviados']


def recordatorios():
    return [c for c in db.correos() if c['asunto'].startswith('Recordatorio:')]


def reserva_en(socio, horas, minutos=0, nombre='Yoga', instructor='Sofía'):
    clase = db.crear_clase(nombre, instructor, AHORA + timedelta(hours=horas, minutes=minutos))
    return db.crear_reserva(socio['id'], clase['id'], AHORA)


def test_pide_clave_de_admin(cliente):
    assert cliente.post('/admin/recordatorios').status_code == 401
    assert cliente.post('/admin/recordatorios', headers={'X-Admin-Key': 'otra'}).status_code == 401


def test_sin_reservas_no_manda_nada(cliente):
    assert recordar(cliente) == 0
    assert recordatorios() == []


def test_manda_a_las_clases_de_las_proximas_24_horas(cliente, socio):
    reserva_en(socio, 23)
    reserva_en(socio, 0, 1)
    reserva_en(socio, 25)
    assert recordar(cliente) == 2
    assert len(recordatorios()) == 2


def test_las_24_horas_justas_se_incluyen(cliente, socio):
    reserva_en(socio, 24)
    reserva_en(socio, 24, 1)
    assert recordar(cliente) == 1


def test_no_manda_a_clases_que_ya_empezaron(cliente, socio):
    reserva_en(socio, 0)
    reserva_en(socio, -1)
    assert recordar(cliente) == 0


def test_cada_reserva_recibe_un_solo_recordatorio(cliente, socio):
    reserva_en(socio, 20)
    assert recordar(cliente) == 1
    assert recordar(cliente) == 0
    reloj.fijar(AHORA + timedelta(minutes=15))
    assert recordar(cliente) == 0
    assert len(recordatorios()) == 1


def test_las_que_entran_en_la_ventana_mas_tarde(cliente, socio):
    reserva_en(socio, 20)
    reserva_en(socio, 26)
    assert recordar(cliente) == 1
    reloj.fijar(AHORA + timedelta(hours=2))
    assert recordar(cliente) == 1
    assert len(recordatorios()) == 2


def test_reserva_hecha_con_menos_de_24_horas(cliente, socio):
    clase = db.crear_clase('Yoga', 'Sofía', AHORA + timedelta(hours=3))
    r = cliente.post('/reservas', json={'clase_id': clase['id']}, headers={'Authorization': f"Bearer {socio['token']}"})
    assert r.status_code == 201
    assert recordar(cliente) == 1
    assert recordar(cliente) == 0


def test_no_manda_a_reservas_canceladas(cliente, socio):
    reserva = reserva_en(socio, 5)
    with db.conexion() as con:
        con.execute("UPDATE reservas SET estado = 'cancelada' WHERE id = ?", (reserva['id'],))
    assert recordar(cliente) == 0


def test_cada_socio_recibe_el_suyo(cliente, socio, otro):
    clase = db.crear_clase('Spinning', 'Leo', AHORA + timedelta(hours=6))
    db.crear_reserva(socio['id'], clase['id'], AHORA)
    db.crear_reserva(otro['id'], clase['id'], AHORA)
    assert recordar(cliente) == 2
    assert sorted(c['para'] for c in recordatorios()) == ['ana@example.com', 'juan@example.com']


def test_asunto_y_cuerpo(cliente, socio):
    reserva_en(socio, 6, 30, nombre='Yoga', instructor='Sofía')
    reserva_en(socio, 21, 15, nombre='Spinning', instructor='Leo')
    recordar(cliente)
    enviados = sorted(recordatorios(), key=lambda c: c['asunto'])
    assert [c['asunto'] for c in enviados] == ['Recordatorio: Spinning el 11/11 a las 09:15',
                                               'Recordatorio: Yoga el 10/11 a las 18:30']
    assert 'Leo' in enviados[0]['cuerpo']
    assert 'Sofía' in enviados[1]['cuerpo']

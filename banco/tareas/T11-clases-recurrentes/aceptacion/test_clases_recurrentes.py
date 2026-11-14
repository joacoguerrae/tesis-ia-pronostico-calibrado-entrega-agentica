import sqlite3
from datetime import timedelta, timezone
from itertools import count

import pytest
from fastapi.testclient import TestClient

from apoyo import ADMIN, AHORA, auth, local
from pulso import db, reloj
from pulso.main import crear_app

# AHORA es el martes 10/11/2026 a las 12:00 de Montevideo.
YOGA = {'nombre': 'Yoga', 'instructor': 'Sofía', 'dia': 'martes', 'hora': '19:00', 'duracion_min': 60, 'cupo': 15,
        'desde': '2026-11-10', 'hasta': '2026-12-31'}
MARTES = ['2026-11-10', '2026-11-17', '2026-11-24', '2026-12-01', '2026-12-08', '2026-12-15', '2026-12-22',
          '2026-12-29']
_numero = count(1)


def utc(momento):
    return momento.astimezone(timezone.utc).isoformat()


def a_las(fecha, hora):
    """'2026-11-17', '19:00' de Montevideo -> inicio en UTC como lo devuelve la API."""
    anio, mes, dia = map(int, fecha.split('-'))
    h, m = map(int, hora.split(':'))
    return utc(local(anio, mes, dia, h, m))


def crear_serie(cliente, **cambios):
    r = cliente.post('/admin/series', json=dict(YOGA, **cambios), headers=ADMIN)
    assert r.status_code == 201, r.text
    return r.json()


def ver_serie(cliente, serie):
    r = cliente.get(f"/admin/series/{serie['id']}", headers=ADMIN)
    assert r.status_code == 200
    return r.json()


def cambiar(cliente, serie, **datos):
    return cliente.patch(f"/admin/series/{serie['id']}", json=datos, headers=ADMIN)


def cancelar(cliente, clase_id):
    return cliente.post(f'/admin/clases/{clase_id}/cancelar', headers=ADMIN)


def nuevo_socio(creditos=8):
    n = next(_numero)
    return db.crear_socio(f'Socio {n}', f'socio{n}@example.com', creditos=creditos)


def reservar(cliente, socio, clase_id):
    return cliente.post('/reservas', json={'clase_id': clase_id}, headers=auth(socio))


def asuntos(socio):
    return [c['asunto'] for c in db.correos() if c['para'] == socio['email']]


def creditos(cliente, socio):
    return cliente.get('/yo', headers=auth(socio)).json()['creditos']


# Crear una serie

def test_crea_una_clase_por_semana_a_la_hora_de_montevideo(cliente):
    serie = crear_serie(cliente)
    assert {k: serie[k] for k in YOGA} == YOGA
    assert [c['inicio'] for c in serie['clases']] == [a_las(f, '19:00') for f in MARTES]
    primera = serie['clases'][0]
    assert primera['inicio'] == '2026-11-10T22:00:00+00:00'
    assert {k: primera[k] for k in ('nombre', 'instructor', 'duracion_min', 'cupo', 'lugares_libres', 'serie_id',
                                    'estado')} == {'nombre': 'Yoga', 'instructor': 'Sofía', 'duracion_min': 60,
                                                   'cupo': 15, 'lugares_libres': 15, 'serie_id': serie['id'],
                                                   'estado': 'programada'}


def test_las_clases_de_la_serie_son_clases_comunes(cliente):
    serie = crear_serie(cliente)
    ids = [c['id'] for c in serie['clases']]
    assert [c['id'] for c in cliente.get('/clases').json()] == ids
    assert cliente.get(f'/clases/{ids[2]}').json()['serie_id'] == serie['id']
    assert reservar(cliente, nuevo_socio(), ids[2]).status_code == 201


def test_una_hora_de_la_noche_cae_al_dia_siguiente_en_utc(cliente):
    serie = crear_serie(cliente, dia='lunes', hora='22:30', desde='2026-11-16', hasta='2026-11-30')
    assert [c['inicio'] for c in serie['clases']] == [
        '2026-11-17T01:30:00+00:00', '2026-11-24T01:30:00+00:00', '2026-12-01T01:30:00+00:00']


def test_acepta_los_dias_con_tilde(cliente):
    sabados = crear_serie(cliente, dia='sábado', hora='10:00', desde='2026-11-14', hasta='2026-11-28')
    assert [c['inicio'] for c in sabados['clases']] == [a_las(f, '10:00') for f in
                                                         ['2026-11-14', '2026-11-21', '2026-11-28']]
    miercoles = crear_serie(cliente, dia='miércoles', desde='2026-11-10', hasta='2026-11-20')
    assert [c['inicio'] for c in miercoles['clases']] == [a_las(f, '19:00') for f in ['2026-11-11', '2026-11-18']]


def test_desde_y_hasta_estan_incluidos(cliente):
    serie = crear_serie(cliente, desde='2026-11-17', hasta='2026-11-24')
    assert [c['inicio'] for c in serie['clases']] == [a_las('2026-11-17', '19:00'), a_las('2026-11-24', '19:00')]


def test_no_crea_clases_los_dias_que_cierra_el_gimnasio(cliente):
    viernes = crear_serie(cliente, dia='viernes', desde='2026-12-18', hasta='2027-01-08')
    assert [c['inicio'] for c in viernes['clases']] == [a_las('2026-12-18', '19:00'), a_las('2027-01-08', '19:00')]
    lunes = crear_serie(cliente, dia='lunes', desde='2027-02-01', hasta='2027-02-15')
    assert [c['inicio'] for c in lunes['clases']] == [a_las('2027-02-01', '19:00'), a_las('2027-02-15', '19:00')]


def test_no_crea_clases_que_ya_empezaron(cliente):
    manana = crear_serie(cliente, hora='09:00', desde='2026-11-10', hasta='2026-11-24')
    assert [c['inicio'] for c in manana['clases']] == [a_las('2026-11-17', '09:00'), a_las('2026-11-24', '09:00')]
    mediodia = crear_serie(cliente, hora='12:00', desde='2026-11-10', hasta='2026-11-17')
    assert [c['inicio'] for c in mediodia['clases']] == [a_las('2026-11-17', '12:00')]


def test_una_serie_sin_clases_es_valida(cliente):
    serie = crear_serie(cliente, dia='viernes', desde='2026-12-25', hasta='2026-12-25')
    assert serie['clases'] == []


@pytest.mark.parametrize('cambio', [
    {'dia': 'miercoles'}, {'dia': 'Martes'}, {'dia': 'feriado'}, {'hora': '24:00'}, {'hora': '19:60'},
    {'hora': 'siete'}, {'nombre': ''}, {'instructor': ''}, {'cupo': 0}, {'duracion_min': 0},
    {'desde': '2026-11-20', 'hasta': '2026-11-19'}, {'desde': '2026-11-10', 'hasta': '2027-11-12'},
])
def test_rechaza_datos_invalidos_sin_crear_nada(cliente, cambio):
    r = cliente.post('/admin/series', json=dict(YOGA, **cambio), headers=ADMIN)
    assert r.status_code == 422
    assert cliente.get('/clases').json() == []


def test_hasta_366_dias_se_acepta(cliente):
    serie = crear_serie(cliente, desde='2026-11-10', hasta='2027-11-11')
    assert serie['clases'][-1]['inicio'] == a_las('2027-11-09', '19:00')


def test_pide_la_clave_de_administracion(cliente):
    assert cliente.post('/admin/series', json=YOGA).status_code == 401
    assert cliente.get('/admin/series/1').status_code == 401
    assert cliente.patch('/admin/series/1', json={'desde_clase_id': 1, 'cupo': 3}).status_code == 401
    assert cliente.post('/admin/clases/1/cancelar').status_code == 401


def test_ver_una_serie(cliente):
    serie = crear_serie(cliente)
    assert ver_serie(cliente, serie) == serie
    assert cliente.get('/admin/series/999', headers=ADMIN).status_code == 404


# Clases que ya existían

def test_las_clases_sueltas_no_tienen_serie(cliente):
    vieja = db.crear_clase('Pilates', 'Marta', AHORA + timedelta(days=1))
    datos = {'nombre': 'Funcional', 'instructor': 'Leo', 'inicio': '2026-11-12T22:00:00Z', 'duracion_min': 45, 'cupo': 10}
    nueva = cliente.post('/admin/clases', json=datos, headers=ADMIN).json()
    for clase_id in (vieja['id'], nueva['id']):
        clase = cliente.get(f'/clases/{clase_id}').json()
        assert (clase['serie_id'], clase['estado']) == (None, 'programada')
    assert nueva['serie_id'] is None and nueva['estado'] == 'programada'


ESQUEMA_DE_HOY = """
CREATE TABLE socios (id INTEGER PRIMARY KEY, nombre TEXT NOT NULL, email TEXT NOT NULL UNIQUE, plan TEXT NOT NULL,
                     creditos INTEGER NOT NULL, token TEXT NOT NULL UNIQUE);
CREATE TABLE clases (id INTEGER PRIMARY KEY, nombre TEXT NOT NULL, instructor TEXT NOT NULL, inicio TEXT NOT NULL,
                     duracion_min INTEGER NOT NULL, cupo INTEGER NOT NULL);
CREATE TABLE reservas (id INTEGER PRIMARY KEY, socio_id INTEGER NOT NULL REFERENCES socios(id),
                       clase_id INTEGER NOT NULL REFERENCES clases(id), estado TEXT NOT NULL, creada TEXT NOT NULL);
CREATE TABLE correos (id INTEGER PRIMARY KEY, para TEXT NOT NULL, asunto TEXT NOT NULL, cuerpo TEXT NOT NULL,
                      creado TEXT NOT NULL);
INSERT INTO clases (nombre, instructor, inicio, duracion_min, cupo) VALUES ('Pilates', 'Marta', '2026-11-12T22:00:00+00:00', 45, 10);
"""


def test_la_base_de_produccion_sigue_andando(tmp_path, monkeypatch):
    """La base de producción ya tiene clases, cargadas con la versión de hoy de la app."""
    monkeypatch.setenv('PULSO_DB', str(tmp_path / 'pulso.db'))
    monkeypatch.setenv('PULSO_ADMIN_KEY', ADMIN['X-Admin-Key'])
    con = sqlite3.connect(tmp_path / 'pulso.db')
    con.executescript(ESQUEMA_DE_HOY)
    con.close()
    reloj.fijar(AHORA)
    try:
        cliente = TestClient(crear_app())
        [clase] = cliente.get('/clases').json()
        assert (clase['nombre'], clase['serie_id'], clase['estado']) == ('Pilates', None, 'programada')
        serie = crear_serie(cliente)
        assert len(cliente.get('/clases').json()) == 1 + len(serie['clases'])
        assert cancelar(cliente, clase['id']).status_code == 200
    finally:
        reloj.fijar(None)


# Cambiar una serie de una clase en adelante

def test_cambiar_la_hora_desde_una_clase_en_adelante(cliente):
    serie = crear_serie(cliente)
    ids = [c['id'] for c in serie['clases']]
    r = cambiar(cliente, serie, desde_clase_id=ids[2], hora='20:00')
    assert r.status_code == 200
    despues = r.json()
    assert despues['hora'] == '20:00'
    assert [c['id'] for c in despues['clases']] == ids
    assert [c['inicio'] for c in despues['clases']] == (
        [a_las(f, '19:00') for f in MARTES[:2]] + [a_las(f, '20:00') for f in MARTES[2:]])
    assert ver_serie(cliente, serie) == despues


def test_el_cambio_de_hora_conserva_las_reservas_y_avisa_solo_a_los_afectados(cliente):
    serie = crear_serie(cliente)
    ids = [c['id'] for c in serie['clases']]
    antes, despues = nuevo_socio(), nuevo_socio()
    reservar(cliente, antes, ids[0])
    reservar(cliente, despues, ids[3])
    cambiar(cliente, serie, desde_clase_id=ids[2], hora='20:30')
    assert [r['clase_id'] for r in cliente.get('/reservas', headers=auth(despues)).json()] == [ids[3]]
    assert asuntos(despues)[-1] == 'Cambio de horario: Yoga el 01/12 a las 20:30'
    assert [a for a in asuntos(antes) if a.startswith('Cambio de horario')] == []


def test_cambiar_el_instructor_y_el_cupo_no_avisa(cliente):
    serie = crear_serie(cliente)
    ids = [c['id'] for c in serie['clases']]
    socio = nuevo_socio()
    reservar(cliente, socio, ids[4])
    r = cambiar(cliente, serie, desde_clase_id=ids[4], instructor='Leo', cupo=12)
    assert r.status_code == 200
    clases = r.json()['clases']
    assert [(c['instructor'], c['cupo']) for c in clases] == [('Sofía', 15)] * 4 + [('Leo', 12)] * 4
    assert clases[4]['lugares_libres'] == 11
    assert (r.json()['instructor'], r.json()['cupo']) == ('Leo', 12)
    assert len(asuntos(socio)) == 1


def test_las_clases_canceladas_no_cambian(cliente):
    serie = crear_serie(cliente)
    ids = [c['id'] for c in serie['clases']]
    cancelar(cliente, ids[4])
    clases = cambiar(cliente, serie, desde_clase_id=ids[2], hora='20:00', instructor='Leo').json()['clases']
    assert (clases[4]['estado'], clases[4]['inicio'], clases[4]['instructor']) == (
        'cancelada', a_las(MARTES[4], '19:00'), 'Sofía')
    assert clases[5]['inicio'] == a_las(MARTES[5], '20:00')


def test_un_cupo_menor_que_las_reservas_rechaza_el_cambio_entero(cliente):
    serie = crear_serie(cliente)
    ids = [c['id'] for c in serie['clases']]
    for _ in range(3):
        reservar(cliente, nuevo_socio(), ids[5])
    r = cambiar(cliente, serie, desde_clase_id=ids[2], cupo=2, instructor='Leo')
    assert r.status_code == 409
    assert ver_serie(cliente, serie) == dict(serie, clases=[dict(c, lugares_libres=12 if c['id'] == ids[5] else 15)
                                                            for c in serie['clases']])


def test_no_se_cambia_desde_una_clase_que_ya_empezo(cliente):
    serie = crear_serie(cliente)
    ids = [c['id'] for c in serie['clases']]
    reloj.fijar(local(2026, 11, 10, 19, 30))
    assert cambiar(cliente, serie, desde_clase_id=ids[0], instructor='Leo').status_code == 409
    assert cambiar(cliente, serie, desde_clase_id=ids[1], instructor='Leo').status_code == 200


def test_no_se_mueve_una_clase_a_una_hora_que_ya_paso(cliente):
    serie = crear_serie(cliente)
    ids = [c['id'] for c in serie['clases']]
    assert cambiar(cliente, serie, desde_clase_id=ids[0], hora='11:00').status_code == 409
    assert ver_serie(cliente, serie) == serie
    assert cambiar(cliente, serie, desde_clase_id=ids[1], hora='11:00').status_code == 200


def test_errores_al_cambiar_una_serie(cliente):
    serie = crear_serie(cliente)
    otra = crear_serie(cliente, dia='jueves')
    ids = [c['id'] for c in serie['clases']]
    assert cambiar(cliente, serie, desde_clase_id=otra['clases'][0]['id'], hora='20:00').status_code == 404
    assert cliente.patch('/admin/series/999', json={'desde_clase_id': ids[0], 'hora': '20:00'},
                         headers=ADMIN).status_code == 404
    assert cambiar(cliente, serie, desde_clase_id=ids[0]).status_code == 422
    assert cambiar(cliente, serie, desde_clase_id=ids[0], cupo=0).status_code == 422
    assert cambiar(cliente, serie, desde_clase_id=ids[0], hora='25:00').status_code == 422
    assert ver_serie(cliente, serie) == serie


# Cancelar una clase

def test_cancelar_devuelve_creditos_y_avisa(cliente):
    serie = crear_serie(cliente)
    clase_id = serie['clases'][1]['id']
    socios = [nuevo_socio(), nuevo_socio()]
    for s in socios:
        reservar(cliente, s, clase_id)
    r = cancelar(cliente, clase_id)
    assert r.status_code == 200
    assert (r.json()['id'], r.json()['estado']) == (clase_id, 'cancelada')
    for s in socios:
        assert creditos(cliente, s) == 8
        assert [x['estado'] for x in cliente.get('/reservas', headers=auth(s)).json()] == ['cancelada']
        assert asuntos(s)[-1] == 'Clase cancelada: Yoga el 17/11 a las 19:00'


def test_una_clase_cancelada_no_se_lista_ni_se_reserva(cliente):
    serie = crear_serie(cliente)
    clase_id = serie['clases'][1]['id']
    cancelar(cliente, clase_id)
    assert clase_id not in [c['id'] for c in cliente.get('/clases').json()]
    assert cliente.get(f'/clases/{clase_id}').json()['estado'] == 'cancelada'
    r = reservar(cliente, nuevo_socio(), clase_id)
    assert (r.status_code, r.json()['detail']) == (409, 'La clase está cancelada')
    assert [c['estado'] for c in ver_serie(cliente, serie)['clases']].count('cancelada') == 1


def test_cancelar_una_clase_suelta(cliente):
    clase = db.crear_clase('Pilates', 'Marta', AHORA + timedelta(days=1))
    socio = nuevo_socio()
    reservar(cliente, socio, clase['id'])
    r = cancelar(cliente, clase['id'])
    assert (r.status_code, r.json()['estado'], r.json()['serie_id']) == (200, 'cancelada', None)
    assert creditos(cliente, socio) == 8


def test_errores_al_cancelar(cliente):
    serie = crear_serie(cliente)
    ids = [c['id'] for c in serie['clases']]
    socio = nuevo_socio()
    reservar(cliente, socio, ids[1])
    assert cancelar(cliente, ids[1]).status_code == 200
    assert cancelar(cliente, ids[1]).status_code == 409
    assert creditos(cliente, socio) == 8
    assert cancelar(cliente, 999).status_code == 404
    reloj.fijar(local(2026, 11, 10, 19, 0))
    assert cancelar(cliente, ids[0]).status_code == 409

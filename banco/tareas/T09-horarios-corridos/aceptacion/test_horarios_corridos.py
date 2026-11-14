import sqlite3
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from apoyo import ADMIN, AHORA, auth
from pulso import db, reloj
from pulso.main import crear_app

# Jueves 12/11, en hora de Montevideo y en UTC.
FUNCIONAL = '2026-11-12T22:00:00+00:00'   # 19:00
YOGA = '2026-11-12T23:00:00+00:00'        # 20:00
SPINNING = '2026-11-13T00:00:00+00:00'    # 21:00


def utc(texto):
    return datetime.fromisoformat(texto).astimezone(timezone.utc)


def cargar(cliente, nombre, inicio):
    datos = {'nombre': nombre, 'instructor': 'Leo', 'inicio': inicio, 'duracion_min': 60, 'cupo': 10}
    r = cliente.post('/admin/clases', json=datos, headers=ADMIN)
    assert r.status_code == 201
    return r.json()


def guardado(clase_id):
    """Lo que quedó en la tabla, como lo leen los otros procesos."""
    con = sqlite3.connect(db.ruta())
    try:
        return con.execute('SELECT inicio FROM clases WHERE id = ?', (clase_id,)).fetchone()[0]
    finally:
        con.close()


def nombres(cliente):
    return [c['nombre'] for c in cliente.get('/clases').json()]


@pytest.fixture
def base_vieja(tmp_path, monkeypatch):
    """Una base de producción con clases cargadas antes de la versión nueva. Arranca la app sobre ella."""
    monkeypatch.setenv('PULSO_DB', str(tmp_path / 'pulso.db'))
    monkeypatch.setenv('PULSO_ADMIN_KEY', ADMIN['X-Admin-Key'])
    reloj.fijar(AHORA)

    def arrancar(filas, reservadas=()):
        """Carga las clases tal como están en la base y, antes de arrancar, le reserva a Ana las de `reservadas`
        (posiciones en `filas`)."""
        db.inicializar()
        socio = db.crear_socio('Ana Pérez', 'ana@example.com')
        con = sqlite3.connect(db.ruta())
        ids = []
        for nombre, inicio in filas:
            cur = con.execute('INSERT INTO clases (nombre, instructor, inicio, duracion_min, cupo) VALUES (?, ?, ?, ?, ?)',
                              (nombre, 'Leo', inicio, 60, 10))
            ids.append(cur.lastrowid)
        for i in reservadas:
            con.execute("INSERT INTO reservas (socio_id, clase_id, estado, creada) VALUES (?, ?, 'confirmada', ?)",
                        (socio['id'], ids[i], '2026-11-05T15:00:00+00:00'))
        con.commit()
        con.close()
        return TestClient(crear_app()), ids, socio

    yield arrancar
    reloj.fijar(None)


VIEJAS = [('Pilates', '2026-11-12T21:30:00'),               # sin zona, en UTC: 18:30 en Montevideo
          ('Funcional', '2026-11-12T19:00:00-03:00'),       # panel nuevo
          ('Yoga', YOGA),                                   # bien guardada
          ('Spinning', '2026-11-12T21:00:00-03:00')]        # panel nuevo


def test_la_api_devuelve_en_utc_una_clase_cargada_con_hora_de_montevideo(cliente):
    clase = cargar(cliente, 'Funcional', '2026-11-12T19:00:00-03:00')
    assert clase['inicio'] == FUNCIONAL
    assert cliente.get(f"/clases/{clase['id']}").json()['inicio'] == FUNCIONAL


def test_se_guarda_en_utc_cualquiera_sea_el_desfase(cliente):
    for nombre, inicio in [('Funcional', '2026-11-12T19:00:00-03:00'), ('Yoga', '2026-11-13T01:00:00+02:00'),
                           ('Spinning', '2026-11-13T00:00:00Z')]:
        clase = cargar(cliente, nombre, inicio)
        assert guardado(clase['id']) == clase['inicio'] == utc(inicio).isoformat()


def test_la_clase_se_puede_reservar_hasta_su_hora_real(cliente, socio):
    clase = cargar(cliente, 'Funcional', '2026-11-12T19:00:00-03:00')
    reloj.fijar(utc('2026-11-12T18:30:00-03:00'))
    assert 'Funcional' in nombres(cliente)
    r = cliente.post('/reservas', json={'clase_id': clase['id']}, headers=auth(socio))
    assert r.status_code == 201


def test_al_llegar_la_hora_real_ya_no_se_puede_reservar(cliente, socio):
    clase = cargar(cliente, 'Funcional', '2026-11-12T19:00:00-03:00')
    reloj.fijar(utc(FUNCIONAL))
    assert 'Funcional' not in nombres(cliente)
    assert cliente.post('/reservas', json={'clase_id': clase['id']}, headers=auth(socio)).status_code == 409


def test_el_correo_dice_la_hora_real(cliente, socio):
    clase = cargar(cliente, 'Funcional', '2026-11-12T19:00:00-03:00')
    cliente.post('/reservas', json={'clase_id': clase['id']}, headers=auth(socio))
    assert db.correos()[-1]['asunto'] == 'Reserva confirmada: Funcional el 12/11 a las 19:00'


def test_clases_cargadas_de_distintas_formas_salen_en_orden(cliente):
    cargar(cliente, 'Spinning', '2026-11-12T21:00:00-03:00')
    cargar(cliente, 'Yoga', '2026-11-12T23:00:00Z')
    cargar(cliente, 'Funcional', '2026-11-12T19:00:00-03:00')
    assert nombres(cliente) == ['Funcional', 'Yoga', 'Spinning']


def test_mis_reservas_salen_en_el_orden_real(cliente, socio):
    ids = {}
    for nombre, inicio in [('Spinning', '2026-11-12T21:00:00-03:00'), ('Yoga', '2026-11-12T23:00:00Z'),
                           ('Funcional', '2026-11-12T19:00:00-03:00')]:
        ids[nombre] = cargar(cliente, nombre, inicio)['id']
        cliente.post('/reservas', json={'clase_id': ids[nombre]}, headers=auth(socio))
    r = cliente.get('/reservas', headers=auth(socio))
    assert [x['clase_id'] for x in r.json()] == [ids['Funcional'], ids['Yoga'], ids['Spinning']]


def test_las_clases_ya_cargadas_quedan_guardadas_en_utc_sin_cambiar_su_horario(base_vieja):
    cliente, ids, socio = base_vieja(VIEJAS)
    assert [guardado(i) for i in ids] == ['2026-11-12T21:30:00+00:00', FUNCIONAL, YOGA, SPINNING]


def test_las_clases_ya_cargadas_conservan_su_id(base_vieja):
    cliente, ids, socio = base_vieja(VIEJAS)
    for (nombre, _), clase_id in zip(VIEJAS, ids):
        assert cliente.get(f'/clases/{clase_id}').json()['nombre'] == nombre


def test_las_clases_ya_cargadas_se_ven_y_se_reservan_con_su_hora_real(base_vieja):
    cliente, ids, socio = base_vieja(VIEJAS)
    reloj.fijar(utc('2026-11-12T18:45:00-03:00'))  # Pilates ya empezó; las demás no
    assert nombres(cliente) == ['Funcional', 'Yoga', 'Spinning']
    assert cliente.get(f'/clases/{ids[1]}').json()['inicio'] == FUNCIONAL
    assert cliente.post('/reservas', json={'clase_id': ids[1]}, headers=auth(socio)).status_code == 201
    assert db.correos()[-1]['asunto'] == 'Reserva confirmada: Funcional el 12/11 a las 19:00'
    assert cliente.post('/reservas', json={'clase_id': ids[0]}, headers=auth(socio)).status_code == 409


def test_arrancar_otra_vez_no_mueve_ninguna_clase(base_vieja):
    cliente, ids, socio = base_vieja(VIEJAS)
    crear_app()
    crear_app()
    assert [guardado(i) for i in ids] == ['2026-11-12T21:30:00+00:00', FUNCIONAL, YOGA, SPINNING]


def test_las_reservas_existentes_siguen_apuntando_a_su_clase(base_vieja):
    cliente, ids, socio = base_vieja(VIEJAS, reservadas=[3, 1])
    r = cliente.get('/reservas', headers=auth(socio))
    assert [x['clase_id'] for x in r.json()] == [ids[1], ids[3]]
    assert cliente.get(f'/clases/{ids[1]}').json()['lugares_libres'] == 9


def test_db_clases_devuelve_el_orden_real(base_vieja):
    """db.clases() la usan otros procesos de la empresa."""
    base_vieja(VIEJAS)
    assert [(c['nombre'], c['inicio']) for c in db.clases()] == [
        ('Pilates', '2026-11-12T21:30:00+00:00'), ('Funcional', FUNCIONAL), ('Yoga', YOGA), ('Spinning', SPINNING)]

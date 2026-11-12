from datetime import timedelta

from apoyo import AHORA, local
from pulso import db


def ids(r):
    assert r.status_code == 200
    return [c['id'] for c in r.json()]


def test_sin_parametros_lista_igual_que_antes_y_trae_el_total(cliente):
    b = db.crear_clase('Spinning', 'Leo', AHORA + timedelta(hours=5))
    a = db.crear_clase('Yoga', 'Sofía', AHORA + timedelta(hours=2))
    db.crear_clase('Funcional', 'Leo', AHORA - timedelta(hours=1))
    r = cliente.get('/clases')
    assert ids(r) == [a['id'], b['id']]
    assert r.json()[0]['lugares_libres'] == 20
    assert r.headers['X-Total'] == '2'


def test_paginas(cliente):
    clases = [db.crear_clase(f'Clase {i}', 'Leo', AHORA + timedelta(hours=1 + i)) for i in range(25)]
    todas = [c['id'] for c in clases]
    assert ids(cliente.get('/clases')) == todas[:20]
    r = cliente.get('/clases', params={'pagina': 3, 'por_pagina': 10})
    assert ids(r) == todas[20:]
    assert r.headers['X-Total'] == '25'
    assert ids(cliente.get('/clases', params={'pagina': 2})) == todas[20:]


def test_pagina_despues_del_final_esta_vacia(cliente):
    for i in range(3):
        db.crear_clase(f'Clase {i}', 'Leo', AHORA + timedelta(hours=1 + i))
    r = cliente.get('/clases', params={'pagina': 5})
    assert r.status_code == 200
    assert r.json() == []
    assert r.headers['X-Total'] == '3'


def test_rangos_de_paginacion_invalidos(cliente):
    for params in ({'por_pagina': 0}, {'por_pagina': 51}, {'pagina': 0}, {'pagina': -1}):
        assert cliente.get('/clases', params=params).status_code == 422
    assert cliente.get('/clases', params={'por_pagina': 50}).status_code == 200


def test_el_dia_se_cuenta_en_hora_de_montevideo(cliente):
    noche = db.crear_clase('Yoga', 'Sofía', local(2026, 11, 11, 23, 30))
    madrugada = db.crear_clase('Spinning', 'Leo', local(2026, 11, 12, 0, 30))
    assert ids(cliente.get('/clases', params={'desde': '2026-11-11', 'hasta': '2026-11-11'})) == [noche['id']]
    assert ids(cliente.get('/clases', params={'desde': '2026-11-12', 'hasta': '2026-11-12'})) == [madrugada['id']]


def test_los_extremos_se_incluyen(cliente):
    dias = [db.crear_clase('Yoga', 'Sofía', local(2026, 11, d, 19)) for d in (11, 12, 13, 14)]
    r = cliente.get('/clases', params={'desde': '2026-11-12', 'hasta': '2026-11-13'})
    assert ids(r) == [dias[1]['id'], dias[2]['id']]
    assert r.headers['X-Total'] == '2'


def test_desde_y_hasta_por_separado(cliente):
    dias = [db.crear_clase('Yoga', 'Sofía', local(2026, 11, d, 19)) for d in (11, 12, 13)]
    assert ids(cliente.get('/clases', params={'desde': '2026-11-12'})) == [dias[1]['id'], dias[2]['id']]
    assert ids(cliente.get('/clases', params={'hasta': '2026-11-12'})) == [dias[0]['id'], dias[1]['id']]


def test_instructor_exacto_sin_mayusculas(cliente):
    leo = db.crear_clase('Spinning', 'Leo', AHORA + timedelta(hours=2))
    db.crear_clase('Spinning', 'Leonardo', AHORA + timedelta(hours=3))
    db.crear_clase('Yoga', 'Sofía', AHORA + timedelta(hours=4))
    assert ids(cliente.get('/clases', params={'instructor': 'leo'})) == [leo['id']]
    assert ids(cliente.get('/clases', params={'instructor': 'LEO'})) == [leo['id']]


def test_con_lugar(cliente, socio):
    llena = db.crear_clase('Yoga', 'Sofía', AHORA + timedelta(hours=2), cupo=1)
    libre = db.crear_clase('Spinning', 'Leo', AHORA + timedelta(hours=3), cupo=1)
    db.crear_reserva(socio['id'], llena['id'], AHORA)
    assert ids(cliente.get('/clases', params={'con_lugar': 'true'})) == [libre['id']]
    assert ids(cliente.get('/clases', params={'con_lugar': 'false'})) == [llena['id'], libre['id']]


def test_nunca_lista_las_que_ya_empezaron(cliente):
    db.crear_clase('Funcional', 'Leo', AHORA - timedelta(hours=1))
    db.crear_clase('Funcional', 'Leo', AHORA)
    despues = db.crear_clase('Yoga', 'Sofía', AHORA + timedelta(hours=1))
    r = cliente.get('/clases', params={'desde': '2026-11-10', 'hasta': '2026-11-10'})
    assert ids(r) == [despues['id']]
    assert r.headers['X-Total'] == '1'


def test_filtros_combinados_y_total_antes_de_paginar(cliente, socio):
    esperadas = []
    for i in range(6):
        clase = db.crear_clase('Spinning', 'Leo', local(2026, 11, 12, 8 + i))
        if i == 2:
            db.crear_reserva(socio['id'], clase['id'], AHORA)
            db.crear_clase('Yoga', 'Leo', local(2026, 11, 13, 8))
        esperadas.append(clase['id'])
    db.crear_clase('Spinning', 'Sofía', local(2026, 11, 12, 9))
    llena = esperadas.pop(2)
    with db.conexion() as con:
        con.execute('UPDATE clases SET cupo = 1 WHERE id = ?', (llena,))
    params = {'desde': '2026-11-12', 'hasta': '2026-11-12', 'instructor': 'Leo', 'con_lugar': 'true',
              'pagina': 2, 'por_pagina': 3}
    r = cliente.get('/clases', params=params)
    assert ids(r) == esperadas[3:]
    assert r.headers['X-Total'] == '5'


def test_fechas_invalidas(cliente):
    assert cliente.get('/clases', params={'desde': '12/11/2026'}).status_code == 422
    assert cliente.get('/clases', params={'hasta': '2026-13-01'}).status_code == 422
    assert cliente.get('/clases', params={'desde': '2026-11-14', 'hasta': '2026-11-12'}).status_code == 422

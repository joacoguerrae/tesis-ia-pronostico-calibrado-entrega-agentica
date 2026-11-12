import csv
import io

from apoyo import ADMIN, AHORA, local
from pulso import db

ENCABEZADO = ['fecha', 'hora', 'clase', 'instructor', 'cupo', 'confirmadas', 'ocupacion_pct']
NOVIEMBRE = {'desde': '2026-11-01', 'hasta': '2026-11-30'}


def exportar(cliente, params=NOVIEMBRE):
    r = cliente.get('/admin/ocupacion.csv', params=params, headers=ADMIN)
    assert r.status_code == 200
    return r


def filas(r):
    return list(csv.reader(io.StringIO(r.text)))


def llenar(clase, n, estado='confirmada'):
    for i in range(n):
        socio = db.crear_socio(f'Socio {clase["id"]}-{estado}-{i}', f'{clase["id"]}.{estado}.{i}@example.com')
        db.crear_reserva(socio['id'], clase['id'], AHORA, estado=estado)


def test_pide_clave_de_admin(cliente):
    assert cliente.get('/admin/ocupacion.csv', params=NOVIEMBRE).status_code == 401
    r = cliente.get('/admin/ocupacion.csv', params=NOVIEMBRE, headers={'X-Admin-Key': 'otra'})
    assert r.status_code == 401


def test_tipo_de_contenido_y_encabezado(cliente):
    r = exportar(cliente)
    assert r.headers['content-type'].startswith('text/csv')
    assert 'utf-8' in r.headers['content-type'].lower()
    assert filas(r)[0] == ENCABEZADO


def test_sin_clases_solo_el_encabezado(cliente):
    assert filas(exportar(cliente)) == [ENCABEZADO]


def test_una_fila_por_clase_en_hora_de_montevideo(cliente):
    clase = db.crear_clase('Spinning', 'Leo', local(2026, 11, 3, 7), cupo=20)
    llenar(clase, 15)
    assert filas(exportar(cliente))[1:] == [['2026-11-03', '07:00', 'Spinning', 'Leo', '20', '15', '75']]


def test_la_fecha_es_la_de_montevideo_aunque_en_utc_sea_otro_dia(cliente):
    db.crear_clase('Yoga', 'Sofía', local(2026, 11, 30, 22, 15))
    db.crear_clase('Yoga', 'Sofía', local(2026, 10, 31, 23, 0))
    assert [f[:2] for f in filas(exportar(cliente))[1:]] == [['2026-11-30', '22:15']]


def test_entran_pasadas_y_futuras_y_los_extremos(cliente):
    db.crear_clase('Funcional', 'Leo', local(2026, 11, 1, 0, 0))
    db.crear_clase('Yoga', 'Sofía', local(2026, 11, 9, 19))
    db.crear_clase('Spinning', 'Leo', local(2026, 11, 30, 23, 59))
    db.crear_clase('Spinning', 'Leo', local(2026, 12, 1, 0, 0))
    assert [f[0] for f in filas(exportar(cliente))[1:]] == ['2026-11-01', '2026-11-09', '2026-11-30']


def test_orden_por_inicio_y_despues_por_id(cliente):
    db.crear_clase('Spinning', 'Leo', local(2026, 11, 12, 19))
    temprano_b = db.crear_clase('Yoga', 'Sofía', local(2026, 11, 12, 8))
    temprano_a = db.crear_clase('Pilates', 'Marta', local(2026, 11, 12, 8))
    assert temprano_b['id'] < temprano_a['id']
    assert [f[2] for f in filas(exportar(cliente))[1:]] == ['Yoga', 'Pilates', 'Spinning']


def test_las_canceladas_no_cuentan(cliente):
    clase = db.crear_clase('Yoga', 'Sofía', local(2026, 11, 12, 19), cupo=10)
    llenar(clase, 3)
    llenar(clase, 4, estado='cancelada')
    assert filas(exportar(cliente))[1][5:] == ['3', '30']


def test_redondeo(cliente):
    casos = [(8, 1, '13'), (3, 1, '33'), (3, 2, '67'), (16, 1, '6'), (40, 1, '3'), (5, 0, '0'), (4, 4, '100')]
    for i, (cupo, n, _) in enumerate(casos):
        llenar(db.crear_clase(f'Clase {i}', 'Leo', local(2026, 11, 12, 8 + i), cupo=cupo), n)
    assert [f[6] for f in filas(exportar(cliente))[1:]] == [esperado for _, _, esperado in casos]


def test_textos_con_comas_y_comillas(cliente):
    db.crear_clase('Yoga, nivel 1', 'Ana "La Profe" Ruiz', local(2026, 11, 12, 19))
    r = exportar(cliente)
    assert '"Yoga, nivel 1","Ana ""La Profe"" Ruiz"' in r.text
    assert filas(r)[1][2:4] == ['Yoga, nivel 1', 'Ana "La Profe" Ruiz']


def test_fechas_invalidas(cliente):
    for params in ({'desde': '2026-11-01'}, {'hasta': '2026-11-30'}, {},
                   {'desde': '01/11/2026', 'hasta': '2026-11-30'},
                   {'desde': '2026-11-30', 'hasta': '2026-11-01'},
                   {'desde': '2026-10-01', 'hasta': '2026-11-01'}):
        assert cliente.get('/admin/ocupacion.csv', params=params, headers=ADMIN).status_code == 422, params


def test_treinta_y_un_dias_se_aceptan(cliente):
    assert cliente.get('/admin/ocupacion.csv', params={'desde': '2026-10-01', 'hasta': '2026-10-31'},
                       headers=ADMIN).status_code == 200
    assert cliente.get('/admin/ocupacion.csv', params={'desde': '2026-11-12', 'hasta': '2026-11-12'},
                       headers=ADMIN).status_code == 200

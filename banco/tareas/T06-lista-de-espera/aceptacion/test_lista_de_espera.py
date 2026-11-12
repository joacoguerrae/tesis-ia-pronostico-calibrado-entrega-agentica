from datetime import timedelta
from itertools import count

from apoyo import ADMIN, AHORA, auth
from pulso import db, reloj

# 10/11 a las 18:30 en Montevideo.
INICIO = AHORA + timedelta(hours=6, minutes=30)
_numero = count(1)


def nuevo_socio(creditos=8):
    n = next(_numero)
    return db.crear_socio(f'Socio {n}', f'socio{n}@example.com', creditos=creditos)


def clase_llena(cupo=1, inicio=INICIO):
    """Una clase de Yoga con todos los lugares reservados por otros socios."""
    clase = db.crear_clase('Yoga', 'Sofía', inicio, cupo=cupo)
    reservas = [db.crear_reserva(nuevo_socio()['id'], clase['id'], AHORA) for _ in range(cupo)]
    return clase, reservas


def reservar(cliente, socio, clase):
    return cliente.post('/reservas', json={'clase_id': clase['id']}, headers=auth(socio))


def anotar(cliente, socio, clase):
    return cliente.post(f"/clases/{clase['id']}/espera", headers=auth(socio))


def ver_espera(cliente, socio, clase):
    return cliente.get(f"/clases/{clase['id']}/espera", headers=auth(socio))


def bajar(cliente, socio, clase):
    return cliente.delete(f"/clases/{clase['id']}/espera", headers=auth(socio))


def posicion(cliente, socio, clase):
    r = ver_espera(cliente, socio, clase)
    assert r.status_code == 200
    return r.json()['posicion']


def cancelar(cliente, reserva):
    return cliente.post(f"/admin/reservas/{reserva['id']}/cancelar", headers=ADMIN)


def cambiar_cupo(cliente, clase, cupo):
    return cliente.patch(f"/admin/clases/{clase['id']}", json={'cupo': cupo}, headers=ADMIN)


def creditos(cliente, socio):
    return cliente.get('/yo', headers=auth(socio)).json()['creditos']


def reservas(cliente, socio, clase):
    """Estados de las reservas del socio para esa clase."""
    return [r['estado'] for r in cliente.get('/reservas', headers=auth(socio)).json() if r['clase_id'] == clase['id']]


def confirmadas_de(cliente, socio, clase):
    return reservas(cliente, socio, clase).count('confirmada')


def lugares(cliente, clase):
    return cliente.get(f"/clases/{clase['id']}").json()['lugares_libres']


def asuntos(socio, comienzo):
    return [c['asunto'] for c in db.correos() if c['para'] == socio['email'] and c['asunto'].startswith(comienzo)]


def test_se_anota_en_una_clase_llena(cliente, socio, otro):
    clase, _ = clase_llena()
    r = anotar(cliente, socio, clase)
    assert r.status_code == 201
    assert r.json()['clase_id'] == clase['id']
    assert r.json()['posicion'] == 1
    assert anotar(cliente, otro, clase).json()['posicion'] == 2
    r = ver_espera(cliente, otro, clase)
    assert r.status_code == 200
    assert r.json()['clase_id'] == clase['id']
    assert r.json()['posicion'] == 2
    assert creditos(cliente, socio) == 8
    assert confirmadas_de(cliente, socio, clase) == 0


def test_no_se_anota_si_la_clase_tiene_lugar(cliente, socio):
    clase = db.crear_clase('Yoga', 'Sofía', INICIO, cupo=2)
    db.crear_reserva(nuevo_socio()['id'], clase['id'], AHORA)
    assert anotar(cliente, socio, clase).status_code == 409
    assert ver_espera(cliente, socio, clase).status_code == 404


def test_no_se_anota_si_ya_tiene_reserva_o_ya_esta_anotado(cliente, socio, otro):
    clase = db.crear_clase('Yoga', 'Sofía', INICIO, cupo=1)
    assert reservar(cliente, socio, clase).status_code == 201
    assert anotar(cliente, socio, clase).status_code == 409
    assert ver_espera(cliente, socio, clase).status_code == 404
    assert anotar(cliente, otro, clase).status_code == 201
    assert anotar(cliente, otro, clase).status_code == 409
    assert posicion(cliente, otro, clase) == 1


def test_no_se_anota_si_la_clase_ya_empezo(cliente, socio):
    justo, _ = clase_llena(inicio=AHORA)
    empezada, _ = clase_llena(inicio=AHORA - timedelta(minutes=10))
    assert anotar(cliente, socio, justo).status_code == 409
    assert anotar(cliente, socio, empezada).status_code == 409


def test_no_se_anota_sin_creditos(cliente):
    socio = nuevo_socio(creditos=0)
    clase, _ = clase_llena()
    assert anotar(cliente, socio, clase).status_code == 409
    assert ver_espera(cliente, socio, clase).status_code == 404


def test_clase_inexistente_sin_token_o_sin_anotarse(cliente, socio):
    clase, _ = clase_llena()
    assert cliente.post('/clases/999/espera', headers=auth(socio)).status_code == 404
    ruta = f"/clases/{clase['id']}/espera"
    for metodo in ('POST', 'GET', 'DELETE'):
        assert cliente.request(metodo, ruta).status_code == 401
        assert cliente.request(metodo, ruta, headers={'Authorization': 'Bearer no-existe'}).status_code == 401
    assert ver_espera(cliente, socio, clase).status_code == 404
    assert bajar(cliente, socio, clase).status_code == 404


def test_bajarse_y_volver_a_anotarse(cliente, socio, otro):
    eva = nuevo_socio()
    clase, _ = clase_llena()
    for s in (socio, otro, eva):
        assert anotar(cliente, s, clase).status_code == 201
    r = bajar(cliente, otro, clase)
    assert r.status_code == 204
    assert r.content == b''
    assert ver_espera(cliente, otro, clase).status_code == 404
    assert posicion(cliente, eva, clase) == 2
    assert bajar(cliente, otro, clase).status_code == 404
    assert anotar(cliente, otro, clase).json()['posicion'] == 3
    assert posicion(cliente, socio, clase) == 1
    assert posicion(cliente, eva, clase) == 2


def test_recepcion_cancela_y_devuelve_el_credito(cliente, socio):
    clase = db.crear_clase('Yoga', 'Sofía', AHORA + timedelta(minutes=30))
    reserva = reservar(cliente, socio, clase).json()
    assert creditos(cliente, socio) == 7
    r = cancelar(cliente, reserva)
    assert r.status_code == 200
    assert r.json()['id'] == reserva['id']
    assert r.json()['clase_id'] == clase['id']
    assert r.json()['estado'] == 'cancelada'
    assert r.json()['creada'] == reserva['creada']
    assert creditos(cliente, socio) == 8
    assert reservas(cliente, socio, clase) == ['cancelada']
    assert lugares(cliente, clase) == 20
    assert cliente.post('/admin/reservas/999/cancelar', headers=ADMIN).status_code == 404


def test_cancelar_dos_veces_no_devuelve_ni_asigna_dos_veces(cliente, socio, otro):
    eva = nuevo_socio()
    clase = db.crear_clase('Yoga', 'Sofía', INICIO, cupo=1)
    reserva = reservar(cliente, eva, clase).json()
    anotar(cliente, socio, clase)
    anotar(cliente, otro, clase)
    assert cancelar(cliente, reserva).status_code == 200
    assert cancelar(cliente, reserva).status_code == 409
    assert creditos(cliente, eva) == 8
    assert confirmadas_de(cliente, socio, clase) == 1
    assert confirmadas_de(cliente, otro, clase) == 0
    assert posicion(cliente, otro, clase) == 1
    assert db.confirmadas(clase['id']) == 1


def test_endpoints_de_recepcion_piden_la_clave(cliente, socio):
    clase, [reserva] = clase_llena()
    for headers in ({}, {'X-Admin-Key': 'otra'}, auth(socio)):
        assert cliente.post(f"/admin/reservas/{reserva['id']}/cancelar", headers=headers).status_code == 401
        assert cliente.patch(f"/admin/clases/{clase['id']}", json={'cupo': 5}, headers=headers).status_code == 401
    assert db.reserva(reserva['id'])['estado'] == 'confirmada'
    assert cliente.get(f"/clases/{clase['id']}").json()['cupo'] == 1


def test_no_baja_el_cupo_por_debajo_de_las_confirmadas(cliente):
    clase = db.crear_clase('Yoga', 'Sofía', INICIO, cupo=3)
    for _ in range(2):
        db.crear_reserva(nuevo_socio()['id'], clase['id'], AHORA)
    assert cambiar_cupo(cliente, clase, 1).status_code == 409
    assert cliente.get(f"/clases/{clase['id']}").json()['cupo'] == 3
    r = cambiar_cupo(cliente, clase, 2)
    assert r.status_code == 200
    assert r.json()['cupo'] == 2
    assert r.json()['lugares_libres'] == 0
    vacia = db.crear_clase('Pilates', 'Marta', INICIO)
    assert cambiar_cupo(cliente, vacia, 0).status_code == 422
    assert cliente.patch(f"/admin/clases/{vacia['id']}", json={}, headers=ADMIN).status_code == 422
    assert cliente.get(f"/clases/{vacia['id']}").json()['cupo'] == 20
    assert cliente.patch('/admin/clases/999', json={'cupo': 5}, headers=ADMIN).status_code == 404


def test_el_lugar_pasa_al_primero_en_anotarse(cliente, socio, otro):
    clase, [reserva] = clase_llena()
    # Juan se registró después que Ana, pero se anota antes.
    anotar(cliente, otro, clase)
    anotar(cliente, socio, clase)
    assert cancelar(cliente, reserva).status_code == 200
    assert confirmadas_de(cliente, otro, clase) == 1
    assert creditos(cliente, otro) == 7
    assert ver_espera(cliente, otro, clase).status_code == 404
    assert confirmadas_de(cliente, socio, clase) == 0
    assert creditos(cliente, socio) == 8
    assert posicion(cliente, socio, clase) == 1
    assert lugares(cliente, clase) == 0


def test_correo_al_que_recibe_el_lugar(cliente, socio):
    clase, [reserva] = clase_llena()
    anotar(cliente, socio, clase)
    cancelar(cliente, reserva)
    assert asuntos(socio, 'Se liberó un lugar') == ['Se liberó un lugar: Yoga el 10/11 a las 18:30']
    assert asuntos(socio, 'Reserva confirmada') == []


def test_saltea_al_que_se_quedo_sin_creditos(cliente, socio, otro):
    eva = nuevo_socio(creditos=1)
    clase, [reserva] = clase_llena()
    for s in (eva, socio, otro):
        assert anotar(cliente, s, clase).status_code == 201
    # Eva usa su último crédito en otra clase mientras espera.
    assert reservar(cliente, eva, db.crear_clase('Spinning', 'Leo', AHORA + timedelta(days=1))).status_code == 201
    assert cancelar(cliente, reserva).status_code == 200
    assert confirmadas_de(cliente, eva, clase) == 0
    assert creditos(cliente, eva) == 0
    assert ver_espera(cliente, eva, clase).status_code == 404
    assert asuntos(eva, 'No pudimos darte el lugar') == ['No pudimos darte el lugar: Yoga el 10/11 a las 18:30']
    assert asuntos(eva, 'Se liberó un lugar') == []
    assert confirmadas_de(cliente, socio, clase) == 1
    assert posicion(cliente, otro, clase) == 1
    assert lugares(cliente, clase) == 0


def test_ampliar_el_cupo_libera_varios_lugares(cliente, socio, otro):
    eva = nuevo_socio()
    clase, _ = clase_llena(cupo=2)
    for s in (socio, otro, eva):
        anotar(cliente, s, clase)
    r = cambiar_cupo(cliente, clase, 4)
    assert r.status_code == 200
    assert r.json()['cupo'] == 4
    assert r.json()['lugares_libres'] == 0
    assert confirmadas_de(cliente, socio, clase) == 1
    assert confirmadas_de(cliente, otro, clase) == 1
    assert creditos(cliente, socio) == creditos(cliente, otro) == 7
    assert confirmadas_de(cliente, eva, clase) == 0
    assert posicion(cliente, eva, clase) == 1
    assert cambiar_cupo(cliente, clase, 4).json()['lugares_libres'] == 0
    assert posicion(cliente, eva, clase) == 1
    assert cambiar_cupo(cliente, clase, 6).json()['lugares_libres'] == 1
    assert confirmadas_de(cliente, eva, clase) == 1
    assert db.confirmadas(clase['id']) == 5


def test_no_asigna_lugares_si_la_clase_ya_empezo(cliente, socio, otro):
    clase = db.crear_clase('Yoga', 'Sofía', AHORA + timedelta(hours=1), cupo=1)
    reserva = reservar(cliente, otro, clase).json()
    anotar(cliente, socio, clase)
    reloj.fijar(AHORA + timedelta(hours=1))
    assert cancelar(cliente, reserva).status_code == 200
    assert creditos(cliente, otro) == 8
    assert cambiar_cupo(cliente, clase, 3).json()['lugares_libres'] == 3
    assert confirmadas_de(cliente, socio, clase) == 0
    assert creditos(cliente, socio) == 8
    assert asuntos(socio, 'Se liberó un lugar') == []
    assert asuntos(socio, 'No pudimos darte el lugar') == []
    assert posicion(cliente, socio, clase) == 1

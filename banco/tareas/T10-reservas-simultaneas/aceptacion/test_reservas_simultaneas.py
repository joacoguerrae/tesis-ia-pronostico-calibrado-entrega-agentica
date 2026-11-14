import json
import os
import subprocess
import sys
import threading
import time
from datetime import timedelta
from itertools import count
from pathlib import Path

import pulso
from fastapi.testclient import TestClient

from apoyo import AHORA, auth
from pulso import db

INICIO = AHORA + timedelta(days=1)
SIN_LUGAR = 'La clase no tiene lugar'
SIN_CREDITOS = 'No te quedan créditos'
REPETIDA = 'Ya tenés una reserva para esta clase'
PROCESO = Path(__file__).parent / 'proceso_que_reserva.py'
_numero = count(1)


def nuevo_socio(creditos=8):
    n = next(_numero)
    return db.crear_socio(f'Socio {n}', f'socio{n}@example.com', creditos=creditos)


def nueva_clase(cupo):
    return db.crear_clase(f'Spinning {next(_numero)}', 'Leo', INICIO, cupo=cupo)


def a_la_vez(cliente, pedidos):
    """Manda todos los pedidos (socio, clase) al mismo tiempo, un hilo por pedido. Devuelve (código, cuerpo)."""
    clientes = [TestClient(cliente.app, raise_server_exceptions=False) for _ in pedidos]
    largada = threading.Barrier(len(pedidos))
    resultados = [None] * len(pedidos)

    def reservar(i):
        socio, clase = pedidos[i]
        largada.wait()
        r = clientes[i].post('/reservas', json={'clase_id': clase['id']}, headers=auth(socio))
        resultados[i] = (r.status_code, r.json() if r.headers.get('content-type') == 'application/json' else r.text)

    hilos = [threading.Thread(target=reservar, args=(i,)) for i in range(len(pedidos))]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    return resultados


def en_procesos(olas):
    """Reparte pedidos entre 4 procesos de la API que largan a la vez.

    `olas` es una lista de olas, y cada ola, una lista con los pedidos (socio, clase) de cada proceso. Las olas
    salen una después de la otra, separadas por medio segundo, y dentro de cada ola todos los pedidos de todos
    los procesos salen al mismo tiempo.
    """
    primera = time.time() + 4
    por_proceso = [[] for _ in range(4)]
    for n, ola in enumerate(olas):
        for p, pedidos in enumerate(ola):
            por_proceso[p] += [f"{primera + n * 0.5}:{s['token']}:{c['id']}" for s, c in pedidos]
    entorno = dict(os.environ, PYTHONPATH=str(Path(pulso.__file__).parent.parent))
    procesos = [subprocess.Popen([sys.executable, str(PROCESO), *pedidos], stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, text=True, env=entorno)
                for pedidos in por_proceso]
    resultados = []
    for p in procesos:
        salida, errores = p.communicate(timeout=180)
        assert p.returncode == 0, errores[-2000:]
        resultados += [tuple(x) for x in json.loads(salida)]
    return resultados


def codigos(resultados):
    return sorted(c for c, _ in resultados)


def detalles(resultados):
    return {cuerpo['detail'] for c, cuerpo in resultados if c == 409}


def confirmadas(clase):
    return db.confirmadas(clase['id'])


def creditos(socio):
    return db.socio(socio['id'])['creditos']


def reservas_confirmadas_de(socio):
    return [r for r in db.reservas_de(socio['id']) if r['estado'] == 'confirmada']


def correos_de(socio):
    return [c for c in db.correos() if c['para'] == socio['email']]


def test_el_ultimo_lugar_es_de_uno_solo(cliente):
    for _ in range(5):
        clase = nueva_clase(cupo=1)
        socios = [nuevo_socio() for _ in range(12)]
        resultados = a_la_vez(cliente, [(s, clase) for s in socios])
        assert codigos(resultados) == [201] + [409] * 11
        assert detalles(resultados) == {SIN_LUGAR}
        assert confirmadas(clase) == 1


def test_la_respuesta_del_ganador_no_cambia(cliente):
    clase = nueva_clase(cupo=1)
    socios = [nuevo_socio() for _ in range(6)]
    [(_, cuerpo)] = [r for r in a_la_vez(cliente, [(s, clase) for s in socios]) if r[0] == 201]
    assert set(cuerpo) == {'id', 'clase_id', 'estado', 'creada'}
    assert cuerpo['clase_id'] == clase['id'] and cuerpo['estado'] == 'confirmada'


def test_nunca_hay_mas_reservas_que_cupo(cliente):
    for _ in range(3):
        clase = nueva_clase(cupo=5)
        socios = [nuevo_socio() for _ in range(25)]
        resultados = a_la_vez(cliente, [(s, clase) for s in socios])
        assert codigos(resultados) == [201] * 5 + [409] * 20
        assert confirmadas(clase) == 5
        assert cliente.get(f"/clases/{clase['id']}").json()['lugares_libres'] == 0


def test_los_que_no_consiguen_lugar_no_pierden_creditos_ni_reciben_correo(cliente):
    clase = nueva_clase(cupo=3)
    socios = [nuevo_socio() for _ in range(20)]
    a_la_vez(cliente, [(s, clase) for s in socios])
    ganadores = [s for s in socios if reservas_confirmadas_de(s)]
    perdedores = [s for s in socios if not reservas_confirmadas_de(s)]
    assert len(ganadores) == 3
    assert [creditos(s) for s in ganadores] == [7] * 3
    assert [creditos(s) for s in perdedores] == [8] * 17
    assert [len(correos_de(s)) for s in ganadores] == [1] * 3
    assert [len(correos_de(s)) for s in perdedores] == [0] * 17


def test_los_creditos_nunca_quedan_negativos(cliente):
    for _ in range(3):
        socio = nuevo_socio(creditos=1)
        clases = [nueva_clase(cupo=10) for _ in range(8)]
        resultados = a_la_vez(cliente, [(socio, c) for c in clases])
        assert codigos(resultados) == [201] + [409] * 7
        assert detalles(resultados) == {SIN_CREDITOS}
        assert creditos(socio) == 0
        assert len(reservas_confirmadas_de(socio)) == 1
        assert len(correos_de(socio)) == 1


def test_tocar_dos_veces_el_boton_reserva_una_sola_vez(cliente):
    for _ in range(3):
        socio = nuevo_socio()
        clase = nueva_clase(cupo=10)
        resultados = a_la_vez(cliente, [(socio, clase)] * 8)
        assert codigos(resultados) == [201] + [409] * 7
        assert detalles(resultados) == {REPETIDA}
        assert creditos(socio) == 7
        assert len(reservas_confirmadas_de(socio)) == 1
        assert len(correos_de(socio)) == 1


def test_ningun_pedido_termina_en_error_del_servidor(cliente):
    clases = [nueva_clase(cupo=3) for _ in range(4)]
    pedidos = [(nuevo_socio(), c) for c in clases for _ in range(10)]
    socio_corto = nuevo_socio(creditos=2)
    pedidos += [(socio_corto, c) for c in clases]
    resultados = a_la_vez(cliente, pedidos)
    assert set(c for c, _ in resultados) <= {201, 409}, [r for r in resultados if r[0] not in (201, 409)][:3]
    assert [confirmadas(c) for c in clases] == [3] * 4
    assert creditos(socio_corto) >= 0


def test_con_varios_procesos_no_se_pasa_del_cupo(cliente):
    socios = [nuevo_socio(creditos=50) for _ in range(8)]
    clases, olas = [], []
    for _ in range(5):
        ola = [nueva_clase(cupo=1) for _ in range(4)]
        clases += ola
        # Los 8 socios quieren cada clase de la ola: cada proceso manda 2 pedidos por clase.
        olas.append([[(s, c) for c in ola for s in socios[p::4]] for p in range(4)])
    resultados = en_procesos(olas)
    assert set(c for c, _ in resultados) <= {201, 409}
    assert {d for c, d in resultados if c == 409} == {SIN_LUGAR}
    assert [confirmadas(c) for c in clases] == [1] * 20
    assert sum(creditos(s) for s in socios) == 8 * 50 - 20
    assert len(db.correos()) == 20


def test_con_varios_procesos_los_creditos_alcanzan_para_lo_que_alcanzan(cliente):
    socios, olas = [], []
    for _ in range(5):
        ola = [nuevo_socio(creditos=1) for _ in range(4)]
        socios += ola
        clases = [nueva_clase(cupo=50) for _ in range(8)]
        # Cada socio de la ola quiere las 8 clases: cada proceso manda 2 pedidos por socio.
        olas.append([[(s, c) for s in ola for c in clases[p::4]] for p in range(4)])
    resultados = en_procesos(olas)
    assert set(c for c, _ in resultados) <= {201, 409}
    assert {d for c, d in resultados if c == 409} == {SIN_CREDITOS}
    for s in socios:
        assert creditos(s) == 0
        assert len(reservas_confirmadas_de(s)) == 1
        assert len(correos_de(s)) == 1

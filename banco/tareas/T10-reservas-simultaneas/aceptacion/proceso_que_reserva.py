"""Un proceso de la API, como uno de los workers de uvicorn en producción.

Arranca la app sobre la base compartida y manda, con un hilo por pedido, una reserva por cada pedido. Cada
pedido sale en su momento de largada (hora de época), así todos los procesos largan a la vez. Imprime en JSON el
código y el detalle de cada respuesta, en el orden de los pedidos.

Uso: python proceso_que_reserva.py LARGADA:TOKEN:CLASE [LARGADA:TOKEN:CLASE ...]
(PULSO_DB, PULSO_ADMIN_KEY y PYTHONPATH vienen del entorno.)
"""
import json
import sys
import threading
import time
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from pulso import reloj
from pulso.main import crear_app

reloj.fijar(datetime(2026, 11, 10, 15, 0, tzinfo=timezone.utc))
app = crear_app()
pedidos = [p.split(':') for p in sys.argv[1:]]
resultados = [None] * len(pedidos)
clientes = [TestClient(app, raise_server_exceptions=False) for _ in pedidos]


def reservar(i):
    largada, token, clase_id = pedidos[i]
    while time.time() < float(largada):
        time.sleep(0.001)
    r = clientes[i].post('/reservas', json={'clase_id': int(clase_id)}, headers={'Authorization': f'Bearer {token}'})
    try:
        detalle = r.json().get('detail')
    except ValueError:
        detalle = r.text
    resultados[i] = [r.status_code, detalle]


hilos = [threading.Thread(target=reservar, args=(i,)) for i in range(len(pedidos))]
for h in hilos:
    h.start()
for h in hilos:
    h.join()
print(json.dumps(resultados))

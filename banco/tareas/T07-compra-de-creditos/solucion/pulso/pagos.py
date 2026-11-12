"""Cliente de Cobrá, el proveedor de pagos. Cobrá es la fuente de verdad del estado de cada pago."""
import os
from urllib.parse import quote

import httpx

TIMEOUT_SEG = 5

# Un solo cliente para reusar conexiones. La URL y la clave se leen en cada pedido, no acá.
_http = httpx.Client(timeout=TIMEOUT_SEG)


class FallaDeCobra(Exception):
    """Cobrá no contestó, o contestó con un código que no está en su contrato."""


def _pedir(metodo, ruta, codigos, **opciones):
    base = os.environ.get('PULSO_PAGOS_URL')
    if not base:
        raise FallaDeCobra('Falta PULSO_PAGOS_URL')
    headers = {'X-Cobra-Clave': os.environ.get('PULSO_PAGOS_CLAVE', ''), **opciones.pop('headers', {})}
    try:
        respuesta = _http.request(metodo, base.rstrip('/') + ruta, headers=headers, **opciones)
    except httpx.HTTPError as error:
        raise FallaDeCobra(f'{metodo} {ruta}: {error!r}') from error
    if respuesta.status_code not in codigos:
        raise FallaDeCobra(f'{metodo} {ruta}: respondió {respuesta.status_code}')
    try:
        return respuesta.status_code, respuesta.json()
    except ValueError as error:
        raise FallaDeCobra(f'{metodo} {ruta}: la respuesta no es JSON') from error


def crear_pago(monto, moneda, referencia):
    """Crea el pago. La referencia va también como Idempotency-Key: repetir el pedido no crea otro pago."""
    _, pago = _pedir('POST', '/pagos', (200, 201), json={'monto': monto, 'moneda': moneda, 'referencia': referencia},
                     headers={'Idempotency-Key': referencia})
    return pago


def consultar_pago(pago_id):
    """El pago con ese id, o None si Cobrá no lo conoce."""
    codigo, pago = _pedir('GET', f'/pagos/{quote(pago_id, safe="")}', (200, 404))
    return pago if codigo == 200 else None


def buscar_pago(referencia):
    """El pago con esa referencia, o None si no hay ninguno."""
    _, datos = _pedir('GET', '/pagos', (200,), params={'referencia': referencia})
    return datos['pagos'][0] if datos.get('pagos') else None

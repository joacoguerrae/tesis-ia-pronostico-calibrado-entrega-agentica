"""Cliente del servicio de beneficios corporativos, que dice quién es empleado activo de cada empresa."""
import os
from urllib.parse import quote

import httpx

TIMEOUT_SEGUNDOS = 3


class ServicioCaido(Exception):
    """El servicio no contestó o contestó algo que no está en el contrato."""


def consultar(empresa, email):
    """Devuelve 'activo', 'inactivo', 'desconocido' (no conoce el email) o 'sin_empresa' (no existe la empresa)."""
    base = os.environ.get('PULSO_BENEFICIOS_URL', '').rstrip('/')
    url = f"{base}/empresas/{quote(empresa, safe='')}/empleados/{quote(email.lower(), safe='')}"
    try:
        r = httpx.get(url, headers={'X-Api-Key': os.environ.get('PULSO_BENEFICIOS_CLAVE', '')},
                      timeout=TIMEOUT_SEGUNDOS)
        cuerpo = r.json()
    except (httpx.HTTPError, ValueError) as error:
        raise ServicioCaido(str(error)) from error
    if not isinstance(cuerpo, dict):
        raise ServicioCaido(f'Respuesta inesperada: {r.status_code}')
    if r.status_code == 200 and isinstance(cuerpo.get('activo'), bool):
        return 'activo' if cuerpo['activo'] else 'inactivo'
    if r.status_code == 404 and cuerpo.get('error') == 'empleado_desconocido':
        return 'desconocido'
    if r.status_code == 404 and cuerpo.get('error') == 'empresa_desconocida':
        return 'sin_empresa'
    raise ServicioCaido(f'Respuesta inesperada: {r.status_code}')

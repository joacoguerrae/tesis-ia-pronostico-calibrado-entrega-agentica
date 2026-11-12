from datetime import datetime, timedelta, timezone

# Martes 10/11/2026, 12:00 en Montevideo.
AHORA = datetime(2026, 11, 10, 15, 0, tzinfo=timezone.utc)
ADMIN = {'X-Admin-Key': 'clave-admin'}
MONTEVIDEO = timezone(timedelta(hours=-3))


def auth(socio):
    return {'Authorization': f"Bearer {socio['token']}"}


def local(anio, mes, dia, hora=0, minuto=0):
    """Un momento dado en hora de Montevideo."""
    return datetime(anio, mes, dia, hora, minuto, tzinfo=MONTEVIDEO)

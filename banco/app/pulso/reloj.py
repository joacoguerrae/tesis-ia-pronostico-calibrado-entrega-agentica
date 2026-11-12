"""Hora actual de la app. Todo el código la toma de acá para que los tests la puedan fijar."""
from datetime import datetime, timedelta, timezone

# Montevideo está en UTC-3 todo el año (no hay horario de verano).
MONTEVIDEO = timezone(timedelta(hours=-3), 'America/Montevideo')

_fija = None


def ahora():
    return _fija or datetime.now(timezone.utc)


def fijar(momento):
    global _fija
    _fija = momento

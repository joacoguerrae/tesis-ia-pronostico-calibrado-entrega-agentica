from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from pulso import db, reloj
from pulso.main import crear_app

# Martes 10/11/2026, 12:00 en Montevideo.
AHORA = datetime(2026, 11, 10, 15, 0, tzinfo=timezone.utc)
ADMIN = {'X-Admin-Key': 'clave-admin'}


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    monkeypatch.setenv('PULSO_DB', str(tmp_path / 'pulso.db'))
    monkeypatch.setenv('PULSO_ADMIN_KEY', ADMIN['X-Admin-Key'])
    reloj.fijar(AHORA)
    yield TestClient(crear_app())
    reloj.fijar(None)


@pytest.fixture
def socio(cliente):
    return db.crear_socio('Ana Pérez', 'ana@example.com')


def auth(socio):
    return {'Authorization': f"Bearer {socio['token']}"}

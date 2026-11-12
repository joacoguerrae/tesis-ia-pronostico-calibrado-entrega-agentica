"""Fixtures de los tests de aceptación. Solo usan lo que la app base ya tiene y su README garantiza."""
import pytest
from fastapi.testclient import TestClient

from apoyo import ADMIN, AHORA
from pulso import db, reloj
from pulso.main import crear_app


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


@pytest.fixture
def otro(cliente):
    return db.crear_socio('Juan Gómez', 'juan@example.com')

"""Acceso a la base SQLite. Las fechas se guardan como texto ISO 8601 en UTC."""
import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

ESQUEMA = """
CREATE TABLE IF NOT EXISTS socios (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    plan TEXT NOT NULL,
    creditos INTEGER NOT NULL,
    token TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS clases (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    instructor TEXT NOT NULL,
    inicio TEXT NOT NULL,
    duracion_min INTEGER NOT NULL,
    cupo INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS reservas (
    id INTEGER PRIMARY KEY,
    socio_id INTEGER NOT NULL REFERENCES socios(id),
    clase_id INTEGER NOT NULL REFERENCES clases(id),
    estado TEXT NOT NULL,
    creada TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS correos (
    id INTEGER PRIMARY KEY,
    para TEXT NOT NULL,
    asunto TEXT NOT NULL,
    cuerpo TEXT NOT NULL,
    creado TEXT NOT NULL
);
"""


def ruta():
    return os.environ.get('PULSO_DB', 'pulso.db')


@contextmanager
def conexion():
    con = sqlite3.connect(ruta())
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys = ON')
    try:
        yield con
        con.commit()
    finally:
        con.close()


def inicializar():
    with conexion() as con:
        con.executescript(ESQUEMA)


def a_texto(momento):
    return momento.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def a_fecha(texto):
    # Las clases de antes de setiembre se guardaron sin zona horaria, en UTC.
    return datetime.fromisoformat(texto).replace(tzinfo=timezone.utc)


def _una(sql, parametros=()):
    with conexion() as con:
        fila = con.execute(sql, parametros).fetchone()
    return dict(fila) if fila else None


def _varias(sql, parametros=()):
    with conexion() as con:
        return [dict(f) for f in con.execute(sql, parametros).fetchall()]


def crear_socio(nombre, email, plan='basico', creditos=8):
    with conexion() as con:
        cur = con.execute('INSERT INTO socios (nombre, email, plan, creditos, token) VALUES (?, ?, ?, ?, ?)',
                          (nombre, email, plan, creditos, secrets.token_hex(16)))
    return socio(cur.lastrowid)


def socio(socio_id):
    return _una('SELECT * FROM socios WHERE id = ?', (socio_id,))


def socio_por_token(token):
    return _una('SELECT * FROM socios WHERE token = ?', (token,))


def crear_clase(nombre, instructor, inicio, duracion_min=60, cupo=20):
    with conexion() as con:
        cur = con.execute('INSERT INTO clases (nombre, instructor, inicio, duracion_min, cupo) VALUES (?, ?, ?, ?, ?)',
                          (nombre, instructor, inicio.isoformat(timespec='seconds'), duracion_min, cupo))
    return clase(cur.lastrowid)


def clase(clase_id):
    return _una('SELECT * FROM clases WHERE id = ?', (clase_id,))


def clases():
    return _varias('SELECT * FROM clases ORDER BY inicio, id')


def confirmadas(clase_id):
    return _una("SELECT COUNT(*) AS n FROM reservas WHERE clase_id = ? AND estado = 'confirmada'", (clase_id,))['n']


def crear_reserva(socio_id, clase_id, creada, estado='confirmada'):
    with conexion() as con:
        cur = con.execute('INSERT INTO reservas (socio_id, clase_id, estado, creada) VALUES (?, ?, ?, ?)',
                          (socio_id, clase_id, estado, a_texto(creada)))
    return reserva(cur.lastrowid)


def reserva(reserva_id):
    return _una('SELECT * FROM reservas WHERE id = ?', (reserva_id,))


def reservas_de(socio_id):
    return _varias('SELECT r.* FROM reservas r JOIN clases c ON c.id = r.clase_id '
                   'WHERE r.socio_id = ? ORDER BY c.inicio, r.id', (socio_id,))


def sumar_creditos(socio_id, cantidad):
    with conexion() as con:
        con.execute('UPDATE socios SET creditos = creditos + ? WHERE id = ?', (cantidad, socio_id))


def correos():
    return _varias('SELECT * FROM correos ORDER BY id')

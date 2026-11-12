"""Bandeja de salida de correos. Un proceso aparte la vacía; la app solo guarda cada correo acá."""
from pulso import db, reloj


def enviar(para, asunto, cuerpo):
    with db.conexion() as con:
        con.execute('INSERT INTO correos (para, asunto, cuerpo, creado) VALUES (?, ?, ?, ?)',
                    (para, asunto, cuerpo, db.a_texto(reloj.ahora())))


def fecha_y_hora(momento):
    """Formato que usan los correos: '10/11 a las 18:30', en hora de Montevideo."""
    local = momento.astimezone(reloj.MONTEVIDEO)
    return f'{local:%d/%m} a las {local:%H:%M}'

"""Formato común de telemetría: una fila por corrida de una versión del agente sobre una tarea."""

COLUMNAS = ['version', 'tarea', 'repeticion', 'exito', 'costo_usd',
            'tokens_entrada', 'tokens_salida', 'pasos', 'duracion_s']

# Las métricas positivas se comparan en escala log (diferencias relativas);
# el éxito, como diferencia de proporciones.
METRICAS = {
    'exito': 'proporcion',
    'costo_usd': 'log',
    'tokens_entrada': 'log',
    'tokens_salida': 'log',
    'pasos': 'log',
    'duracion_s': 'log',
}


def validar(df):
    faltan = set(COLUMNAS) - set(df.columns)
    if faltan:
        raise ValueError(f'Faltan columnas: {sorted(faltan)}')
    if df.duplicated(['version', 'tarea', 'repeticion']).any():
        raise ValueError('Hay más de una corrida con la misma versión, tarea y repetición')
    return df

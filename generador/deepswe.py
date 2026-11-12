"""Adaptador del trials.json público de DeepSWE (v1.1) al formato común."""
import json
from pathlib import Path

import pandas as pd

from formato import COLUMNAS, validar

RUTA = Path(__file__).parent / 'datos' / 'deepswe' / 'trials.json'

RENOMBRE = {
    'config': 'version',
    'task_name': 'tarea',
    'passed': 'exito',
    'cost_usd': 'costo_usd',
    'n_input_tokens': 'tokens_entrada',
    'n_output_tokens': 'tokens_salida',
    'n_agent_steps': 'pasos',
    'agent_duration_seconds': 'duracion_s',
    'model': 'modelo',
    'reasoning_effort': 'esfuerzo',
}


def cargar(ruta=RUTA):
    df = pd.DataFrame(json.loads(Path(ruta).read_text())['rows'])
    # Las 155 corridas con error de infraestructura no tienen resultado.
    df = df[~df.errored].rename(columns=RENOMBRE)
    df['exito'] = df.exito.astype(float)
    # El archivo no numera las repeticiones: se ordenan por hora de inicio.
    df['inicio'] = pd.to_datetime(df.started_at, format='ISO8601')
    df = df.sort_values('inicio')
    df['repeticion'] = df.groupby(['version', 'tarea']).cumcount() + 1
    return validar(df[COLUMNAS + ['modelo', 'esfuerzo']].reset_index(drop=True))

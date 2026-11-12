"""Adaptador de las corridas del banco (Claude Code) al formato común.

Lee las carpetas que deja banco/herramientas/corredor.py. Además de la fila por corrida, devuelve
una tabla por llamada al modelo y otra por uso de herramienta, que llevan el id de la corrida para
poder rastrear cada fact hasta las corridas que lo respaldan.
"""
import json
from pathlib import Path

import pandas as pd

from formato import COLUMNAS, validar


def _jsonl(ruta):
    if not ruta.exists():
        return []
    return [json.loads(l) for l in ruta.read_text().splitlines() if l.strip()]


def _nombre(evento):
    return str(evento.get('event.name') or evento.get('_cuerpo') or '').removeprefix('claude_code.')


def _num(valor):
    return pd.to_numeric(valor, errors='coerce')


def cargar(carpeta):
    filas, llamadas, herramientas = [], [], []
    for d in sorted(p for p in Path(carpeta).iterdir() if (p / 'evaluacion.json').exists()):
        meta = json.loads((d / 'corrida.json').read_text())
        evaluacion = json.loads((d / 'evaluacion.json').read_text())
        resultado = next((e for e in reversed(_jsonl(d / 'stream.jsonl')) if e.get('type') == 'result'), {})
        otel = _jsonl(d / 'otel.jsonl')
        clave = dict(corrida=meta['id'], version=meta['version'], tarea=meta['tarea'], repeticion=meta['repeticion'])

        api = [e for e in otel if _nombre(e) == 'api_request']
        for e in api:
            llamadas.append(dict(clave, modelo=e.get('model'), duracion_ms=_num(e.get('duration_ms')),
                                 costo_usd=_num(e.get('cost_usd')), tokens_entrada=_num(e.get('input_tokens')),
                                 tokens_cache_lectura=_num(e.get('cache_read_tokens')),
                                 tokens_cache_escritura=_num(e.get('cache_creation_tokens')),
                                 tokens_salida=_num(e.get('output_tokens'))))
        for e in otel:
            if _nombre(e) == 'tool_result':
                herramientas.append(dict(clave, herramienta=e.get('tool_name'), exito=e.get('success'),
                                         duracion_ms=_num(e.get('duration_ms'))))

        uso = resultado.get('usage', {})
        entrada_total = sum(_num(uso.get(k)) or 0 for k in
                            ('input_tokens', 'cache_read_input_tokens', 'cache_creation_input_tokens'))
        filas.append(dict(
            clave, exito=float(evaluacion['exito']), costo_usd=_num(resultado.get('total_cost_usd')),
            # Los tokens de entrada incluyen los leídos y escritos en caché, como en DeepSWE.
            tokens_entrada=entrada_total if uso else float('nan'), tokens_salida=_num(uso.get('output_tokens')),
            # Un paso es una llamada al modelo; si no llegó la telemetría, se usan los turnos del resultado.
            pasos=len(api) if api else _num(resultado.get('num_turns')),
            duracion_s=meta['duracion_s'], tests_pasados=evaluacion['pasados'], tests=evaluacion['tests'],
            usos_de_herramientas=sum(1 for e in otel if _nombre(e) == 'tool_result'),
            permisos_negados=len(resultado.get('permission_denials') or []),
            termino=meta['termino'], resultado=resultado.get('subtype'), toco_banco=meta['toco_banco'],
            traza=meta.get('traza_id'), tramos=len(_jsonl(d / 'trazas.jsonl'))))

    corridas = pd.DataFrame(filas)
    validar(corridas[COLUMNAS])
    return corridas, pd.DataFrame(llamadas), pd.DataFrame(herramientas)

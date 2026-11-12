"""Claude Code falso para probar el corredor sin gastar tokens.

Imita la salida stream-json, los eventos de telemetría OTLP y los tramos de la traza de `claude -p`.
Respeta --max-turns: si el plan al azar tiene más pasos, corta y termina con error_max_turns. Con probabilidad
CLAUDE_FALSO_EXITO (0,7 por defecto) copia la solución de referencia de la tarea, así algunas
corridas pasan los tests y otras no. Los tokens y las duraciones salen al azar.
"""
import json
import os
import random
import shutil
import sys
import time
import urllib.request
import uuid
from pathlib import Path

BANCO = Path(__file__).resolve().parents[2]


def emitir(evento):
    print(json.dumps(evento, ensure_ascii=False), flush=True)


def atributo(clave, valor):
    if isinstance(valor, bool):
        v = {'boolValue': valor}
    elif isinstance(valor, int):
        v = {'intValue': str(valor)}
    elif isinstance(valor, float):
        v = {'doubleValue': valor}
    else:
        v = {'stringValue': str(valor)}
    return {'key': clave, 'value': v}


def enviar(ruta, cuerpo):
    pedido = urllib.request.Request(os.environ['OTEL_EXPORTER_OTLP_ENDPOINT'].rstrip('/') + ruta,
                                    data=json.dumps(cuerpo).encode(), headers={'Content-Type': 'application/json'})
    urllib.request.build_opener(urllib.request.ProxyHandler({})).open(pedido, timeout=5)


def recurso():
    return {'attributes': [atributo('service.name', 'claude-code'), atributo('service.version', '0.0.0-falso')]}


def telemetria(eventos):
    if not os.environ.get('OTEL_EXPORTER_OTLP_ENDPOINT'):
        return
    registros = [{'timeUnixNano': str(time.time_ns()), 'body': {'stringValue': f'claude_code.{nombre}'},
                  'attributes': [atributo('event.name', nombre), *[atributo(k, v) for k, v in attrs.items()]]}
                 for nombre, attrs in eventos]
    enviar('/v1/logs', {'resourceLogs': [{'resource': recurso(), 'scopeLogs': [
        {'scope': {'name': 'claude_falso'}, 'logRecords': registros}]}]})


def trazas(nombres):
    """Un tramo de pedido que cuelga del TRACEPARENT del corredor, con un tramo hijo por paso."""
    if os.environ.get('OTEL_TRACES_EXPORTER') != 'otlp' or not os.environ.get('OTEL_EXPORTER_OTLP_ENDPOINT'):
        return
    _, traza, padre, _ = os.environ.get('TRACEPARENT', f'00-{uuid.uuid4().hex}-{"0" * 16}-01').split('-')
    raiz, ahora = uuid.uuid4().hex[:16], str(time.time_ns())
    tramos = [{'traceId': traza, 'spanId': raiz, 'parentSpanId': padre, 'name': 'claude_code.interaction',
               'startTimeUnixNano': ahora, 'endTimeUnixNano': ahora, 'attributes': [], 'status': {}}]
    tramos += [{'traceId': traza, 'spanId': uuid.uuid4().hex[:16], 'parentSpanId': raiz, 'name': f'claude_code.{n}',
                'startTimeUnixNano': ahora, 'endTimeUnixNano': ahora, 'attributes': [], 'status': {}} for n in nombres]
    enviar('/v1/traces', {'resourceSpans': [{'resource': recurso(), 'scopeSpans': [
        {'scope': {'name': 'claude_falso'}, 'spans': tramos}]}]})


def main():
    if '--version' in sys.argv:
        print('0.0.0 (claude falso)')
        return
    prompt = sys.argv[sys.argv.index('-p') + 1]
    modelo = sys.argv[sys.argv.index('--model') + 1]
    sesion = str(uuid.uuid4())
    azar = random.Random()
    emitir({'type': 'system', 'subtype': 'init', 'session_id': sesion, 'model': modelo, 'cwd': os.getcwd(),
            'tools': ['Bash', 'Read', 'Edit'], 'apiKeySource': 'ANTHROPIC_API_KEY'})

    eventos, entrada, salida, costo, inicio = [], 0, 0, 0.0, time.monotonic()
    pasos = azar.randint(4, 12)
    tope = int(sys.argv[sys.argv.index('--max-turns') + 1]) if '--max-turns' in sys.argv else pasos
    cortada, pasos = pasos > tope, min(pasos, tope)
    for i in range(pasos):
        e, s = azar.randint(8000, 30000), azar.randint(200, 2500)
        entrada, salida = entrada + e, salida + s
        c = round(e * 3e-6 + s * 15e-6, 6)
        costo += c
        herramienta = azar.choice(['Read', 'Edit', 'Bash'])
        emitir({'type': 'assistant', 'session_id': sesion, 'parent_tool_use_id': None,
                'message': {'id': f'msg_{i}', 'model': modelo, 'role': 'assistant',
                            'content': [{'type': 'tool_use', 'id': f'toolu_{i}', 'name': herramienta, 'input': {}}],
                            'usage': {'input_tokens': e // 10, 'cache_read_input_tokens': e - e // 10,
                                      'cache_creation_input_tokens': 0, 'output_tokens': s}}})
        emitir({'type': 'user', 'session_id': sesion, 'parent_tool_use_id': None,
                'message': {'role': 'user', 'content': [{'type': 'tool_result', 'tool_use_id': f'toolu_{i}',
                                                         'content': 'ok', 'is_error': False}]}})
        eventos += [('api_request', {'session.id': sesion, 'model': modelo, 'cost_usd': c,
                                     'duration_ms': azar.randint(2000, 20000), 'input_tokens': e // 10,
                                     'cache_read_tokens': e - e // 10, 'cache_creation_tokens': 0,
                                     'output_tokens': s}),
                    ('tool_result', {'session.id': sesion, 'tool_name': herramienta, 'success': azar.random() > 0.1,
                                     'duration_ms': azar.randint(5, 4000)})]

    titulo = prompt.splitlines()[0]
    tarea = next(d for d in (BANCO / 'tareas').iterdir() if d.name.startswith('T')
                 and (d / 'pedido.md').read_text().splitlines()[0] == titulo)
    if not cortada and azar.random() < float(os.environ.get('CLAUDE_FALSO_EXITO', 0.7)):
        shutil.copytree(tarea / 'solucion', os.getcwd(), dirs_exist_ok=True)
    telemetria(eventos)
    trazas([n for i in range(pasos) for n in ('llm_request', 'tool')])
    emitir({'type': 'result', 'subtype': 'error_max_turns' if cortada else 'success', 'is_error': cortada,
            'session_id': sesion,
            'duration_ms': int((time.monotonic() - inicio) * 1000), 'num_turns': pasos, 'result': 'Listo.',
            'total_cost_usd': round(costo, 6), 'permission_denials': [],
            'usage': {'input_tokens': entrada // 10, 'cache_read_input_tokens': entrada - entrada // 10,
                      'cache_creation_input_tokens': 0, 'output_tokens': salida}})


if __name__ == '__main__':
    main()

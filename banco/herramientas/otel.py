"""Receptor mínimo de OTLP/HTTP en JSON para guardar la telemetría de Claude Code.

Claude Code manda un evento `api_request` por cada llamada al modelo (modelo, tokens, costo y
duración) y un `tool_result` por cada uso de herramienta (nombre, éxito y duración). Con las trazas
activadas manda además un tramo por pedido, otro por llamada al modelo y otro por herramienta, que
se vinculan entre sí por el id del tramo padre.
"""
import gzip
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def _valor(v):
    if 'stringValue' in v:
        return v['stringValue']
    if 'intValue' in v:
        return int(v['intValue'])
    if 'doubleValue' in v:
        return float(v['doubleValue'])
    if 'boolValue' in v:
        return bool(v['boolValue'])
    if 'arrayValue' in v:
        return [_valor(x) for x in v['arrayValue'].get('values', [])]
    if 'kvlistValue' in v:
        return _atributos(v['kvlistValue'].get('values'))
    return None


def _atributos(lista):
    return {a['key']: _valor(a.get('value', {})) for a in lista or []}


def registros(cuerpo):
    for rl in cuerpo.get('resourceLogs', []):
        recurso = _atributos(rl.get('resource', {}).get('attributes'))
        for sl in rl.get('scopeLogs', []):
            for lr in sl.get('logRecords', []):
                yield dict(recurso, **_atributos(lr.get('attributes')),
                           _cuerpo=_valor(lr.get('body', {})), _tiempo_ns=int(lr.get('timeUnixNano') or 0))


def tramos(cuerpo):
    for rs in cuerpo.get('resourceSpans', []):
        recurso = _atributos(rs.get('resource', {}).get('attributes'))
        for ss in rs.get('scopeSpans', []):
            for t in ss.get('spans', []):
                yield dict(recurso, **_atributos(t.get('attributes')), _nombre=t.get('name'),
                           _traza=t.get('traceId'), _tramo=t.get('spanId'), _padre=t.get('parentSpanId') or None,
                           _inicio_ns=int(t.get('startTimeUnixNano') or 0), _fin_ns=int(t.get('endTimeUnixNano') or 0),
                           _estado=t.get('status', {}).get('code'))


class Receptor:
    def __init__(self):
        self.eventos, self.trazas = [], []
        self._candado = threading.Lock()
        receptor = self

        class Manejador(BaseHTTPRequestHandler):
            def do_POST(self):
                datos = self.rfile.read(int(self.headers.get('Content-Length', 0)))
                if self.headers.get('Content-Encoding') == 'gzip':
                    datos = gzip.decompress(datos)
                try:
                    cuerpo = json.loads(datos)
                    nuevos, nuevas = list(registros(cuerpo)), list(tramos(cuerpo))
                except ValueError:
                    nuevos, nuevas = [dict(_error='cuerpo que no es JSON', _ruta=self.path, _bytes=len(datos))], []
                with receptor._candado:
                    receptor.eventos += nuevos
                    receptor.trazas += nuevas
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{}')

            def log_message(self, *args):
                pass

        self.servidor = ThreadingHTTPServer(('127.0.0.1', 0), Manejador)
        self.url = f'http://127.0.0.1:{self.servidor.server_port}'
        threading.Thread(target=self.servidor.serve_forever, daemon=True).start()

    def vaciar(self):
        """Devuelve los eventos y los tramos recibidos desde la última vez, y empieza de cero."""
        with self._candado:
            eventos, trazas = self.eventos, self.trazas
            self.eventos, self.trazas = [], []
        return eventos, trazas

    def cerrar(self):
        self.servidor.shutdown()

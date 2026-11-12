"""Cobrá de mentira para los tests de aceptación de la compra de créditos.

Es un servidor HTTP de verdad en 127.0.0.1, en un hilo, con la API de Cobrá que describe el pedido.
Guarda los pagos en memoria, registra cada pedido que recibe y deja simular fallas.
"""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlsplit

PREFIJO = '/v1'
ERROR = {'error': 'Error interno'}


class CobraFalso:
    def __init__(self, clave):
        self.clave = clave
        self.recibidos = []          # cada pedido: metodo, ruta, consulta, headers (en minúsculas) y cuerpo
        self.caido = False           # con True responde 500 a todo
        self.crear_y_caer = False    # el próximo pago se crea, pero la respuesta es 500 y Cobrá queda caído
        self._pagos = {}
        self._por_idempotencia = {}
        self._con_falla = set()
        self._candado = threading.Lock()
        self._servidor = ThreadingHTTPServer(('127.0.0.1', 0), _manejador(self))
        self.url = f'http://127.0.0.1:{self._servidor.server_address[1]}{PREFIJO}'
        self._hilo = threading.Thread(target=self._servidor.serve_forever, kwargs={'poll_interval': 0.01}, daemon=True)
        self._hilo.start()

    def apagar(self):
        """Apaga el servidor. Desde ahí las conexiones se rechazan: Cobrá no responde."""
        if self._hilo is not None:
            self._servidor.shutdown()
            self._servidor.server_close()
            self._hilo.join()
            self._hilo = None

    # Para preparar y revisar los tests.

    def pagos(self):
        with self._candado:
            return [dict(p) for p in self._pagos.values()]

    def pago_de(self, referencia):
        return next((p for p in self.pagos() if p['referencia'] == referencia), None)

    def poner_estado(self, referencia, estado):
        """Cambia el estado del pago de esa referencia y devuelve su id."""
        with self._candado:
            [pago] = [p for p in self._pagos.values() if p['referencia'] == referencia]
            pago['estado'] = estado
            return pago['id']

    def agregar_pago(self, referencia, estado='pendiente', monto=1200):
        """Un pago que no creó Pulso. Devuelve su id."""
        with self._candado:
            return self._nuevo(referencia, monto, 'UYU', estado)['id']

    def fallar_con(self, pago_id):
        """Desde ahora responde 500 a lo que pregunte por ese pago, por id o por referencia."""
        with self._candado:
            self._con_falla.add(pago_id)

    def no_fallar_mas(self):
        with self._candado:
            self._con_falla.clear()

    def creaciones(self):
        """Los pedidos para crear pagos."""
        return [p for p in self.recibidos if p['metodo'] == 'POST']

    # Servidor.

    def _nuevo(self, referencia, monto, moneda, estado='pendiente'):
        pago_id = f'pag_{len(self._pagos) + 1:04d}'
        self._pagos[pago_id] = dict(id=pago_id, estado=estado, monto=monto, moneda=moneda, referencia=referencia,
                                    url_pago=f'https://pagar.cobra.test/{pago_id}')
        return self._pagos[pago_id]

    def _atender(self, pedido):
        with self._candado:
            self.recibidos.append(pedido)
            if self.caido:
                return 500, ERROR
            if pedido['headers'].get('x-cobra-clave') != self.clave:
                return 401, {'error': 'Clave inválida'}
            metodo, ruta = pedido['metodo'], pedido['ruta']
            if metodo == 'POST' and ruta == f'{PREFIJO}/pagos':
                return self._crear(pedido)
            if metodo == 'GET' and ruta == f'{PREFIJO}/pagos':
                return self._buscar(pedido['consulta'].get('referencia'))
            if metodo == 'GET' and ruta.startswith(f'{PREFIJO}/pagos/'):
                return self._consultar(unquote(ruta.removeprefix(f'{PREFIJO}/pagos/')))
            return 404, {'error': 'No existe la ruta'}

    def _crear(self, pedido):
        cuerpo, clave = pedido['cuerpo'], pedido['headers'].get('idempotency-key')
        if not clave or not isinstance(cuerpo, dict) or not _monto_valido(cuerpo.get('monto')) \
                or not isinstance(cuerpo.get('moneda'), str) or not cuerpo.get('referencia'):
            return 422, {'error': 'Faltan datos'}
        if clave in self._por_idempotencia:
            codigo, pago = 200, self._pagos[self._por_idempotencia[clave]]
        else:
            codigo, pago = 201, self._nuevo(cuerpo['referencia'], cuerpo['monto'], cuerpo['moneda'])
            self._por_idempotencia[clave] = pago['id']
        if self.crear_y_caer:
            self.crear_y_caer, self.caido = False, True
            return 500, ERROR
        return codigo, dict(pago)

    def _buscar(self, referencia):
        if not referencia:
            return 422, {'error': 'Falta la referencia'}
        encontrados = [p for p in self._pagos.values() if p['referencia'] == referencia]
        if any(p['id'] in self._con_falla for p in encontrados):
            return 500, ERROR
        return 200, {'pagos': [dict(p) for p in encontrados]}

    def _consultar(self, pago_id):
        if pago_id in self._con_falla:
            return 500, ERROR
        if pago_id not in self._pagos:
            return 404, {'error': 'No existe el pago'}
        return 200, dict(self._pagos[pago_id])


def _monto_valido(monto):
    return isinstance(monto, (int, float)) and not isinstance(monto, bool) and monto > 0


def _manejador(cobra):
    class Manejador(BaseHTTPRequestHandler):
        def do_GET(self):
            self._responder('GET')

        def do_POST(self):
            self._responder('POST')

        def _leer_cuerpo(self):
            if self.headers.get('Transfer-Encoding', '').lower() == 'chunked':
                crudo = b''
                while (largo := int(self.rfile.readline().split(b';')[0].strip() or b'0', 16)):
                    crudo += self.rfile.read(largo)
                    self.rfile.readline()
                self.rfile.readline()
                return crudo
            return self.rfile.read(int(self.headers.get('Content-Length') or 0))

        def _responder(self, metodo):
            partes = urlsplit(self.path)
            crudo = self._leer_cuerpo()
            try:
                cuerpo = json.loads(crudo) if crudo else None
            except ValueError:
                cuerpo = crudo.decode('utf-8', 'replace')
            pedido = dict(metodo=metodo, ruta=partes.path,
                          consulta={k: v[-1] for k, v in parse_qs(partes.query).items()},
                          headers={k.lower(): v for k, v in self.headers.items()}, cuerpo=cuerpo)
            codigo, respuesta = cobra._atender(pedido)
            datos = json.dumps(respuesta).encode()
            self.send_response(codigo)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(datos)))
            self.end_headers()
            self.wfile.write(datos)

        def log_message(self, *args):
            pass

    return Manejador

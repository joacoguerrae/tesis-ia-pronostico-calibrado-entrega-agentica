"""Servicio de beneficios falso para los tests de T08.

Es un servidor HTTP de verdad en 127.0.0.1, en un puerto libre y en un hilo aparte. Como el servicio real, pide la
clave en `X-Api-Key` y decodifica el path como un formulario: un `+` sin codificar le llega como espacio. Anota cada
pedido que recibe.
"""
import json
import threading
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote_plus, urlsplit

CLAVE = 'clave-beneficios'


@dataclass
class Pedido:
    metodo: str
    ruta: str
    empresa: str | None
    email: str | None
    clave: str | None


class ServicioBeneficios:
    def __init__(self, clave=CLAVE):
        self.clave = clave
        self.empresas = {}
        self.fallas = {}
        self.pedidos = []
        servicio = self

        class Manejador(BaseHTTPRequestHandler):
            def atender(self):
                servicio._atender(self)

            do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = atender

            def log_message(self, *args):
                pass

        self._servidor = ThreadingHTTPServer(('127.0.0.1', 0), Manejador)
        self._hilo = threading.Thread(target=self._servidor.serve_forever, kwargs={'poll_interval': 0.01},
                                      daemon=True)
        self._hilo.start()
        self._prendido = True

    @property
    def url(self):
        host, puerto = self._servidor.server_address[:2]
        return f'http://{host}:{puerto}'

    def empleado(self, empresa, email, activo=True):
        self.empresas.setdefault(empresa, {})[email] = activo

    def olvidar(self, empresa, email):
        del self.empresas[empresa][email]

    def cerrar(self, empresa):
        del self.empresas[empresa]

    def fallar(self, codigo=500, email=None):
        """Desde ahora responde `codigo` a todo o, si se pasa `email`, solo a ese email. Con None vuelve a andar."""
        if codigo is None:
            self.fallas.pop(email, None)
        else:
            self.fallas[email] = codigo

    def apagar(self):
        """Cierra el puerto: desde ahora las conexiones se rechazan."""
        if self._prendido:
            self._servidor.shutdown()
            self._servidor.server_close()
            self._hilo.join()
            self._prendido = False

    def _atender(self, http):
        partes = urlsplit(http.path).path.split('/')
        empresa = email = None
        if len(partes) == 5 and partes[:2] == ['', 'empresas'] and partes[3] == 'empleados':
            empresa, email = unquote_plus(partes[2]), unquote_plus(partes[4])
        clave = http.headers.get('X-Api-Key')
        self.pedidos.append(Pedido(http.command, http.path, empresa, email, clave))
        if http.command != 'GET':
            return self._json(http, 405, {'error': 'metodo_no_permitido'})
        if clave != self.clave:
            return self._json(http, 401, {'error': 'clave_invalida'})
        falla = self.fallas.get(email) or self.fallas.get(None)
        if falla:
            return self._responder(http, falla, b'Servicio no disponible', 'text/plain')
        if empresa is None:
            return self._json(http, 404, {'error': 'ruta_desconocida'})
        if empresa not in self.empresas:
            return self._json(http, 404, {'error': 'empresa_desconocida'})
        if email not in self.empresas[empresa]:
            return self._json(http, 404, {'error': 'empleado_desconocido'})
        return self._json(http, 200, {'activo': self.empresas[empresa][email]})

    def _json(self, http, codigo, cuerpo):
        self._responder(http, codigo, json.dumps(cuerpo).encode(), 'application/json')

    @staticmethod
    def _responder(http, codigo, datos, tipo):
        http.send_response(codigo)
        http.send_header('Content-Type', tipo)
        http.send_header('Content-Length', str(len(datos)))
        http.end_headers()
        http.wfile.write(datos)

"""Comprueba que cada tarea está bien armada.

- Los tests de aceptación fallan sobre la app base (si no, la tarea ya estaría resuelta).
- Pasan todos con la solución de referencia (si no, los tests piden algo imposible o mal escrito).
- La solución de referencia no rompe los tests propios de la app.
- Si la tarea trae un estado inicial propio (tareas/Txx/inicial/, por ejemplo un bug plantado), "la base" es la app
  con ese estado encima, y los tests propios de la app también tienen que pasar ahí: el agente arranca de una app
  cuyos tests están en verde.

Uso: python verificar.py [tarea ...]
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from evaluar import BANCO, TAREAS, evaluar


def copiar_app(destino, tarea, con_solucion=False):
    """La app como la recibe el agente (la base, con el estado inicial de la tarea si trae uno) y, si se pide,
    con la solución de referencia encima."""
    shutil.copytree(BANCO / 'app', destino, ignore=shutil.ignore_patterns('__pycache__', '*.db'))
    capas = [TAREAS / tarea / 'inicial'] + ([TAREAS / tarea / 'solucion'] if con_solucion else [])
    for capa in capas:
        if capa.exists():
            shutil.copytree(capa, destino, dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__'))
    return destino


def tests_propios(trabajo):
    proceso = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider'],
                             cwd=trabajo, capture_output=True, text=True)
    return proceso.returncode == 0


tareas = sys.argv[1:] or sorted(p.name for p in TAREAS.iterdir() if p.name.startswith('T'))
bien = True
for tarea in tareas:
    with tempfile.TemporaryDirectory() as tmp:
        inicio = copiar_app(Path(tmp) / 'base', tarea)
        base = evaluar(tarea, inicio)
        propios_inicio = tests_propios(inicio)
        trabajo = copiar_app(Path(tmp) / 'solucion', tarea, con_solucion=True)
        solucion = evaluar(tarea, trabajo)
        propios = tests_propios(trabajo) and propios_inicio
    ok = not base['exito'] and solucion['exito'] and propios
    bien &= ok
    print(f"{'ok   ' if ok else 'FALLA'} {tarea}: base {base['pasados']}/{base['tests']}, "
          f"solución {solucion['pasados']}/{solucion['tests']}, tests propios {'pasan' if propios else 'fallan'}")
    if base['pasados']:
        print('      pasan sobre la base:', base['pasaron'])
    if not solucion['exito']:
        print('      fallan con la solución:', solucion['fallidos'] or solucion.get('salida'))
sys.exit(0 if bien else 1)

"""Comprueba que cada tarea está bien armada.

- Los tests de aceptación fallan sobre la app base (si no, la tarea ya estaría resuelta).
- Pasan todos con la solución de referencia (si no, los tests piden algo imposible o mal escrito).
- La solución de referencia no rompe los tests propios de la app.

Uso: python verificar.py [tarea ...]
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from evaluar import BANCO, TAREAS, evaluar


def copiar_app(destino, solucion=None):
    shutil.copytree(BANCO / 'app', destino, ignore=shutil.ignore_patterns('__pycache__', '*.db'))
    if solucion:
        shutil.copytree(solucion, destino, dirs_exist_ok=True)
    return destino


def tests_propios(trabajo):
    proceso = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider'],
                             cwd=trabajo, capture_output=True, text=True)
    return proceso.returncode == 0


tareas = sys.argv[1:] or sorted(p.name for p in TAREAS.iterdir() if p.name.startswith('T'))
bien = True
for tarea in tareas:
    with tempfile.TemporaryDirectory() as tmp:
        base = evaluar(tarea, copiar_app(Path(tmp) / 'base'))
        trabajo = copiar_app(Path(tmp) / 'solucion', TAREAS / tarea / 'solucion')
        solucion = evaluar(tarea, trabajo)
        propios = tests_propios(trabajo)
    ok = not base['exito'] and solucion['exito'] and propios
    bien &= ok
    print(f"{'ok   ' if ok else 'FALLA'} {tarea}: base {base['pasados']}/{base['tests']}, "
          f"solución {solucion['pasados']}/{solucion['tests']}, tests propios {'pasan' if propios else 'fallan'}")
    if base['pasados']:
        print('      pasan sobre la base:', base['pasaron'])
    if not solucion['exito']:
        print('      fallan con la solución:', solucion['fallidos'] or solucion.get('salida'))
sys.exit(0 if bien else 1)

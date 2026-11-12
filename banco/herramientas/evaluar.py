"""Corre los tests de aceptación de una tarea sobre un directorio de trabajo.

Los tests se copian recién al evaluar y se borran después, así el agente nunca los ve.

Uso: python evaluar.py T01-cancelar-reserva /ruta/al/repo
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

BANCO = Path(__file__).resolve().parent.parent
TAREAS = BANCO / 'tareas'


def evaluar(tarea, trabajo, python=sys.executable):
    trabajo = Path(trabajo)
    destino = trabajo / '_aceptacion'
    shutil.rmtree(destino, ignore_errors=True)
    shutil.copytree(TAREAS / '_comun', destino)
    shutil.copytree(TAREAS / tarea / 'aceptacion', destino, dirs_exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        informe = Path(tmp) / 'junit.xml'
        proceso = subprocess.run(
            [python, '-m', 'pytest', '_aceptacion', '-q', '-p', 'no:cacheprovider', f'--junitxml={informe}'],
            cwd=trabajo, capture_output=True, text=True, timeout=600,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
        shutil.rmtree(destino)
        if not informe.exists():
            return dict(tarea=tarea, tests=0, pasados=0, exito=False, pasaron=[], fallidos=[],
                        salida=(proceso.stdout + proceso.stderr)[-2000:])
        raiz = ET.parse(informe).getroot()
    suite = raiz if raiz.tag == 'testsuite' else raiz.find('testsuite')
    fallidos = [c.get('name') for c in suite.iter('testcase')
                if c.find('failure') is not None or c.find('error') is not None]
    pasaron = [c.get('name') for c in suite.iter('testcase')
               if c.get('name') not in fallidos and c.find('skipped') is None]
    tests = int(suite.get('tests'))
    return dict(tarea=tarea, tests=tests, pasados=len(pasaron), exito=tests > 0 and len(pasaron) == tests,
                pasaron=pasaron, fallidos=fallidos)


if __name__ == '__main__':
    print(json.dumps(evaluar(sys.argv[1], sys.argv[2]), ensure_ascii=False, indent=2))

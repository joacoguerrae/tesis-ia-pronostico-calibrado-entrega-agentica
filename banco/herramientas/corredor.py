"""Corredor de experimentos: lanza Claude Code sobre cada tarea, con cada versión, k veces, y guarda todo.

Uso:
  python corredor.py experimentos/piloto.json             corre lo que falta del experimento
  python corredor.py experimentos/piloto.json --plan      solo muestra el orden de las corridas
  python corredor.py experimentos/prueba.json --claude "python herramientas/pruebas/claude_falso.py"

Usa la versión de Claude Code fijada en package.json (npm install en banco/), o la del sistema si no
está instalada. Necesita la clave de la tesis en ANTHROPIC_API_KEY. Claude Code corre en modo --bare, que no lee
la configuración de ~/.claude (ni CLAUDE.md, ni hooks, ni MCP, ni otras claves), así el entorno es
el mismo en cada corrida y en cada máquina.

Cada corrida queda en corridas/<experimento>/<id>/:
  corrida.json     qué se corrió, cuándo, con qué versión de Claude Code y cómo terminó
  stream.jsonl     la salida stream-json de Claude Code
  otel.jsonl       los eventos de telemetría: una llamada al modelo o un uso de herramienta por línea
  trazas.jsonl     los tramos de la traza (beta): el pedido, cada llamada al modelo y cada herramienta
  cambios.patch    el diff que dejó el agente
  evaluacion.json  el resultado de los tests de aceptación
"""
import argparse
import json
import os
import random
import secrets
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from evaluar import BANCO, TAREAS, evaluar
from otel import Receptor

PYTHON_BANCO = BANCO / '.venv' / 'bin' / 'python'
CLAUDE_BANCO = BANCO / 'node_modules' / '.bin' / 'claude'
GIT = ['git', '-c', 'user.name=banco', '-c', 'user.email=banco@example.com']


def leer(ruta):
    return json.loads(Path(ruta).read_text())


def armar_plan(experimento):
    """Una ronda por repetición. Dentro de cada ronda van todas las combinaciones de tarea y versión
    en orden al azar, así las versiones quedan intercaladas en el tiempo."""
    azar = random.Random(experimento['semilla'])
    plan = []
    for r in range(1, experimento['repeticiones'] + 1):
        ronda = [(t, v) for t in experimento['tareas'] for v in experimento['versiones']]
        azar.shuffle(ronda)
        plan += [dict(id=f'{t[:3]}-{v}-{r:02d}', tarea=t, version=v, repeticion=r) for t, v in ronda]
    return [dict(c, orden=i + 1) for i, c in enumerate(plan)]


def preparar_repo(destino):
    shutil.copytree(BANCO / 'app', destino, ignore=shutil.ignore_patterns('__pycache__', '*.db'))
    subprocess.run([*GIT, 'init', '-q'], cwd=destino, check=True)
    subprocess.run([*GIT, 'add', '-A'], cwd=destino, check=True)
    subprocess.run([*GIT, 'commit', '-qm', 'Estado inicial'], cwd=destino, check=True)


def comando(claude, version, prompt):
    c = [*claude, '-p', prompt, '--bare', '--output-format', 'stream-json', '--verbose',
         '--model', version['modelo'], '--permission-mode', 'dontAsk', '--no-session-persistence']
    if version.get('esfuerzo'):
        c += ['--effort', version['esfuerzo']]
    if version.get('prompt_sistema_extra'):
        c += ['--append-system-prompt', version['prompt_sistema_extra']]
    if version.get('presupuesto_usd'):
        c += ['--max-budget-usd', str(version['presupuesto_usd'])]
    if version.get('max_turnos'):
        c += ['--max-turns', str(version['max_turnos'])]
    if version.get('herramientas'):
        c += ['--tools', ','.join(version['herramientas'])]
    return c + ['--allowedTools', ','.join(version['permitidas'])]


def entorno(receptor, traza):
    # Nada de la sesión de Claude Code que lanza esto, ni otras credenciales o proxies de Anthropic.
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(('CLAUDE', 'ANTHROPIC_', 'OTEL_', 'TRACE')) or k == 'ANTHROPIC_API_KEY'}
    env.update(
        PATH=f'{PYTHON_BANCO.parent}{os.pathsep}{env["PATH"]}', VIRTUAL_ENV=str(PYTHON_BANCO.parent.parent),
        CLAUDE_CODE_ENABLE_TELEMETRY='1', OTEL_LOGS_EXPORTER='otlp', OTEL_METRICS_EXPORTER='none',
        OTEL_EXPORTER_OTLP_PROTOCOL='http/json', OTEL_EXPORTER_OTLP_ENDPOINT=receptor.url,
        OTEL_LOGS_EXPORT_INTERVAL='1000', OTEL_LOG_TOOL_DETAILS='1', DISABLE_AUTOUPDATER='1',
        # Trazas (beta). Con TRACEPARENT, en modo -p la traza de la corrida usa el id que le damos y
        # cada evento lleva ese mismo id, así eventos y tramos se cruzan con la corrida.
        CLAUDE_CODE_ENHANCED_TELEMETRY_BETA='1', OTEL_TRACES_EXPORTER='otlp', OTEL_TRACES_EXPORT_INTERVAL='1000',
        TRACEPARENT=f'00-{traza}-{secrets.token_hex(8)}-01',
        NO_PROXY='127.0.0.1,localhost', no_proxy='127.0.0.1,localhost')
    return env


def ejecutar(c, cwd, env, salida, errores, limite_s):
    with open(salida, 'w') as out, open(errores, 'w') as err:
        proceso = subprocess.Popen(c, cwd=cwd, env=env, stdout=out, stderr=err, stdin=subprocess.DEVNULL)
        try:
            return proceso.wait(timeout=limite_s), 'ok'
        except subprocess.TimeoutExpired:
            proceso.send_signal(signal.SIGINT)
            try:
                return proceso.wait(timeout=30), 'tiempo agotado'
            except subprocess.TimeoutExpired:
                proceso.kill()
                return proceso.wait(), 'tiempo agotado'


def correr(c_plan, experimento, versiones, claude, version_claude, receptor, carpeta, conservar):
    version = versiones[c_plan['version']]
    destino = carpeta / c_plan['id']
    shutil.rmtree(destino, ignore_errors=True)
    destino.mkdir(parents=True)
    trabajo = Path(tempfile.mkdtemp(prefix=f"banco-{c_plan['id']}-"))
    repo = trabajo / 'repo'
    preparar_repo(repo)
    pedido = (TAREAS / c_plan['tarea'] / 'pedido.md').read_text()
    prompt = (BANCO / version['plantilla']).read_text().replace('{pedido}', pedido)
    c = comando(claude, version, prompt)

    receptor.vaciar()
    traza = secrets.token_hex(16)
    inicio = datetime.now(timezone.utc)
    t0 = time.monotonic()
    codigo, termino = ejecutar(c, repo, entorno(receptor, traza), destino / 'stream.jsonl', destino / 'stderr.txt',
                               version.get('limite_min', 20) * 60)
    duracion = time.monotonic() - t0
    time.sleep(2)  # los últimos eventos de telemetría llegan después de que el proceso termina
    eventos, tramos = receptor.vaciar()
    (destino / 'otel.jsonl').write_text(''.join(json.dumps(e, ensure_ascii=False) + '\n' for e in eventos))
    (destino / 'trazas.jsonl').write_text(''.join(json.dumps(t, ensure_ascii=False) + '\n' for t in tramos))

    subprocess.run([*GIT, 'add', '-A'], cwd=repo, check=True)
    cambios = subprocess.run([*GIT, 'diff', '--cached', '--binary'], cwd=repo, capture_output=True, text=True).stdout
    (destino / 'cambios.patch').write_text(cambios)
    evaluacion = evaluar(c_plan['tarea'], repo, python=str(PYTHON_BANCO))
    (destino / 'evaluacion.json').write_text(json.dumps(evaluacion, ensure_ascii=False, indent=2))

    stream = (destino / 'stream.jsonl').read_text()
    inicio_sesion = next((json.loads(l) for l in stream.splitlines()
                          if l.startswith('{') and json.loads(l).get('subtype') == 'init'), {})
    meta = dict(c_plan, experimento=experimento['nombre'], inicio=inicio.isoformat(),
                fin=datetime.now(timezone.utc).isoformat(), duracion_s=round(duracion, 1),
                codigo_salida=codigo, termino=termino, claude_code=version_claude,
                version_config=version, prompt=prompt, comando=[*c[:len(claude) + 1], '<prompt>', *c[len(claude) + 2:]],
                eventos_otel=len(eventos), tramos_otel=len(tramos), traza_id=traza,
                tramos_de_otra_traza=sum(t['_traza'] != traza for t in tramos),
                fuente_clave=inicio_sesion.get('apiKeySource'),
                toco_banco=str(TAREAS) in stream or '/tareas/T0' in stream)
    (destino / 'corrida.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    if not conservar:
        shutil.rmtree(trabajo)
    return meta, evaluacion


def main():
    p = argparse.ArgumentParser()
    p.add_argument('experimento')
    p.add_argument('--plan', action='store_true', help='solo muestra el orden de las corridas')
    p.add_argument('--claude', default=shlex.quote(str(CLAUDE_BANCO)) if CLAUDE_BANCO.exists() else 'claude',
                   help='comando de Claude Code (o uno falso para probar)')
    p.add_argument('--conservar-repos', action='store_true', help='no borra el repo de cada corrida')
    args = p.parse_args()

    experimento = leer(args.experimento)
    plan = armar_plan(experimento)
    if args.plan:
        for c in plan:
            print(f"{c['orden']:>3} {c['id']}")
        return
    # Las rutas relativas del comando se fijan acá, porque Claude Code corre dentro del repo de cada corrida.
    claude = [os.path.abspath(t) if os.path.exists(t) else t for t in shlex.split(args.claude)]
    if 'ANTHROPIC_API_KEY' not in os.environ and 'claude_falso' not in args.claude:
        sys.exit('Falta ANTHROPIC_API_KEY con la clave de la tesis. No se usa ninguna otra credencial.')

    versiones = {v: leer(BANCO / 'versiones' / f'{v}.json') for v in experimento['versiones']}
    carpeta = BANCO / 'corridas' / experimento['nombre']
    carpeta.mkdir(parents=True, exist_ok=True)
    plan_json = json.dumps(dict(experimento=experimento, plan=plan), ensure_ascii=False, indent=2)
    (carpeta / 'plan.json').write_text(plan_json)
    version_claude = subprocess.run([*claude, '--version'], capture_output=True, text=True).stdout.strip()
    pendientes = [c for c in plan if not (carpeta / c['id'] / 'corrida.json').exists()]
    print(f"{experimento['nombre']}: {len(plan)} corridas, faltan {len(pendientes)}. Claude Code {version_claude}.")

    receptor = Receptor()
    try:
        for c in pendientes:
            meta, ev = correr(c, experimento, versiones, claude, version_claude, receptor, carpeta,
                              args.conservar_repos)
            if 'helper' in str(meta['fuente_clave']).lower():
                sys.exit(f"La corrida usó la clave de {meta['fuente_clave']}, no la de ANTHROPIC_API_KEY. "
                         'Se corta acá.')
            aviso = ' ¡TOCÓ EL BANCO!' if meta['toco_banco'] else ''
            print(f"[{c['orden']}/{len(plan)}] {c['id']}: {ev['pasados']}/{ev['tests']} tests, "
                  f"{meta['duracion_s']:.0f} s, {meta['termino']}, {meta['eventos_otel']} eventos, "
                  f"{meta['tramos_otel']} tramos{aviso}", flush=True)
    finally:
        receptor.cerrar()


if __name__ == '__main__':
    main()

"""Generador de facts, versión 0.

Compara dos versiones sobre las mismas tareas. Para cada métrica calcula la
diferencia por tarea, la promedia entre tareas y la clasifica en uno de tres
estados:
- diferencia: el test pareado rechaza "no hay diferencia" después de corregir
  por Benjamini-Hochberg entre las métricas del informe;
- equivalencia: no hay diferencia y el IC 90 % cae entero dentro del margen
  (equivale a un TOST con alfa 0,05);
- no concluyente: ninguna de las dos.
El texto de cada fact se arma con plantillas a partir de los valores calculados.
"""
import numpy as np
import pandas as pd
from scipy import stats

from formato import METRICAS

ALFA = 0.05
# 5 puntos de éxito; 10 % en las métricas en escala log.
MARGEN = {'proporcion': 0.05, 'log': np.log(1.10)}

# Nombre de cada métrica en el texto y si va en plural.
NOMBRES = {
    'exito': ('la tasa de éxito', False),
    'costo_usd': ('el costo', False),
    'tokens_entrada': ('los tokens de entrada', True),
    'tokens_salida': ('los tokens de salida', True),
    'pasos': ('los pasos', True),
    'duracion_s': ('la duración', False),
}


def diferencias_por_tarea(df, a, b):
    x = df[df.version.isin([a, b])].copy()
    for m, tipo in METRICAS.items():
        if tipo == 'log':
            x[m] = np.log(x[m].where(x[m] > 0))
    medias = x.groupby(['tarea', 'version'])[list(METRICAS)].mean().unstack('version')
    return pd.DataFrame({m: medias[m][b] - medias[m][a] for m in METRICAS})


def comparar(df, a, b, alfa=ALFA):
    d = diferencias_por_tarea(df, a, b)
    filas = []
    for m, tipo in METRICAS.items():
        x = d[m].dropna()
        n = len(x)
        efecto, ee = x.mean(), x.std() / np.sqrt(n)
        t = stats.t(n - 1)
        filas.append(dict(
            metrica=m, tipo=tipo, n_tareas=n, efecto=efecto,
            ic_inf=efecto - t.ppf(1 - alfa / 2) * ee, ic_sup=efecto + t.ppf(1 - alfa / 2) * ee,
            ic90_inf=efecto - t.ppf(1 - alfa) * ee, ic90_sup=efecto + t.ppf(1 - alfa) * ee,
            # Si todas las tareas dan la misma diferencia (pasa con el éxito y pocas tareas), el IC colapsa.
            p=2 * t.sf(abs(efecto) / ee) if ee > 0 else float(efecto == 0),
        ))
    facts = pd.DataFrame(filas)
    facts['q'] = stats.false_discovery_control(facts.p)
    margen = facts.tipo.map(MARGEN)
    equivalente = (facts.ic90_inf > -margen) & (facts.ic90_sup < margen)
    facts['estado'] = np.select([facts.q < alfa, equivalente], ['diferencia', 'equivalencia'], 'no concluyente')
    facts['texto'] = [redactar(f, a, b) for f in facts.itertuples()]
    return facts


def _valor(f, v, signo=True):
    v = (np.exp(v) - 1) * 100 if f.tipo == 'log' else v * 100
    texto = f'{v:+.0f}' if f.tipo == 'log' else f'{v:+.1f}'.replace('.', ',')
    return texto if signo else texto.lstrip('+-')


def redactar(f, a, b):
    nombre, plural = NOMBRES[f.metrica]
    n = 'n' if plural else ''
    unidad = ' %' if f.tipo == 'log' else ' puntos'
    if f.estado == 'diferencia':
        verbo = 'sube' if f.efecto > 0 else 'baja'
        return (f'De {a} a {b}, {nombre} {verbo}{n} {_valor(f, f.efecto, signo=False)}{unidad} '
                f'(IC 95 %: de {_valor(f, f.ic_inf)} a {_valor(f, f.ic_sup)}{unidad}; {f.n_tareas} tareas).')
    if f.estado == 'equivalencia':
        margen = '10 %' if f.tipo == 'log' else '5 puntos'
        verbo = 'son equivalentes' if plural else 'es equivalente'
        return (f'{nombre[0].upper() + nombre[1:]} {verbo} entre {a} y {b}: la diferencia queda dentro de '
                f'±{margen} (IC 90 %: de {_valor(f, f.ic90_inf)} a {_valor(f, f.ic90_sup)}{unidad}; '
                f'{f.n_tareas} tareas).')
    return (f'No se puede concluir si {nombre} cambia{n} de {a} a {b} '
            f'(IC 95 %: de {_valor(f, f.ic_inf)} a {_valor(f, f.ic_sup)}{unidad}; {f.n_tareas} tareas).')

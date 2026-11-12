"""Métodos que se usan hoy, para comparar contra el generador."""
from functools import lru_cache

import numpy as np
import pandas as pd
from scipy import stats

from formato import METRICAS


def diferencia_de_medias(df, a, b):
    """Lo que muestran las plataformas: el promedio de cada versión, sin inferencia.

    Se toma como fact de diferencia todo cambio que supere el mismo margen que usa
    el generador (10 % relativo, o 5 puntos de éxito).
    """
    medias = df[df.version.isin([a, b])].groupby('version')[list(METRICAS)].mean()
    filas = []
    for m, tipo in METRICAS.items():
        if tipo == 'log':
            efecto = medias.loc[b, m] / medias.loc[a, m] - 1
            margen = 0.10
        else:
            efecto = medias.loc[b, m] - medias.loc[a, m]
            margen = 0.05
        filas.append(dict(metrica=m, efecto=efecto,
                          estado='diferencia' if abs(efecto) >= margen else 'sin cambio'))
    return pd.DataFrame(filas)


@lru_cache(maxsize=None)
def _fisher(exitos_a, n_a, exitos_b, n_b):
    return stats.fisher_exact([[exitos_b, n_b - exitos_b], [exitos_a, n_a - exitos_a]]).pvalue


def _mann_whitney(va, vb):
    """Un p por fila. scipy usa el cálculo exacto solo si la fila no tiene empates, así que las filas
    con y sin empates van por separado para dar lo mismo que llamarlo fila por fila."""
    p = np.empty(len(va))
    empates = np.array([len(np.unique(f)) < len(f) for f in np.hstack([va, vb])])
    for e in (False, True):
        if (empates == e).any():
            p[empates == e] = stats.mannwhitneyu(va[empates == e], vb[empates == e], axis=1).pvalue
    return p


def agentrial(df, a, b, alfa=0.05):
    """Los tests de `agentrial snapshot check`, reimplementados a partir de su código
    (alepot55/agentrial, commit 0c8ef03, archivo agentrial/snapshots.py).

    Cada tarea se compara por separado: test exacto de Fisher en el éxito y Mann-Whitney en el
    costo y la duración. La corrección de Benjamini-Hochberg va entre todos los tests de todas las
    tareas. Como en agentrial, el éxito informa subas y bajas, y las demás métricas solo subas, que
    son las regresiones. agentrial no testea los tokens ni los pasos; acá se tratan como el costo.

    El informe tiene un fact por métrica: diferencia si al menos una tarea muestra un cambio. El
    efecto es el signo de esos cambios, o 0 si hay tareas que cambian en sentidos opuestos.
    """
    x = df[df.version.isin([a, b])]
    pruebas = []
    for m, tipo in METRICAS.items():
        valores = x.dropna(subset=[m]).groupby(['tarea', 'version'])[m].apply(np.array).unstack('version').dropna()
        tamanos = valores.map(len)
        for (n_a, n_b), g in valores.groupby([tamanos[a], tamanos[b]]):
            va, vb = np.stack(g[a].to_list()), np.stack(g[b].to_list())
            if tipo == 'proporcion':
                p = [_fisher(int(sa), n_a, int(sb), n_b) for sa, sb in zip(va.sum(axis=1), vb.sum(axis=1))]
            else:
                p = _mann_whitney(va, vb)
            pruebas += [dict(metrica=m, p=pi, delta=d) for pi, d in zip(p, vb.mean(axis=1) - va.mean(axis=1))]
    pruebas = pd.DataFrame(pruebas)
    pruebas['q'] = stats.false_discovery_control(pruebas.p.fillna(1))
    informa = (pruebas.q < alfa) & ((pruebas.delta > 0) | ((pruebas.metrica == 'exito') & (pruebas.delta < 0)))
    filas = []
    for m in METRICAS:
        signos = np.sign(pruebas.delta[informa & (pruebas.metrica == m)])
        filas.append(dict(metrica=m, tareas=len(signos),
                          estado='diferencia' if len(signos) else 'sin cambio',
                          efecto=signos.iloc[0] if len(signos) and (signos == signos.iloc[0]).all() else 0.0))
    return pd.DataFrame(filas)

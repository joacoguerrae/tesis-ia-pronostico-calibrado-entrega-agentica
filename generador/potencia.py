"""Potencia del test del generador y menor efecto que detecta.

La diferencia por tarea entre dos versiones con r corridas cada una tiene
varianza  s_tau^2 + 2 s_eps^2 / r,  donde s_eps es el ruido entre corridas de
la misma versión y tarea, y s_tau es cuánto varía el efecto real de una tarea a
otra. El promedio sobre n tareas divide esa varianza por n. Con eso se calcula
la potencia del test del generador, incluida la corrección de Benjamini-Hochberg
entre las seis métricas, y el menor efecto que se detecta en el 80 % de los casos.
"""
import numpy as np
import pandas as pd
from scipy import stats

from formato import METRICAS
from generador import ALFA

POTENCIA = 0.8
SIMULACIONES = 20000


def sorteos(n, rng):
    """Números al azar fijos por cantidad de tareas, para que la potencia sea monótona en el efecto."""
    return (rng.standard_normal(SIMULACIONES), rng.chisquare(n - 1, SIMULACIONES),
            rng.random((SIMULACIONES, len(METRICAS) - 1)))


def potencia(efecto, desvio, n, azar):
    """Probabilidad de que el generador marque diferencia, con el signo correcto, en la métrica con efecto."""
    z, chi2, p_nulas = azar
    t = (z + efecto / (desvio / np.sqrt(n))) / np.sqrt(chi2 / (n - 1))
    p = np.column_stack([2 * stats.t(n - 1).sf(np.abs(t)), p_nulas])
    rechaza = stats.false_discovery_control(p, axis=1)[:, 0] <= ALFA
    return np.mean(rechaza & (t > 0))


def efecto_minimo(desvio, n, azar):
    """Menor efecto con potencia de al menos 80 %, por bisección."""
    bajo, alto = 0.0, 10 * desvio / np.sqrt(n)
    for _ in range(40):
        medio = (bajo + alto) / 2
        bajo, alto = (medio, alto) if potencia(medio, desvio, n, azar) < POTENCIA else (bajo, medio)
    return alto


def en_unidades(m, v):
    return f'{(np.exp(v) - 1) * 100:.0f} %' if METRICAS[m] == 'log' else f'{v * 100:.0f} pts'


def menor_efecto_por_diseno(eps, tau, tareas, repeticiones, azar):
    """Menor efecto detectable de cada métrica según la cantidad de tareas y de corridas por versión.

    eps es el ruido entre corridas y tau, la variación del efecto entre tareas. Se calcula con el
    efecto parejo entre tareas (tau = 0) y con el efecto variable.
    """
    filas = []
    for escenario, het in [('efecto parejo', 0 * tau), ('efecto variable', tau)]:
        for n in tareas:
            for r in repeticiones:
                fila = dict(escenario=escenario, tareas=n, repeticiones=r, corridas=2 * n * r)
                for m in METRICAS:
                    fila[m] = en_unidades(m, efecto_minimo(np.sqrt(het[m] ** 2 + 2 * eps[m] ** 2 / r), n, azar[n]))
                filas.append(fila)
    return pd.DataFrame(filas)

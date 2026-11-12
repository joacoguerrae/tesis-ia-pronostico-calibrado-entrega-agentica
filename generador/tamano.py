"""Cuántas tareas y repeticiones hacen falta, con el ruido medido en DeepSWE.

Usa la fórmula de potencia.py: valida sus predicciones contra los efectos
plantados de aa_deepswe.py y calcula el menor efecto detectable según la
cantidad de tareas y de repeticiones.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

import deepswe
from formato import METRICAS
from potencia import menor_efecto_por_diseno, potencia, sorteos

SALIDA = Path(__file__).parent / 'resultados'
TAREAS = [10, 15, 20, 30, 50]
REPETICIONES = [2, 3, 5, 10]
ESFUERZOS = ['low', 'medium', 'high', 'xhigh', 'max']

rng = np.random.default_rng(2026)


def validar_formula(df, ruido, plantados, azar):
    """Detección predicha contra la observada en los efectos plantados de aa_deepswe.py (2 contra 2).

    En las métricas positivas el efecto plantado es parejo. En el éxito no: se convierte una fracción q
    de los éxitos (o de las fallas) de cada tarea, así que el efecto de la tarea es q por su tasa y
    varía entre tareas con varianza q^2 por la varianza de las tasas, que es el s_tau^2 de la fórmula.
    """
    tasas = df.groupby(['version', 'tarea']).exito.mean()
    tasa_media = tasas.groupby('version').mean()
    var_tasas = (tasas.groupby('version').var() - ruido.exito / 4).clip(lower=0)
    observado = (plantados[plantados.metrica == plantados.plantada]
                 .assign(detectado=lambda x: (x.estado == 'diferencia') & ~x.falso)
                 .groupby(['n_tareas', 'plantada', 'tamano']).detectado.mean())
    filas = []
    for (n_tareas, m, tamano), obs in observado.items():
        n = df.tarea.nunique() if n_tareas == 'todas' else int(n_tareas)
        if METRICAS[m] == 'log':
            efecto, tau2 = np.log1p(tamano), 0 * ruido[m]
        else:
            efecto, tau2 = tamano, (tamano / np.maximum(tasa_media, 1 - tasa_media)) ** 2 * var_tasas
        predicho = np.mean([potencia(efecto, np.sqrt(s2 + t2), n, azar[n]) for s2, t2 in zip(ruido[m], tau2)])
        filas.append(dict(n_tareas=n_tareas, metrica=m, tamano=tamano, observado=obs, predicho=predicho))
    return pd.DataFrame(filas)


def variacion_entre_tareas(df, ruido):
    """Cuánto varía el efecto real entre tareas, en pares de esfuerzo contiguo del mismo modelo (4 contra 4)."""
    medias = df.groupby(['version', 'tarea'])[list(METRICAS)].mean()
    info = df.drop_duplicates('version').set_index('version')
    filas = []
    for modelo, g in info[info.esfuerzo.isin(ESFUERZOS)].groupby('modelo'):
        g = g.sort_values('esfuerzo', key=lambda e: e.map(ESFUERZOS.index))
        for a, b in zip(g.index[:-1], g.index[1:]):
            d = (medias.loc[b] - medias.loc[a]).dropna()
            tau2 = d.var() - (ruido.loc[a] + ruido.loc[b]) / 4
            filas.append(dict(modelo=modelo, a=info.esfuerzo[a], b=info.esfuerzo[b],
                              **{f'efecto_{m}': d[m].mean() for m in METRICAS},
                              **{f'tau_{m}': np.sqrt(max(tau2[m], 0)) for m in METRICAS}))
    return pd.DataFrame(filas)


def precision_del_piloto():
    """Con qué precisión estima el ruido un piloto de una sola versión, según tareas y repeticiones."""
    filas = []
    for n, r in [(3, 10), (5, 6), (5, 10), (8, 6), (10, 5), (10, 10)]:
        gl = n * (r - 1)
        bajo, alto = np.sqrt(gl / stats.chi2(gl).ppf(0.975)), np.sqrt(gl / stats.chi2(gl).ppf(0.025))
        filas.append(dict(tareas=n, repeticiones=r, corridas=n * r,
                          ic95_del_ruido=f'{(bajo - 1) * 100:+.0f} % a {(alto - 1) * 100:+.0f} %'))
    return pd.DataFrame(filas)


def main():
    df = deepswe.cargar()
    df = df[df.groupby(['version', 'tarea']).tarea.transform('size') == 4].copy()
    for m, tipo in METRICAS.items():
        if tipo == 'log':
            df[m] = np.log(df[m].where(df[m] > 0))
    # Ruido entre corridas de la misma versión y tarea, promediado entre tareas.
    ruido = df.groupby(['version', 'tarea'])[list(METRICAS)].var().groupby('version').mean()
    azar = {n: sorteos(n, rng) for n in [15, df.tarea.nunique()] + TAREAS}

    validacion = validar_formula(df, ruido, pd.read_csv(SALIDA / 'plantados.csv'), azar)
    pares = variacion_entre_tareas(df, ruido)
    tau = pd.Series({m: pares[f'tau_{m}'].median() for m in METRICAS})
    relativo = pd.Series({m: (pares[f'tau_{m}'] / pares[f'efecto_{m}'].abs()).median() for m in METRICAS})
    error = (validacion.observado - validacion.predicho).abs()

    pd.set_option('display.width', 200)
    resumen = '\n'.join([
        'Ruido entre corridas de la misma versión y tarea '
        '(desvío; en log para las métricas positivas, en proporción para el éxito)',
        np.sqrt(ruido).describe().loc[['25%', '50%', '75%']].round(3).to_string(),
        '',
        'Validación: detección observada en los efectos plantados contra la que predice la fórmula',
        validacion.round(3).to_string(index=False),
        f'Diferencia absoluta media: {error.mean():.3f}',
        'Por métrica: ' + '; '.join(f'{m} {v:.3f}' for m, v in error.groupby(validacion.metrica).mean().items()),
        '',
        f'Variación del efecto real entre tareas, en {len(pares)} pares de esfuerzo contiguo (mediana)',
        pd.DataFrame({'desvio_entre_tareas': tau, 'relativo_al_efecto': relativo}).round(3).to_string(),
        '',
        'Menor efecto detectado en el 80 % de los casos, con el ruido de la configuración mediana',
        '(corridas = total de las dos versiones; efecto variable = como varían entre tareas los cambios de esfuerzo)',
        menor_efecto_por_diseno(np.sqrt(ruido.median()), tau, TAREAS, REPETICIONES, azar).to_string(index=False),
        '',
        'Piloto con una sola versión: intervalo del 95 % del ruido estimado, relativo al real',
        precision_del_piloto().to_string(index=False),
    ]) + '\n'
    (SALIDA / 'tamano.txt').write_text(resumen)
    pares.to_csv(SALIDA / 'pares_esfuerzo.csv', index=False)
    print(resumen, end='')


if __name__ == '__main__':
    main()

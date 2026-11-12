"""Del piloto a la decisión de alcance.

Lee las corridas del piloto (una sola versión, varias corridas por tarea) y calcula:
- si el corredor anduvo bien: corridas cortadas por un tope, sin telemetría o que tocaron el banco;
- la dificultad de cada tarea, con su tasa de éxito y si queda entre 20 % y 80 %;
- el costo y la duración por corrida;
- el ruido entre corridas de cada métrica, con su intervalo del 95 %, junto al de DeepSWE;
- el menor efecto que detectaría el generador con ese ruido, según la cantidad de tareas y de
  corridas por versión, y lo que cuesta cada comparación. El efecto parejo entre tareas es el
  caso optimista, porque el piloto tiene una sola versión; el variable usa la variación medida
  en DeepSWE, que incluye la deriva temporal, y es el pesimista.

Uso: python piloto.py ../banco/corridas/piloto
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

import claude_code
import deepswe
from formato import METRICAS
from potencia import menor_efecto_por_diseno, sorteos

SALIDA = Path(__file__).parent / 'resultados'
DIFICULTAD = (0.2, 0.8)
TAREAS = [10, 15, 20, 30]
REPETICIONES = [3, 5, 10]

rng = np.random.default_rng(2026)


def en_log(df):
    df = df.copy()
    for m, tipo in METRICAS.items():
        if tipo == 'log':
            df[m] = np.log(df[m].where(df[m] > 0))
    return df


def controles(corridas):
    return pd.Series({
        'corridas': len(corridas),
        'tareas': corridas.tarea.nunique(),
        'versiones': corridas.version.nunique(),
        'terminaron con error o en un tope (resultado distinto de success)': (corridas.resultado != 'success').sum(),
        'cortadas por tiempo': (corridas.termino != 'ok').sum(),
        'sin tramos de traza': (corridas.tramos == 0).sum(),
        'tocaron el banco': corridas.toco_banco.sum(),
    })


def ruido(corridas):
    """Desvío entre corridas de la misma tarea: varianza dentro de cada tarea, combinada por grados de libertad."""
    x = en_log(corridas)
    filas = []
    for m in METRICAS:
        g = x.dropna(subset=[m]).groupby('tarea')[m]
        gl = (g.size() - 1).clip(lower=0)
        s2 = (g.var().fillna(0) * gl).sum() / gl.sum()
        bajo, alto = (np.sqrt(s2 * gl.sum() / stats.chi2(gl.sum()).ppf(q)) for q in (0.975, 0.025))
        filas.append(dict(metrica=m, desvio=np.sqrt(s2), ic95=f'{bajo:.3f} a {alto:.3f}', gl=gl.sum()))
    return pd.DataFrame(filas).set_index('metrica')


def ruido_deepswe():
    """El mismo desvío en DeepSWE, como mediana entre configuraciones."""
    d = deepswe.cargar()
    d = en_log(d[d.groupby(['version', 'tarea']).tarea.transform('size') == 4])
    return np.sqrt(d.groupby(['version', 'tarea'])[list(METRICAS)].var().groupby('version').mean()).median()


def main(carpeta):
    corridas, _, _ = claude_code.cargar(carpeta)
    dificultad = corridas.groupby('tarea').agg(corridas=('exito', 'size'), exito=('exito', 'mean'),
                                               costo_medio=('costo_usd', 'mean'),
                                               duracion_media_s=('duracion_s', 'mean'))
    dificultad['informativa'] = dificultad.exito.between(*DIFICULTAD)
    por_corrida = corridas[['costo_usd', 'duracion_s', 'tokens_entrada', 'tokens_salida', 'pasos']].describe()

    desvios = ruido(corridas)
    desvios['deepswe'] = ruido_deepswe()
    pares = pd.read_csv(SALIDA / 'pares_esfuerzo.csv')
    tau = pd.Series({m: pares[f'tau_{m}'].median() for m in METRICAS})
    azar = {n: sorteos(n, rng) for n in TAREAS}
    plan = menor_efecto_por_diseno(desvios.desvio, tau, TAREAS, REPETICIONES, azar)
    plan.insert(4, 'presupuesto_usd', (plan.corridas * corridas.costo_usd.mean()).round())

    pd.set_option('display.width', 200)
    resumen = '\n'.join([
        f'Piloto: {carpeta.name}',
        '',
        'Controles del corredor',
        controles(corridas).to_string(),
        '',
        f'Dificultad por tarea (informativa: éxito entre {DIFICULTAD[0]:.0%} y {DIFICULTAD[1]:.0%})',
        dificultad.round(3).to_string(),
        f'Tareas informativas para el éxito: {dificultad.informativa.sum()} de {len(dificultad)}',
        '',
        'Por corrida (promedio, mediana y máximo)',
        por_corrida.loc[['mean', '50%', 'max']].round(3).to_string(),
        f'Costo total del piloto: {corridas.costo_usd.sum():.2f} dólares',
        '',
        'Ruido entre corridas de la misma tarea (desvío; en log para las métricas positivas, en proporción',
        'para el éxito), con la mediana de las configuraciones de DeepSWE para comparar',
        desvios.round(3).to_string(),
        '',
        'Menor efecto detectado en el 80 % de los casos y costo de una comparación (A y B).',
        'Efecto parejo: optimista; efecto variable: con la variación entre tareas de DeepSWE, pesimista.',
        plan.to_string(index=False),
    ]) + '\n'
    SALIDA.mkdir(exist_ok=True)
    (SALIDA / f'piloto_{carpeta.name}.txt').write_text(resumen)
    print(resumen, end='')


if __name__ == '__main__':
    main(Path(sys.argv[1]))

"""Comparaciones A/A y efectos plantados con los datos públicos de DeepSWE.

Cada configuración de DeepSWE tiene cuatro corridas por tarea. Si se parten en
dos y dos, las mitades son la misma versión (A/A): toda diferencia que se
informe es falsa. Si además a una mitad se le multiplica una métrica por un
factor, el efecto real es exactamente ese factor y se puede ver si se detecta.
En el éxito, que es binario, se convierten al azar éxitos en fallas o fallas en
éxitos; ahí el efecto real se aproxima con la tasa observada (ver plantar).
"""
from pathlib import Path

import numpy as np
import pandas as pd

import deepswe
from formato import METRICAS
from generador import MARGEN, comparar, diferencias_por_tarea
from rivales import agentrial, diferencia_de_medias

SALIDA = Path(__file__).parent / 'resultados'
REPARTOS_AA = 20
REPARTOS_PLANTADOS = 3
TAREAS = [None, 15]  # todas las tareas, o 15 al azar como en el banco propio
# Tamaño de los efectos plantados: cambio relativo en las métricas positivas, puntos en el éxito.
EFECTOS = ([(m, t) for m, tipo in METRICAS.items() if tipo == 'log' for t in [0.05, 0.10, 0.20, 0.30, 0.50]]
           + [('exito', t) for t in [0.05, 0.10, 0.20, 0.30]])

rng = np.random.default_rng(2026)


def partir(x, equilibrado=True):
    """Dos contra dos. Equilibrado: cada mitad lleva una de las dos primeras corridas
    y una de las dos últimas, para que el corte no coincida con el momento de ejecución.
    Si no, las dos primeras contra las dos últimas."""
    x = x.copy()
    if equilibrado:
        tareas = x.tarea.unique()
        socio_de_la_1 = x.tarea.map(dict(zip(tareas, rng.choice([3, 4], len(tareas)))))
        invertir = x.tarea.map(dict(zip(tareas, rng.random(len(tareas)) < 0.5)))
        con_la_1 = (x.repeticion == 1) | (x.repeticion == socio_de_la_1)
        x['version'] = np.where(con_la_1 ^ invertir, 'A', 'B')
    else:
        x['version'] = np.where(x.repeticion <= 2, 'A', 'B')
    return x


def submuestra(x, n_tareas):
    if n_tareas is None:
        return x
    elegidas = rng.choice(x.tarea.unique(), n_tareas, replace=False)
    return x[x.tarea.isin(elegidas)]


def plantar(x, metrica, tamano):
    """Planta un efecto en la mitad B y devuelve las corridas y el efecto real, en la escala del generador.

    En las métricas positivas multiplica por 1 + tamano, y el efecto real es exacto. En el éxito
    convierte éxitos de B en fallas si la tasa es de 50 % o más, y fallas en éxitos si no, con la
    probabilidad que da un cambio esperado de `tamano` puntos. Esa probabilidad sale de la tasa
    observada en las cuatro corridas de cada tarea, porque la verdadera no se conoce, así que el
    efecto real es aproximado (ver error_de_la_verdad).
    """
    x = x.copy()
    if METRICAS[metrica] == 'log':
        x.loc[x.version == 'B', metrica] *= 1 + tamano
        return x, np.log1p(tamano)
    tasa = x.exito.mean()
    origen, signo = (1.0, -1) if tasa >= 0.5 else (0.0, 1)
    cambia = ((x.version == 'B') & (x.exito == origen)
              & (rng.random(len(x)) < tamano / (tasa if origen else 1 - tasa)))
    x.loc[cambia, 'exito'] = 1 - origen
    return x, signo * tamano


def error_de_la_verdad(x):
    """Desvío relativo de la tasa observada como estimación de la verdadera, en un plantado de éxito."""
    tasa = x.exito.mean()
    var_por_tarea = x.groupby('tarea').exito.var()  # el promedio de cuatro corridas tiene varianza var / 4
    return np.sqrt(var_por_tarea.sum() / 4) / x.tarea.nunique() / max(tasa, 1 - tasa)


def es_falso(estado, estimado, real, margen):
    # Los rivales no declaran equivalencia: su "sin cambio" no cuenta como fact.
    if estado == 'diferencia':
        return real == 0 or np.sign(estimado) != np.sign(real)
    if estado == 'equivalencia':
        return abs(real) >= margen
    return False


def evaluar(x, real, **etiquetas):
    """Corre el generador y los dos rivales sobre A contra B y marca cada fact como falso o no."""
    g = comparar(x, 'A', 'B')
    medias = diferencia_de_medias(x, 'A', 'B').set_index('metrica')
    tests = agentrial(x, 'A', 'B').set_index('metrica')
    filas = []
    for f in g.itertuples():
        margen = MARGEN[f.tipo]
        rival, otro = medias.loc[f.metrica], tests.loc[f.metrica]
        efecto_rival = np.log1p(rival.efecto) if f.tipo == 'log' else rival.efecto
        filas.append(dict(
            etiquetas, metrica=f.metrica, real=real[f.metrica], estado=f.estado,
            falso=es_falso(f.estado, f.efecto, real[f.metrica], margen),
            cubre=f.ic_inf <= real[f.metrica] <= f.ic_sup,
            estado_rival=rival.estado,
            falso_rival=es_falso(rival.estado, efecto_rival, real[f.metrica], margen),
            estado_agentrial=otro.estado,
            falso_agentrial=es_falso(otro.estado, otro.efecto, real[f.metrica], margen),
        ))
    return filas


def correr(df):
    """Arma todos los informes. Devuelve las filas A/A, las de los efectos plantados y, por cada
    informe, sus diferencias por tarea (informes × métricas × tareas), que usa intervalos.py."""
    tareas = sorted(df.tarea.unique())
    nulo = {m: 0.0 for m in METRICAS}
    diferencias = []

    def informe(x, real, **etiquetas):
        d = diferencias_por_tarea(x, 'A', 'B').reindex(tareas)[list(METRICAS)].to_numpy('float32').T
        diferencias.append(d)
        return evaluar(x, real, informe=len(diferencias) - 1, **etiquetas)

    filas = []
    for v in sorted(df.version.unique()):
        x = df[df.version == v]
        for n in TAREAS:
            for i in range(REPARTOS_AA):
                filas += informe(partir(submuestra(x, n)), nulo, diseno='A/A equilibrado',
                                 version=v, n_tareas=str(n or 'todas'), reparto=i)
        filas += informe(partir(x, equilibrado=False), nulo, diseno='A/A por orden de corrida',
                         version=v, n_tareas='todas', reparto=0)
    aa = pd.DataFrame(filas)

    filas = []
    for m, tamano in EFECTOS:
        for v in sorted(df.version.unique()):
            x = df[df.version == v]
            for n in TAREAS:
                for i in range(REPARTOS_PLANTADOS):
                    y = partir(submuestra(x, n))
                    error = error_de_la_verdad(y) if m == 'exito' else 0.0
                    y, efecto = plantar(y, m, tamano)
                    filas += informe(y, dict(nulo, **{m: efecto}), plantada=m, tamano=tamano, error_verdad=error,
                                     version=v, n_tareas=str(n or 'todas'), reparto=i)
    return aa, pd.DataFrame(filas), np.stack(diferencias), tareas


def resumir(df, aa, plantados, ejemplo):
    informes_aa = (aa.groupby(['diseno', 'n_tareas', 'version', 'reparto'])
                   .agg(falso=('falso', 'any'), falso_rival=('falso_rival', 'any'),
                        falso_agentrial=('falso_agentrial', 'any'))
                   .groupby(['diseno', 'n_tareas'], sort=False).mean())
    tabla_aa = (aa.groupby(['diseno', 'n_tareas', 'metrica'], sort=False)
                .agg(falsos=('falso', 'mean'), falsos_rival=('falso_rival', 'mean'),
                     falsos_agentrial=('falso_agentrial', 'mean'), cobertura=('cubre', 'mean'),
                     equivalencia=('estado', lambda e: (e == 'equivalencia').mean()),
                     no_concluyente=('estado', lambda e: (e == 'no concluyente').mean())))

    objetivo = plantados[plantados.metrica == plantados.plantada]
    otras = plantados[plantados.metrica != plantados.plantada]
    objetivo = objetivo.assign(
        detectado=(objetivo.estado == 'diferencia') & ~objetivo.falso,
        detectado_rival=(objetivo.estado_rival == 'diferencia') & ~objetivo.falso_rival,
        detectado_agentrial=(objetivo.estado_agentrial == 'diferencia') & ~objetivo.falso_agentrial)
    tabla_plantados = (objetivo.groupby(['n_tareas', 'plantada', 'tamano'], sort=False)
                       .agg(detectado=('detectado', 'mean'), detectado_rival=('detectado_rival', 'mean'),
                            detectado_agentrial=('detectado_agentrial', 'mean'), cobertura=('cubre', 'mean'),
                            falsos=('falso', 'mean'), falsos_rival=('falso_rival', 'mean'),
                            falsos_agentrial=('falso_agentrial', 'mean')))
    falsos_otras = otras.groupby('n_tareas').agg(falsos=('falso', 'mean'), falsos_rival=('falso_rival', 'mean'),
                                                 falsos_agentrial=('falso_agentrial', 'mean'))
    error_exito = objetivo[objetivo.plantada == 'exito'].groupby('n_tareas').error_verdad.median()
    detectables = tabla_plantados[tabla_plantados.detectado >= 0.8].reset_index()
    efecto_minimo = (detectables.groupby(['n_tareas', 'plantada'], sort=False).tamano.min()
                     .unstack('n_tareas').reindex(list(METRICAS)))

    return [
        f'Datos: {df.version.nunique()} configuraciones, {df.tarea.nunique()} tareas, '
        f'{len(df)} corridas con cuatro repeticiones.',
        '',
        'A/A: proporción de facts falsos por métrica, cobertura del IC 95 % y estados del generador',
        tabla_aa.round(3).to_string(),
        '',
        'A/A: proporción de informes con al menos un fact falso',
        informes_aa.round(3).to_string(),
        '',
        'Efectos plantados: detección de la métrica plantada',
        tabla_plantados.round(3).to_string(),
        '',
        'Efectos plantados: facts falsos en las métricas sin efecto',
        falsos_otras.round(3).to_string(),
        '',
        'Efectos plantados en el éxito: error típico del efecto real, relativo al plantado (mediana)',
        error_exito.round(3).to_string(),
        '',
        'Menor efecto detectado en al menos 80 % de los casos: relativo, o en puntos para el éxito '
        '(vacío: ninguno de los probados)',
        efecto_minimo.to_string(),
        '',
        'Ejemplo de informe: claude-opus-5, esfuerzo medium contra high (todas las corridas válidas)',
        *[f'- {t}' for t in ejemplo],
    ]


def main():
    todas = deepswe.cargar()
    # Para partir dos contra dos, solo las celdas con las cuatro repeticiones.
    df = todas[todas.groupby(['version', 'tarea']).tarea.transform('size') == 4]
    aa, plantados, diferencias, tareas = correr(df)

    SALIDA.mkdir(exist_ok=True)
    aa.to_csv(SALIDA / 'aa.csv', index=False)
    plantados.to_csv(SALIDA / 'plantados.csv', index=False)
    np.savez_compressed(SALIDA / 'diferencias.npz', d=diferencias, tareas=np.array(tareas),
                        metricas=np.array(list(METRICAS)))

    # El ejemplo sigue la regla del generador: entran todas las corridas válidas, no solo las celdas de cuatro.
    ejemplo = todas[todas.version.str.endswith(('claude_opus_5_medium', 'claude_opus_5_high'))].copy()
    ejemplo['version'] = 'opus-5-' + ejemplo.esfuerzo
    textos = comparar(ejemplo, 'opus-5-medium', 'opus-5-high').texto

    pd.set_option('display.width', 200)
    resumen = '\n'.join(resumir(df, aa, plantados, textos)) + '\n'
    (SALIDA / 'resumen.txt').write_text(resumen)
    print(resumen, end='')


if __name__ == '__main__':
    main()

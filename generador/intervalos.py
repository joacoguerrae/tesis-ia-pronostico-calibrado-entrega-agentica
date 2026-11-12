"""Intervalos de las medidas de evaluación, con la variación por configuraciones y por tareas.

Los informes de aa_deepswe.py comparten configuraciones y tareas, que en DeepSWE
están cruzadas, así que no son independientes. La varianza de cada medida se
arma con dos partes que se suman:
- configuraciones: bootstrap que sortea con reposición las configuraciones, con
  las tareas fijas;
- tareas: jackknife que saca al azar el 20 % de las tareas y recalcula el
  generador en todos los informes (delete-d jackknife, Shao y Wu, 1989).
Las tareas no se sortean con reposición porque una tarea repetida entra dos veces
en el test pareado de un mismo informe, como si fueran independientes, y eso solo
ya infla los facts falsos. Sumar las dos partes cuenta dos veces la interacción
entre configuración y tarea, así que el intervalo es algo conservador.

Los rivales tienen solo la parte de configuraciones: recalcularlos sin una tarea
necesita las corridas, no solo las diferencias.

Criterios del capítulo 4: el generador supera el nivel nominal si el límite
inferior del intervalo de los informes con algún fact falso queda por encima del
5 %, y cubre menos de lo declarado si el límite superior de la cobertura queda
por debajo del 95 %.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from formato import METRICAS
from generador import ALFA, MARGEN

SALIDA = Path(__file__).parent / 'resultados'
REPLICAS = 2000
SACADAS = 0.2  # fracción de tareas que saca cada subconjunto del jackknife
SUBCONJUNTOS = 500
MEDIDAS_AA = ['informes con algún fact falso', 'facts falsos', 'cobertura', 'equivalencias',
              'informes con algún fact falso (diferencia de medias)', 'informes con algún fact falso (agentrial)']

rng = np.random.default_rng(2026)


class Informes:
    """Los informes de aa_deepswe.py, con lo necesario para recalcular el generador con otras tareas."""

    def __init__(self, carpeta):
        guardado = np.load(carpeta / 'diferencias.npz')
        self.valida = (~np.isnan(guardado['d'])).astype('float64')
        self.d = np.nan_to_num(guardado['d'].astype('float64'))  # informes × métricas × tareas
        self.n_tareas = self.d.shape[2]
        self.filas = pd.concat([pd.read_csv(carpeta / 'aa.csv'), pd.read_csv(carpeta / 'plantados.csv')],
                               ignore_index=True)
        self.real = self.por_metrica('real')
        self.margen = np.array([MARGEN[t] for t in METRICAS.values()])

        info = self.filas.groupby('informe').first()
        self.configuracion, versiones = pd.factorize(info.version)
        self.n_config = len(versiones)
        self.aa = info.plantada.isna().to_numpy()
        self.diseno = (info.diseno.fillna('') + ', ' + info.n_tareas.astype(str)).to_numpy()
        self.objetivo = info.plantada.map(list(METRICAS).index, na_action='ignore').fillna(0).astype(int).to_numpy()
        self.grupo = (info.n_tareas.astype(str) + ', ' + info.plantada.fillna('') + ', '
                      + info.tamano.map('{:.2f}'.format, na_action='ignore').fillna('')).to_numpy()

        rivales = self.filas.groupby('informe')[['falso_rival', 'falso_agentrial']].any()
        self.falso_medias = rivales.falso_rival.to_numpy()
        self.falso_agentrial = rivales.falso_agentrial.to_numpy()
        plantada = self.filas[self.filas.metrica == self.filas.plantada].set_index('informe')
        self.deteccion_medias = (((plantada.estado_rival == 'diferencia') & ~plantada.falso_rival.astype(bool))
                                 .reindex(info.index, fill_value=False).to_numpy())

    def por_metrica(self, columna):
        return self.filas.pivot(index='informe', columns='metrica', values=columna)[list(METRICAS)].to_numpy()

    def generador(self, peso):
        """Diferencia, equivalencia, falsedad y cobertura de cada fact, con cada tarea contada `peso` veces.

        Un fact que se queda con menos de dos tareas no tiene estado ni cobertura. Pasa solo al sacar
        muchas tareas, en algún informe de 15 tareas.
        """
        n = self.valida @ peso
        with np.errstate(divide='ignore', invalid='ignore'):
            media = (self.d @ peso) / n
            var = np.clip((self.d ** 2 @ peso - n * media ** 2) / (n - 1), 0, None)
            var[var < 1e-12] = 0  # todas las tareas con la misma diferencia, como en generador.py
            ee = np.sqrt(var / n)
            t = stats.t(n - 1)
            p = np.where(ee > 0, 2 * t.sf(np.abs(media) / ee), (media == 0).astype(float))
            diferencia = stats.false_discovery_control(np.nan_to_num(p, nan=1.0), axis=1) < ALFA
            ic90, ic95 = t.ppf(1 - ALFA) * ee, t.ppf(1 - ALFA / 2) * ee
        equivalencia = ~diferencia & (media - ic90 > -self.margen) & (media + ic90 < self.margen)
        falso = ((diferencia & ((self.real == 0) | (np.sign(media) != np.sign(self.real))))
                 | (equivalencia & (np.abs(self.real) >= self.margen)))
        cubre = (media - ic95 <= self.real) & (self.real <= media + ic95)
        return diferencia, equivalencia, falso, cubre

    def medidas(self, diferencia, equivalencia, falso, cubre):
        """Para cada medida: un valor por informe, qué informes entran y en qué grupo va cada uno."""
        en_objetivo = np.arange(len(self.objetivo)), self.objetivo
        aa, plantados = (self.aa, self.diseno), (~self.aa, self.grupo)
        return {
            'informes con algún fact falso': (falso.any(axis=1), *aa),
            'facts falsos': (falso.mean(axis=1), *aa),
            'cobertura': (cubre.mean(axis=1), *aa),
            'equivalencias': (equivalencia.mean(axis=1), *aa),
            'informes con algún fact falso (diferencia de medias)': (self.falso_medias, *aa),
            'informes con algún fact falso (agentrial)': (self.falso_agentrial, *aa),
            'detección': ((diferencia & ~falso)[en_objetivo], *plantados),
            'detección (diferencia de medias)': (self.deteccion_medias, *plantados),
            'cobertura del efecto plantado': (cubre[en_objetivo], *plantados),
            'equivalencias falsas': ((equivalencia & falso)[en_objetivo], *plantados),
        }


def promedios(informes, valores, grupos, peso_config):
    """Promedio de cada medida por grupo, con cada configuración contada `peso_config` veces."""
    salida = []
    for nombre, (x, entra, grupo) in valores.items():
        codigo = pd.Categorical(grupo[entra], categories=grupos[nombre]).codes
        w = peso_config[informes.configuracion[entra]]
        k = len(grupos[nombre])
        salida.append(np.bincount(codigo, weights=w * x[entra], minlength=k)
                      / np.bincount(codigo, weights=w, minlength=k))
    return np.concatenate(salida)


def jackknife(informes, grupos, sacadas, subconjuntos):
    """Varianza por tareas: (n - d) / d por la varianza de la medida sin d tareas al azar."""
    n = informes.n_tareas
    resultados = []
    for _ in range(subconjuntos):
        peso = np.ones(n)
        peso[rng.choice(n, sacadas, replace=False)] = 0
        resultados.append(promedios(informes, informes.medidas(*informes.generador(peso)), grupos,
                                    np.ones(informes.n_config)))
    return (n - sacadas) / sacadas * np.array(resultados).var(axis=0)


def jackknife_de_a_una(informes, grupos):
    n = informes.n_tareas
    resultados = [promedios(informes, informes.medidas(*informes.generador(np.where(np.arange(n) == t, 0., 1.))),
                            grupos, np.ones(informes.n_config)) for t in range(n)]
    return (n - 1) * np.array(resultados).var(axis=0)


def a_texto(tabla):
    columnas = ['estimacion', 'ic95_inf', 'ic95_sup', 'parte_tareas']
    return tabla.assign(**{c: tabla[c].map('{:.3f}'.format) for c in columnas}).to_string(index=False)


def main():
    informes = Informes(SALIDA)
    n, n_config = informes.n_tareas, informes.n_config

    # Comprobación: con todas las tareas una vez, tiene que dar lo mismo que aa_deepswe.py.
    facts = informes.generador(np.ones(n))
    distintos = int((facts[2] != informes.por_metrica('falso').astype(bool)).sum())

    valores = informes.medidas(*facts)
    grupos = {nombre: pd.factorize(grupo[entra])[1] for nombre, (_, entra, grupo) in valores.items()}
    estimacion = promedios(informes, valores, grupos, np.ones(n_config))
    replicas = np.array([promedios(informes, valores, grupos,
                                   rng.multinomial(n_config, np.full(n_config, 1 / n_config)).astype(float))
                         for _ in range(REPLICAS)])
    var_config = replicas.var(axis=0, ddof=1)
    var_tareas = jackknife(informes, grupos, round(SACADAS * n), SUBCONJUNTOS)
    error = np.sqrt(var_config + var_tareas)
    # Sensibilidad a cuántas tareas saca el jackknife: una sola o la mitad.
    var_una = jackknife_de_a_una(informes, grupos)
    var_mitad = jackknife(informes, grupos, n // 2, SUBCONJUNTOS)

    tabla = pd.DataFrame([(nombre, g) for nombre in grupos for g in grupos[nombre]], columns=['medida', 'grupo'])
    tabla['estimacion'] = estimacion
    tabla['ic95_inf'] = np.clip(estimacion - 1.96 * error, 0, 1)
    tabla['ic95_sup'] = np.clip(estimacion + 1.96 * error, 0, 1)
    tabla['parte_tareas'] = np.divide(var_tareas, error ** 2, out=np.full_like(error, np.nan), where=error > 0)
    tabla['criterio'] = ''
    falsos = tabla.medida.isin(['informes con algún fact falso', 'equivalencias falsas'])
    tabla.loc[falsos & (tabla.ic95_inf > ALFA), 'criterio'] = 'supera el 5 %'
    cobertura = tabla.medida.str.startswith('cobertura')
    tabla.loc[cobertura & (tabla.ic95_sup < 1 - ALFA), 'criterio'] = 'cubre menos del 95 %'
    tabla.to_csv(SALIDA / 'intervalos.csv', index=False)

    principales = (tabla.medida.isin(['informes con algún fact falso', 'cobertura'])
                   & tabla.grupo.str.startswith('A/A equilibrado')).to_numpy()
    sensibilidad = tabla[principales][['medida', 'grupo', 'estimacion']].assign(
        configuraciones=np.sqrt(var_config[principales]), una_tarea=np.sqrt(var_una[principales]),
        **{f'{SACADAS:.0%}': np.sqrt(var_tareas[principales]), 'la_mitad': np.sqrt(var_mitad[principales])},
    ).round(4)

    pd.set_option('display.width', 200)
    pd.set_option('display.max_rows', 500)
    aa = tabla.medida.isin(MEDIDAS_AA)
    resumen = '\n'.join([
        f'Intervalos del 95 %: bootstrap de configuraciones ({REPLICAS} réplicas) más jackknife de tareas',
        f'({SUBCONJUNTOS} subconjuntos sin {round(SACADAS * n)} de las {n} tareas).',
        'Los rivales, solo configuraciones. parte_tareas: qué parte de la varianza viene de las tareas.',
        f'Comprobación: con las tareas sin remuestrear, el recálculo difiere de aa_deepswe.py '
        f'en {distintos} de {facts[2].size} facts.',
        '',
        'Comparaciones A/A (grupo: diseño, cantidad de tareas)',
        a_texto(tabla[aa]),
        '',
        'Sensibilidad: error estándar de las medidas principales del A/A equilibrado, por configuraciones',
        'y por tareas según cuántas tareas saca el jackknife',
        sensibilidad.to_string(index=False),
        '',
        'Efectos plantados (grupo: cantidad de tareas, métrica, tamaño)',
        a_texto(tabla[~aa]),
    ]) + '\n'
    (SALIDA / 'intervalos.txt').write_text(resumen)
    print(resumen, end='')


if __name__ == '__main__':
    main()

"""Propiedades del generador que se cumplen por construcción (capítulo 4, sección 4.6).

Si alguna falla, es un defecto del código, no un resultado.
"""
import numpy as np
import pandas as pd
import pytest

from formato import COLUMNAS, validar
from generador import _valor, comparar
from rivales import agentrial


def corridas(tareas=30, repeticiones=4, efecto_costo=1.0, semilla=0):
    """Dos versiones sobre las mismas tareas. B multiplica el costo de cada corrida por `efecto_costo`."""
    rng = np.random.default_rng(semilla)
    filas = []
    for t in range(tareas):
        base, tasa = rng.lognormal(0, 1), rng.uniform(0.2, 0.8)
        for version, factor in [('A', 1.0), ('B', efecto_costo)]:
            for r in range(1, repeticiones + 1):
                ruido = rng.lognormal(0, 0.2)
                filas.append(dict(version=version, tarea=f't{t}', repeticion=r, exito=float(rng.random() < tasa),
                                  costo_usd=base * factor * ruido, tokens_entrada=1e5 * base * ruido,
                                  tokens_salida=1e4 * base * ruido, pasos=round(30 * base * ruido) + 1,
                                  duracion_s=60 * base * ruido))
    return pd.DataFrame(filas)[COLUMNAS]


def copia_de_a(df, factor_costo=1.0):
    """B idéntica a A, salvo el costo multiplicado por `factor_costo`: toda diferencia por tarea es exacta."""
    a = df[df.version == 'A']
    b = a.assign(version='B', costo_usd=a.costo_usd * factor_costo)
    return pd.concat([a, b], ignore_index=True)


def test_la_misma_entrada_da_los_mismos_facts():
    df = corridas()
    pd.testing.assert_frame_equal(comparar(df, 'A', 'B'), comparar(df.sample(frac=1, random_state=1), 'A', 'B'))


def test_un_efecto_grande_se_informa_como_diferencia_con_su_signo():
    facts = comparar(corridas(efecto_costo=1.5), 'A', 'B').set_index('metrica')
    assert facts.loc['costo_usd', 'estado'] == 'diferencia'
    assert facts.loc['costo_usd', 'efecto'] == pytest.approx(np.log(1.5), abs=0.1)


def test_sin_ningun_cambio_todo_es_equivalencia():
    facts = comparar(copia_de_a(corridas()), 'A', 'B')
    assert (facts.estado == 'equivalencia').all()


def test_la_diferencia_gana_a_la_equivalencia():
    # Un 2 % exacto en todas las tareas: el test rechaza y el intervalo queda dentro del margen del 10 %.
    facts = comparar(copia_de_a(corridas(), factor_costo=1.02), 'A', 'B').set_index('metrica')
    assert facts.loc['costo_usd', 'estado'] == 'diferencia'


@pytest.mark.parametrize('efecto_costo', [1.0, 1.5])
def test_el_texto_dice_los_numeros_del_fact(efecto_costo):
    for f in comparar(corridas(efecto_costo=efecto_costo), 'A', 'B').itertuples():
        assert f'{f.n_tareas} tareas' in f.texto
        if f.estado == 'equivalencia':
            assert _valor(f, f.ic90_inf) in f.texto and _valor(f, f.ic90_sup) in f.texto
        else:
            assert _valor(f, f.ic_inf) in f.texto and _valor(f, f.ic_sup) in f.texto
        if f.estado == 'diferencia':
            assert _valor(f, f.efecto, signo=False) in f.texto
            assert ('sube' in f.texto) == (f.efecto > 0)


def test_validar_rechaza_columnas_faltantes_y_corridas_repetidas():
    df = corridas(tareas=2)
    with pytest.raises(ValueError, match='Faltan columnas'):
        validar(df.drop(columns='pasos'))
    with pytest.raises(ValueError, match='misma versión, tarea y repetición'):
        validar(pd.concat([df, df.head(1)]))


def test_agentrial_necesita_varias_corridas_por_version():
    # Con dos corridas por versión ningún test por tarea baja de p = 0,19: no declara nada, ni con un efecto enorme.
    assert (agentrial(corridas(repeticiones=2, efecto_costo=3.0), 'A', 'B').estado == 'sin cambio').all()
    con_diez = agentrial(corridas(repeticiones=10, efecto_costo=3.0), 'A', 'B').set_index('metrica')
    assert con_diez.loc['costo_usd', 'estado'] == 'diferencia'

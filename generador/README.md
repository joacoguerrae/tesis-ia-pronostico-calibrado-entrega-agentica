# Generador de facts

Compara dos versiones de un agente a partir de corridas repetidas sobre las mismas tareas. Devuelve un fact por métrica (éxito, costo, tokens de entrada y de salida, pasos y duración) con su estado, su intervalo y un texto armado con plantillas. El estado es diferencia, equivalencia o no concluyente.

La validación usa los datos públicos de DeepSWE. Las corridas del banco propio (carpeta `banco/`, junto a esta) se leen con `claude_code.py`.

## Archivos

| Archivo | Qué hace |
|---|---|
| `formato.py` | Formato común: una fila por corrida, con versión, tarea, repetición y las seis métricas. |
| `generador.py` | Compara dos versiones y devuelve los facts. |
| `deepswe.py` | Pasa el `trials.json` de DeepSWE al formato común. |
| `claude_code.py` | Pasa las corridas del banco al formato común, con una tabla por llamada al modelo y otra por uso de herramienta. |
| `rivales.py` | Los dos métodos contra los que se compara el generador: la diferencia de medias y los tests de agentrial. |
| `aa_deepswe.py` | Comparaciones A/A y efectos plantados sobre DeepSWE, con el generador y los rivales. |
| `intervalos.py` | Intervalos del 95 % de cada medida de evaluación y comparación con los criterios del capítulo 4. |
| `potencia.py` | Fórmula de la potencia y del menor efecto detectable. |
| `tamano.py` | Valida la fórmula contra los efectos plantados y calcula cuántas tareas y corridas hacen falta. |
| `piloto.py` | Resume el piloto del banco: controles, dificultad, costo, ruido y menor efecto detectable con su presupuesto. |
| `tests/` | Propiedades que el generador cumple por construcción. |

## Cómo correrlo

Con Python 3.11:

```
pip install -r requirements.txt
python -m pytest
```

Los datos de DeepSWE no están en el repositorio. No tienen una licencia explícita, y sus autores piden que no aparezcan en corpus de entrenamiento. Hay que bajar `https://deepswe.datacurve.ai/artifacts/v1.1/trials.json` (51 MB) a `datos/deepswe/trials.json`. El archivo cambia sin cambiar de versión. El que se usó tiene sha256 `310cb428fe8914cff21b8edcb0b17256884efca55666bd6d6646d223c77d2ce6`, y con otro los números pueden cambiar.

Después se corren en este orden:

```
python aa_deepswe.py   # unos 13 minutos
python tamano.py
python intervalos.py
```

Todos usan una semilla fija, así que dan siempre lo mismo. Los resúmenes quedan en `resultados/`. Las tablas por informe (`aa.csv`, `plantados.csv`, `diferencias.npz`) pesan decenas de MB, y por eso no se suben.

Para el piloto del banco: `python piloto.py ../banco/corridas/<experimento>`.

## Método

- **Comparación.**
  - Es pareada por tarea: cada métrica se promedia por tarea y versión, y la diferencia se calcula dentro de cada tarea.
  - Las métricas positivas se comparan en escala logarítmica, así que el efecto es un cambio relativo (cociente de medias geométricas). El éxito se compara en puntos.
- **Estados.**
  - Hay diferencia cuando el test t pareado rechaza después de corregir por Benjamini-Hochberg entre las seis métricas (q < 0,05).
  - Hay equivalencia cuando no hay diferencia y el IC 90 % queda dentro del margen: ±10 % en las métricas continuas y ±5 puntos en el éxito.
  - Si se cumplen las dos condiciones, gana la diferencia.
  - Los intervalos no se ajustan por multiplicidad.
- **Comparaciones A/A.**
  - Las cuatro corridas de cada tarea se parten dos contra dos. En el corte principal, cada mitad lleva una de las dos primeras corridas y una de las dos últimas.
  - El corte por orden de corrida (primeras contra últimas) se informa aparte, como prueba de estrés.
- **Efectos plantados.**
  - En las métricas continuas se multiplica la mitad B por 1,05 a 1,50, y el efecto real es exacto. En los pasos no se redondea.
  - En el éxito se convierten al azar éxitos en fallas, o al revés, con la probabilidad que da un cambio de 5 a 30 puntos. Esa probabilidad sale de la tasa observada, así que el efecto real es aproximado: el error típico es de 2,7 % del efecto con 113 tareas y de 7,1 % con 15.
- **Rivales.**
  - Diferencia de medias con el mismo umbral que el margen.
  - Los tests de `agentrial snapshot check`, reimplementados del commit 0c8ef03 de su repositorio. Por tarea aplican Fisher al éxito y Mann-Whitney al costo y la duración, con Benjamini-Hochberg entre todos los tests. Del costo y la duración informan solo las subas. Los tokens y los pasos, que agentrial no analiza, se tratan como el costo.
  - Ninguno de los dos declara equivalencia.
- **Intervalos de las medidas.**
  - Se suman dos partes: un bootstrap de configuraciones, con las tareas fijas, y un jackknife que saca al azar el 20 % de las tareas.
  - Las tareas no se sortean con reposición: una tarea repetida entra dos veces en el test pareado e infla los facts falsos.

## Resultados con DeepSWE

El detalle está en `resultados/resumen.txt`, `intervalos.txt` y `tamano.txt`. Entre corchetes van los intervalos del 95 %.

| A/A, informes con algún fact falso | Generador | Diferencia de medias |
|---|---|---|
| Corte equilibrado, 113 tareas | 3,9 % [2,1 a 5,7] | 17,2 % [14,2 a 20,2] |
| Corte equilibrado, 15 tareas | 3,2 % [1,3 a 5,1] | 72,4 % [69,5 a 75,4] |
| Corte por orden de corrida | 44,3 % [28,0 a 60,6] | 34,3 % [23,3 a 45,3] |

- **Criterios del capítulo 4.** El generador no falla ninguno. La cobertura de los IC 95 % en el A/A es de 95,1 % [93,9 a 96,2], y en los efectos plantados ningún límite superior baja de 97,9 %. Las equivalencias falsas no pasan de 0,5 %. El corte por orden de corrida falla los dos criterios: las corridas de las dos versiones tienen que ir intercaladas.
- **agentrial** no declara nada con dos corridas por versión, porque ninguno de sus tests por tarea baja de p = 0,19.
- **Menor efecto que se detecta en el 80 % de los casos.**
  - Con 113 tareas: 5 % en tokens de salida; 10 % en costo, pasos y duración; 20 % en tokens de entrada; 20 puntos en el éxito.
  - Con 15 tareas: de 20 % a 50 % en las métricas continuas, y en el éxito ninguno de los probados (hasta 30 puntos).
- **La fórmula de potencia** predice la detección observada con un error de 0,7 a 2,3 puntos en las métricas continuas. En el éxito la sobreestima en 5,7 puntos, así que ahí es una cota optimista.
- **Con el ruido de DeepSWE**, un banco de 15 tareas con 5 corridas por versión (150 corridas por comparación) detecta cambios de 14 % a 18 % en el costo y de 24 a 26 puntos en el éxito. Con la misma cantidad de corridas, rinden más las tareas que las repeticiones.

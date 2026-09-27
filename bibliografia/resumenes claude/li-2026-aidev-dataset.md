# Li, H., Zhang, H. & Hassan, A. E. (2026). AIDev: Studying AI Coding Agents on GitHub. MSR 2026 (Mining Challenge dataset). arXiv:2602.09185

**Estado de lectura:** leído completo desde https://arxiv.org/html/2602.09185 (paper corto, 5 secciones). Complementado con la ficha del dataset en Hugging Face (https://huggingface.co/datasets/hao-li/AIDev) para licencia y columnas, y con el abstract del paper compañero arXiv:2507.15003. Se aclara en cada caso qué viene del paper y qué de afuera.
**Tipo:** paper de presentación de dataset (el del Mining Challenge de MSR 2026). El encabezado del HTML declara MSR '26, Rio de Janeiro, 13–14 abril 2026; aceptación **declarada**, no verificada contra el programa. · **Datos:** 932.791 PRs agénticos en 116.211 repos, 72.189 usuarios; subconjunto curado de 33.596 PRs en 2.807 repos con >100 estrellas. Corte: 1 de agosto de 2025. · **Objeto:** agentes **autónomos** que abren PRs (OpenAI Codex, Devin, GitHub Copilot coding agent, Cursor, Claude Code).
**Tiempo de lectura del original:** ~15 min · **Tiempo de lectura de este resumen:** ~7 min

## En una frase
AIDev es un dataset relacional de casi un millón de pull requests abiertos por cinco agentes de código en GitHub, con un subconjunto enriquecido de 33.596 PRs que incluye la línea de tiempo completa de eventos, reviews, commits con diffs e issues relacionados, publicado para estudiar adopción, calidad, revisión y riesgos de los agentes.

## Por qué está en nuestra lista (qué decisión del proyecto toca)
Es nuestro **plan B de datos** si no cierra el acuerdo con la consultora. La pregunta concreta es si permite reconstruir, por unidad, (momento del pronóstico, momento del desenlace) sin leakage, y qué covariables de nuestra telemetría se pueden aproximar. También sirve como referencia de escala y de convenciones de campo para definir nuestro esquema canónico (R1).

## Resumen sección por sección

### 1. Visión general
Enmarcan el momento como "SE 3.0": los agentes ya no asisten dentro del editor sino que abren miles de PRs por día. La Figura 1 muestra un caso: Copilot recibe un issue asignado, genera el parche, abre el PR con descripción, un revisor humano comenta y el agente responde con un commit adicional. Aclaran que no todos los agentes soportan responder a reviews. De ahí la motivación: no existía un dataset amplio de esta dinámica.

### 2. Estructura interna (Tabla 1)
El paper solo da la tabla resumen; el esquema relacional completo está en Hugging Face/Zenodo.

| Tabla | Registros | Contenido declarado |
|---|---|---|
| all_pull_request | 932.791 | título, cuerpo, agente, estado, timestamps, repo, usuario |
| all_repository | 116.211 | nombre, licencia, lenguaje, URL, estrellas, forks |
| all_user | 72.189 | login, seguidores, fecha de creación |
| pull_request | 33.596 | igual, solo repos >100 estrellas |
| repository | 2.807 | idem |
| user | 1.796 | idem |
| pr_comments | 39.122 | comentarios de discusión (autor, cuerpo, timestamp) |
| pr_reviews | 28.875 | veredictos de review (approve / request changes) con timestamp |
| pr_review_comments | 19.450 | comentarios inline sobre el código, con contexto de archivo |
| pr_commits | 88.576 | commits del PR (SHA, autor, mensaje) |
| pr_commit_details | 711.923 | diffs a nivel archivo (adiciones, borrados, patch) |
| related_issue | 4.923 | mapeo PR→issue |
| issue | 4.614 | issues (título, cuerpo, estado, usuario, timestamps) |
| pr_timeline | 325.500 | historial de eventos del PR (committed, closed, merged, labeled, reviewed…) |
| pr_task_type | 33.596 | clasificación automática del propósito (Conventional Commits + GPT) |

**Qué campos exactos hay:** el paper NO enumera columnas. Según la ficha de Hugging Face (fuera del paper), la tabla de PRs tiene id, título, cuerpo, etiqueta de agente, info de usuario, estado y timestamps, y se nombran explícitamente `created_at`, `closed_at` y `merged_at`. Las tablas de comentarios y reviews tienen timestamp por registro; `pr_timeline` tiene un evento por fila con su tiempo. Para el detalle real hay que abrir el esquema en HF/Zenodo.

**Cómo identifican los PRs agénticos:** el paper **no lo dice**. Hay un campo `agent` por PR, pero ni este texto ni la ficha de HF describen las heurísticas. La ficha manda a citar el paper compañero "The Rise of AI Teammates in SE 3.0" (arXiv:2507.15003), cuyo abstract tampoco lo explica. Dato de segunda mano: Dao et al. (2026) dicen que identifican por metadatos (`type='Bot'`) más nombres de agente, con 94% de precisión en auditoría manual; eso es de ellos, no de Li et al.

### 3. Acceso
Hugging Face (con "Data Studio" para correr SQL en el navegador), Zenodo (DOI 10.5281/zenodo.16899501) y GitHub (SAILResearch/AI_Teammates_in_SE3, con notebooks de ejemplo).

**Licencia:** el paper **no declara licencia del dataset**. La ficha de Hugging Face declara **CC-BY-4.0** y aclara que cada repo fuente conserva su copyright original. Para la tesis: uso con atribución está bien; evitar redistribuir código de repos con licencias restrictivas y, por nuestra regla del proyecto, no exponer logins de usuarios.

**Ojo con la versión:** la ficha de HF hoy muestra un dataset más grande que el del paper: 2.743.854 PRs de seis agentes (Codex 2.069.595; Copilot 349.695; Cursor 212.544; Google Jules 50.490; Devin 43.298; Claude Code 18.232). El paper describe el corte del 1/8/2025 (932.791 PRs, cinco agentes). Si lo usamos hay que **fijar versión y fecha de corte explícitamente**. El paper no da desglose por agente para su versión.

### 4. Preguntas de investigación que proponen
Cinco familias: adopción y prácticas; características del parche; testing; dinámica de revisión; y fallas y riesgos — dentro de la última, **si señales tempranas (descripción, paths tocados, características del parche) predicen rechazo o esfuerzo de revisión**, que es la que Dao et al. atacan y la más cercana a nuestro pronóstico.

### 5. Trabajo relacionado
Tres bloques: agentes de código (SWE-agent, OpenHands, SWE-bench; más vulnerabilidades en código generado); contribuciones automatizadas en OSS (los bots clásicos tienen menor aceptación e interacciones más lentas; los PRs con ChatGPT cierran más lento y con más revisión); y estudios de adopción y productividad.

**No hay sección de limitaciones ni de amenazas a la validez en el paper.**

## Los números que hay que recordar
- **932.791 PRs / 116.211 repos / 72.189 usuarios**, cinco agentes, corte 1/8/2025 (sección 1).
- **33.596 PRs / 2.807 repos (>100 estrellas) / 1.796 usuarios** en el subconjunto enriquecido (Tabla 1).
- **325.500 eventos en pr_timeline**, **28.875 reviews**, **88.576 commits**, **711.923 diffs**, **4.923 vínculos PR-issue** (Tabla 1).
- **Licencia CC-BY-4.0** según la ficha de HF; el paper no la declara.
- Versión actual en HF: **2.743.854 PRs, seis agentes** (fuera del paper).

## Limitaciones
**Declaradas:** ninguna en el texto.
**Nuestras:** no explica cómo detecta PRs agénticos ni reporta precisión. Un PR no es una "tarea/capability" de consultora: no hay cliente, no hay decisiones pendientes, no hay versión de proceso, no hay QA formal ni horas humanas. Sesgo de agente: Codex domina por volumen y se comporta muy distinto (según Dao et al., 42,9% de merges en menos de un minuto), lo que contamina cualquier distribución de duración si no se estratifica. Solo se ven PRs abiertos por el agente; el trabajo humano fuera del PR es invisible. Ventana temporal corta y dataset en crecimiento: reproducibilidad exige fijar versión.

## Qué tomamos tal cual y qué hacemos distinto

**¿Permite reconstruir (momento del pronóstico, momento del desenlace)? Sí, con una unidad distinta a la nuestra.**
- **Unidad:** el PR (o el par issue→PR cuando existe `related_issue`, 4.923 casos).
- **Momento del pronóstico:** `created_at` del PR. Disponible en ese instante: título, cuerpo, agente, repo (lenguaje, estrellas, licencia), autor, y —si se toma el primer commit como parte del estado inicial— tamaño del diff y archivos tocados. **Ojo con leakage:** `pr_commits` incluye commits posteriores hechos en respuesta a reviews; hay que filtrar por fecha de commit ≤ `created_at` o usar solo el primero.
- **Momento del desenlace:** `merged_at` (entrega) o `closed_at` sin merge (rechazo); alternativamente el evento `merged`/`closed` en `pr_timeline`. Permite backtesting de origen móvil: para cada origen t, entrenar con PRs cuyo desenlace ocurrió antes de t y pronosticar los abiertos en t. Los PRs aún abiertos al corte son **censurados** y hay que tratarlos como tales, no descartarlos.
- **Covariables dinámicas:** `pr_timeline`, `pr_reviews` y `pr_comments` tienen timestamp por evento, así que se reconstruye el estado en cualquier instante intermedio (rondas de review hasta t ≈ nuestras "iteraciones de QA"; primer comentario humano ≈ "escalación").

**Qué le falta respecto a nuestra telemetría:** duración de ejecución del agente (solo se ve el PR ya abierto), latencia de decisiones del cliente (no hay cliente), versión del proceso (no existe), horas de intervención humana (a lo sumo conteo de comentarios como proxy ordinal), tamaño de tarea en sentido de negocio. La escala también es otra: nosotros esperamos 100–300 unidades en ~10 proyectos; acá hay decenas de miles, lo que cambia qué modelos son viables. **El plan B no es un reemplazo uno a uno: es un experimento distinto, y hay que decirlo así.**

**Tomamos tal cual:** la granularidad de `pr_timeline` (evento + timestamp) como referencia para pedirle a la consultora telemetría "event-sourced" en vez de agregados; la clasificación de tipo de tarea con Conventional Commits como categoría barata; el filtro >100 estrellas si usamos el plan B.

**Alcance:** usar AIDev como plan B no suma alcance a R1–R5 si nos limitamos a la misma pregunta. Lo que sí sale del camino crítico es cualquier análisis de contenido de los diffs.

## Si igual lo vas a abrir
Es corto: sección 1 y Tabla 1 (5 minutos), y la sección 4.5 (fallas y riesgos) porque contiene la pregunta parecida a la nuestra. Salteá la sección 5. Lo importante —columnas, esquema, licencia, método de detección— **no está en el paper**: hay que ir a la ficha de Hugging Face, al esquema en Zenodo, y al paper compañero arXiv:2507.15003 (pendiente de leer).

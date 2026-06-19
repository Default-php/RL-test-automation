# RL Test Prioritizer

RL Test Prioritizer es una herramienta para ordenar casos de prueba usando un motor de aprendizaje por refuerzo. El sistema recibe un conjunto de pruebas con información como tiempo estimado, probabilidad histórica de falla, cobertura y prioridad funcional; luego recomienda qué pruebas ejecutar primero cuando el tiempo o el presupuesto de ejecución es limitado.

El proyecto incluye dos formas de uso:

- Una interfaz web en Django para cargar datasets, ejecutar el motor y descargar reportes.
- Un flujo por línea de comandos para reproducir ejecuciones y generar resultados JSON.

> Nota: este proyecto prioriza casos de prueba a partir de metadatos. No ejecuta automáticamente pruebas reales de Selenium, Playwright, pytest u otros frameworks; funciona como un motor de decisión y simulación.

## Características Principales

- Priorización automática de casos de prueba con un agente Q-learning.
- Comparación contra estrategias base: prioridad, riesgo histórico y orden aleatorio.
- Presupuesto configurable de ejecución por episodio.
- Datasets incluidos para probar el sistema inmediatamente.
- Carga de datasets personalizados en formato JSON desde la interfaz web.
- Validación de estructura para archivos cargados desde la web.
- Reportes descargables con métricas, trazas y orden recomendado.
- Resultados reproducibles mediante semillas configurables.

## Cómo Funciona

Cada caso de prueba se representa con estos atributos:

- `id`: identificador del caso de prueba.
- `name`: nombre descriptivo.
- `estimated_time`: tiempo estimado de ejecución.
- `failure_probability`: probabilidad histórica o esperada de detectar una falla.
- `coverage_gain`: aporte estimado de cobertura.
- `priority`: prioridad funcional.

Durante el entrenamiento, el agente aprende a seleccionar pruebas bajo un presupuesto limitado. La recompensa favorece pruebas con alta probabilidad de falla, buen aporte de cobertura y selección temprana, aplicando una penalización por tiempo estimado.

Al finalizar, el sistema compara el agente contra tres estrategias:

- **Priority baseline**: ejecuta primero las pruebas con mayor prioridad funcional.
- **Risk baseline**: ejecuta primero las pruebas con mayor probabilidad histórica de falla.
- **Random baseline**: usa un orden aleatorio reproducible mediante semilla.

## Tecnologías

- Python
- Django 5
- Q-learning tabular
- Django Templates
- Bootstrap 5
- JSON para datasets y reportes

La dependencia principal del proyecto está declarada en `requirements.txt`.

## Estructura del Proyecto

```text
core/
  agent.py          Agente Q-learning.
  baseline.py       Estrategias base de comparación.
  environment.py    Entorno de simulación.
  evaluator.py      Evaluación y agregación de métricas.
  models.py         Modelo de datos TestCase.
  trainer.py        Ciclo de entrenamiento.

data/
  sample_tests.json         Dataset base.
  payment_tests.json        Dataset orientado a pagos.
  large_tests.json          Dataset ampliado.
  evaluation_results.json   Resultados de referencia.
  training_history.json     Historial de entrenamiento.

src/
  run_experiment.py  Ejecutor principal por línea de comandos.

scripts/
  run_experiment.py  Wrapper de compatibilidad.

test_prioritizer/
  settings.py  Configuración de Django.
  urls.py      Rutas principales del proyecto.

web/
  forms.py      Formulario de ejecución.
  services.py   Validación, ejecución y reportes.
  views.py      Vistas web.
  urls.py       Rutas de la aplicación web.
  templates/    Plantillas HTML.

manage.py
requirements.txt
README.md
```

## Clonar, Ejecutar y Observar el Proyecto

### 1. Clonar el Repositorio

```powershell
git clone https://github.com/Default-php/RL-test-automation.git
cd RL-test-automation
```

### 2. Crear el Entorno Virtual

En Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -r requirements.txt
```

En Git Bash:

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. Ejecutar la Interfaz Web

En Windows PowerShell:

```powershell
.\.venv\Scripts\python manage.py runserver
```

En Git Bash, con el entorno activado:

```bash
python manage.py runserver
```

Abre la aplicación en:

```text
http://127.0.0.1:8000/
```

Desde la interfaz puedes:

1. Seleccionar un dataset incluido.
2. Subir un archivo JSON propio.
3. Configurar episodios de entrenamiento y evaluación.
4. Ajustar el presupuesto de ejecución.
5. Ejecutar el motor de priorización.
6. Revisar el orden recomendado y la comparación contra baselines.
7. Descargar el reporte JSON generado.

Los reportes creados desde la web se guardan en:

```text
outputs/web_reports/
```

### 4. Ejecutar un Experimento por Consola

Ejemplo con el dataset base:

```powershell
.\.venv\Scripts\python -m src.run_experiment `
  --data-file data\sample_tests.json `
  --output-dir outputs `
  --training-episodes 2000 `
  --evaluation-episodes 100 `
  --execution-budget 3 `
  --seed 42 `
  --agent-seed 123
```

En sistemas tipo Unix o Git Bash:

```bash
python -m src.run_experiment \
  --data-file data/sample_tests.json \
  --output-dir outputs \
  --training-episodes 2000 \
  --evaluation-episodes 100 \
  --execution-budget 3 \
  --seed 42 \
  --agent-seed 123
```

### 5. Observar los Resultados

Después de una ejecución por consola, revisa:

```text
outputs/evaluation_results.json
outputs/training_history.json
```

`evaluation_results.json` contiene el resumen comparativo entre el agente y las estrategias base. Incluye métricas como:

- Recompensa promedio.
- Cobertura promedio.
- Fallas detectadas.
- Tasa de detección de fallas.
- Presupuesto usado.
- Orden de ejecución de muestra.

`training_history.json` contiene el historial por episodio del entrenamiento, incluyendo recompensa, cobertura, fallas detectadas, presupuesto usado y valor de exploración `epsilon`.

## Formato de Dataset

Un dataset debe ser un arreglo JSON de casos de prueba:

```json
[
  {
    "id": 1,
    "name": "Login with valid credentials",
    "estimated_time": 1.2,
    "failure_probability": 0.25,
    "coverage_gain": 0.14,
    "priority": 5
  }
]
```

Reglas principales:

- El archivo debe ser JSON válido.
- Debe contener al menos un caso de prueba.
- `estimated_time` debe ser mayor que `0`.
- `failure_probability` debe estar entre `0` y `1`.
- `coverage_gain` debe estar entre `0` y `1`.
- `priority` debe ser un entero mayor que `0`.
- Los `id` no deben repetirse.

## Parámetros Disponibles en Consola

| Parámetro | Descripción |
| --- | --- |
| `--data-file` | Ruta del archivo JSON con casos de prueba. |
| `--output-dir` | Carpeta donde se guardan los resultados. |
| `--training-episodes` | Cantidad de episodios de entrenamiento. |
| `--evaluation-episodes` | Cantidad de episodios de evaluación. |
| `--execution-budget` | Cantidad máxima de pruebas por episodio. |
| `--seed` | Semilla del entorno y de las estrategias reproducibles. |
| `--agent-seed` | Semilla específica del agente Q-learning. |

## Pruebas del Proyecto

Ejecuta las pruebas con:

```powershell
.\.venv\Scripts\python manage.py test
```

También puedes verificar la configuración de Django con:

```powershell
.\.venv\Scripts\python manage.py check
```

## Archivos Generados

Los directorios `outputs/` y `docs/` se consideran salidas o material auxiliar. No forman parte del flujo principal de código fuente.

Archivos comunes generados:

- `outputs/evaluation_results.json`
- `outputs/training_history.json`
- `outputs/web_reports/<report_id>.json`

## Resultados de Referencia

Una ejecución de referencia con `data/sample_tests.json`, presupuesto `3`, semilla de entorno `42`, semilla de agente `123`, `2000` episodios de entrenamiento y `100` episodios de evaluación produjo estos resultados:

| Estrategia | Recompensa promedio | Cobertura promedio | Fallas promedio | Tasa de detección |
| --- | ---: | ---: | ---: | ---: |
| Agente Q-learning | 45.5266 | 0.4811 | 0.88 | 0.69 |
| Baseline por prioridad | 45.7700 | 0.4200 | 0.85 | 0.68 |
| Baseline por riesgo | 48.6000 | 0.5000 | 0.90 | 0.71 |
| Baseline aleatorio | 35.3390 | 0.3935 | 0.65 | 0.56 |

Estos valores sirven como referencia inicial. Los resultados pueden variar al cambiar dataset, presupuesto, semillas o número de episodios.

## Posibles Mejoras

- Integrar el priorizador con un runner real de pruebas automatizadas.
- Agregar ejecución en segundo plano para corridas largas desde la web.
- Guardar historiales y reportes en base de datos.
- Ampliar la cobertura de pruebas unitarias del motor de aprendizaje.
- Evaluar resultados sobre múltiples semillas y datasets.
- Incorporar cobertura por componente para representar solapamiento entre pruebas.

## Licencia

Este proyecto está disponible bajo la licencia incluida en `LICENSE`.

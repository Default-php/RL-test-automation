# Automatización de pruebas con aprendizaje por refuerzo

Este repositorio presenta un prototipo experimental para la priorización de casos de prueba mediante aprendizaje por refuerzo. El objetivo principal es evaluar si un agente basado en Q-learning puede seleccionar, bajo un presupuesto limitado de ejecución, un subconjunto de pruebas que maximice indicadores relevantes para la automatización de pruebas, tales como detección temprana de fallas, cobertura acumulada y eficiencia en el uso del tiempo.

El proyecto se plantea como una aproximación académica al problema de test case prioritization. En este contexto, cada caso de prueba se modela con atributos observables, entre ellos tiempo estimado de ejecución, probabilidad histórica de falla, ganancia de cobertura y prioridad funcional. A partir de dichos atributos, el entorno simula episodios de ejecución y entrega recompensas al agente según el valor esperado de cada selección.

## Objetivos

- Implementar un entorno simulado para priorización de pruebas automatizadas.
- Entrenar un agente de Q-learning tabular para seleccionar pruebas bajo restricciones de presupuesto.
- Comparar el desempeño del agente contra estrategias base: prioridad funcional, riesgo histórico y selección aleatoria.
- Registrar métricas cuantitativas que permitan analizar recompensa promedio, cobertura, detección de fallas y eficiencia por presupuesto.
- Proveer una interfaz web ligera que permita cargar conjuntos de prueba, ejecutar el motor y descargar un reporte de resultados.

## Estructura del repositorio

```text
core/
  agent.py          Implementación del agente Q-learning.
  baseline.py       Estrategias base para comparación experimental.
  environment.py    Entorno de simulación para ejecución de pruebas.
  evaluator.py      Funciones de evaluación y agregación de métricas.
  models.py         Modelo de datos para los casos de prueba.
  trainer.py        Ciclo de entrenamiento del agente.

data/
  sample_tests.json         Conjunto base de casos de prueba.
  payment_tests.json        Conjunto alternativo de pruebas.
  large_tests.json          Conjunto ampliado de pruebas.
  evaluation_results.json   Resultados agregados de la última ejecución.
  training_history.json     Historial de entrenamiento por episodio.

scripts/
  run_experiment.py  Punto de entrada de compatibilidad.

src/
  run_experiment.py  Punto de entrada principal para ejecutar experimentos.

test_prioritizer/
  settings.py  Configuración principal del proyecto Django.
  urls.py      Enrutamiento global de la aplicación web.

web/
  forms.py      Formulario de carga y selección de datasets.
  services.py   Capa de orquestación entre Django y el motor de aprendizaje por refuerzo.
  views.py      Vistas para entrada, resultados y descarga de reportes.
  templates/    Vistas HTML renderizadas con Django Templates.

manage.py         Utilidad de administración de Django.
requirements.txt  Dependencias mínimas del proyecto.
```

## Metodología

El agente utiliza Q-learning tabular. El estado del entorno se discretiza a partir de variables como pruebas pendientes, pruebas ejecutadas, cobertura acumulada, fallas detectadas, tiempo consumido, pasos ejecutados, presupuesto restante y máscara de pruebas ejecutadas.

En cada episodio, el agente selecciona acciones válidas que representan casos de prueba aún no ejecutados. La función de recompensa favorece pruebas con mayor probabilidad histórica de falla, mayor aporte de cobertura y selección temprana dentro del presupuesto disponible. También incorpora penalización por tiempo estimado de ejecución.

Para la evaluación, el agente entrenado se compara con tres líneas base:

- Baseline por prioridad: ejecuta primero los casos con mayor prioridad funcional.
- Baseline por riesgo: ejecuta primero los casos con mayor probabilidad histórica de falla.
- Baseline aleatorio: ejecuta los casos en un orden aleatorio reproducible mediante semilla.

## Ejecución del experimento

Desde la raíz del repositorio, el experimento puede ejecutarse con:

```powershell
py -m src.run_experiment --agent-seed 123 --output-dir data
```

Parámetros principales:

- `--data-file`: archivo JSON con los casos de prueba.
- `--output-dir`: directorio donde se guardan los resultados.
- `--training-episodes`: número de episodios de entrenamiento.
- `--evaluation-episodes`: número de episodios de evaluación.
- `--execution-budget`: cantidad máxima de pruebas por episodio.
- `--seed`: semilla del entorno y de las líneas base reproducibles.
- `--agent-seed`: semilla específica del agente Q-learning.

## Interfaz web Django

El proyecto incluye una capa de producto implementada con Django. Esta interfaz permite seleccionar un dataset incluido en `data/`, cargar un archivo JSON externo, validar la estructura del dataset, ejecutar el motor de priorización, visualizar la recomendación de orden de ejecución y comparar los resultados contra las líneas base disponibles.

Instalación de dependencias en Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python manage.py runserver
```

Ejecución equivalente desde Git Bash:

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
python manage.py runserver
```

Una vez iniciado el servidor, la aplicación queda disponible en:

```text
http://127.0.0.1:8000/
```

La interfaz web genera reportes JSON descargables en `outputs/web_reports/`. Este directorio se considera salida de ejecución y no forma parte del código fuente principal.

## Resultados experimentales

La última ejecución registrada utilizó los siguientes parámetros:

| Parámetro | Valor |
| --- | ---: |
| Presupuesto de ejecución | 3 |
| Semilla del entorno | 42 |
| Semilla del agente | 123 |
| Episodios de entrenamiento | 2000 |
| Episodios de evaluación | 100 |

Resumen de resultados agregados:

| Estrategia | Recompensa promedio | Cobertura promedio | Fallas promedio | Tasa de detección de fallas | Cobertura por presupuesto |
| --- | ---: | ---: | ---: | ---: | ---: |
| Agente Q-learning | 45.5266 | 0.4811 | 0.88 | 0.69 | 0.1604 |
| Baseline por prioridad | 45.7700 | 0.4200 | 0.85 | 0.68 | 0.1400 |
| Baseline por riesgo | 48.6000 | 0.5000 | 0.90 | 0.71 | 0.1667 |
| Baseline aleatorio | 35.3390 | 0.3935 | 0.65 | 0.56 | 0.1312 |

Los resultados muestran que el agente entrenado supera de forma clara a la estrategia aleatoria y presenta un comportamiento competitivo frente a la línea base por prioridad. En la ejecución registrada, la línea base por riesgo obtiene la mayor recompensa promedio y la mayor tasa de detección de fallas, lo que sugiere que la probabilidad histórica de falla es una variable especialmente relevante en el conjunto de datos utilizado. Este comportamiento también indica un punto de mejora para futuras iteraciones del agente y de la función de recompensa.

## Reproducibilidad

Los archivos generados por la ejecución se almacenan en `data/evaluation_results.json` y `data/training_history.json`. El primero contiene las métricas agregadas de evaluación, mientras que el segundo conserva el historial episodio por episodio del entrenamiento.

Para reproducir la ejecución documentada, se recomienda mantener las mismas semillas y parámetros:

```powershell
py -m src.run_experiment --agent-seed 123 --output-dir data
```

## Consideraciones futuras

- Evaluar el agente con conjuntos de pruebas de mayor escala y mayor variabilidad.
- Incorporar representaciones de estado más expresivas para capturar dependencias entre casos de prueba.
- Comparar Q-learning tabular con técnicas de aprendizaje por refuerzo profundo.
- Ajustar la función de recompensa para balancear de manera más precisa detección temprana, cobertura y costo temporal.
- Incorporar validación estadística sobre múltiples semillas de entrenamiento y evaluación.

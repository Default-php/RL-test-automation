# RL Test Automation - Technical Project Report

Generated on: 2026-06-19  
Repository path: `c:\Users\agarellano\Desktop\RL_test_automation`  
Current branch observed: `feature/test-prioritizer-dashboard`  
Remote observed: `https://github.com/Default-php/RL-test-automation`

## 1. Executive Summary

This project is a compact academic prototype for automated test case prioritization using reinforcement learning. It models a set of test cases as a simulated environment where an agent must choose which tests to execute under a fixed execution budget. The main goal is to maximize useful testing outcomes such as expected failure discovery, coverage gain, and efficient budget usage.

The implementation contains two user-facing workflows:

1. A command-line experiment runner in `src/run_experiment.py`.
2. A Django web interface in the `web/` app for dataset selection/upload, parameter entry, result visualization, and JSON report download.

The core learning logic is intentionally lightweight: it uses only Python standard library features plus a tabular Q-learning implementation. Django is the only declared third-party dependency.

Overall, the project is coherent, readable, and well scoped for a prototype. Its strongest parts are the separation between RL core and web orchestration, the clear dataset schema validation in the web layer, and the reproducible seed-based experiment configuration. The main limitations are that the agent is tabular and small-scale, test coverage is narrow, output persistence is file-based, and the Django settings are suitable for local prototype use rather than production.

## 2. Functional Purpose

The project solves a simulated version of the test case prioritization problem:

- Given a list of test cases.
- Each test case has execution cost, historical failure probability, coverage gain, and priority.
- The system has a limited budget, expressed as the maximum number of tests executable in one episode.
- The agent chooses the next test case to run.
- The environment simulates whether that test exposes a failure.
- Rewards are given based on expected failure value, early selection, coverage contribution, observed failures, and execution time penalty.
- After training, the learned agent is compared against baseline strategies.

The project does not execute real automated tests. It is a simulation engine and decision-support prototype. A test case in this system is metadata, not a direct link to Selenium, Playwright, pytest, Postman, or another real test runner.

## 3. Repository Structure

Tracked source-level files observed with `rg --files`:

```text
core/
  agent.py          Tabular Q-learning agent.
  baseline.py       Baseline ordering strategies.
  environment.py    Simulated test execution environment.
  evaluator.py      Agent/baseline evaluation and metrics aggregation.
  models.py         TestCase dataclass.
  trainer.py        Training loop.

data/
  sample_tests.json         Small built-in dataset.
  payment_tests.json        Payment-domain dataset.
  large_tests.json          Larger mixed-domain dataset.
  evaluation_results.json   Stored aggregate experiment result.
  training_history.json     Stored episode-by-episode training history.

src/
  run_experiment.py  Main CLI experiment runner.

scripts/
  run_experiment.py  Compatibility wrapper that delegates to src.run_experiment.

test_prioritizer/
  settings.py  Django project settings.
  urls.py      Root URL configuration.
  asgi.py      ASGI entry point.
  wsgi.py      WSGI entry point.

web/
  forms.py      Django form for dataset/parameter input.
  services.py   Orchestration, validation, report persistence.
  views.py      Home, results, and report download views.
  urls.py       Web app URL routes.
  tests.py      Dataset validation tests.
  templates/    Bootstrap-based HTML templates.

manage.py
requirements.txt
README.md
LICENSE
.gitignore
```

Additional local directories exist but are ignored by Git:

- `.venv/`: local virtual environment.
- `outputs/`: generated experiment/report artifacts.
- `docs/`: archived datasets/results copied outside the tracked source set.

The `.gitignore` explicitly ignores `docs/*` and `outputs/*`, so those directories should be considered generated/reference material rather than primary source.

## 4. Technology Stack

### Runtime

- Python: local virtualenv reports Python `3.14.3`.
- Django: installed from `requirements.txt` as `5.2.15`.
- HTML templates: Django Templates.
- CSS/UI: Bootstrap 5.3.3 via CDN plus inline custom CSS.

### Python Dependencies

`requirements.txt` contains:

```text
Django>=5.2,<6.0
```

After installing requirements, pip installed:

- `Django==5.2.15`
- `asgiref==3.11.1`
- `sqlparse==0.5.5`
- `tzdata==2026.2`

The RL core itself uses only the Python standard library:

- `dataclasses`
- `random`
- `json`
- `pathlib`
- `argparse`
- `typing`
- `collections.defaultdict`

### External Framework Notes

The Django web layer follows common Django patterns for:

- Binding uploaded files through `request.FILES`.
- Using Django forms for validation.
- Rendering server-side templates.
- Serving local static assets in development through `django.contrib.staticfiles`.

Relevant official Django documentation checked:

- https://docs.djangoproject.com/en/5.2/topics/http/file-uploads/
- https://docs.djangoproject.com/en/5.2/ref/settings/
- https://docs.djangoproject.com/en/5.2/howto/static-files/

## 5. Domain Model

The core domain entity is `TestCase` in `core/models.py`.

```python
@dataclass
class TestCase:
    id: int
    name: str
    estimated_time: float
    failure_probability: float
    coverage_gain: float
    priority: int = 1
    executed: bool = False
```

Field meaning:

- `id`: external identifier for the test case.
- `name`: human-readable test name.
- `estimated_time`: simulated execution cost. It is used as a reward penalty.
- `failure_probability`: probability that the simulated run exposes a failure.
- `coverage_gain`: simulated coverage gained by executing the test.
- `priority`: functional or business priority used by one baseline.
- `executed`: mutable execution flag used inside environment episodes.

The model is intentionally simple and serializable. There is no database model for test cases; datasets are JSON files or uploaded JSON content converted into dataclass instances.

## 6. Dataset Schema

The web layer validates datasets in `web/services.py`.

Required fields:

- `id`
- `name`
- `estimated_time`
- `failure_probability`
- `coverage_gain`

Optional fields:

- `priority`
- `executed`

Validation rules:

- Dataset must be a non-empty JSON array.
- Every item must be a JSON object.
- Missing required fields are rejected.
- Unsupported extra fields are rejected.
- `id` must be an integer and unique.
- `name` must be a non-empty string.
- `estimated_time` must be numeric and greater than zero.
- `failure_probability` must be numeric between `0` and `1`.
- `coverage_gain` must be numeric between `0` and `1`.
- `priority` must be an integer greater than zero.
- `executed` must be boolean if present.

Built-in datasets:

- `data/sample_tests.json`: 6 test cases around login/profile behavior.
- `data/payment_tests.json`: 10 payment-related test cases.
- `data/large_tests.json`: 12 broader workflow test cases.

The schema is strong enough for the current engine. For future integration with real test automation, it would need fields such as test command, suite, tags, owning component, historical failure source, dependency data, and execution environment.

## 7. Reinforcement Learning Core

### Environment

`core/environment.py` defines `TestEnvironment`.

Responsibilities:

- Clone original test cases at the start of each episode.
- Track pending and executed test indices.
- Track accumulated coverage, failures, time spent, step count, remaining budget, and an execution mask.
- Provide valid actions.
- Execute a selected action through `step(action)`.
- Simulate observed failure using `random.random() < failure_probability`.
- Calculate reward.
- Return next state, reward, done flag, and info dictionary.

State returned by `_get_state()`:

```text
pending_tests
executed_tests
coverage_accumulated
failures_detected
time_spent
steps
remaining_budget
executed_mask
```

The environment is order-sensitive because:

- Already executed tests are removed from valid actions.
- The `executed_mask` is part of the state.
- Reward uses an `early_weight` based on remaining budget.

The environment is budget-limited. An episode ends when:

- `remaining_budget <= 0`, or
- there are no pending tests left.

### Reward Function

The reward combines expected and observed test value:

```text
early_weight = 1 + ((remaining_budget - 1) / max(execution_budget - 1, 1))

expected_failure_reward = failure_probability * 30.0 * early_weight
coverage_reward = coverage_gain * 6.0
time_penalty = estimated_time

reward = expected_failure_reward + coverage_reward - time_penalty

if failed:
    reward += 10.0 * early_weight
```

Interpretation:

- High historical failure probability is strongly rewarded.
- High-risk tests are more valuable when selected earlier.
- Coverage gain contributes a smaller positive term.
- Longer tests reduce reward.
- Actually observed failures add extra reward.

This reward design explains why the risk baseline is a strong competitor: `failure_probability` is the dominant term in both the learned reward and the risk ordering strategy.

### Agent

`core/agent.py` defines `QLearningAgent`.

Key parameters:

- `alpha=0.15` in the experiment runner.
- `gamma=0.95`.
- Initial `epsilon=1.0`.
- `epsilon_min=0.02`.
- `epsilon_decay=0.995`.
- Optional `seed` for reproducible exploration/tie-breaking.

The Q-table type is:

```python
defaultdict(lambda: defaultdict(float))
```

State discretization converts the environment dictionary into an 8-item tuple:

```text
pending
executed
coverage_bin
failures
time_bin
steps
remaining_budget
executed_mask
```

Notable implementation detail:

- `coverage_accumulated` is binned with `int(coverage * 10)`.
- `time_spent` is binned with `int(time_spent)`.
- `executed_mask` keeps action history visible to the tabular agent.

Action selection:

- During training, epsilon-greedy exploration chooses a random valid action with probability `epsilon`.
- Otherwise, the agent chooses one of the currently best-valued valid actions.
- Ties are broken randomly through the agent's seeded RNG.

Learning update:

```text
Q(s,a) = Q(s,a) + alpha * (target - Q(s,a))
target = reward + gamma * max(Q(next_state, next_valid_action))
```

If the transition is terminal, `target = reward`.

### Trainer

`core/trainer.py` defines `Trainer`.

Training flow:

1. Reset environment.
2. Discretize state.
3. While episode is not done:
   - Get valid actions.
   - Select action with exploration enabled.
   - Step environment.
   - Update Q-table.
   - Accumulate episode metrics.
4. Decay epsilon.
5. Append episode summary to training history.

History entries include:

- Episode number.
- Total reward.
- Steps.
- Coverage.
- Failures detected.
- Time spent.
- Remaining budget.
- Budget used.
- Epsilon.

## 8. Baseline Strategies

Baselines are defined in `core/baseline.py` and evaluated in `core/evaluator.py`.

### Priority Baseline

Sorts tests by descending `priority`.

Strength:

- Simple, business-readable strategy.

Limitation:

- Does not consider failure risk, coverage, or execution time except indirectly through whatever priority represents.

### Risk Baseline

Sorts tests by:

1. Descending `failure_probability`.
2. Descending `coverage_gain`.
3. Shorter `estimated_time` as a tie-breaker.

Strength:

- Closely aligned with the reward function's dominant signal.

Limitation:

- Not adaptive and does not learn from episode outcomes.

### Random Baseline

Shuffles test indices using a seeded RNG.

Strength:

- Provides a low-information comparison floor.

Limitation:

- Metrics can be noisy, especially with few evaluation episodes.

## 9. Evaluation Metrics

`core/evaluator.py` evaluates the agent and baselines over multiple episodes and aggregates:

- `avg_reward`
- `avg_coverage`
- `avg_failures_detected`
- `avg_time_spent`
- `avg_steps`
- `avg_remaining_budget`
- `avg_budget_used`
- `avg_failures_per_budget`
- `avg_coverage_per_budget`
- `failure_detection_rate`
- `avg_first_failure_step`
- `sample_selected_actions`
- `sample_trace`

The `sample_trace` is especially useful for explaining a result to a human because it shows:

- Step number.
- Action index.
- Test id.
- Test name.
- Whether the simulated test failed.
- Reward for that step.

Current stored results in `data/evaluation_results.json` use:

- Execution budget: `3`
- Environment seed: `42`
- Agent seed: `123`
- Training episodes: `2000`
- Evaluation episodes: `100`

Stored aggregate results:

| Strategy | Avg reward | Avg coverage | Avg failures | Failure detection rate | Coverage per budget |
| --- | ---: | ---: | ---: | ---: | ---: |
| Q-learning agent | 45.5266 | 0.4811 | 0.88 | 0.69 | 0.1604 |
| Priority baseline | 45.7700 | 0.4200 | 0.85 | 0.68 | 0.1400 |
| Risk baseline | 48.6000 | 0.5000 | 0.90 | 0.71 | 0.1667 |
| Random baseline | 35.3390 | 0.3935 | 0.65 | 0.56 | 0.1312 |

Interpretation:

- The agent clearly beats random selection.
- The agent is competitive with the priority baseline.
- The risk baseline is the strongest stored result.
- The reward function currently favors risk heavily, so a simple risk sort is hard to beat on these small datasets.

## 10. Command-Line Workflow

Primary entry point:

```powershell
.\.venv\Scripts\python -m src.run_experiment
```

Useful parameters:

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

Default constants in `src/run_experiment.py`:

- `TRAINING_EPISODES = 2000`
- `EVALUATION_EPISODES = 100`
- `EXECUTION_BUDGET = 3`
- `SEED = 42`

Workflow:

1. Load test cases from JSON.
2. Build separate environments for training and each evaluation strategy.
3. Train Q-learning agent.
4. Build priority and risk orders.
5. Evaluate agent.
6. Evaluate priority baseline.
7. Evaluate risk baseline.
8. Evaluate random baseline.
9. Print summaries and traces.
10. Write `training_history.json`.
11. Write `evaluation_results.json`.

The compatibility wrapper at `scripts/run_experiment.py` simply imports and runs `src.run_experiment.main()`.

## 11. Web Workflow

The Django application is mounted at the root URL.

Routes:

```text
/                              web.views.home
/results/<report_id>/           web.views.results
/reports/<report_id>/download/  web.views.download_report
```

### Home Page

Template: `web/templates/web/home.html`

Allows users to:

- Select a built-in dataset from `data/*tests.json`.
- Upload a `.json` dataset.
- Configure training episodes.
- Configure evaluation episodes.
- Configure execution budget.
- Configure environment seed.
- Configure optional agent seed.

The form enforces that the user must choose exactly one dataset source:

- Built-in dataset, or
- Uploaded JSON file.

### Web Service Layer

`web/services.py` is the main orchestration layer between Django and the RL core.

Responsibilities:

- Discover built-in datasets.
- Load selected datasets.
- Read uploaded JSON files.
- Validate schema.
- Create cloned environments.
- Train the agent.
- Evaluate strategies.
- Build recommended order.
- Build comparison table rows.
- Save reports under `outputs/web_reports/`.
- Load and validate report IDs for result viewing/download.

The report ID is a random UUID hex string. The loader requires an alphanumeric ID, preventing direct path traversal through the report URL.

### Results Page

Template: `web/templates/web/results.html`

Displays:

- Dataset name and test case count.
- Agent reward.
- Agent coverage.
- Failure detection rate.
- Average budget used.
- Recommended execution order.
- Baseline comparison table.
- Run configuration.

The downloadable report is the raw JSON saved in `outputs/web_reports/<report_id>.json`.

## 12. Persistence and Artifacts

The project uses file-based persistence:

- CLI results go to the configured `output_dir`.
- Web reports go to `outputs/web_reports/`.
- Built-in datasets and sample stored results live under `data/`.

There is a configured SQLite database in Django settings, but the current app does not define database models or use database-backed persistence.

Important artifact categories:

- Source-controlled example data: `data/*.json`.
- Generated runtime output: `outputs/*`.
- Ignored archived/reference output: `docs/*`.

Because `outputs/*` and `docs/*` are ignored, users should not expect generated web reports to be committed unless ignore rules are changed.

## 13. Django Configuration Review

`test_prioritizer/settings.py` is local-prototype oriented.

Current settings include:

- `SECRET_KEY` hardcoded in source.
- `DEBUG = True`.
- `ALLOWED_HOSTS = ["127.0.0.1", "localhost"]`.
- Installed apps:
  - `django.contrib.staticfiles`
  - `web`
- Middleware:
  - security
  - common
  - CSRF
  - clickjacking protection
- SQLite database configured at `BASE_DIR / "db.sqlite3"`.
- Time zone: `America/Caracas`.
- Static URL: `static/`.

Assessment:

- Suitable for local development and academic demonstration.
- Not production-ready because secret management, debug mode, static file deployment, allowed hosts, logging, upload limits, and persistent storage are not hardened.

## 14. Testing and Verification

### Tests Present

`web/tests.py` contains three tests:

1. Valid dataset converts to `TestCase`.
2. Missing required field raises `DatasetValidationError`.
3. Uploaded JSON file is loaded correctly.

These tests focus on dataset validation and upload parsing. There are no direct unit tests for:

- Reward calculation.
- Environment transitions.
- Valid action behavior.
- Agent Q-table updates.
- Epsilon decay.
- Baseline ordering.
- Evaluator aggregation.
- CLI output writing.
- Django views and report download behavior.

### Commands Run During Review

Initial state:

- `git status --short` returned no local changes.
- `.venv` initially did not have Django installed, so `manage.py check` and `manage.py test` failed with `ModuleNotFoundError: No module named 'django'`.

Remediation for verification:

```powershell
.\.venv\Scripts\python -m pip install -r requirements.txt
```

Installed Django `5.2.15`.

Verification commands after installing dependencies:

```powershell
.\.venv\Scripts\python manage.py check
.\.venv\Scripts\python manage.py test
.\.venv\Scripts\python -m django --version
```

Results:

- Django system check: passed, `System check identified no issues`.
- Test suite: passed, `Ran 3 tests`, `OK`.
- Django version: `5.2.15`.

CLI smoke test:

```powershell
.\.venv\Scripts\python -m src.run_experiment `
  --data-file data\sample_tests.json `
  --output-dir outputs\review_smoke `
  --training-episodes 20 `
  --evaluation-episodes 5 `
  --execution-budget 3 `
  --seed 42 `
  --agent-seed 123
```

Result:

- Command completed successfully.
- Wrote:
  - `outputs/review_smoke/evaluation_results.json`
  - `outputs/review_smoke/training_history.json`

Smoke metrics from that short run:

| Strategy | Avg reward | Avg coverage | Avg failures | Failure detection rate |
| --- | ---: | ---: | ---: | ---: |
| Q-learning agent | 54.2120 | 0.4320 | 1.4 | 1.0 |
| Priority baseline | 56.8200 | 0.4200 | 1.4 | 1.0 |
| Risk baseline | 58.6500 | 0.5000 | 1.4 | 1.0 |
| Random baseline | 43.6620 | 0.4020 | 1.2 | 0.8 |

Because this smoke run uses only 20 training episodes and 5 evaluation episodes, it should be treated as a functional verification, not a scientific result.

## 15. Source Size Snapshot

Ignoring `.venv/`, `.git/`, `__pycache__/`, `outputs/`, and `docs/`, the project contains approximately:

| File type | Count | Lines |
| --- | ---: | ---: |
| Python | 24 | 1,136 |
| HTML | 3 | 285 |
| Markdown | 1 | 108 |
| JSON | 5 | 22,423 |
| Text | 1 | 1 |
| License/no extension | 1 | 17 |

The high JSON line count is mainly due to stored training history.

## 16. Strengths

Clear separation of concerns:

- `core/` is framework-independent.
- `src/` handles CLI execution.
- `web/` handles Django UI and orchestration.

Reproducibility:

- Environment seed and agent seed are configurable.
- CLI and web workflows expose the relevant experiment parameters.

Explainability:

- Evaluation output includes sample traces.
- The web UI shows recommended order and baseline comparisons.

Validation:

- Web-uploaded datasets are validated before reaching the RL engine.
- File/report IDs are checked to reduce path traversal risk.

Low dependency footprint:

- The core can run without ML frameworks.
- This makes the project easy to inspect and teach.

## 17. Limitations and Risks

### Scientific/Algorithmic Limitations

The reward function heavily favors `failure_probability`. This makes the risk baseline naturally strong and may reduce the observed value of learning.

The current environment does not model:

- Real test dependencies.
- Flaky tests.
- Component-level coverage overlap.
- Test setup/teardown cost.
- Parallel execution.
- Historical trends over time.
- Real feedback from CI systems.

The Q-learning state representation is tabular. It can work for small datasets, but state/action space grows quickly with more tests, especially because `executed_mask` encodes combinations of executed tests.

Coverage is accumulated as a simple sum. There is no cap or set-based representation, so overlapping coverage cannot be represented.

Evaluation uses repeated stochastic failure simulation from fixed probabilities. This is useful for the prototype, but not equivalent to validating against real historical execution logs.

### Engineering Limitations

There is no CI configuration under `.github/`.

Test coverage is narrow and mostly validates web dataset parsing.

The CLI loader in `src/run_experiment.py` directly constructs `TestCase(**item)` and does not reuse the stricter validation from `web/services.py`. Invalid CLI datasets may fail with less friendly errors or allow fields that the web layer rejects.

Output files are overwritten by the CLI when using the same output directory.

The web workflow is synchronous. Long training runs will block the HTTP request and may time out under a real server.

The virtualenv initially lacked installed dependencies, so a fresh local run required `pip install -r requirements.txt`.

### Security and Deployment Limitations

The Django configuration is not production-ready:

- `SECRET_KEY` is committed.
- `DEBUG = True`.
- `ALLOWED_HOSTS` is local-only.
- No upload size limit is configured in the app.
- Uploaded files are read fully into memory in `load_uploaded_dataset`.
- Reports are stored as local JSON files without authentication or cleanup.
- Bootstrap is loaded from a CDN without local pinning or SRI attributes.

These are acceptable for a local prototype but should be addressed before any shared deployment.

## 18. Recommended Improvements

### Highest Priority

1. Add tests for the RL core:
   - Environment reset and step behavior.
   - Invalid action rejection.
   - Reward calculation.
   - Agent Q-table update.
   - Baseline ordering.
   - Evaluator aggregation.

2. Share dataset validation between CLI and web:
   - Move validation to a core-level dataset loader.
   - Use it from both `src/run_experiment.py` and `web/services.py`.

3. Add CI:
   - Run `python -m pip install -r requirements.txt`.
   - Run `python manage.py check`.
   - Run `python manage.py test`.
   - Run a short CLI smoke test.

4. Add a production/local settings split:
   - Read `SECRET_KEY`, `DEBUG`, and `ALLOWED_HOSTS` from environment variables.
   - Keep local defaults explicit.

### Algorithmic Improvements

1. Evaluate across multiple seeds and report mean/stddev.
2. Add statistical comparison between agent and baselines.
3. Introduce coverage overlap or component-level coverage vectors.
4. Add execution-time budget as time capacity, not only number of tests.
5. Explore reward variants that better balance risk, coverage, priority, and cost.
6. Add a no-learning greedy policy aligned with the reward to clarify whether Q-learning adds value.

### Product/Web Improvements

1. Run long jobs asynchronously through a task queue or background worker.
2. Add progress/status reporting for web runs.
3. Store reports in a database or structured artifact store.
4. Add report retention/cleanup.
5. Add validation for uploaded file size.
6. Add view tests for form submissions, result pages, and downloads.

### Documentation Improvements

1. Add a short "fresh setup" section that explicitly installs dependencies before running Django commands.
2. Document the JSON schema in a standalone file.
3. Include a diagram of the CLI and web flows.
4. Document what the project does not do: it does not run real tests yet.
5. Add guidance for interpreting stochastic evaluation results.

## 19. Suggested Future Architecture

A natural next version could split the system into these layers:

```text
core/
  domain models
  dataset validation
  environment
  policies/baselines
  training/evaluation

adapters/
  json dataset loader
  historical CI log loader
  report writer

interfaces/
  cli
  django web
  future API

storage/
  database-backed experiments
  report artifacts
```

For real-world test automation, the project would need an integration layer that maps selected test cases to actual executable tests. Example future fields:

```json
{
  "id": 1,
  "name": "Login with valid credentials",
  "command": "pytest tests/e2e/test_login.py::test_valid_login",
  "suite": "e2e",
  "component": "auth",
  "estimated_time": 1.2,
  "failure_probability": 0.25,
  "coverage_gain": 0.14,
  "priority": 5,
  "tags": ["auth", "smoke"]
}
```

That would allow the prioritizer to become part of a real CI workflow instead of remaining a simulation-only decision engine.

## 20. Final Assessment

This is a well-contained prototype for demonstrating reinforcement learning applied to automated test prioritization. It is strongest as an academic or exploratory tool: the logic is easy to follow, experiments are reproducible, and the Django interface makes the concept usable without requiring command-line access.

The project is not yet a production test automation system. It does not execute real tests, persist experiments in a database, run jobs asynchronously, or validate model quality across broader statistical scenarios. The next best engineering step is to strengthen test coverage and unify dataset validation. The next best research step is to evaluate whether the RL agent adds value beyond a reward-aligned greedy/risk policy across more datasets and seeds.


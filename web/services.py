from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from core.agent import QLearningAgent
from core.baseline import priority_baseline_order, risk_baseline_order
from core.environment import TestEnvironment
from core.evaluator import evaluate_agent, evaluate_baseline, evaluate_random_baseline
from core.models import TestCase
from core.trainer import Trainer


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
REPORT_DIR = BASE_DIR / "outputs" / "web_reports"

REQUIRED_FIELDS = {
    "id",
    "name",
    "estimated_time",
    "failure_probability",
    "coverage_gain",
}
ALLOWED_FIELDS = REQUIRED_FIELDS | {"priority", "executed"}

STRATEGY_LABELS = {
    "agent": "Q-learning agent",
    "priority_baseline": "Priority baseline",
    "risk_baseline": "Risk baseline",
    "random_baseline": "Random baseline",
}


class DatasetValidationError(ValueError):
    """Raised when an uploaded or selected dataset does not match the schema."""


def available_dataset_choices() -> list[tuple[str, str]]:
    choices = []
    for path in sorted(DATA_DIR.glob("*tests.json")):
        label = path.stem.replace("_", " ").title()
        choices.append((path.name, label))
    return choices


def load_builtin_dataset(filename: str) -> tuple[list[TestCase], str]:
    if Path(filename).name != filename:
        raise DatasetValidationError("Invalid dataset name.")

    path = DATA_DIR / filename
    if not path.exists():
        raise DatasetValidationError("The selected dataset does not exist.")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DatasetValidationError(f"Invalid JSON syntax: {exc.msg}.") from exc

    return validate_dataset(data), path.name


def load_uploaded_dataset(uploaded_file: Any) -> tuple[list[TestCase], str]:
    try:
        raw_content = uploaded_file.read()
        text_content = raw_content.decode("utf-8")
        data = json.loads(text_content)
    except UnicodeDecodeError as exc:
        raise DatasetValidationError("The uploaded file must be encoded as UTF-8.") from exc
    except json.JSONDecodeError as exc:
        raise DatasetValidationError(f"Invalid JSON syntax: {exc.msg}.") from exc

    return validate_dataset(data), uploaded_file.name


def validate_dataset(data: Any) -> list[TestCase]:
    if not isinstance(data, list):
        raise DatasetValidationError("The dataset must be a JSON array of test cases.")

    if not data:
        raise DatasetValidationError("The dataset must include at least one test case.")

    test_cases: list[TestCase] = []
    seen_ids: set[int] = set()

    for index, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise DatasetValidationError(f"Item {index} must be a JSON object.")

        missing_fields = REQUIRED_FIELDS - set(item)
        if missing_fields:
            fields = ", ".join(sorted(missing_fields))
            raise DatasetValidationError(f"Item {index} is missing: {fields}.")

        extra_fields = set(item) - ALLOWED_FIELDS
        if extra_fields:
            fields = ", ".join(sorted(extra_fields))
            raise DatasetValidationError(f"Item {index} has unsupported fields: {fields}.")

        test_id = _require_int(item["id"], f"Item {index} id")
        if test_id in seen_ids:
            raise DatasetValidationError(f"Duplicated test case id: {test_id}.")
        seen_ids.add(test_id)

        name = item["name"]
        if not isinstance(name, str) or not name.strip():
            raise DatasetValidationError(f"Item {index} name must be a non-empty string.")

        estimated_time = _require_number(
            item["estimated_time"], f"Item {index} estimated_time"
        )
        if estimated_time <= 0:
            raise DatasetValidationError(
                f"Item {index} estimated_time must be greater than zero."
            )

        failure_probability = _require_number(
            item["failure_probability"], f"Item {index} failure_probability"
        )
        if not 0 <= failure_probability <= 1:
            raise DatasetValidationError(
                f"Item {index} failure_probability must be between 0 and 1."
            )

        coverage_gain = _require_number(item["coverage_gain"], f"Item {index} coverage_gain")
        if not 0 <= coverage_gain <= 1:
            raise DatasetValidationError(f"Item {index} coverage_gain must be between 0 and 1.")

        priority = _require_int(item.get("priority", 1), f"Item {index} priority")
        if priority < 1:
            raise DatasetValidationError(f"Item {index} priority must be greater than zero.")

        executed = item.get("executed", False)
        if not isinstance(executed, bool):
            raise DatasetValidationError(f"Item {index} executed must be a boolean.")

        test_cases.append(
            TestCase(
                id=test_id,
                name=name.strip(),
                estimated_time=float(estimated_time),
                failure_probability=float(failure_probability),
                coverage_gain=float(coverage_gain),
                priority=priority,
                executed=executed,
            )
        )

    return test_cases


def run_prioritization(
    test_cases: list[TestCase],
    dataset_name: str,
    training_episodes: int,
    evaluation_episodes: int,
    execution_budget: int,
    seed: int,
    agent_seed: int | None,
) -> dict[str, Any]:
    resolved_agent_seed = seed if agent_seed is None else agent_seed

    train_env = _build_environment(test_cases, execution_budget, seed)
    agent = QLearningAgent(
        alpha=0.15,
        gamma=0.95,
        epsilon=1.0,
        epsilon_min=0.02,
        epsilon_decay=0.995,
        seed=resolved_agent_seed,
    )

    trainer = Trainer(env=train_env, agent=agent)
    training_history = trainer.train(episodes=training_episodes)

    agent_results = evaluate_agent(
        env=_build_environment(test_cases, execution_budget, seed),
        agent=agent,
        episodes=evaluation_episodes,
    )
    priority_results = evaluate_baseline(
        env=_build_environment(test_cases, execution_budget, seed),
        order=priority_baseline_order(test_cases),
        episodes=evaluation_episodes,
        name="priority_baseline",
    )
    risk_results = evaluate_baseline(
        env=_build_environment(test_cases, execution_budget, seed),
        order=risk_baseline_order(test_cases),
        episodes=evaluation_episodes,
        name="risk_baseline",
    )
    random_results = evaluate_random_baseline(
        env=_build_environment(test_cases, execution_budget, seed),
        test_cases=test_cases,
        episodes=evaluation_episodes,
        seed=seed,
        name="random_baseline",
    )

    evaluation_results = {
        "agent": agent_results,
        "priority_baseline": priority_results,
        "risk_baseline": risk_results,
        "random_baseline": random_results,
    }

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_name": dataset_name,
        "test_case_count": len(test_cases),
        "execution_budget": execution_budget,
        "seed": seed,
        "agent_seed": resolved_agent_seed,
        "training_episodes": training_episodes,
        "evaluation_episodes": evaluation_episodes,
        "training_summary": training_history[-1],
        "recommended_order": _build_recommended_order(agent_results),
        "comparison_rows": _build_comparison_rows(evaluation_results),
        "evaluation_results": evaluation_results,
    }
    return result


def save_report(result: dict[str, Any]) -> str:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_id = uuid4().hex
    report = {**result, "report_id": report_id}
    report_path = REPORT_DIR / f"{report_id}.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report_id


def load_report(report_id: str) -> dict[str, Any]:
    if not report_id.isalnum():
        raise FileNotFoundError("Invalid report id.")

    report_path = REPORT_DIR / f"{report_id}.json"
    if not report_path.exists():
        raise FileNotFoundError("Report not found.")

    return json.loads(report_path.read_text(encoding="utf-8"))


def report_path(report_id: str) -> Path:
    if not report_id.isalnum():
        raise FileNotFoundError("Invalid report id.")

    path = REPORT_DIR / f"{report_id}.json"
    if not path.exists():
        raise FileNotFoundError("Report not found.")
    return path


def _build_environment(
    test_cases: list[TestCase],
    execution_budget: int,
    seed: int,
) -> TestEnvironment:
    cloned_cases = [TestCase(**asdict(test_case)) for test_case in test_cases]
    return TestEnvironment(
        test_cases=cloned_cases,
        execution_budget=execution_budget,
        seed=seed,
    )


def _build_recommended_order(agent_results: dict[str, Any]) -> list[dict[str, Any]]:
    order = []
    for item in agent_results["sample_trace"]:
        order.append(
            {
                "position": item["step"],
                "test_id": item["id"],
                "name": item["name"],
                "action": item["action"],
                "observed_failure": item["failed"],
                "reward": item["reward"],
            }
        )
    return order


def _build_comparison_rows(
    evaluation_results: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    rows = []
    for key in ["agent", "priority_baseline", "risk_baseline", "random_baseline"]:
        metrics = evaluation_results[key]
        rows.append(
            {
                "label": STRATEGY_LABELS[key],
                "avg_reward": metrics["avg_reward"],
                "avg_coverage": metrics["avg_coverage"],
                "avg_failures_detected": metrics["avg_failures_detected"],
                "avg_first_failure_step": metrics["avg_first_failure_step"],
                "avg_budget_used": metrics["avg_budget_used"],
                "failure_detection_rate": metrics["failure_detection_rate"],
                "sample_selected_actions": " -> ".join(
                    str(action) for action in metrics["sample_selected_actions"]
                ),
            }
        )
    return rows


def _require_number(value: Any, field_name: str) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise DatasetValidationError(f"{field_name} must be numeric.")
    return value


def _require_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise DatasetValidationError(f"{field_name} must be an integer.")
    return value

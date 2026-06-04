import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.agent import QLearningAgent
from core.baseline import priority_baseline_order, risk_baseline_order
from core.environment import TestEnvironment
from core.evaluator import evaluate_agent, evaluate_baseline, evaluate_random_baseline
from core.models import TestCase
from core.trainer import Trainer


TRAINING_EPISODES = 2000
EVALUATION_EPISODES = 100
EXECUTION_BUDGET = 3
SEED = 42


def load_test_cases(file_path: str) -> list[TestCase]:
    path = Path(file_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    return [TestCase(**item) for item in data]


def main() -> None:
    test_cases = load_test_cases("data/sample_tests.json")

    execution_budget = EXECUTION_BUDGET
    seed = SEED

    train_env = TestEnvironment(
        test_cases=test_cases,
        execution_budget=execution_budget,
        seed=seed,
    )

    eval_env_agent = TestEnvironment(
        test_cases=test_cases,
        execution_budget=execution_budget,
        seed=seed,
    )

    eval_env_priority = TestEnvironment(
        test_cases=test_cases,
        execution_budget=execution_budget,
        seed=seed,
    )

    eval_env_random = TestEnvironment(
        test_cases=test_cases,
        execution_budget=execution_budget,
        seed=seed,
    )

    eval_env_risk = TestEnvironment(
        test_cases=test_cases,
        execution_budget=execution_budget,
        seed=seed,
    )

    agent = QLearningAgent(
        alpha=0.15,
        gamma=0.95,
        epsilon=1.0,
        epsilon_min=0.02,
        epsilon_decay=0.995,
        seed=seed,
    )

    trainer = Trainer(env=train_env, agent=agent)
    training_history = trainer.train(episodes=TRAINING_EPISODES)

    priority_order = priority_baseline_order(test_cases)
    risk_order = risk_baseline_order(test_cases)

    agent_results = evaluate_agent(
        env=eval_env_agent,
        agent=agent,
        episodes=EVALUATION_EPISODES,
    )

    priority_results = evaluate_baseline(
        env=eval_env_priority,
        order=priority_order,
        episodes=EVALUATION_EPISODES,
        name="priority_baseline",
    )

    risk_results = evaluate_baseline(
        env=eval_env_risk,
        order=risk_order,
        episodes=EVALUATION_EPISODES,
        name="risk_baseline",
    )

    random_results = evaluate_random_baseline(
        env=eval_env_random,
        test_cases=test_cases,
        episodes=EVALUATION_EPISODES,
        seed=seed,
        name="random_baseline",
    )

    print("\nTRAINING SUMMARY")
    print("-" * 40)
    print(f"Episodes trained: {len(training_history)}")
    print(f"Evaluation episodes: {EVALUATION_EPISODES}")
    print(f"Execution budget per episode: {execution_budget}")
    print(f"Seed: {seed}")
    print(f"Final epsilon: {agent.epsilon:.4f}")
    print(f"Last episode reward: {training_history[-1]['total_reward']:.4f}")
    print(f"Last episode coverage: {training_history[-1]['coverage']:.4f}")
    print(f"Last episode failures detected: {training_history[-1]['failures_detected']}")
    print(f"Last episode time spent: {training_history[-1]['time_spent']:.4f}")
    print(f"Last episode budget used: {training_history[-1]['budget_used']}")

    print("\nAGENT RESULTS")
    print("-" * 40)
    print(json.dumps(agent_results, indent=2))

    print("\nPRIORITY BASELINE RESULTS")
    print("-" * 40)
    print(json.dumps(priority_results, indent=2))

    print("\nRISK BASELINE RESULTS")
    print("-" * 40)
    print(json.dumps(risk_results, indent=2))

    print("\nRANDOM BASELINE RESULTS")
    print("-" * 40)
    print(json.dumps(random_results, indent=2))

    print("\nSAMPLE ORDER TRACES")
    print("-" * 40)
    print(f"Agent sample actions: {agent_results['sample_selected_actions']}")
    print(f"Priority sample actions: {priority_results['sample_selected_actions']}")
    print(f"Risk sample actions: {risk_results['sample_selected_actions']}")
    print(f"Random sample actions: {random_results['sample_selected_actions']}")

    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    (output_dir / "training_history.json").write_text(
        json.dumps(training_history, indent=2),
        encoding="utf-8",
    )

    (output_dir / "evaluation_results.json").write_text(
        json.dumps(
            {
                "execution_budget": execution_budget,
                "seed": seed,
                "training_episodes": TRAINING_EPISODES,
                "evaluation_episodes": EVALUATION_EPISODES,
                "agent": agent_results,
                "priority_baseline": priority_results,
                "risk_baseline": risk_results,
                "random_baseline": random_results,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print("\nResults saved in ./outputs")


if __name__ == "__main__":
    main()

import json
from pathlib import Path

from core.agent import QLearningAgent
from core.baseline import priority_baseline_order
from core.environment import TestEnvironment
from core.evaluator import evaluate_agent, evaluate_baseline
from core.models import TestCase
from core.trainer import Trainer


def load_test_cases(file_path: str) -> list[TestCase]:
    path = Path(file_path)
    data = json.loads(path.read_text(encoding="utf-8"))

    return [TestCase(**item) for item in data]


def main() -> None:
    test_cases = load_test_cases("data/sample_tests.json")

    env = TestEnvironment(test_cases=test_cases, seed=42)
    agent = QLearningAgent(
        alpha=0.15,
        gamma=0.95,
        epsilon=1.0,
        epsilon_min=0.05,
        epsilon_decay=0.99,
        seed=42,
    )

    trainer = Trainer(env=env, agent=agent)
    training_history = trainer.train(episodes=200)

    baseline_order = priority_baseline_order(test_cases)

    agent_results = evaluate_agent(env=env, agent=agent, episodes=20)
    baseline_results = evaluate_baseline(env=env, order=baseline_order, episodes=20)

    print("\nTRAINING SUMMARY")
    print("-" * 40)
    print(f"Episodes trained: {len(training_history)}")
    print(f"Final epsilon: {agent.epsilon:.4f}")
    print(f"Last episode reward: {training_history[-1]['total_reward']:.4f}")

    print("\nAGENT RESULTS")
    print("-" * 40)
    print(json.dumps(agent_results, indent=2))

    print("\nBASELINE RESULTS")
    print("-" * 40)
    print(json.dumps(baseline_results, indent=2))

    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    (output_dir / "training_history.json").write_text(
        json.dumps(training_history, indent=2),
        encoding="utf-8",
    )
    (output_dir / "evaluation_results.json").write_text(
        json.dumps(
            {
                "agent": agent_results,
                "baseline": baseline_results,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print("\nResults saved in ./outputs")


if __name__ == "__main__":
    main()
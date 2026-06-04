from __future__ import annotations

from typing import Any, Dict, List

from core.agent import QLearningAgent
from core.environment import TestEnvironment


def _run_order_policy(env: TestEnvironment, order: List[int]) -> Dict[str, Any]:
    state = env.reset()
    done = False
    total_reward = 0.0
    ordered_copy = list(order)

    while not done:
        valid_actions = env.valid_actions()

        action = None
        for candidate in ordered_copy:
            if candidate in valid_actions:
                action = candidate
                ordered_copy.remove(candidate)
                break

        if action is None:
            action = valid_actions[0]

        state, reward, done, _info = env.step(action)
        total_reward += reward

    return {
        "total_reward": round(total_reward, 4),
        "coverage": round(env.coverage_accumulated, 4),
        "failures_detected": env.failures_detected,
        "time_spent": round(env.time_spent, 4),
        "steps": env.steps,
        "remaining_budget": env.remaining_budget,
        "budget_used": env.execution_budget - env.remaining_budget,
    }


def evaluate_agent(
    env: TestEnvironment,
    agent: QLearningAgent,
    episodes: int = 20,
) -> Dict[str, Any]:
    previous_epsilon = agent.epsilon
    agent.set_greedy_mode()

    results = []
    for _ in range(episodes):
        state = env.reset()
        state_key = agent.discretize_state(state)
        done = False
        total_reward = 0.0

        while not done:
            valid_actions = env.valid_actions()
            action = agent.select_action(state_key, valid_actions, explore=False)

            next_state, reward, done, _info = env.step(action)
            state_key = agent.discretize_state(next_state)
            total_reward += reward

        results.append(
            {
                "total_reward": total_reward,
                "coverage": env.coverage_accumulated,
                "failures_detected": env.failures_detected,
                "time_spent": env.time_spent,
                "steps": env.steps,
                "remaining_budget": env.remaining_budget,
                "budget_used": env.execution_budget - env.remaining_budget,
            }
        )

    agent.epsilon = previous_epsilon
    return _aggregate_results("agent", results)


def evaluate_baseline(
    env: TestEnvironment,
    order: List[int],
    episodes: int = 20,
    name: str = "baseline",
) -> Dict[str, Any]:
    results = []
    for _ in range(episodes):
        results.append(_run_order_policy(env, order))

    return _aggregate_results(name, results)


def _aggregate_results(name: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
    count = len(results)

    return {
        "name": name,
        "episodes": count,
        "avg_reward": round(sum(r["total_reward"] for r in results) / count, 4),
        "avg_coverage": round(sum(r["coverage"] for r in results) / count, 4),
        "avg_failures_detected": round(
            sum(r["failures_detected"] for r in results) / count, 4
        ),
        "avg_time_spent": round(sum(r["time_spent"] for r in results) / count, 4),
        "avg_steps": round(sum(r["steps"] for r in results) / count, 4),
        "avg_remaining_budget": round(
            sum(r["remaining_budget"] for r in results) / count, 4
        ),
        "avg_budget_used": round(sum(r["budget_used"] for r in results) / count, 4),
    }
from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from core.agent import QLearningAgent
from core.environment import TestEnvironment
from core.models import TestCase


def _run_order_policy(env: TestEnvironment, order: List[int]) -> Dict[str, Any]:
    env.reset()
    done = False
    total_reward = 0.0
    ordered_copy = list(order)
    selected_actions: List[int] = []
    first_failure_step: Optional[int] = None

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

        next_state, reward, done, info = env.step(action)
        total_reward += reward
        selected_actions.append(action)

        if info.get("failed") and first_failure_step is None:
            first_failure_step = len(selected_actions)

    return {
        "total_reward": round(total_reward, 4),
        "coverage": round(env.coverage_accumulated, 4),
        "failures_detected": env.failures_detected,
        "time_spent": round(env.time_spent, 4),
        "steps": env.steps,
        "remaining_budget": env.remaining_budget,
        "budget_used": env.execution_budget - env.remaining_budget,
        "selected_actions": selected_actions,
        "first_failure_step": first_failure_step,
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
        selected_actions: List[int] = []
        first_failure_step: Optional[int] = None

        while not done:
            valid_actions = env.valid_actions()
            action = agent.select_action(state_key, valid_actions, explore=False)

            next_state, reward, done, info = env.step(action)
            state_key = agent.discretize_state(next_state)
            total_reward += reward
            selected_actions.append(action)

            if info.get("failed") and first_failure_step is None:
                first_failure_step = len(selected_actions)

        results.append(
            {
                "total_reward": total_reward,
                "coverage": env.coverage_accumulated,
                "failures_detected": env.failures_detected,
                "time_spent": env.time_spent,
                "steps": env.steps,
                "remaining_budget": env.remaining_budget,
                "budget_used": env.execution_budget - env.remaining_budget,
                "selected_actions": selected_actions,
                "first_failure_step": first_failure_step,
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


def evaluate_random_baseline(
    env: TestEnvironment,
    test_cases: List[TestCase],
    episodes: int = 20,
    seed: Optional[int] = None,
    name: str = "random_baseline",
) -> Dict[str, Any]:
    rng = random.Random(seed)
    results = []

    for _ in range(episodes):
        order = list(range(len(test_cases)))
        rng.shuffle(order)
        results.append(_run_order_policy(env, order))

    return _aggregate_results(name, results)


def _aggregate_results(name: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
    count = len(results)
    failures_in_episodes = [r for r in results if r["failures_detected"] > 0]
    first_failure_steps = [
        r["first_failure_step"] for r in results if r["first_failure_step"] is not None
    ]

    avg_first_failure_step = None
    if first_failure_steps:
        avg_first_failure_step = round(
            sum(first_failure_steps) / len(first_failure_steps), 4
        )

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
        "failure_detection_rate": round(len(failures_in_episodes) / count, 4),
        "avg_first_failure_step": avg_first_failure_step,
        "sample_selected_actions": results[0]["selected_actions"] if results else [],
    }
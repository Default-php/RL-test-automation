from __future__ import annotations

import random
from dataclasses import asdict
from typing import Any, Dict, List, Optional, Tuple

from core.models import TestCase


class TestEnvironment:
    """
    Simulation environment for test prioritization using reinforcement learning.

    The agent selects which test case to execute next, but execution is limited
    by a fixed budget. This makes prioritization meaningful because not all
    tests can be executed in each episode.
    """

    def __init__(
        self,
        test_cases: List[TestCase],
        execution_budget: int = 3,
        seed: Optional[int] = None,
    ):
        if execution_budget <= 0:
            raise ValueError("execution_budget must be greater than zero.")

        self.original_test_cases = test_cases
        self.execution_budget = execution_budget
        self.random = random.Random(seed)
        self.reset()

    def reset(self) -> Dict[str, Any]:
        """
        Resets the environment to its initial state for a new episode.
        """
        self.test_cases = [TestCase(**asdict(tc)) for tc in self.original_test_cases]
        self.pending_indices = list(range(len(self.test_cases)))
        self.executed_indices: List[int] = []

        self.coverage_accumulated = 0.0
        self.failures_detected = 0
        self.time_spent = 0.0
        self.steps = 0
        self.remaining_budget = self.execution_budget
        self.executed_mask = 0

        return self._get_state()

    def _get_state(self) -> Dict[str, Any]:
        """
        Returns the current observable state of the environment.
        """
        return {
            "pending_tests": len(self.pending_indices),
            "executed_tests": len(self.executed_indices),
            "coverage_accumulated": round(self.coverage_accumulated, 4),
            "failures_detected": self.failures_detected,
            "time_spent": round(self.time_spent, 4),
            "steps": self.steps,
            "remaining_budget": self.remaining_budget,
            "executed_mask": self.executed_mask,
        }

    def valid_actions(self) -> List[int]:
        """
        Returns the list of available test indices that can still be executed.
        """
        return list(self.pending_indices)

    def step(self, action: int) -> Tuple[Dict[str, Any], float, bool, Dict[str, Any]]:
        """
        Executes a selected test case and returns:
        next_state, reward, done, info
        """
        if action not in self.pending_indices:
            raise ValueError(f"Invalid action: test case {action} is not available.")

        test_case = self.test_cases[action]

        # Simulate whether the test exposes a failure.
        failed = self.random.random() < test_case.failure_probability

        # Reward design for budget-limited prioritization:
        # - favor tests with a high expected probability of exposing failures
        # - increase that signal when the test is selected earlier
        # - keep smaller terms for observed failures, coverage, and execution time
        reward = 0.0

        early_weight = 1.0 + (
            (self.remaining_budget - 1) / max(self.execution_budget - 1, 1)
        )
        expected_failure_reward = test_case.failure_probability * 30.0 * early_weight
        coverage_reward = test_case.coverage_gain * 6.0
        time_penalty = test_case.estimated_time

        reward += expected_failure_reward
        reward += coverage_reward
        reward -= time_penalty

        if failed:
            observed_failure_reward = 10.0 * early_weight
            reward += observed_failure_reward
            self.failures_detected += 1

        self.coverage_accumulated += test_case.coverage_gain
        self.time_spent += test_case.estimated_time
        self.steps += 1
        self.remaining_budget -= 1

        self.pending_indices.remove(action)
        self.executed_indices.append(action)
        self.executed_mask |= 1 << action
        test_case.executed = True

        done = self.remaining_budget <= 0 or len(self.pending_indices) == 0

        info = {
            "test_case": asdict(test_case),
            "failed": failed,
            "remaining_budget": self.remaining_budget,
            "reward": round(reward, 4),
            "early_weight": round(early_weight, 4),
        }

        return self._get_state(), reward, done, info

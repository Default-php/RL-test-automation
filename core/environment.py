from __future__ import annotations

import random
from dataclasses import asdict
from typing import List, Tuple, Dict, Any, Optional

from core.models import TestCase


class TestEnvironment:
    """
    Simulation environment for test prioritization using reinforcement learning.
    The agent selects the next test case to execute.
    """

    def __init__(
        self,
        test_cases: List[TestCase],
        max_steps: Optional[int] = None,
        seed: Optional[int] = None,
    ):
        self.original_test_cases = test_cases
        self.max_steps = max_steps if max_steps is not None else len(test_cases)
        self.random = random.Random(seed)
        self.reset()

    def reset(self) -> Dict[str, Any]:
        self.test_cases = [
            TestCase(**asdict(tc)) for tc in self.original_test_cases
        ]
        self.pending_indices = list(range(len(self.test_cases)))
        self.executed_indices = []
        self.coverage_accumulated = 0.0
        self.failures_detected = 0
        self.time_spent = 0.0
        self.steps = 0
        return self._get_state()

    def _get_state(self) -> Dict[str, Any]:
        pending = len(self.pending_indices)
        return {
            "pending_tests": pending,
            "executed_tests": len(self.executed_indices),
            "coverage_accumulated": round(self.coverage_accumulated, 4),
            "failures_detected": self.failures_detected,
            "time_spent": round(self.time_spent, 4),
            "steps": self.steps,
        }

    def valid_actions(self) -> List[int]:
        return list(self.pending_indices)

    def step(self, action: int) -> Tuple[Dict[str, Any], float, bool, Dict[str, Any]]:
        if action not in self.pending_indices:
            raise ValueError(f"Invalid action: test case {action} is not available.")

        test_case = self.test_cases[action]

        # Simulate execution outcome
        failed = self.random.random() < test_case.failure_probability

        reward = 0.0
        if failed:
            self.failures_detected += 1
            reward += 10.0

        reward += test_case.coverage_gain * 5.0
        reward -= test_case.estimated_time * 1.5

        self.coverage_accumulated += test_case.coverage_gain
        self.time_spent += test_case.estimated_time
        self.steps += 1

        self.pending_indices.remove(action)
        self.executed_indices.append(action)
        test_case.executed = True

        done = len(self.pending_indices) == 0 or self.steps >= self.max_steps

        info = {
            "test_case": asdict(test_case),
            "failed": failed,
        }

        return self._get_state(), reward, done, info
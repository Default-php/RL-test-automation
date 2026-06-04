from collections import defaultdict
from typing import Any, DefaultDict, Dict, List, Tuple
import random

StateKey = Tuple[int, int, int, int, int, int]


class QLearningAgent:
    """
    Tabular Q-learning agent for test prioritization.
    The state is discretized so it can be stored in a Q-table.
    """

    def __init__(
        self,
        alpha: float = 0.1,
        gamma: float = 0.95,
        epsilon: float = 1.0,
        epsilon_min: float = 0.05,
        epsilon_decay: float = 0.995,
        seed: int | None = None,
    ):
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.random = random.Random(seed)

        self.q_table: DefaultDict[StateKey, DefaultDict[int, float]] = defaultdict(
            lambda: defaultdict(float)
        )

    def discretize_state(self, state: Dict[str, Any]) -> StateKey:
        """
        Convert a numeric state dictionary into a compact tuple.
        This keeps the implementation suitable for tabular Q-learning.
        """
        pending = int(state["pending_tests"])
        executed = int(state["executed_tests"])
        coverage_bin = int(float(state["coverage_accumulated"]) * 10)
        failures = int(state["failures_detected"])
        time_bin = int(float(state["time_spent"]))
        steps = int(state["steps"])

        return (pending, executed, coverage_bin, failures, time_bin, steps)

    def select_action(
        self,
        state: StateKey,
        valid_actions: List[int],
        explore: bool = True,
    ) -> int:
        if not valid_actions:
            raise ValueError("No valid actions available.")

        if explore and self.random.random() < self.epsilon:
            return self.random.choice(valid_actions)

        q_values = self.q_table[state]
        best_value = max(q_values[a] for a in valid_actions)
        best_actions = [a for a in valid_actions if q_values[a] == best_value]
        return self.random.choice(best_actions)

    def update(
        self,
        state: StateKey,
        action: int,
        reward: float,
        next_state: StateKey,
        next_valid_actions: List[int],
        done: bool,
    ) -> None:
        current_q = self.q_table[state][action]

        if done or not next_valid_actions:
            target = reward
        else:
            next_max = max(self.q_table[next_state][a] for a in next_valid_actions)
            target = reward + self.gamma * next_max

        self.q_table[state][action] = current_q + self.alpha * (target - current_q)

    def decay_epsilon(self) -> None:
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def set_greedy_mode(self) -> None:
        self.epsilon = 0.0
from typing import Any, Dict, List

from core.agent import QLearningAgent
from core.environment import TestEnvironment


class Trainer:
    """
    Trains the agent inside the simulated test prioritization environment.
    """

    def __init__(self, env: TestEnvironment, agent: QLearningAgent):
        self.env = env
        self.agent = agent

    def train(self, episodes: int = 100) -> List[Dict[str, Any]]:
        history: List[Dict[str, Any]] = []

        for episode in range(1, episodes + 1):
            state = self.env.reset()
            state_key = self.agent.discretize_state(state)

            done = False
            total_reward = 0.0
            steps = 0

            while not done:
                valid_actions = self.env.valid_actions()
                action = self.agent.select_action(state_key, valid_actions, explore=True)

                next_state, reward, done, _info = self.env.step(action)
                next_state_key = self.agent.discretize_state(next_state)
                next_valid_actions = self.env.valid_actions()

                self.agent.update(
                    state=state_key,
                    action=action,
                    reward=reward,
                    next_state=next_state_key,
                    next_valid_actions=next_valid_actions,
                    done=done,
                )

                state_key = next_state_key
                total_reward += reward
                steps += 1

            self.agent.decay_epsilon()

            budget_used = self.env.execution_budget - self.env.remaining_budget

            history.append(
                {
                    "episode": episode,
                    "total_reward": round(total_reward, 4),
                    "steps": steps,
                    "coverage": round(self.env.coverage_accumulated, 4),
                    "failures_detected": self.env.failures_detected,
                    "time_spent": round(self.env.time_spent, 4),
                    "remaining_budget": self.env.remaining_budget,
                    "budget_used": budget_used,
                    "epsilon": round(self.agent.epsilon, 6),
                }
            )

        return history
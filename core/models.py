from dataclasses import dataclass


@dataclass
class TestCase:
    """
    Represents a simulated test case used by the RL environment.
    """
    id: int
    name: str
    estimated_time: float
    failure_probability: float
    coverage_gain: float
    priority: int = 1
    executed: bool = False
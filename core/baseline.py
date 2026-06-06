import random
from typing import List, Optional

from core.models import TestCase


def random_baseline_order(
    test_cases: List[TestCase],
    seed: Optional[int] = None,
) -> List[int]:
    """
    Baseline simple: random execution order.
    """
    indices = list(range(len(test_cases)))
    rng = random.Random(seed)
    rng.shuffle(indices)
    return indices


def priority_baseline_order(test_cases: List[TestCase]) -> List[int]:
    """
    Baseline: execute tests with higher priority first.
    """
    return sorted(
        range(len(test_cases)),
        key=lambda i: test_cases[i].priority,
        reverse=True,
    )


def risk_baseline_order(test_cases: List[TestCase]) -> List[int]:
    """
    Baseline: execute tests with higher historical failure probability first.
    Coverage and estimated time are used only as simple tie-breakers.
    """
    return sorted(
        range(len(test_cases)),
        key=lambda i: (
            test_cases[i].failure_probability,
            test_cases[i].coverage_gain,
            -test_cases[i].estimated_time,
        ),
        reverse=True,
    )

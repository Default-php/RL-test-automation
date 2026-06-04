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
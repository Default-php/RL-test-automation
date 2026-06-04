from typing import List

from core.models import TestCase


def random_baseline_order(test_cases: List[TestCase]) -> List[int]:
    """
    Simple baseline: random execution order.
    """
    indices = list(range(len(test_cases)))
    import random
    random.shuffle(indices)
    return indices


def priority_baseline_order(test_cases: List[TestCase]) -> List[int]:
    """
    Baseline: execute tests with higher priority first.
    """
    return sorted(range(len(test_cases)), key=lambda i: test_cases[i].priority, reverse=True)
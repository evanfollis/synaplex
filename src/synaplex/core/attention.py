from __future__ import annotations

from typing import Dict

from synaplex.core.types import Lens, Signal


def sparse_dot(keys_a: Dict[str, float], keys_b: Dict[str, float]) -> float:
    """
    Simple sparse dot product between two key-weight maps.

    Missing keys are treated as 0.0.
    """
    if not keys_a or not keys_b:
        return 0.0
    # Iterate over the smaller dict for efficiency.
    if len(keys_a) > len(keys_b):
        keys_a, keys_b = keys_b, keys_a
    return sum(weight * keys_b.get(key, 0.0) for key, weight in keys_a.items())


def attention_score(signal: Signal, lens: Lens) -> float:
    """
    Compute an attention score between a Signal and a Lens.

    This is intentionally transparent and easy to tweak or replace.
    """
    return sparse_dot(signal.keys, lens.keys)

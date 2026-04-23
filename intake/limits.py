"""Layer 1 per-source rate limits (ADR-0029 §Adversarial review response §6).

Per-source hard cap of 200 items/day. The cap is soft (truncate + friction
event) rather than reject — the goal is backlog-poisoning protection, not
adapter correctness. Sources that regularly blow the cap either need a
tighter fetch query or per-source tuning.
"""

from __future__ import annotations

LAYER1_MAX_ITEMS_PER_SOURCE_PER_DAY = 200
LAYER2_MAX_CANDIDATES_PER_BEAT_PER_DAY_BOOTSTRAP = 5
LAYER2_MAX_CANDIDATES_PER_BEAT_PER_DAY_STEADY = 10


def layer1_cap() -> int:
    return LAYER1_MAX_ITEMS_PER_SOURCE_PER_DAY

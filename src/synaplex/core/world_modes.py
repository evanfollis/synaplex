from __future__ import annotations

from enum import Enum


class WorldMode(str, Enum):
    """
    World-level configuration for how much of the unified cognitive loop is active.

    These correspond exactly to the three modes described in the docs:

    - GRAPH_ONLY:
        Perception only.
        No LLM reasoning, no manifold usage or updates.

    - REASONING_ONLY:
        Perception + Reasoning.
        The mind thinks each tick, but does not consult or update its persistent worldview.

    - MANIFOLD:
        Full loop: Perception → Reasoning → Internal Update.
        The mind maintains and evolves a private manifold, which is used during reasoning
        and updated via the checkpoint ritual.
    """

    GRAPH_ONLY = "graph_only"
    REASONING_ONLY = "reasoning_only"
    MANIFOLD = "manifold"

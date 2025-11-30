from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any


@dataclass
class ManifoldEnvelope:
    """
    Opaque manifold container written by a Mind for its future self.

    The `manifold_text` is never parsed or mutated by the system.
    """
    mind_id: str
    world_id: str
    version: int
    created_at: datetime
    manifold_text: str


@dataclass
class Lens:
    """
    Sparse conceptual attention vector, used to decide what an agent cares about.
    """
    keys: Dict[str, float] = field(default_factory=dict)


@dataclass
class Signal:
    """
    Lightweight broadcast emitted by an agent after a tick.

    Downstream agents can compute alignment between their lens and this signal.
    """
    from_agent: str
    world_id: str
    keys: Dict[str, float]
    summary: str
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Projection:
    """
    A richer, structured slice of an agent's reasoning and context.

    For v0, keep it minimal. In later versions, this can carry structured
    invariants, scaffolds, tensions, etc.
    """
    from_agent: str
    to_agent: str
    world_id: str
    content: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.utcnow)

# synaplex/cognition/manifolds.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from synaplex.core.ids import AgentId


@dataclass
class ManifoldEnvelope:
    """
    Opaque container for a mind's internal worldview snapshot.

    The system does not parse or interpret 'content' here.
    """
    agent_id: AgentId
    version: int
    content: str
    metadata: Dict[str, Any]


class ManifoldStore:
    """
    Minimal in-memory manifold store.

    Real deployments may swap this for a database-backed implementation.
    """

    def __init__(self) -> None:
        self._by_agent: Dict[AgentId, ManifoldEnvelope] = {}

    def load_latest(self, agent_id: AgentId) -> Optional[ManifoldEnvelope]:
        return self._by_agent.get(agent_id)

    def save(self, envelope: ManifoldEnvelope) -> None:
        self._by_agent[envelope.agent_id] = envelope

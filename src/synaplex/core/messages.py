# synaplex/core/messages.py

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .ids import AgentId, MessageId


@dataclass
class Signal:
    """
    Lightweight broadcast.

    A small, structured advertisement of aspects of an agent's state.
    No manifold/worldview content is allowed here.
    """

    id: MessageId
    sender: AgentId
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Request:
    """
    Directed query for information.

    Built by the receiver (via its lens), but addressed to a specific sender.
    """

    id: MessageId
    sender: AgentId
    receiver: AgentId
    shape: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Projection:
    """
    Structured, lens-conditioned slice of what a receiver is allowed to see.

    This must only contain:
    - structured state,
    - explicitly exposed manifold-derived views (never raw text).
    """

    id: MessageId
    sender: AgentId
    receiver: AgentId
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Percept:
    """
    Structured view of the environment as seen by a single agent at a tick.

    Constructed by the environment from:
    - projections from subscribed agents,
    - structured data feeds,
    - attended signals.
    """

    agent_id: AgentId
    tick: int
    projections: List[Projection] = field(default_factory=list)
    data_feeds: Dict[str, Any] = field(default_factory=dict)
    signals: List[Signal] = field(default_factory=list)
    extras: Dict[str, Any] = field(default_factory=dict)

    def to_context(self) -> Dict[str, Any]:
        """
        Convert into a generic context dict for reasoning.

        Worlds can extend/override, but this provides a default.
        """
        return {
            "tick": self.tick,
            "agent_id": self.agent_id.value,
            "projections": [p.payload for p in self.projections],
            "data_feeds": self.data_feeds,
            "signals": [s.payload for s in self.signals],
            "extras": self.extras,
        }

# synaplex/core/messages.py

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .ids import AgentId, MessageId


@dataclass
class Signal:
    """
    Lightweight broadcast.
    
    - payload: structured metadata
    - frottage: optional semantic soup
    """

    id: MessageId
    sender: AgentId
    payload: Dict[str, Any] = field(default_factory=dict)
    frottage: Optional[str] = None


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
    What a receiver sees from a sender.
    
    - payload: structured metadata (for routing/filtering)
    - frottage: semantic soup (for the receiver to make sense of)
    """

    id: MessageId
    sender: AgentId
    receiver: AgentId
    payload: Dict[str, Any] = field(default_factory=dict)
    frottage: Optional[str] = None


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
        
        Note: frottage from projections and signals is passed through as-is.
        The receiving Mind will compress it during its reasoning/update step.
        """
        return {
            "tick": self.tick,
            "agent_id": self.agent_id.value,
            "projections": [
                {
                    "payload": p.payload,
                    "frottage": p.frottage,  # Pass through unmodified
                    "sender": p.sender.value,
                }
                for p in self.projections
            ],
            "data_feeds": self.data_feeds,
            "signals": [
                {
                    "payload": s.payload,
                    "frottage": s.frottage,  # Pass through unmodified
                    "sender": s.sender.value,
                }
                for s in self.signals
            ],
            "extras": self.extras,
        }

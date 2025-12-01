# synaplex/core/dna.py

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .ids import AgentId


@dataclass
class DNA:
    """
    Structural blueprint for an agent.

    Purely 'nature' – no LLMs, no manifolds.
    """

    agent_id: AgentId
    role: str
    subscriptions: List[AgentId] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    behavior_params: Dict[str, float] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    config: Dict[str, object] = field(default_factory=dict)

    def get_param(self, name: str, default: Optional[float] = None) -> Optional[float]:
        value = self.behavior_params.get(name, default)
        if isinstance(value, (int, float)) or value is None:
            return value
        raise TypeError(f"Behavior param '{name}' must be numeric, got {type(value)}.")

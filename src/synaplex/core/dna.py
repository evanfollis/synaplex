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
        """
        Get a behavior parameter by name.
        
        Args:
            name: Parameter name
            default: Default value if parameter doesn't exist
            
        Returns:
            Parameter value (must be numeric) or default
            
        Raises:
            TypeError: If parameter exists but is not numeric
            KeyError: If parameter doesn't exist and no default provided
        """
        if name not in self.behavior_params:
            if default is not None:
                return default
            raise KeyError(
                f"Behavior parameter '{name}' not found in DNA for agent '{self.agent_id.value}'. "
                f"Available parameters: {list(self.behavior_params.keys())}"
            )
        
        value = self.behavior_params[name]
        if isinstance(value, (int, float)) or value is None:
            return value
        raise TypeError(
            f"Behavior param '{name}' for agent '{self.agent_id.value}' must be numeric, "
            f"got {type(value).__name__} with value: {value}"
        )

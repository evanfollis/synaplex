# synaplex/core/env_state.py

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class EnvState:
    """
    Shared environmental state (nature).

    This is structured, external state that belongs to the world,
    not to any specific agent's internal worldview.
    """

    data: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value

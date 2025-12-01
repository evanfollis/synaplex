# synaplex/cognition/tools.py

from __future__ import annotations

from typing import Any, Dict


class ToolContext:
    """
    Placeholder for tool-calling context.

    In a real system, this might include:
    - http clients,
    - database handles,
    - API keys, etc.
    """

    def __init__(self) -> None:
        self._extras: Dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        self._extras[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._extras.get(key, default)

# synaplex/core/env_state.py

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable


@dataclass
class EnvState:
    """
    Shared environmental state (nature).

    This is structured, external state that belongs to the world,
    not to any specific agent's internal worldview.

    Supports:
    - Basic key-value storage
    - Structured views and querying
    - Pattern-based filtering
    """

    data: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value by key."""
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a value by key."""
        self.data[key] = value

    def query(self, pattern: Optional[str] = None, predicate: Optional[Callable[[str, Any], bool]] = None) -> Dict[str, Any]:
        """
        Query the environment state with optional filtering.

        Args:
            pattern: Optional string pattern to match keys (simple prefix/suffix matching)
            predicate: Optional function (key, value) -> bool for custom filtering

        Returns:
            Dict of matching key-value pairs
        """
        if pattern is None and predicate is None:
            return self.data.copy()

        result = {}
        for key, value in self.data.items():
            match = True

            if pattern:
                # Simple pattern matching: prefix, suffix, or contains
                if pattern.startswith("*") and pattern.endswith("*"):
                    match = pattern[1:-1] in key
                elif pattern.startswith("*"):
                    match = key.endswith(pattern[1:])
                elif pattern.endswith("*"):
                    match = key.startswith(pattern[:-1])
                else:
                    match = pattern in key

            if match and predicate:
                match = predicate(key, value)

            if match:
                result[key] = value

        return result

    def get_view(self, keys: List[str]) -> Dict[str, Any]:
        """
        Get a structured view of specific keys.

        Args:
            keys: List of keys to include in the view

        Returns:
            Dict containing only the requested keys
        """
        return {key: self.data.get(key) for key in keys if key in self.data}

    def update_batch(self, updates: Dict[str, Any]) -> None:
        """
        Update multiple keys at once.

        Args:
            updates: Dict of key-value pairs to update
        """
        self.data.update(updates)

    def remove(self, key: str) -> Optional[Any]:
        """
        Remove a key and return its value.

        Args:
            key: Key to remove

        Returns:
            The removed value, or None if key didn't exist
        """
        return self.data.pop(key, None)

    def clear(self) -> None:
        """Clear all state."""
        self.data.clear()

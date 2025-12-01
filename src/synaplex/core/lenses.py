# synaplex/core/lenses.py

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Lens:
    """
    Receiver-owned semantics for perception.

    Lenses define:
    - how signals are filtered / attended to,
    - how projections are requested and interpreted.
    """

    name: str
    # Freeform configuration; concrete worlds can subclass this.
    config: Dict[str, Any] = field(default_factory=dict)

    def should_attend(self, signal_payload: Dict[str, Any]) -> bool:
        """
        Decide whether to attend to a given signal.

        Default: attend to everything.
        Worlds can override with richer semantics.
        """
        return True

    def build_request_shape(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a request shape for a projection given current context.

        Default: echo context.
        """
        return context

    def transform_projection(self, raw_projection: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform a raw projection into the receiver's perceptual space.

        Default: identity.
        """
        return raw_projection

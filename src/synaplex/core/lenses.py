# synaplex/core/lenses.py

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class Lens:
    """
    Receiver-owned filtering.
    
    Lenses only decide what to attend to.
    They don't transform. They don't add metadata.
    The Mind decides what things mean.
    """

    name: str
    config: Dict[str, Any] = field(default_factory=dict)

    def should_attend(self, signal_payload: Dict[str, Any]) -> bool:
        """Filter signals. Default: attend to all."""
        return True

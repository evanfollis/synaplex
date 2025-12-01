# synaplex/manifolds_indexers/types.py

from dataclasses import dataclass
from typing import Any, Dict

from synaplex.core.ids import AgentId


@dataclass
class ManifoldSnapshot:
    """
    One exported snapshot of a mind's worldview.

    This is the object indexer worlds operate on.
    """
    agent_id: AgentId
    version: int
    content: str
    metadata: Dict[str, Any]

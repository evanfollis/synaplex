# synaplex/substrate_science/types.py

from dataclasses import dataclass
from typing import Any, Dict

from synaplex.core.ids import AgentId


@dataclass
class SubstrateSnapshot:
    """
    One exported snapshot of a mind's substrate.

    This is the object indexer worlds operate on.
    """
    agent_id: AgentId
    version: int
    content: str
    metadata: Dict[str, Any]

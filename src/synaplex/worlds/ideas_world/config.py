# synaplex/worlds/ideas_world/config.py

from dataclasses import dataclass, field
from typing import List

from synaplex.core.ids import WorldId, AgentId
from synaplex.core.runtime_inprocess import GraphConfig, EdgeConfig


@dataclass
class IdeasWorldConfig:
    """Configuration for the Ideas World."""
    world_id: WorldId
    graph: GraphConfig = field(default_factory=lambda: GraphConfig(
        edges=[
            EdgeConfig(subscriber=AgentId("architect"), publisher=AgentId("archivist")),
            EdgeConfig(subscriber=AgentId("critic"), publisher=AgentId("archivist")),
        ]
    ))
    ideas_dir: str = "docs/ideas"
    manifold_store_root: str = "manifolds/ideas_world"


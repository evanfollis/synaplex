# synaplex/worlds/fractalmesh/config.py

from dataclasses import dataclass, field
from typing import List

from synaplex.core.ids import WorldId
from synaplex.core.runtime_inprocess import GraphConfig, EdgeConfig


@dataclass
class FractalMeshConfig:
    world_id: WorldId
    graph: GraphConfig = field(default_factory=GraphConfig)

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any

from synaplex.core.mind import Mind
from synaplex.core.types import Lens, Signal, Projection


@dataclass
class Agent:
    """
    Base agent: a Mind + a Lens executed inside a World.

    Subclasses override `tick` and `project_for` to implement behavior.
    """
    id: str
    world_id: str
    mind: Mind
    lens: Lens

    def tick(self, world_ctx: Dict[str, Any]) -> Signal:
        """
        Perform one reasoning step in the world.

        In v0, we just write a new checkpoint using some world context and emit
        a simple Signal keyed by the lens.
        """
        experience = f"world_ctx={world_ctx}"
        previous = self.mind.load_latest(self.world_id)
        self.mind.write_checkpoint(
            world_id=self.world_id,
            previous=previous,
            additional_context=experience,
        )

        # For now, the Signal just mirrors the lens keys.
        return Signal(
            from_agent=self.id,
            world_id=self.world_id,
            keys=self.lens.keys,
            summary="basic tick completed",
        )

    def project_for(self, to_agent_id: str) -> Projection:
        """
        Return a minimal Projection for another agent.

        Later, this can read from manifold and world state to build rich views.
        """
        content = {
            "note": "projection placeholder; future versions will expose structured reasoning",
            "from_agent": self.id,
            "world_id": self.world_id,
        }
        return Projection(
            from_agent=self.id,
            to_agent=to_agent_id,
            world_id=self.world_id,
            content=content,
        )

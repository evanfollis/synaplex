# synaplex/cognition/update.py

from __future__ import annotations

from typing import Any, Dict, Optional

from .manifolds import ManifoldEnvelope


class UpdateMechanism:
    """
    Encapsulates strategies for turning reasoning_output into a new manifold.

    This is where checkpoint rituals live.
    """

    def update_worldview(
        self,
        prior: Optional[ManifoldEnvelope],
        reasoning_output: Dict[str, Any],
    ) -> ManifoldEnvelope:
        """
        Skeleton implementation: just wraps reasoning_output["notes"].

        Real implementations will build prompts and call the LLMClient.
        """
        if prior is None:
            version = 1
            agent_id = reasoning_output["agent_id"]
        else:
            version = prior.version + 1
            agent_id = prior.agent_id

        content = reasoning_output.get("notes", "")
        metadata = {"source": "skeleton-update"}

        return ManifoldEnvelope(
            agent_id=agent_id,
            version=version,
            content=content,
            metadata=metadata,
        )

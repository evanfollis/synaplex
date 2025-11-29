from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from synaplex.core.types import ManifoldEnvelope
from synaplex.infra.llm import LLMClient, LLMRequest
from synaplex.infra.storage import FileStorage


UPGRADE_RITUAL_SYSTEM = """You are about to be upgraded to a smarter, better reasoning version of yourself.
You are writing notes ONLY for your future self.
Do NOT optimize for human readability.
Preserve contradictions, half-formed ideas, and fuzzy threads.
Assume your future self can interpret any format or structure you choose.
"""


@dataclass
class Mind:
    """
    A persistent identity that owns a manifold history.

    The Mind doesn't "think" about tasks directly; it maintains a self-authored
    manifold that other layers (agents/worlds) use as context.
    """
    mind_id: str
    storage: FileStorage
    llm: LLMClient

    def load_latest(self, world_id: str) -> Optional[ManifoldEnvelope]:
        return self.storage.load_latest_manifold(self.mind_id, world_id)

    def write_checkpoint(
        self,
        world_id: str,
        previous: Optional[ManifoldEnvelope],
        additional_context: str,
    ) -> ManifoldEnvelope:
        """
        Core manifold update operation.

        - previous.manifold_text (if any) is treated as prior notes.
        - additional_context is raw material from the current tick (experience).
        """
        version = (previous.version + 1) if previous else 1

        prev_notes = previous.manifold_text if previous else ""
        user_prompt = (
            "Here are some of your previous notes to yourself (if any):\n"
            f"{prev_notes}\n\n"
            "Below is some new experience from this world tick. "
            "Update your notes for your future self. Do not explain yourself "
            "to a human; assume only you will ever see this.\n\n"
            f"New experience:\n{additional_context}\n"
        )

        response = self.llm.complete(
            LLMRequest(system_prompt=UPGRADE_RITUAL_SYSTEM, user_prompt=user_prompt)
        )

        env = ManifoldEnvelope(
            mind_id=self.mind_id,
            world_id=world_id,
            version=version,
            created_at=datetime.utcnow(),
            manifold_text=response,
        )

        self.storage.save_manifold(env)
        return env

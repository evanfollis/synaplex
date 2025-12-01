# synaplex/cognition/update.py

from __future__ import annotations

from typing import Any, Dict, Optional

from .llm_client import LLMClient
from .manifolds import ManifoldEnvelope
from synaplex.core.ids import AgentId


class UpdateMechanism:
    """
    Encapsulates strategies for turning reasoning_output into a new manifold.

    This is where checkpoint rituals live. The update mechanism:
    - Integrates prior manifold with new reasoning notes
    - Preserves important tensions and contradictions
    - Maintains worldview continuity
    - Performs epistemic compression for the agent's future self (not human summaries)
    """

    def __init__(self, llm_client: Optional[LLMClient] = None) -> None:
        """
        Initialize the update mechanism.

        Args:
            llm_client: Optional LLM client for checkpoint rituals.
                       If None, falls back to simple concatenation.
        """
        self._llm = llm_client

    def update_worldview(
        self,
        prior: Optional[ManifoldEnvelope],
        reasoning_output: Dict[str, Any],
    ) -> ManifoldEnvelope:
        """
        Perform checkpoint ritual: integrate prior worldview with new reasoning.

        This is the Internal Update step of the unified loop.
        The result is a new manifold envelope that:
        - Builds on the prior manifold (if it exists)
        - Integrates new insights from reasoning
        - Preserves important contradictions and tensions
        - Is optimized for the agent's own future reasoning (not human readability)

        Args:
            prior: Previous manifold envelope (None for initial manifold)
            reasoning_output: Dict with:
                - "agent_id": AgentId
                - "notes": str (internal notes from reasoning)
                - "context": dict (percept-derived context, optional)

        Returns:
            New ManifoldEnvelope with updated worldview
        """
        # Extract agent_id
        if prior is None:
            version = 1
            agent_id = reasoning_output["agent_id"]
            if isinstance(agent_id, str):
                agent_id = AgentId(agent_id)
        else:
            version = prior.version + 1
            agent_id = prior.agent_id

        # Get new reasoning notes
        new_notes = reasoning_output.get("notes", "")
        context = reasoning_output.get("context", {})

        # If no LLM client, fall back to simple concatenation
        if self._llm is None:
            content = self._simple_update(prior, new_notes)
            metadata = {"source": "simple-update", "version": version}
        else:
            # Perform LLM-backed checkpoint ritual
            content = self._checkpoint_ritual(prior, new_notes, context)
            metadata = {
                "source": "checkpoint-ritual",
                "version": version,
                "tick": context.get("tick"),
            }

        return ManifoldEnvelope(
            agent_id=agent_id,
            version=version,
            content=content,
            metadata=metadata,
        )

    def _simple_update(
        self, prior: Optional[ManifoldEnvelope], new_notes: str
    ) -> str:
        """
        Simple update: concatenate prior and new notes.

        Used when no LLM client is available.
        """
        if prior is None:
            return new_notes

        # Simple concatenation with separator
        if prior.content:
            return f"{prior.content}\n\n---\n\n{new_notes}"
        return new_notes

    def _checkpoint_ritual(
        self,
        prior: Optional[ManifoldEnvelope],
        new_notes: str,
        context: Dict[str, Any],
    ) -> str:
        """
        Perform LLM-backed checkpoint ritual.

        This integrates the prior manifold with new reasoning notes.
        The prompt emphasizes:
        - This is for the agent's future self, not humans
        - Preserve tensions and contradictions when useful
        - Maintain worldview continuity
        - Perform epistemic compression, not summarization
        """
        prompt = self._build_checkpoint_prompt(prior, new_notes, context)

        try:
            response = self._llm.complete(prompt)
            # Extract text from response
            if hasattr(response, "text"):
                return response.text
            return str(response)
        except Exception as e:
            # Fall back to simple update on error
            return self._simple_update(prior, new_notes)

    def _build_checkpoint_prompt(
        self,
        prior: Optional[ManifoldEnvelope],
        new_notes: str,
        context: Dict[str, Any],
    ) -> str:
        """
        Build the checkpoint prompt for manifold update.

        This prompt guides the LLM to:
        - Integrate prior worldview with new insights
        - Preserve important structural elements
        - Maintain contradictions/tensions that might be useful
        - Optimize for future reasoning, not human readability
        """
        if prior is None:
            # Initial manifold creation
            return f"""You are creating your initial internal worldview based on your first reasoning.

New reasoning notes:
{new_notes}

Create an internal worldview representation for your future self. This is NOT a summary for humans.
Focus on:
- What you've learned or noticed
- Patterns or structures you're beginning to recognize
- Questions or tensions that feel important
- Any half-formed ideas that might be useful later

Write this as raw internal notes optimized for your own future reasoning, not for external readability.
Structure it however helps you think better next time."""

        # Update existing manifold
        tick_info = f"Tick {context.get('tick', '?')}" if context.get("tick") is not None else "Current tick"

        return f"""You are updating your internal worldview through a checkpoint ritual.

This is for YOUR future self, not for humans. Do NOT optimize for human readability.
Do NOT summarize or clean up. This is epistemic compression for continued reasoning.

Your prior worldview (version {prior.version}):
---
{prior.content}
---

New reasoning notes from {tick_info}:
---
{new_notes}
---

Your task:
1. Integrate the new notes into your existing worldview
2. Preserve important structural elements, invariants, and patterns from your prior worldview
3. Maintain contradictions and tensions if they feel important or unresolved
4. Let go of details that no longer matter
5. Promote vague ideas into explicit scaffolds if they feel significant
6. Note what changed and why (for your future self)

Write the updated worldview. This should:
- Build naturally on your prior worldview
- Incorporate new insights seamlessly
- Maintain continuity while allowing evolution
- Be optimized for YOUR own future reasoning, not external consumption
- Preserve epistemic richness (don't collapse into summaries)

Your updated worldview:"""


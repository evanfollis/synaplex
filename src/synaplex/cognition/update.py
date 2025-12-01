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

        # Preserve geometric hints from prior if they exist, allowing the Mind to update them
        if prior and prior.metadata:
            # Copy geometric hints from prior (Mind will update them in content/metadata)
            if "curvature_hints" in prior.metadata:
                metadata["curvature_hints"] = prior.metadata["curvature_hints"]
            if "attractor_hints" in prior.metadata:
                metadata["attractor_hints"] = prior.metadata["attractor_hints"]
            if "teleology_hints" in prior.metadata:
                metadata["teleology_hints"] = prior.metadata["teleology_hints"]

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
        - Explicitly apply forgetting/dissipation (Ξ) to prune details that no longer matter
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

        # Extract geometric hints from prior metadata if available
        prior_metadata = prior.metadata if prior else {}
        curvature_hints = prior_metadata.get("curvature_hints", {})
        attractor_hints = prior_metadata.get("attractor_hints", [])
        teleology_hints = prior_metadata.get("teleology_hints", {})

        # Build forgetting guidance
        forgetting_guidance = self._apply_forgetting(prior, curvature_hints, attractor_hints)

        # Build geometric evolution guidance
        geometric_evolution_guidance = self._build_geometric_evolution_guidance(
            curvature_hints, attractor_hints, teleology_hints
        )

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

{forgetting_guidance}

{geometric_evolution_guidance}

Your task:
1. Integrate the new notes into your existing worldview
2. Preserve important structural elements, invariants, and patterns from your prior worldview
3. Maintain contradictions and tensions if they feel important or unresolved
4. **Apply forgetting/dissipation (Ξ)**: Let go of details that no longer matter, prune outdated information,
   and reduce detail in regions that have become less relevant. This is geometric dissipation - smoothing
   and pruning to maintain focus on what matters.
5. Update geometric hints if patterns have changed:
   - Adjust attractor hints (A): strengthen stable patterns that persist, weaken those that fade
   - Adjust curvature hints (K): note sensitivity changes - what perturbations matter more/less now
   - Adjust teleology hints (τ): update your sense of "improvement direction" based on what worked
6. Promote vague ideas into explicit scaffolds if they feel significant
7. Note what changed and why (for your future self)

Write the updated worldview. This should:
- Build naturally on your prior worldview
- Incorporate new insights seamlessly
- Maintain continuity while allowing evolution
- Be optimized for YOUR own future reasoning, not external consumption
- Preserve epistemic richness (don't collapse into summaries)
- Explicitly prune and forget what no longer serves you (geometric dissipation)

Your updated worldview:"""

    def _apply_forgetting(
        self,
        prior: Optional[ManifoldEnvelope],
        curvature_hints: Dict[str, Any],
        attractor_hints: List[str],
    ) -> str:
        """
        Generate guidance for the forgetting/dissipation operator (Ξ).

        This guides the checkpoint ritual to explicitly prune and forget details
        that no longer matter, reducing detail in less relevant regions of the manifold.

        Args:
            prior: Previous manifold envelope (if exists)
            curvature_hints: Hints about sensitivity patterns (K)
            attractor_hints: Hints about stable patterns (A)

        Returns:
            String guidance to include in checkpoint prompt
        """
        if prior is None:
            return ""

        guidance_parts = [
            "**Forgetting/Dissipation (Ξ) Guidance:**",
            "As you update your worldview, explicitly apply forgetting:",
        ]

        # Guide based on attractor hints
        if attractor_hints:
            guidance_parts.append(
                f"- You have identified these stable patterns/attractors: {', '.join(attractor_hints[:5])}"
            )
            guidance_parts.append(
                "- Strengthen details around these patterns if they persist; weaken details around patterns that fade"
            )
        else:
            guidance_parts.append(
                "- Identify which patterns from your prior worldview are still relevant vs fading"
            )

        # Guide based on curvature hints
        if curvature_hints:
            guidance_parts.append(
                "- Your prior sensitivity patterns suggest some regions are more/less important"
            )
            guidance_parts.append(
                "- Prune detail in low-sensitivity regions; preserve detail in high-sensitivity regions"
            )

        guidance_parts.extend([
            "- Let go of specific details, examples, or edge cases that no longer inform your reasoning",
            "- Smooth over contradictions that have been resolved or are no longer relevant",
            "- Reduce redundancy: if you've said something multiple ways, consolidate",
            "- Prune outdated context: remove references to situations that no longer apply",
        ])

        return "\n".join(guidance_parts)

    def _build_geometric_evolution_guidance(
        self,
        curvature_hints: Dict[str, Any],
        attractor_hints: List[str],
        teleology_hints: Dict[str, Any],
    ) -> str:
        """
        Build guidance for evolving geometric fields A, K, τ.

        This guides the checkpoint ritual to explicitly update:
        - A (attractors): stable patterns/habits
        - K (curvature): sensitivity to perturbations
        - τ (teleology): direction of improvement

        Args:
            curvature_hints: Prior curvature hints (K)
            attractor_hints: Prior attractor hints (A)
            teleology_hints: Prior teleology hints (τ)

        Returns:
            String guidance to include in checkpoint prompt
        """
        guidance_parts = [
            "**Geometric Evolution Guidance (A, K, τ):**",
            "As you update your worldview, explicitly evolve your geometric fields:",
        ]

        # Attractor evolution (A)
        if attractor_hints:
            guidance_parts.append(
                f"\n**Attractors (A) - Current stable patterns:** {', '.join(attractor_hints[:5])}"
            )
            guidance_parts.extend([
                "- Strengthen attractors that persist and prove useful",
                "- Weaken or remove attractors that fade or become counterproductive",
                "- Identify new stable patterns emerging from your reasoning",
                "- Note which patterns are becoming habits vs exploratory",
            ])
        else:
            guidance_parts.extend([
                "\n**Attractors (A) - Stable patterns:**",
                "- Identify patterns, habits, or conceptual equilibria that are stabilizing",
                "- Note what you tend to fall back to when uncertain",
                "- Track which explanations or frameworks are becoming stable",
            ])

        # Curvature evolution (K)
        if curvature_hints:
            guidance_parts.append(
                f"\n**Curvature (K) - Current sensitivity patterns:** {str(curvature_hints)[:100]}..."
            )
            guidance_parts.extend([
                "- Update sensitivity: what perturbations matter more/less now?",
                "- Note regions of high curvature (where small changes cause big shifts)",
                "- Note regions of low curvature (where you're resistant to change)",
                "- Adjust based on what surprised you or what you shrugged off",
            ])
        else:
            guidance_parts.extend([
                "\n**Curvature (K) - Sensitivity to perturbations:**",
                "- Track how sensitive you are to different types of new information",
                "- Note what causes you to radically reweight vs. what you ignore",
                "- Identify your risk/volatility profile: where are you brittle vs. flexible?",
            ])

        # Teleology evolution (τ)
        if teleology_hints:
            guidance_parts.append(
                f"\n**Teleology (τ) - Current improvement direction:** {str(teleology_hints)[:100]}..."
            )
            guidance_parts.extend([
                "- Update your sense of 'what better looks like' based on what worked",
                "- Adjust your epistemic gradient: what directions of reasoning helped?",
                "- Note which approaches led to useful insights vs. dead ends",
                "- Evolve your internal compass for 'improvement'",
            ])
        else:
            guidance_parts.extend([
                "\n**Teleology (τ) - Direction of improvement:**",
                "- Define your internal sense of 'better' - what are you optimizing for?",
                "- Track what reasoning directions seem promising",
                "- Note your epistemic gradient: where does improvement lie?",
            ])

        guidance_parts.append(
            "\nAfter updating your worldview, consider updating these geometric hints in your metadata:"
        )
        guidance_parts.append(
            "- 'attractor_hints': List of stable patterns you've identified"
        )
        guidance_parts.append(
            "- 'curvature_hints': Dict describing your sensitivity patterns"
        )
        guidance_parts.append(
            "- 'teleology_hints': Dict describing your improvement direction"
        )

        return "\n".join(guidance_parts)


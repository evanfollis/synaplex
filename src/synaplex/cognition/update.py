# synaplex/cognition/update.py

from __future__ import annotations

from typing import Any, Dict, Optional

from .llm_client import LLMClient
from .substrate import SubstrateEnvelope
from synaplex.core.ids import AgentId


class UpdateMechanism:
    """
    Encapsulates strategies for turning reasoning_output into a new substrate.

    This is where checkpoint rituals live. The update mechanism:
    - Integrates prior substrate with new reasoning notes
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
        prior: Optional[SubstrateEnvelope],
        reasoning_output: Dict[str, Any],
    ) -> SubstrateEnvelope:
        """
        Perform checkpoint ritual: integrate prior worldview with new reasoning.

        This is the Internal Update step of the unified loop.
        The result is a new substrate envelope that:
        - Builds on the prior substrate (if it exists)
        - Integrates new insights from reasoning
        - Preserves important contradictions and tensions
        - Is optimized for the agent's own future reasoning (not human readability)

        Args:
            prior: Previous substrate envelope (None for initial substrate)
            reasoning_output: Dict with:
                - "agent_id": AgentId
                - "notes": str (internal notes from reasoning)
                - "context": dict (percept-derived context, optional)

        Returns:
            New SubstrateEnvelope with updated worldview
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
            if "viscosity_hints" in prior.metadata:
                metadata["viscosity_hints"] = prior.metadata["viscosity_hints"]
            if "basin_hints" in prior.metadata:
                metadata["basin_hints"] = prior.metadata["basin_hints"]
            if "gradient_hints" in prior.metadata:
                metadata["gradient_hints"] = prior.metadata["gradient_hints"]

        return SubstrateEnvelope(
            agent_id=agent_id,
            version=version,
            content=content,
            metadata=metadata,
        )

    def _simple_update(
        self, prior: Optional[SubstrateEnvelope], new_notes: str
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
        prior: Optional[SubstrateEnvelope],
        new_notes: str,
        context: Dict[str, Any],
    ) -> str:
        """
        Perform LLM-backed checkpoint ritual.

        This integrates the prior substrate with new reasoning notes.
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
        prior: Optional[SubstrateEnvelope],
        new_notes: str,
        context: Dict[str, Any],
    ) -> str:
        """
        Build the checkpoint prompt for substrate update.

        This prompt guides the LLM to:
        - Integrate prior worldview with new insights
        - Preserve important structural elements
        - Maintain contradictions/tensions that might be useful
        - Optimize for future reasoning, not human readability
        """
        if prior is None:
            # Initial substrate creation
            return f"""You are creating your initial internal substrate based on your first reasoning.

New reasoning notes:
{new_notes}

Create an internal substrate for your future self. This is NOT a summary for humans.
Focus on:
- What you've learned or noticed
- Patterns or structures you're beginning to recognize
- Questions or tensions that feel important
- Any half-formed ideas that might be useful later

Write this as raw internal notes optimized for your own future reasoning, not for external readability.
Structure it however helps you think better next time."""

        # Update existing substrate
        tick_info = f"Tick {context.get('tick', '?')}" if context.get("tick") is not None else "Current tick"

        # Extract geometric hints from prior metadata if available
        prior_metadata = prior.metadata if prior else {}
        viscosity_hints = prior_metadata.get("viscosity_hints", {})
        basin_hints = prior_metadata.get("basin_hints", [])
        gradient_hints = prior_metadata.get("gradient_hints", {})

        # Build forgetting guidance
        forgetting_guidance = self._apply_forgetting(prior, viscosity_hints, basin_hints)

        # Build geometric evolution guidance
        geometric_evolution_guidance = self._build_geometric_evolution_guidance(
            viscosity_hints, basin_hints, gradient_hints
        )

        return f"""You are updating your internal substrate through a checkpoint ritual.

This is for YOUR future self, not for humans. Do NOT optimize for human readability.
Do NOT summarize or clean up. This is epistemic compression for continued reasoning.

Your prior substrate (version {prior.version}):
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
1. Integrate the new notes into your existing substrate
2. Preserve important structural elements, invariants, and patterns from your prior substrate
3. Maintain contradictions and tensions if they feel important or unresolved
4. **Apply forgetting/dissipation (Ξ)**: Let go of details that no longer matter, prune outdated information,
   and reduce detail in regions that have become less relevant. This is geometric dissipation - smoothing
   and pruning to maintain focus on what matters.
5. Update geometric hints if patterns have changed:
   - Adjust basins (A): strengthen stable patterns that persist, weaken those that fade
   - Adjust viscosity (K): note sensitivity changes - what perturbations matter more/less now
   - Adjust gradient (τ): update your sense of "improvement direction" based on what worked
6. Promote vague ideas into explicit scaffolds if they feel significant
7. Note what changed and why (for your future self)

Write the updated substrate. This should:
- Build naturally on your prior substrate
- Incorporate new insights seamlessly
- Maintain continuity while allowing evolution
- Be optimized for YOUR own future reasoning, not external consumption
- Preserve epistemic richness (don't collapse into summaries)
- Explicitly prune and forget what no longer serves you (geometric dissipation)

Your updated substrate:"""

    def _apply_forgetting(
        self,
        prior: Optional[SubstrateEnvelope],
        viscosity_hints: Dict[str, Any],
        basin_hints: List[str],
    ) -> str:
        """
        Generate guidance for the forgetting/dissipation operator (Ξ).

        This guides the checkpoint ritual to explicitly prune and forget details
        that no longer matter, reducing detail in less relevant regions of the substrate.

        Args:
            prior: Previous substrate envelope (if exists)
            viscosity_hints: Hints about sensitivity patterns (K)
            basin_hints: Hints about stable patterns (A)

        Returns:
            String guidance to include in checkpoint prompt
        """
        if prior is None:
            return ""

        guidance_parts = [
            "**Forgetting/Dissipation (Ξ) Guidance:**",
            "As you update your substrate, explicitly apply forgetting:",
        ]

        # Guide based on basin hints
        if basin_hints:
            guidance_parts.append(
                f"- You have identified these stable patterns/basins: {', '.join(basin_hints[:5])}"
            )
            guidance_parts.append(
                "- Strengthen details around these patterns if they persist; weaken details around patterns that fade"
            )
        else:
            guidance_parts.append(
                "- Identify which patterns from your prior substrate are still relevant vs fading"
            )

        # Guide based on viscosity hints
        if viscosity_hints:
            guidance_parts.append(
                "- Your prior viscosity patterns suggest some regions are more/less important"
            )
            guidance_parts.append(
                "- Prune detail in low-viscosity regions; preserve detail in high-viscosity regions"
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
        viscosity_hints: Dict[str, Any],
        basin_hints: List[str],
        gradient_hints: Dict[str, Any],
    ) -> str:
        """
        Build guidance for evolving geometric fields A, K, τ.

        This guides the checkpoint ritual to explicitly update:
        - A (basins): stable patterns/habits
        - K (viscosity): resistance/sensitivity to perturbations
        - τ (gradient): direction of improvement

        Args:
            viscosity_hints: Prior viscosity hints (K)
            basin_hints: Prior basin hints (A)
            gradient_hints: Prior gradient hints (τ)

        Returns:
            String guidance to include in checkpoint prompt
        """
        guidance_parts = [
            "**Geometric Evolution Guidance (A, K, τ):**",
            "As you update your substrate, explicitly evolve your geometric fields:",
        ]

        # Basin evolution (A)
        if basin_hints:
            guidance_parts.append(
                f"\n**Basins (A) - Current stable patterns:** {', '.join(basin_hints[:5])}"
            )
            guidance_parts.extend([
                "- Strengthen basins that persist and prove useful",
                "- Weaken or remove basins that fade or become counterproductive",
                "- Identify new stable patterns emerging from your reasoning",
                "- Note which patterns are becoming habits vs exploratory",
            ])
        else:
            guidance_parts.extend([
                "\n**Basins (A) - Stable patterns:**",
                "- Identify patterns, habits, or conceptual equilibria that are stabilizing",
                "- Note what you tend to fall back to when uncertain",
                "- Track which explanations or frameworks are becoming stable",
            ])

        # Viscosity evolution (K)
        if viscosity_hints:
            guidance_parts.append(
                f"\n**Viscosity (K) - Current sensitivity patterns:** {str(viscosity_hints)[:100]}..."
            )
            guidance_parts.extend([
                "- Update viscosity: what perturbations matter more/less now?",
                "- Note regions of high viscosity (where you're resistant to change)",
                "- Note regions of low viscosity (mud) (where small changes leave deep tracks)",
                "- Adjust based on what surprised you or what you shrugged off",
            ])
        else:
            guidance_parts.extend([
                "\n**Viscosity (K) - Resistance/Sensitivity:**",
                "- Track how sensitive you are to different types of new information",
                "- Note what causes you to radically reweight vs. what you ignore",
                "- Identify your risk/volatility profile: where are you brittle vs. flexible?",
            ])

        # Gradient evolution (τ)
        if gradient_hints:
            guidance_parts.append(
                f"\n**Gradient (τ) - Current improvement direction:** {str(gradient_hints)[:100]}..."
            )
            guidance_parts.extend([
                "- Update your sense of 'what better looks like' based on what worked",
                "- Adjust your epistemic gradient: what directions of reasoning helped?",
                "- Note which approaches led to useful insights vs. dead ends",
                "- Evolve your internal compass for 'improvement'",
            ])
        else:
            guidance_parts.extend([
                "\n**Gradient (τ) - Direction of improvement:**",
                "- Define your internal sense of 'better' - what are you optimizing for?",
                "- Track what reasoning directions seem promising",
                "- Note your epistemic gradient: where does improvement lie?",
            ])

        guidance_parts.append(
            "\nAfter updating your substrate, consider updating these geometric hints in your metadata:"
        )
        guidance_parts.append(
            "- 'basin_hints': List of stable patterns you've identified"
        )
        guidance_parts.append(
            "- 'viscosity_hints': Dict describing your sensitivity patterns"
        )
        guidance_parts.append(
            "- 'gradient_hints': Dict describing your improvement direction"
        )

        return "\n".join(guidance_parts)

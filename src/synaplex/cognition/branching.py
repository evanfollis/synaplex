# synaplex/cognition/branching.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .llm_client import LLMClient


@dataclass
class BranchOutput:
    """Output from a single reasoning branch."""
    name: str
    notes: str
    outward: Dict[str, Any]


class BranchingStrategy:
    """
    Strategy for creating internal branches (explorer, skeptic, etc.) and consolidating them.

    Branching enables internal multiplicity - a mind can explore multiple reasoning
    paths from the same starting point and then reconcile them into a unified worldview.

    Branches are ephemeral - they exist only within a single tick's reasoning.
    From the Mind's perspective, history is M₀ → M₁, not individual branches.
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        default_styles: Optional[List[str]] = None,
    ) -> None:
        """
        Initialize branching strategy.

        Args:
            llm_client: Optional LLM client for branch generation and consolidation.
                       If None, branching is disabled.
            default_styles: Default branch styles to use if not specified.
                           Default: ["explorer", "skeptic"]
        """
        self._llm = llm_client
        self._default_styles = default_styles or ["explorer", "skeptic"]

    def run_branches(
        self,
        base_prompt: str,
        context: Dict[str, Any],
        styles: Optional[List[str]] = None,
    ) -> List[BranchOutput]:
        """
        Generate multiple reasoning branches from the same starting point.

        Each branch explores the same prompt/percept from a different cognitive style.
        Branches are independent reasoning passes that may diverge significantly.

        Args:
            base_prompt: The base reasoning prompt
            context: Context dict (percept, manifold, etc.)
            styles: List of branch styles (e.g., ["explorer", "skeptic"]).
                   If None, uses default_styles.

        Returns:
            List of BranchOutput, one per branch style
        """
        if self._llm is None:
            # No LLM: return empty list (branching disabled)
            return []

        styles = styles or self._default_styles
        branches = []

        for style in styles:
            # Build style-specific prompt
            style_prompt = self._build_style_prompt(base_prompt, context, style)

            try:
                # Call LLM for this branch
                response = self._llm.complete(style_prompt)
                notes = response.text if hasattr(response, "text") else str(response)

                branches.append(
                    BranchOutput(
                        name=style,
                        notes=notes,
                        outward={},  # Branches don't produce outward behavior directly
                    )
                )
            except Exception:
                # Skip branch on error, continue with others
                continue

        return branches

    def consolidate(
        self,
        branches: List[BranchOutput],
        prior_manifold: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Consolidate branch notes into unified reasoning output.

        This reconciliation step:
        - Takes all branch outputs as if they were prior self-notes
        - Does not reveal branch identities to the consolidation process
        - Produces a single unified reasoning trace

        Args:
            branches: List of branch outputs to consolidate
            prior_manifold: Optional prior manifold content for context
            context: Optional context dict (percept info, etc.)

        Returns:
            Consolidated notes string
        """
        if not branches:
            return ""

        if self._llm is None or len(branches) == 1:
            # No LLM or single branch: simple concatenation
            return "\n\n".join(f"{b.notes}" for b in branches)

        # Build consolidation prompt
        prompt = self._build_consolidation_prompt(branches, prior_manifold, context)

        try:
            response = self._llm.complete(prompt)
            return response.text if hasattr(response, "text") else str(response)
        except Exception:
            # Fall back to simple concatenation on error
            return "\n\n".join(f"{b.notes}" for b in branches)

    def _build_style_prompt(
        self, base_prompt: str, context: Dict[str, Any], style: str
    ) -> str:
        """
        Build a style-specific prompt for a branch.

        Different styles emphasize different reasoning approaches:
        - explorer: generative, divergent, multiple possibilities
        - skeptic: critical, questioning assumptions, finding flaws
        - structuralist: looking for patterns, organizing principles
        """
        style_instructions = {
            "explorer": """You are reasoning in EXPLORER mode.
Focus on:
- Generating multiple possibilities and hypotheses
- Exploring divergent paths and unconventional angles
- Speculative reasoning and provisional models
- Holding multiple options open without premature convergence
- Rapid hypothesis generation""",

            "skeptic": """You are reasoning in SKEPTIC mode.
Focus on:
- Questioning assumptions and finding potential flaws
- Identifying contradictions and tensions
- Critically examining evidence and reasoning
- Looking for what might be wrong or missing
- Challenging received wisdom""",

            "structuralist": """You are reasoning in STRUCTURALIST mode.
Focus on:
- Identifying patterns and organizing principles
- Looking for underlying structures and invariants
- Finding connections and relationships
- Organizing information into coherent frameworks
- Seeking systematic understanding""",

            "synthesizer": """You are reasoning in SYNTHESIZER mode.
Focus on:
- Integrating multiple perspectives
- Finding commonalities and connections
- Building unified frameworks
- Reconciling apparent contradictions
- Creating coherent wholes from parts""",
        }

        style_text = style_instructions.get(
            style.lower(), f"You are reasoning with a {style} perspective."
        )

        return f"""{base_prompt}

---
Branch Style: {style.upper()}

{style_text}

Reason using this style and produce internal notes from this perspective."""

    def _build_consolidation_prompt(
        self,
        branches: List[BranchOutput],
        prior_manifold: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> str:
        """
        Build prompt for consolidating branches.

        The consolidation step treats branches as if they were prior self-notes,
        not revealing their identity. This allows the mind to reconcile them
        naturally without being told to "merge explorer and skeptic views."
        """
        # Collect all branch notes without revealing identities
        branch_notes = "\n\n---\n\n".join(branch.notes for branch in branches)

        prompt = """You are reconciling multiple internal reasoning threads into a unified understanding.

These are prior self-notes from your own reasoning process. Integrate them into a coherent view.

Internal reasoning notes:
---
{branch_notes}
---

Your task:
1. Integrate these reasoning threads into a unified perspective
2. Preserve important insights from each thread
3. Identify and reconcile contradictions (but preserve tensions if unresolved)
4. Build a coherent internal narrative for your future self
5. Note what you've learned and what questions remain

This is for YOUR future self, not for external consumption.
Write consolidated internal notes that help you reason better next time."""

        # Optionally include prior manifold for context
        if prior_manifold:
            prompt = f"""Your prior worldview context:
---
{prior_manifold[:500]}...
---

{prompt}"""

        return prompt.format(branch_notes=branch_notes)

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from synaplex.core.agent_interface import AgentInterface
from synaplex.core.ids import AgentId, MessageId
from synaplex.core.messages import Percept, Projection, Request

from .llm_client import LLMClient
from .manifolds import ManifoldEnvelope, ManifoldStore, InMemoryManifoldStore
from .branching import BranchingStrategy, BranchOutput
from .update import UpdateMechanism
from .tools import ToolRegistry


@dataclass
class ReasoningResult:
    """
    Structured result of a single reasoning pass.

    This is an internal helper object; callers see plain dicts.
    """
    notes: str
    outward: Dict[str, Any]
    context: Dict[str, Any]


class Mind(AgentInterface):
    """
    Default Mind implementation for Synaplex.

    Responsibilities:
    - Respect the unified loop:
        Perception → Reasoning → Internal Update
    - Maintain manifold privacy:
        Only this class loads/saves ManifoldEnvelope;
        no manifold text ever leaves the Mind.
    - Every Mind always has a manifold and runs the full cognitive loop.
    """

    def __init__(
        self,
        agent_id: AgentId,
        llm_client: LLMClient,
        *,
        manifold_store: Optional[ManifoldStore] = None,
        update_mechanism: Optional[UpdateMechanism] = None,
        branching_strategy: Optional[BranchingStrategy] = None,
        tool_registry: Optional[ToolRegistry] = None,
    ) -> None:
        super().__init__(agent_id=agent_id)

        self._llm = llm_client
        # Default to in-memory store for backward compatibility
        self._store = manifold_store or InMemoryManifoldStore()
        # UpdateMechanism gets LLM client for checkpoint rituals
        self._update_mechanism = update_mechanism or UpdateMechanism(llm_client=llm_client)
        # BranchingStrategy gets LLM client if provided
        self._branching = branching_strategy or BranchingStrategy(llm_client=llm_client)
        # Tool registry for tool calling during reasoning
        self._tool_registry = tool_registry

        self._last_percept: Optional[Percept] = None

        # Invariant: every Mind always has a manifold envelope.
        self._ensure_initial_manifold()

    # -------------------------------------------------------------------------
    # Unified loop hooks (AgentInterface)
    # -------------------------------------------------------------------------

    def perceive(self, percept: Percept) -> None:
        """
        Perception (Environment → Mind).

        The runtime constructs the Percept.
        This method simply caches it for the subsequent Reasoning step.
        No manifold access, no LLM calls.
        """
        self._last_percept = percept

    def reason(self) -> Dict[str, Any]:
        """
        Reasoning + Internal Update.

        Every Mind always runs the full cognitive loop:
        - Loads its manifold
        - Reasons with it
        - Updates it via Internal Update checkpoint ritual

        Returns a reasoning_output dict:

            {
                "agent_id": AgentId,
                "notes": str,          # internal notes intended for the Mind's future self
                "outward": { ... },    # outward behavior to be consumed by act()
                "context": { ... },    # percept-derived reasoning context (for debugging/analysis)
            }
        """
        context = self._build_context_from_percept(self._last_percept)
        
        # Load the manifold (always exists due to _ensure_initial_manifold)
        prior_envelope = self._load_manifold()
        
        # Include the current manifold content only for the Mind's own use.
        # This never leaves the Mind.
        context_with_manifold = dict(context)
        context_with_manifold["manifold"] = prior_envelope.content

        # Run reasoning with manifold
        result = self._run_reasoning_with_manifold(context_with_manifold)

        # Internal Update: checkpoint ritual → new ManifoldEnvelope
        envelope = self._update_mechanism.update_worldview(
            prior=prior_envelope,
            reasoning_output={
                "agent_id": self.agent_id,  # Already an AgentId
                "notes": result.notes,
                "context": result.context,
            },
        )
        self._store.save(envelope)
        
        # Include manifold version info in result for logging
        result.context["manifold_version"] = envelope.version
        result.context["manifold_content_length"] = len(envelope.content)
        result.context["manifold_metadata"] = envelope.metadata

        return self._result_to_dict(result)

    def act(self, reasoning_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Produce outward behavior from reasoning_output.

        Returns a dict with:
            {
                "signals": [Signal objects or dicts],
                "requests": [Request objects or dicts],
                "env_updates": {key: value, ...},
            }

        Worlds can extend this pattern, but the outward behavior is always derived
        from Reasoning, not from Perception or Internal Update directly.
        """
        return reasoning_output.get("outward", self._empty_outward_behavior())

    def create_projection(self, request: Request) -> Projection:
        """Create a projection with structured payload and frottage (semantic soup)."""
        # Get visible structured state
        visible_state = self.get_visible_state()

        # Build structured payload (small, schema-aware)
        payload = {
            "kind": "projection",
            "agent_id": self.agent_id.value,
            "state": visible_state,
            # Worlds can extend with domain-specific structured fields
        }
        
        # Generate frottage text: rich, on-topic perturbation
        frottage = self._generate_frottage(request, visible_state)

        return Projection(
            id=MessageId(f"proj-{self.agent_id.value}-{request.id.value}"),
            sender=self.agent_id,
            receiver=request.sender,
            payload=payload,
            frottage=frottage,  # Dense text, separate from structured payload
        )

    def get_visible_state(self) -> Dict[str, Any]:
        """
        Return the agent's externally visible structured state.

        This is used to build projections. The default implementation
        returns minimal state. Worlds can extend Mind to provide richer views.
        """
        return {
            "agent_id": self.agent_id.value,
            # Add more structured state as needed
            # Never include manifold content here
        }

    def _generate_frottage(
        self, request: Request, visible_state: Dict[str, Any]
    ) -> Optional[str]:
        """
        Generate frottage for a projection.
        
        Frottage is semantic soup: dense, unstructured, rich with latent ideas,
        contradictions, unexplored threads, tangential connections. The receiver
        makes sense of it with no special prompting—just context.
        """
        # Load manifold for context
        try:
            manifold = self._load_manifold()
            manifold_content = manifold.content if manifold else ""
        except Exception:
            manifold_content = ""
        
        # Simple prompt: just dump everything relevant
        prompt = f"""Write everything you know, think, suspect, or wonder about this topic.
Include half-formed ideas, contradictions, tangents, interdisciplinary connections.
Don't structure it. Don't summarize. Just dump.

Context:
{visible_state}

{manifold_content if manifold_content else ""}

{request.shape if request.shape else ""}"""
        
        try:
            response = self._llm.complete(prompt)
            text = getattr(response, "text", None)
            if text is None:
                text = str(response)
            return text if text.strip() else None
        except NotImplementedError:
            return self._generate_fallback_frottage(visible_state)
        except Exception:
            return self._generate_fallback_frottage(visible_state)
    
    def _generate_fallback_frottage(self, visible_state: Dict[str, Any]) -> str:
        """Fallback when LLM unavailable: just dump the state."""
        return str(visible_state)

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _ensure_initial_manifold(self) -> None:
        """
        Guarantee that a ManifoldEnvelope exists for this Mind.

        Every Mind always has a manifold. This is an architectural invariant.
        """
        existing = self._store.load_latest(self.agent_id)
        if existing is not None:
            return

        initial = ManifoldEnvelope(
            agent_id=self.agent_id,
            version=0,
            content="",
            metadata={"initial": True},
        )
        self._store.save(initial)

    def _load_manifold(self) -> ManifoldEnvelope:
        """
        Load the latest manifold envelope, guaranteed to exist after __init__.

        Raises:
            RuntimeError: If manifold store fails to load and recovery fails
        """
        try:
            env = self._store.load_latest(self.agent_id)
        except Exception as e:
            raise RuntimeError(
                f"Failed to load manifold for agent '{self.agent_id.value}': {type(e).__name__}: {str(e)}. "
                f"This may indicate a problem with the manifold store."
            ) from e

        if env is None:
            # This should not happen if _ensure_initial_manifold is respected,
            # but we keep a defensive fallback.
            env = ManifoldEnvelope(
                agent_id=self.agent_id,
                version=0,
                content="",
                metadata={"recovered": True},
            )
            try:
                self._store.save(env)
            except Exception as e:
                raise RuntimeError(
                    f"Failed to create recovery manifold for agent '{self.agent_id.value}': "
                    f"{type(e).__name__}: {str(e)}"
                ) from e
        return env

    @staticmethod
    def _empty_outward_behavior() -> Dict[str, Any]:
        """
        Return empty outward behavior structure.

        Outward behavior may include:
        - signals: List of Signal objects or dicts
        - requests: List of Request objects or dicts
        - env_updates: Dict of EnvState key-value updates
        - holonomy_marker: bool - True if this action is holonomy (irreversible-ish)
        - holonomy_type: str - Optional type of holonomy action
        - holonomy_description: str - Optional description of the holonomy
        """
        return {
            "signals": [],
            "requests": [],
            "env_updates": {},
            "holonomy_marker": False,
        }

    @staticmethod
    def _result_to_dict(result: ReasoningResult) -> Dict[str, Any]:
        return {
            "agent_id": result.context.get("agent_id"),
            "notes": result.notes,
            "outward": result.outward,
            "context": result.context,
        }

    def _build_context_from_percept(self, percept: Optional[Percept]) -> Dict[str, Any]:
        """
        Convert a Percept into a generic context dict for reasoning.

        This mirrors Percept.to_context(), but keeps the transformation explicit here
        so worlds can subclass Mind and customize how percepts are rendered.
        """
        if percept is None:
            # Very defensive; in normal runs, runtime always calls perceive() first.
            return {
                "tick": None,
                "agent_id": self.agent_id.value,
                "projections": [],
                "data_feeds": {},
                "signals": [],
                "extras": {},
            }

        ctx = percept.to_context()
        # Ensure agent_id value is always present.
        ctx["agent_id"] = percept.agent_id.value
        return ctx

    # -------------------------------------------------------------------------
    # Reasoning
    # -------------------------------------------------------------------------

    def _run_reasoning_with_manifold(self, context: Dict[str, Any]) -> ReasoningResult:
        """
        Reasoning with manifold.

        The manifold content is included in the context and may be used by the Mind
        for internal thinking, but never leaves this class.

        If branching is enabled, generates multiple reasoning branches and consolidates them.
        """
        # Extract tool names from context if available (from DNA via runtime)
        tool_names = context.get("available_tools", None)
        base_prompt = self._build_prompt(context, include_manifold=True, tool_names=tool_names)

        # Check if branching is enabled (has LLM client)
        if self._branching._llm is not None:
            # Generate multiple reasoning branches
            branches = self._branching.run_branches(
                base_prompt=base_prompt,
                context=context,
                styles=None,  # Use default styles
            )

            if branches:
                # Consolidate branches into unified notes
                prior_manifold = context.get("manifold", "")
                notes = self._branching.consolidate(
                    branches=branches,
                    prior_manifold=prior_manifold if prior_manifold else None,
                    context=context,
                )
            else:
                # Branching failed or disabled, fall back to single pass
                notes = self._call_llm_for_notes(base_prompt)
        else:
            # No branching: single reasoning pass
            notes = self._call_llm_for_notes(base_prompt)

        return ReasoningResult(
            notes=notes,
            outward=self._empty_outward_behavior(),
            context=context,
        )

    # -------------------------------------------------------------------------
    # Prompting and LLM interaction
    # -------------------------------------------------------------------------

    def _build_prompt(self, context: Dict[str, Any], *, include_manifold: bool = True, tool_names: Optional[List[str]] = None) -> str:
        """
        Build prompt for reasoning. Frottage is just context—no special handling needed.
        """
        visible_context = dict(context)
        if not include_manifold and "manifold" in visible_context:
            visible_context.pop("manifold", None)
        
        # Extract any frottage and include as simple context
        frottage_sections = self._extract_frottage_for_prompt(visible_context)

        prompt_parts = [
            "You are an internal Mind. Think about the context and produce notes for your future self.",
        ]
        
        # Frottage is just "notes from before" - no special instructions needed
        if frottage_sections:
            prompt_parts.append("\nNotes from previous conversations:")
            prompt_parts.extend(frottage_sections)

        # Add tool information if available
        if self._tool_registry and tool_names:
            available_tools = self._tool_registry.get_all(tool_names)
            if available_tools:
                prompt_parts.append("\nAvailable tools:")
                for tool_name, tool in available_tools.items():
                    prompt_parts.append(f"  - {tool.name}: {tool.description}")

        prompt_parts.extend([
            "\nContext:",
            f"{self._context_without_frottage(visible_context)}",
        ])

        return "\n".join(prompt_parts)
    
    def _extract_frottage_for_prompt(self, context: Dict[str, Any]) -> List[str]:
        """Extract frottage from context."""
        sections = []
        
        for proj in context.get("projections", []):
            if isinstance(proj, dict) and proj.get("frottage"):
                sections.append(proj["frottage"])
        
        for sig in context.get("signals", []):
            if isinstance(sig, dict) and sig.get("frottage"):
                sections.append(sig["frottage"])
        
        return sections
    
    def _context_without_frottage(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Return context with frottage removed (shown separately)."""
        result = dict(context)
        
        if "projections" in result:
            result["projections"] = [
                {k: v for k, v in (p.items() if isinstance(p, dict) else {}) if k != "frottage"}
                for p in result.get("projections", [])
            ]
        
        if "signals" in result:
            result["signals"] = [
                {k: v for k, v in (s.items() if isinstance(s, dict) else {}) if k != "frottage"}
                for s in result.get("signals", [])
            ]
        
        return result

    def _call_llm_for_notes(self, prompt: str) -> str:
        """
        Call the underlying LLMClient to obtain internal notes.

        This method is robust to different LLMClient.complete return types:
        - the skeleton LLMClient is expected to return an object with a 'text' attribute;
        - tests may override and return simple objects; we fall back to str(resp).

        Raises:
            RuntimeError: If LLM call fails unexpectedly (not NotImplementedError)
        """
        try:
            resp = self._llm.complete(prompt)
        except NotImplementedError:
            # In pure-graph or no-LLM environments, it's acceptable to have empty notes.
            return ""
        except Exception as e:
            # Unexpected error from LLM - provide informative error
            raise RuntimeError(
                f"LLM call failed for agent '{self.agent_id.value}': {type(e).__name__}: {str(e)}. "
                f"This may indicate a configuration issue with the LLM client."
            ) from e

        # Accept either the structured LLMResponse or any object with a 'text' attribute.
        text = getattr(resp, "text", None)
        if text is None:
            text = str(resp)

        return text

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from synaplex.core.agent_interface import AgentInterface
from synaplex.core.ids import AgentId, MessageId
from synaplex.core.messages import Percept, Projection, Request
from synaplex.core.world_modes import WorldMode

from .llm_client import LLMClient
from .manifolds import ManifoldEnvelope, ManifoldStore, InMemoryManifoldStore
from .branching import BranchingStrategy, BranchOutput
from .update import UpdateMechanism


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
    - Respect world modes (loop truncations):
        GRAPH_ONLY, REASONING_ONLY, MANIFOLD
    - Maintain manifold privacy:
        Only this class loads/saves ManifoldEnvelope;
        no manifold text ever leaves the Mind.
    """

    def __init__(
        self,
        agent_id: AgentId,
        llm_client: LLMClient,
        *,
        manifold_store: Optional[ManifoldStore] = None,
        update_mechanism: Optional[UpdateMechanism] = None,
        branching_strategy: Optional[BranchingStrategy] = None,
        # Legacy parameter kept for compatibility with existing tests:
        #   enable_persistent_worldview=False  → REASONING_ONLY
        #   enable_persistent_worldview=True   → MANIFOLD
        enable_persistent_worldview: bool = True,
        world_mode: Optional[WorldMode] = None,
    ) -> None:
        super().__init__(agent_id=agent_id)

        self._llm = llm_client
        # Default to in-memory store for backward compatibility
        self._store = manifold_store or InMemoryManifoldStore()
        # UpdateMechanism gets LLM client for checkpoint rituals
        self._update_mechanism = update_mechanism or UpdateMechanism(llm_client=llm_client)
        # BranchingStrategy gets LLM client if provided
        self._branching = branching_strategy or BranchingStrategy(llm_client=llm_client)

        # WorldMode resolution:
        #   - explicit world_mode wins
        #   - otherwise, map legacy enable_persistent_worldview flag
        if world_mode is not None:
            self._mode = world_mode
        else:
            self._mode = (
                WorldMode.MANIFOLD if enable_persistent_worldview else WorldMode.REASONING_ONLY
            )

        self._last_percept: Optional[Percept] = None

        # Invariants: every Mind has a manifold envelope, even if some modes never use it.
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
        Reasoning (+ Internal Update, when enabled).

        Returns a reasoning_output dict:

            {
                "agent_id": AgentId,
                "notes": str,          # internal notes intended for the Mind's future self
                "outward": { ... },    # outward behavior to be consumed by act()
                "context": { ... },    # percept-derived reasoning context (for debugging/analysis)
            }

        Internal Update (manifold checkpoint) occurs here *only* in MANIFOLD mode.
        """
        context = self._build_context_from_percept(self._last_percept)
        prior_envelope: Optional[ManifoldEnvelope] = None

        # GRAPH_ONLY: deterministic, no reasoning, no manifold usage.
        if self._mode == WorldMode.GRAPH_ONLY:
            result = ReasoningResult(
                notes="",
                outward=self._empty_outward_behavior(),
                context=context,
            )
            return self._result_to_dict(result)

        # REASONING_ONLY: perception + LLM reasoning; manifold exists but is not used.
        if self._mode == WorldMode.REASONING_ONLY:
            result = self._run_reasoning_without_manifold(context)
            # No Internal Update in this mode.
            return self._result_to_dict(result)

        # MANIFOLD: full loop; manifold participates in reasoning and is updated.
        if self._mode == WorldMode.MANIFOLD:
            prior_envelope = self._load_manifold()
            # We include the current manifold content only for the Mind's own use.
            # This never leaves the Mind.
            context_with_manifold = dict(context)
            context_with_manifold["manifold"] = prior_envelope.content

            result = self._run_reasoning_with_manifold(context_with_manifold)

            # Internal Update: checkpoint ritual → new ManifoldEnvelope
            # Pass agent_id as AgentId, not string
            envelope = self._update_mechanism.update_worldview(
                prior=prior_envelope,
                reasoning_output={
                    "agent_id": self.agent_id,  # Already an AgentId
                    "notes": result.notes,
                    "context": result.context,
                },
            )
            self._store.save(envelope)

            return self._result_to_dict(result)

        # Should not be reachable; defensive fallback.
        result = ReasoningResult(
            notes="",
            outward=self._empty_outward_behavior(),
            context=context,
        )
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
        """
        Create a projection in response to a request.

        This exposes structured state views of the agent. The projection:
        - Contains only structured data (never raw manifold text)
        - May include EnvState data the agent has access to
        - Is transformed by the receiver's lens (handled by runtime)

        The projection payload is built from:
        - Agent's visible state (via get_visible_state())
        - Any structured data the agent chooses to expose
        """
        # Get visible structured state
        visible_state = self.get_visible_state()

        # Build projection payload
        # Note: We never include raw manifold content here
        payload = {
            "agent_id": self.agent_id.value,
            "state": visible_state,
            # Worlds can extend this with domain-specific structured views
        }

        return Projection(
            id=MessageId(f"proj-{self.agent_id.value}-{request.id.value}"),
            sender=self.agent_id,
            receiver=request.sender,
            payload=payload,
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

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _ensure_initial_manifold(self) -> None:
        """
        Guarantee that a ManifoldEnvelope exists for this Mind.

        Even in ablation modes (GRAPH_ONLY / REASONING_ONLY), a manifold object exists
        conceptually; those modes simply choose not to consult or update it.
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
        """
        env = self._store.load_latest(self.agent_id)
        if env is None:
            # This should not happen if _ensure_initial_manifold is respected,
            # but we keep a defensive fallback.
            env = ManifoldEnvelope(
                agent_id=self.agent_id,
                version=0,
                content="",
                metadata={"recovered": True},
            )
            self._store.save(env)
        return env

    @staticmethod
    def _empty_outward_behavior() -> Dict[str, Any]:
        return {
            "signals": [],
            "requests": [],
            "env_updates": [],
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
    # Reasoning variants
    # -------------------------------------------------------------------------

    def _run_reasoning_without_manifold(self, context: Dict[str, Any]) -> ReasoningResult:
        """
        Reasoning in REASONING_ONLY mode.

        The Mind thinks each tick but does not consult or update the manifold.
        """
        prompt = self._build_prompt(context, include_manifold=False)
        notes = self._call_llm_for_notes(prompt)

        return ReasoningResult(
            notes=notes,
            outward=self._empty_outward_behavior(),
            context=context,
        )

    def _run_reasoning_with_manifold(self, context: Dict[str, Any]) -> ReasoningResult:
        """
        Reasoning in MANIFOLD mode.

        The manifold content is included in the context and may be used by the Mind
        for internal thinking, but never leaves this class.

        If branching is enabled, generates multiple reasoning branches and consolidates them.
        """
        base_prompt = self._build_prompt(context, include_manifold=True)

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

    def _build_prompt(self, context: Dict[str, Any], *, include_manifold: bool) -> str:
        """
        Build a minimal, architecture-respecting prompt.

        This prompt intentionally:
        - does not impose any schema on the manifold,
        - does not ask for summaries or cleaned-up representations,
        - treats the output strictly as internal notes for the Mind's own future use.
        """
        # We deliberately stringify the context instead of unpacking it into a schema,
        # so that structure remains emergent behavior at the Mind level.
        visible_context = dict(context)
        if not include_manifold and "manifold" in visible_context:
            # Ensure manifold does not accidentally leak into non-manifold modes.
            visible_context.pop("manifold", None)

        return (
            "You are an internal Mind for an agent in a multi-mind system.\n"
            "Your job is to think about the given context and produce internal notes "
            "for your own future self. Do NOT format these as JSON or any rigid schema.\n\n"
            "Context (for you only):\n"
            f"{visible_context}\n\n"
            "Write internal notes that will help your future self reason better next time."
        )

    def _call_llm_for_notes(self, prompt: str) -> str:
        """
        Call the underlying LLMClient to obtain internal notes.

        This method is robust to different LLMClient.complete return types:
        - the skeleton LLMClient is expected to return an object with a 'text' attribute;
        - tests may override and return simple objects; we fall back to str(resp).
        """
        try:
            resp = self._llm.complete(prompt)
        except NotImplementedError:
            # In pure-graph or no-LLM environments, it's acceptable to have empty notes.
            return ""

        # Accept either the structured LLMResponse or any object with a 'text' attribute.
        text = getattr(resp, "text", None)
        if text is None:
            text = str(resp)

        return text

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
        """
        Create a projection in response to a request.

        This exposes structured state views of the agent. The projection:
        - Contains only structured data (never raw manifold text)
        - May include EnvState data the agent has access to
        - Is transformed by the receiver's lens (handled by runtime)
        - Generates "overloaded but on-topic" frottage envelopes (F)

        The projection payload is built from:
        - Agent's visible state (via get_visible_state())
        - Frottage envelope: rich, redundant, overlapping frames
        - Any structured data the agent chooses to expose

        Geometrically, this implements the frottage operator F:
        F(M, R) → E_F(R), where E_F(R) is a high-entropy sampling of
        a region R of the manifold M, including points, tangent directions,
        analogies, tensions, and negative space.
        """
        # Get visible structured state
        visible_state = self.get_visible_state()

        # Generate frottage envelope: overloaded but on-topic
        frottage_envelope = self._generate_frottage_envelope(request, visible_state)

        # Build projection payload
        # Note: We never include raw manifold content here
        payload = {
            "agent_id": self.agent_id.value,
            "state": visible_state,
            "frottage": frottage_envelope,
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

    def _generate_frottage_envelope(
        self, request: Request, visible_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a frottage envelope (F) for a projection.

        Frottage is a geometric operator that produces a high-entropy sampling
        of a region R of the manifold M. The envelope E_F(R) includes:
        - Points in R (concepts, ideas)
        - Nearby tangent directions (related concepts)
        - Successful and failed analogies (local "almost symmetries")
        - Tension directions (non-commuting flows)
        - Negative space ("not-this" shards)

        This is "overloaded but on-topic": rich, redundant, contradictory,
        but concentrated in a region overlapping the receiver's domain.

        Args:
            request: The request from the receiver (shapes what region to sample)
            visible_state: The agent's visible structured state

        Returns:
            Frottage envelope dict with multiple overlapping frames
        """
        # Default implementation: create a rich, redundant envelope from visible state
        # Worlds can override to generate more sophisticated frottage

        # Build multiple overlapping frames
        frames = []

        # Frame 1: Direct state view
        frames.append({
            "type": "direct_state",
            "content": visible_state,
            "perspective": "current structured view",
        })

        # Frame 2: Contextual hints (what this state implies)
        frames.append({
            "type": "contextual_hints",
            "content": {
                "implications": "This state suggests...",
                "related_concepts": [],
                "tensions": [],
            },
            "perspective": "implicit context",
        })

        # Frame 3: Negative space (what this is NOT)
        frames.append({
            "type": "negative_space",
            "content": {
                "not_this": "This does not include...",
                "boundaries": [],
            },
            "perspective": "exclusion boundaries",
        })

        # Frame 4: Tension directions (non-commuting flows)
        frames.append({
            "type": "tensions",
            "content": {
                "tension_directions": [],
                "unresolved": [],
            },
            "perspective": "non-commuting flows",
        })

        return {
            "frames": frames,
            "redundancy_level": "high",  # Explicitly overloaded
            "on_topic": True,  # Concentrated in relevant region
            "metadata": {
                "request_shape": request.shape,
                "generated_by": self.agent_id.value,
            },
        }

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
        Build a minimal, architecture-respecting prompt.

        This prompt intentionally:
        - does not impose any schema on the manifold,
        - does not ask for summaries or cleaned-up representations,
        - treats the output strictly as internal notes for the Mind's own future use.
        - includes tool information if tools are available
        """
        # We deliberately stringify the context instead of unpacking it into a schema,
        # so that structure remains emergent behavior at the Mind level.
        visible_context = dict(context)
        if not include_manifold and "manifold" in visible_context:
            # Ensure manifold does not accidentally leak into non-manifold modes.
            visible_context.pop("manifold", None)

        prompt_parts = [
            "You are an internal Mind for an agent in a multi-mind system.",
            "Your job is to think about the given context and produce internal notes "
            "for your own future self. Do NOT format these as JSON or any rigid schema.",
        ]

        # Add tool information if available
        if self._tool_registry and tool_names:
            available_tools = self._tool_registry.get_all(tool_names)
            if available_tools:
                prompt_parts.append("\nAvailable tools:")
                for tool_name, tool in available_tools.items():
                    prompt_parts.append(f"  - {tool.name}: {tool.description}")
                prompt_parts.append(
                    "\nYou can use these tools during reasoning. Tool results will be "
                    "provided as structured data, not text."
                )

        prompt_parts.extend([
            "\nContext (for you only):",
            f"{visible_context}",
            "\nWrite internal notes that will help your future self reason better next time."
        ])

        return "\n".join(prompt_parts)

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

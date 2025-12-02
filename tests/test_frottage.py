# tests/test_frottage.py

"""
Tests for frottage implementation.

Frottage is pure, unstructured semantic soup.
No schemas. No envelopes. No metadata. Raw language only.
Receiver-owned interpretation.
"""

from typing import Any, Dict

from synaplex.core.ids import AgentId, MessageId, WorldId
from synaplex.core.messages import Signal, Projection, Request, Percept
from synaplex.core.lenses import Lens
from synaplex.core.dna import DNA
from synaplex.core.runtime_inprocess import InProcessRuntime
from synaplex.core.env_state import EnvState
from synaplex.cognition.llm_client import LLMClient
from synaplex.cognition.mind import Mind

from synaplex.worlds.ideas_world.lenses import (
    IdeaArchitectLens,
    IdeaCriticLens,
    IdeaPMLens,
)
from synaplex.worlds.ideas_world.agents import (
    _generate_idea_frottage,
    _generate_idea_frottage_fallback,
)


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------


class DummyLLM(LLMClient):
    """Dummy LLM for testing that returns predictable output."""

    def __init__(self, response_text: str = "dummy-frottage-response"):
        self.response_text = response_text
        self.last_prompt = None

    def complete(self, prompt: str, **kwargs):
        self.last_prompt = prompt
        return type("Resp", (), {"text": self.response_text, "raw": {}})()


class FrottageCaptureMind(Mind):
    """Mind that captures incoming frottage for testing."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.captured_frottage = []

    def reason(self) -> Dict[str, Any]:
        result = super().reason()
        # Capture any frottage from the percept
        if self._last_percept:
            for proj in self._last_percept.projections:
                if proj.frottage:
                    self.captured_frottage.append(
                        {"source": proj.sender.value, "frottage": proj.frottage}
                    )
            for sig in self._last_percept.signals:
                if sig.frottage:
                    self.captured_frottage.append(
                        {"source": sig.sender.value, "frottage": sig.frottage}
                    )
        return result


# ---------------------------------------------------------------------------
# Test: Signal and Projection have frottage fields
# ---------------------------------------------------------------------------


def test_signal_has_frottage_field():
    """Signal should have an optional frottage: str | None field."""
    sig = Signal(
        id=MessageId("sig-1"),
        sender=AgentId("agent-a"),
        payload={"kind": "idea", "title": "Test Idea"},
        frottage="This is dense, on-topic frottage text...",
    )

    assert sig.frottage == "This is dense, on-topic frottage text..."
    assert sig.payload["kind"] == "idea"


def test_signal_frottage_defaults_to_none():
    """Signal frottage should default to None if not provided."""
    sig = Signal(
        id=MessageId("sig-1"),
        sender=AgentId("agent-a"),
        payload={"kind": "idea"},
    )

    assert sig.frottage is None


def test_projection_has_frottage_field():
    """Projection should have an optional frottage: str | None field."""
    proj = Projection(
        id=MessageId("proj-1"),
        sender=AgentId("agent-a"),
        receiver=AgentId("agent-b"),
        payload={"kind": "idea_projection", "domain": "geometry"},
        frottage="Dense, multi-paragraph frottage exploring the idea space...",
    )

    assert proj.frottage == "Dense, multi-paragraph frottage exploring the idea space..."
    assert proj.payload["kind"] == "idea_projection"


def test_projection_frottage_defaults_to_none():
    """Projection frottage should default to None if not provided."""
    proj = Projection(
        id=MessageId("proj-1"),
        sender=AgentId("agent-a"),
        receiver=AgentId("agent-b"),
        payload={"kind": "idea_projection"},
    )

    assert proj.frottage is None


# ---------------------------------------------------------------------------
# Test: Frottage is pure unstructured text
# ---------------------------------------------------------------------------


def test_frottage_is_just_text():
    """Frottage is raw text. No schemas. No structure. Receiver interprets."""
    frottage = """
    Half-formed thought about manifolds... the curvature feels wrong
    but I can't articulate why. Maybe it's related to that paper on
    fiber bundles? Or was it the conversation about teleology vectors?
    There's something here about how perturbations propagate through
    the attractor landscape. Contradicts what I said earlier about K.
    """

    proj = Projection(
        id=MessageId("proj-1"),
        sender=AgentId("sender"),
        receiver=AgentId("receiver"),
        payload={},  # Minimal or empty - the frottage is what matters
        frottage=frottage,
    )

    # Frottage is just a string
    assert isinstance(proj.frottage, str)
    assert "Half-formed" in proj.frottage
    assert "Contradicts" in proj.frottage


# ---------------------------------------------------------------------------
# Test: Percept.to_context() includes frottage
# ---------------------------------------------------------------------------


def test_percept_to_context_includes_frottage():
    """Percept.to_context() should pass frottage through unchanged."""
    proj = Projection(
        id=MessageId("proj-1"),
        sender=AgentId("agent-a"),
        receiver=AgentId("agent-b"),
        payload={"kind": "idea"},
        frottage="Dense frottage text here...",
    )

    sig = Signal(
        id=MessageId("sig-1"),
        sender=AgentId("agent-c"),
        payload={"kind": "update"},
        frottage="Signal frottage text...",
    )

    percept = Percept(
        agent_id=AgentId("agent-b"),
        tick=1,
        projections=[proj],
        signals=[sig],
    )

    context = percept.to_context()

    # Projections should have frottage
    assert len(context["projections"]) == 1
    assert context["projections"][0]["frottage"] == "Dense frottage text here..."
    assert context["projections"][0]["sender"] == "agent-a"

    # Signals should have frottage
    assert len(context["signals"]) == 1
    assert context["signals"][0]["frottage"] == "Signal frottage text..."
    assert context["signals"][0]["sender"] == "agent-c"


# ---------------------------------------------------------------------------
# Test: Lenses only filter, they don't transform
# ---------------------------------------------------------------------------


def test_lenses_only_filter():
    """Lenses should only filter, not transform. Receiver-owned semantics."""
    # All lenses attend to everything now - the Mind decides what's relevant
    architect = IdeaArchitectLens(name="architect")
    critic = IdeaCriticLens(name="critic")
    pm = IdeaPMLens(name="pm")
    
    # All should attend
    assert architect.should_attend({}) is True
    assert critic.should_attend({}) is True
    assert pm.should_attend({}) is True
    
    # Lenses don't have transform_projection anymore
    assert not hasattr(architect, 'transform_projection') or \
           architect.transform_projection == Lens.transform_projection


# ---------------------------------------------------------------------------
# Test: Frottage generation helpers
# ---------------------------------------------------------------------------


def test_generate_idea_frottage_fallback():
    """Fallback frottage should just dump the content."""
    idea = {
        "title": "Manifold Operators",
        "domain": "geometry",
        "content": "The manifold operators form a basis...",
    }

    frottage = _generate_idea_frottage_fallback(idea)

    # Should include the content
    assert "manifold operators" in frottage.lower()


def test_generate_idea_frottage_with_llm():
    """Frottage generation should use LLM when available."""
    idea = {
        "title": "Test Idea",
        "content": "A test idea.",
    }

    llm = DummyLLM(response_text="LLM-generated semantic soup...")

    frottage = _generate_idea_frottage(idea, llm_client=llm)

    assert frottage == "LLM-generated semantic soup..."
    # Prompt should be simple - just dump
    assert "dump" in llm.last_prompt.lower()


def test_generate_idea_frottage_fallback_on_llm_error():
    """Should fall back if LLM fails."""

    class FailingLLM(LLMClient):
        def complete(self, prompt, **kwargs):
            raise RuntimeError("LLM error")

    idea = {
        "title": "Fallback Test",
        "content": "Test content here.",
    }

    frottage = _generate_idea_frottage(idea, llm_client=FailingLLM())

    # Should have the content
    assert "Test content" in frottage


# ---------------------------------------------------------------------------
# Test: Mind generates frottage for projections
# ---------------------------------------------------------------------------


def test_mind_create_projection_includes_frottage():
    """Mind.create_projection should generate frottage."""
    llm = DummyLLM(response_text="Mind-generated frottage for the receiver...")

    mind = Mind(agent_id=AgentId("test-mind"), llm_client=llm)

    request = Request(
        id=MessageId("req-1"),
        sender=AgentId("requester"),
        receiver=mind.agent_id,
        shape={"topic": "geometry"},
    )

    projection = mind.create_projection(request)

    # Projection should have frottage as a string
    assert projection.frottage is not None
    assert isinstance(projection.frottage, str)
    assert len(projection.frottage) > 0

    # Payload should be structured meta, separate from frottage
    assert "kind" in projection.payload
    assert projection.payload["kind"] == "projection"


def test_mind_create_projection_frottage_is_separate_from_payload():
    """Projection frottage should not be inside the payload dict."""
    llm = DummyLLM()
    mind = Mind(agent_id=AgentId("test-mind"), llm_client=llm)

    request = Request(
        id=MessageId("req-1"),
        sender=AgentId("requester"),
        receiver=mind.agent_id,
    )

    projection = mind.create_projection(request)

    # Frottage is a top-level field on Projection, not in payload
    assert projection.frottage is not None
    assert "frottage" not in projection.payload


# ---------------------------------------------------------------------------
# Test: Mind reasoning handles incoming frottage
# ---------------------------------------------------------------------------


def test_mind_prompt_includes_frottage_as_context():
    """Mind prompt should include frottage as simple context (notes from before)."""
    llm = DummyLLM()
    mind = Mind(agent_id=AgentId("test-mind"), llm_client=llm)

    # Create context with incoming frottage
    context = {
        "tick": 1,
        "projections": [
            {
                "payload": {"kind": "idea"},
                "frottage": "Semantic soup from another Mind...",
                "sender": "other-mind",
            }
        ],
        "signals": [],
        "manifold": "",
    }

    prompt = mind._build_prompt(context)

    # Prompt should include the frottage as context
    assert "Semantic soup from another Mind" in prompt
    # Should be framed simply as notes, not with complex instructions
    assert "notes" in prompt.lower()


def test_mind_extracts_frottage_for_prompt():
    """Mind should extract frottage from context."""
    llm = DummyLLM()
    mind = Mind(agent_id=AgentId("test-mind"), llm_client=llm)

    context = {
        "projections": [
            {"frottage": "Projection frottage 1"},
            {"frottage": "Projection frottage 2"},
        ],
        "signals": [
            {"frottage": "Signal frottage"},
        ],
    }

    sections = mind._extract_frottage_for_prompt(context)

    # Should have extracted all frottage
    assert "Projection frottage 1" in sections
    assert "Projection frottage 2" in sections
    assert "Signal frottage" in sections


def test_mind_context_without_frottage_removes_duplication():
    """Mind should remove frottage from context to prevent duplication in prompt."""
    llm = DummyLLM()
    mind = Mind(agent_id=AgentId("test-mind"), llm_client=llm)

    context = {
        "projections": [
            {"payload": {"kind": "idea"}, "frottage": "Should be removed"},
        ],
        "signals": [
            {"payload": {"kind": "update"}, "frottage": "Also removed"},
        ],
    }

    cleaned = mind._context_without_frottage(context)

    # Frottage should be removed
    assert "frottage" not in cleaned["projections"][0]
    assert "frottage" not in cleaned["signals"][0]

    # Payload should remain
    assert cleaned["projections"][0]["payload"]["kind"] == "idea"
    assert cleaned["signals"][0]["payload"]["kind"] == "update"


# ---------------------------------------------------------------------------
# Test: Integration - Frottage flows through runtime
# ---------------------------------------------------------------------------


def test_frottage_flows_through_runtime():
    """Frottage should flow from sender to receiver through runtime unchanged."""
    world_id = WorldId("test-world")
    runtime = InProcessRuntime(world_id, EnvState())

    llm = DummyLLM()
    sender = Mind(agent_id=AgentId("sender"), llm_client=llm)
    receiver = FrottageCaptureMind(agent_id=AgentId("receiver"), llm_client=llm)

    # Receiver subscribes to sender
    dna = DNA(
        agent_id=AgentId("receiver"),
        role="receiver",
        subscriptions=[AgentId("sender")],
    )

    runtime.register_agent(sender)
    runtime.register_agent(receiver, dna=dna)

    # Sender emits signal with frottage
    test_frottage = "Dense, on-topic frottage that should pass through unchanged..."
    signal = Signal(
        id=MessageId("sig-frottage"),
        sender=AgentId("sender"),
        payload={"kind": "test"},
        frottage=test_frottage,
    )
    runtime._current_tick_signals[AgentId("sender")] = [signal]

    # Build percept for receiver
    percept = runtime._build_percept(AgentId("receiver"), 0)

    # Frottage should be in percept unchanged
    assert len(percept.signals) == 1
    assert percept.signals[0].frottage == test_frottage


# ---------------------------------------------------------------------------
# Test: Contract invariants
# ---------------------------------------------------------------------------


def test_frottage_contract_large_text_allowed():
    """Frottage should allow large text (no arbitrary short limits)."""
    # Generate a large frottage (several kilobytes)
    large_frottage = "Dense, on-topic text. " * 500  # ~10KB

    proj = Projection(
        id=MessageId("proj-1"),
        sender=AgentId("sender"),
        receiver=AgentId("receiver"),
        payload={"kind": "idea"},
        frottage=large_frottage,
    )

    # Should work without truncation
    assert len(proj.frottage) == len(large_frottage)


def test_frottage_contract_core_does_not_parse():
    """Core message types should store frottage as opaque string."""
    # Frottage can be any text - doesn't need to be JSON or structured
    weird_frottage = """
    This is messy, exploratory text with:
    - Partial metaphors (like ripples, but not quite...)
    - Contradictions (it's both X and not-X in some sense)
    - Half-formed intuitions ~~~waves hands~~~
    - Unicode: 🎭 🔮 ∞ ∅ ∇
    - Random formatting that makes no sense
    
    {{{this looks like JSON but isn't}}}
    [[this looks like a link but isn't]]
    
    The point is: frottage is OPAQUE to core.
    """

    sig = Signal(
        id=MessageId("sig-1"),
        sender=AgentId("a"),
        payload={"kind": "idea"},
        frottage=weird_frottage,
    )

    # Core just stores it, never parses
    assert sig.frottage == weird_frottage


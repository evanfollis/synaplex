# tests/test_update_mechanism.py

"""
Tests for UpdateMechanism checkpoint rituals.

Tests:
- Simple update (no LLM)
- LLM-backed checkpoint ritual
- Versioning and metadata
- Integration with prior manifold
"""

from synaplex.core.ids import AgentId
from synaplex.cognition.llm_client import LLMClient
from synaplex.cognition.manifolds import ManifoldEnvelope
from synaplex.cognition.update import UpdateMechanism


class DummyLLM(LLMClient):
    """Dummy LLM for testing."""
    def __init__(self, response_text: str = "Updated worldview content"):
        self.response_text = response_text

    def complete(self, prompt: str, **kwargs):
        return type("Resp", (), {"text": self.response_text, "raw": {}})()


def test_simple_update_without_llm():
    """Test simple update mechanism when no LLM is provided."""
    mechanism = UpdateMechanism(llm_client=None)

    # Initial manifold
    reasoning_output = {
        "agent_id": AgentId("agent-1"),
        "notes": "Initial reasoning notes",
        "context": {},
    }

    envelope = mechanism.update_worldview(prior=None, reasoning_output=reasoning_output)

    assert envelope.version == 1
    assert envelope.agent_id == AgentId("agent-1")
    assert envelope.content == "Initial reasoning notes"
    assert envelope.metadata["source"] == "simple-update"

    # Update existing manifold
    prior = envelope
    reasoning_output2 = {
        "agent_id": AgentId("agent-1"),
        "notes": "New reasoning notes",
        "context": {"tick": 1},
    }

    envelope2 = mechanism.update_worldview(prior=prior, reasoning_output=reasoning_output2)

    assert envelope2.version == 2
    assert envelope2.agent_id == AgentId("agent-1")
    assert "Initial reasoning notes" in envelope2.content
    assert "New reasoning notes" in envelope2.content
    assert "---" in envelope2.content  # Separator


def test_llm_backed_checkpoint_ritual():
    """Test LLM-backed checkpoint ritual."""
    llm = DummyLLM(response_text="Integrated worldview with prior and new insights")
    mechanism = UpdateMechanism(llm_client=llm)

    # Initial manifold
    reasoning_output = {
        "agent_id": AgentId("agent-1"),
        "notes": "Initial notes",
        "context": {"tick": 0},
    }

    envelope = mechanism.update_worldview(prior=None, reasoning_output=reasoning_output)

    assert envelope.version == 1
    assert envelope.content == "Integrated worldview with prior and new insights"
    assert envelope.metadata["source"] == "checkpoint-ritual"

    # Update with prior
    prior = ManifoldEnvelope(
        agent_id=AgentId("agent-1"),
        version=1,
        content="Prior worldview content",
        metadata={},
    )

    reasoning_output2 = {
        "agent_id": AgentId("agent-1"),
        "notes": "New insights from tick 1",
        "context": {"tick": 1},
    }

    envelope2 = mechanism.update_worldview(prior=prior, reasoning_output=reasoning_output2)

    assert envelope2.version == 2
    assert envelope2.content == "Integrated worldview with prior and new insights"
    assert envelope2.metadata["source"] == "checkpoint-ritual"
    assert envelope2.metadata["tick"] == 1


def test_update_with_prior_manifold_integration():
    """Test that prior manifold is properly integrated."""
    llm = DummyLLM(response_text="Updated: prior worldview + new notes integrated")
    mechanism = UpdateMechanism(llm_client=llm)

    prior = ManifoldEnvelope(
        agent_id=AgentId("agent-1"),
        version=5,
        content="Existing worldview with patterns and structures",
        metadata={"previous_tick": 10},
    )

    reasoning_output = {
        "agent_id": AgentId("agent-1"),
        "notes": "New observations and insights",
        "context": {"tick": 11, "projections": []},
    }

    envelope = mechanism.update_worldview(prior=prior, reasoning_output=reasoning_output)

    assert envelope.version == 6  # Incremented
    assert envelope.agent_id == prior.agent_id  # Same agent
    assert envelope.metadata["tick"] == 11


def test_fallback_on_llm_error():
    """Test that mechanism falls back to simple update on LLM error."""
    class ErrorLLM(LLMClient):
        def complete(self, prompt: str, **kwargs):
            raise RuntimeError("LLM error")

    llm = ErrorLLM()
    mechanism = UpdateMechanism(llm_client=llm)

    prior = ManifoldEnvelope(
        agent_id=AgentId("agent-1"),
        version=1,
        content="Prior content",
        metadata={},
    )

    reasoning_output = {
        "agent_id": AgentId("agent-1"),
        "notes": "New notes",
        "context": {},
    }

    # Should fall back to simple update
    envelope = mechanism.update_worldview(prior=prior, reasoning_output=reasoning_output)

    assert envelope.version == 2
    # Should contain both prior and new (simple concatenation)
    assert "Prior content" in envelope.content
    assert "New notes" in envelope.content


def test_agent_id_handling():
    """Test that agent_id is handled correctly (AgentId or string)."""
    mechanism = UpdateMechanism(llm_client=None)

    # With string agent_id
    reasoning_output = {
        "agent_id": "agent-1",  # String
        "notes": "Notes",
        "context": {},
    }

    envelope = mechanism.update_worldview(prior=None, reasoning_output=reasoning_output)
    assert isinstance(envelope.agent_id, AgentId)
    assert envelope.agent_id == AgentId("agent-1")

    # With AgentId
    reasoning_output2 = {
        "agent_id": AgentId("agent-2"),  # AgentId
        "notes": "Notes",
        "context": {},
    }

    envelope2 = mechanism.update_worldview(prior=None, reasoning_output=reasoning_output2)
    assert isinstance(envelope2.agent_id, AgentId)
    assert envelope2.agent_id == AgentId("agent-2")


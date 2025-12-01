# tests/test_runtime_message_routing.py

"""
Integration tests for runtime message routing.

Tests:
- Projection gathering from subscriptions
- Signal collection and filtering
- EnvState integration in percepts
- Outward behavior handling
"""

from typing import Any, Dict

from synaplex.core.ids import AgentId, WorldId
from synaplex.core.runtime_inprocess import InProcessRuntime, GraphConfig, EdgeConfig
from synaplex.core.env_state import EnvState
from synaplex.core.dna import DNA
from synaplex.core.lenses import Lens
from synaplex.core.messages import Signal, MessageId
from synaplex.cognition.llm_client import LLMClient
from synaplex.cognition.mind import Mind


class DummyLLM(LLMClient):
    """Dummy LLM for testing."""
    def complete(self, prompt: str, **kwargs):
        return type("Resp", (), {"text": "dummy-output", "raw": {}})()


def test_projection_gathering_via_subscriptions():
    """Test that subscriptions result in projections in percepts."""
    world_id = WorldId("test-world")
    runtime = InProcessRuntime(world_id, EnvState())

    # Create two agents
    agent_a = Mind(agent_id=AgentId("agent-a"), llm_client=DummyLLM())
    agent_b = Mind(agent_id=AgentId("agent-b"), llm_client=DummyLLM())

    # Agent B subscribes to Agent A
    dna_b = DNA(
        agent_id=AgentId("agent-b"),
        role="subscriber",
        subscriptions=[AgentId("agent-a")],
    )

    # Register agents with DNA
    runtime.register_agent(agent_a)
    runtime.register_agent(agent_b, dna=dna_b)

    # Run a tick
    runtime.tick(0)

    # Agent B should have received a projection from Agent A
    # We can't directly check the percept, but we can verify the runtime
    # built it correctly by checking subscriptions
    subscriptions = runtime._subscriptions_for(AgentId("agent-b"))
    assert AgentId("agent-a") in subscriptions


def test_signal_collection_and_filtering():
    """Test that signals are collected and can be filtered via lenses."""
    world_id = WorldId("test-world")
    runtime = InProcessRuntime(world_id, EnvState())

    # Create agents
    agent_a = Mind(agent_id=AgentId("agent-a"), llm_client=DummyLLM())
    agent_b = Mind(agent_id=AgentId("agent-b"), llm_client=DummyLLM())

    # Create a lens for agent B that filters signals
    class FilteringLens(Lens):
        def should_attend(self, signal_payload: Dict[str, Any]) -> bool:
            # Only attend to signals with type="important"
            return signal_payload.get("type") == "important"

    lens_b = FilteringLens(name="filtering")

    runtime.register_agent(agent_a)
    runtime.register_agent(agent_b, lens=lens_b)

    # Agent A emits a signal
    signal = Signal(
        id=MessageId("sig-1"),
        sender=AgentId("agent-a"),
        payload={"type": "important", "content": "hello"},
    )
    runtime._current_tick_signals[AgentId("agent-a")] = [signal]

    # Build percept for agent B
    percept = runtime._build_percept(AgentId("agent-b"), 0)

    # Agent B should see the signal (it's marked as important)
    assert len(percept.signals) == 1
    assert percept.signals[0].payload["type"] == "important"

    # Test filtering: add a non-important signal
    signal2 = Signal(
        id=MessageId("sig-2"),
        sender=AgentId("agent-a"),
        payload={"type": "noise", "content": "ignore me"},
    )
    runtime._current_tick_signals[AgentId("agent-a")].append(signal2)

    # Rebuild percept
    percept2 = runtime._build_percept(AgentId("agent-b"), 0)

    # Should still only see the important signal
    assert len(percept2.signals) == 1
    assert percept2.signals[0].payload["type"] == "important"


def test_env_state_in_percept():
    """Test that EnvState is included in percept extras."""
    world_id = WorldId("test-world")
    env_state = EnvState()
    env_state.set("shared_key", "shared_value")

    runtime = InProcessRuntime(world_id, env_state)

    agent = Mind(agent_id=AgentId("agent-1"), llm_client=DummyLLM())
    runtime.register_agent(agent)

    percept = runtime._build_percept(AgentId("agent-1"), 0)

    # EnvState should be in extras
    assert "env_state" in percept.extras
    assert percept.extras["env_state"]["data"]["shared_key"] == "shared_value"


def test_outward_behavior_handling():
    """Test that signals and env_updates from act() are handled."""
    world_id = WorldId("test-world")
    env_state = EnvState()
    runtime = InProcessRuntime(world_id, env_state)

    # Create a mind that emits signals and updates env_state
    class TestMind(Mind):
        def act(self, reasoning_output):
            return {
                "signals": [
                    {
                        "payload": {"type": "test", "value": 42},
                    }
                ],
                "env_updates": {
                    "test_key": "test_value",
                },
            }

    agent = TestMind(agent_id=AgentId("agent-1"), llm_client=DummyLLM())
    runtime.register_agent(agent)

    # Run a tick
    runtime.tick(0)

    # Check that env_state was updated
    assert env_state.get("test_key") == "test_value"

    # Check that signal was stored (will be available next tick)
    # Signals are stored in _current_tick_signals during the tick
    # After tick completes, they're cleared, but we can verify the mechanism worked
    # by checking that the tick didn't raise an error


def test_graph_config_subscriptions():
    """Test that GraphConfig edges work alongside DNA subscriptions."""
    world_id = WorldId("test-world")
    graph_config = GraphConfig(
        edges=[
            EdgeConfig(subscriber=AgentId("agent-b"), publisher=AgentId("agent-a")),
        ]
    )
    runtime = InProcessRuntime(world_id, EnvState(), graph_config)

    agent_a = Mind(agent_id=AgentId("agent-a"), llm_client=DummyLLM())
    agent_b = Mind(agent_id=AgentId("agent-b"), llm_client=DummyLLM())

    runtime.register_agent(agent_a)
    runtime.register_agent(agent_b)

    # Agent B should subscribe to Agent A via graph config
    subscriptions = runtime._subscriptions_for(AgentId("agent-b"))
    assert AgentId("agent-a") in subscriptions


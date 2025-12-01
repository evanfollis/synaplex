# tests/test_invariants_loop_modes.py

from synaplex.core.ids import WorldId, AgentId
from synaplex.core.runtime_inprocess import InProcessRuntime
from synaplex.core.env_state import EnvState
from synaplex.cognition.llm_client import LLMClient
from synaplex.cognition.mind import Mind


class DummyLLM(LLMClient):
    def complete(self, prompt: str, **kwargs):
        return type("Resp", (), {"text": "dummy-output", "raw": {"prompt": prompt}})()


def test_runtime_can_run_single_tick_with_mind():
    """
    Test that runtime can run a single tick with a Mind.
    
    Every Mind always runs the full cognitive loop:
    Perception → Reasoning → Internal Update
    """
    world_id = WorldId("test-world")
    runtime = InProcessRuntime(world_id, EnvState())

    mind = Mind(agent_id=AgentId("agent-1"), llm_client=DummyLLM())
    runtime.register_agent(mind)

    runtime.tick(0)  # should not raise
    
    # Verify that the Mind has a manifold (architectural invariant)
    assert mind._store.load_latest(AgentId("agent-1")) is not None

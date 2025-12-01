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
    world_id = WorldId("test-world")
    runtime = InProcessRuntime(world_id, EnvState())

    mind = Mind(agent_id=AgentId("agent-1"), llm_client=DummyLLM(), enable_persistent_worldview=False)
    runtime.register_agent(mind)

    runtime.tick(0)  # should not raise

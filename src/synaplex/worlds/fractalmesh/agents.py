# synaplex/worlds/fractalmesh/agents.py

from synaplex.core.ids import AgentId
from synaplex.cognition.llm_client import LLMClient
from synaplex.cognition.mind import Mind


def make_default_mind(agent_id: str, model: str = "gpt-4.1") -> Mind:
    """
    Convenience factory for a default manifold-enabled mind in this world.
    """
    llm = LLMClient(model=model)
    return Mind(agent_id=AgentId(agent_id), llm_client=llm)

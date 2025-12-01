# synaplex/worlds/fractalmesh/agents.py

from typing import Optional

from synaplex.core.ids import AgentId
from synaplex.cognition.openai_client import OpenAILLMClient
from synaplex.cognition.mind import Mind


def make_default_mind(agent_id: str, model: Optional[str] = None) -> Mind:
    """
    Convenience factory for a default manifold-enabled mind in this world.
    
    Uses OpenAILLMClient for real LLM integration.
    Model defaults to OPENAI_LLM_MODEL from .env file if not specified.
    """
    llm = OpenAILLMClient(model=model)  # model=None will use env var
    return Mind(agent_id=AgentId(agent_id), llm_client=llm)

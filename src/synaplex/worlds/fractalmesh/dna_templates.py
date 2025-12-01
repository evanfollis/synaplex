# synaplex/worlds/fractalmesh/dna_templates.py

from synaplex.core.dna import DNA
from synaplex.core.ids import AgentId


def make_macro_agent(agent_id: str) -> DNA:
    return DNA(
        agent_id=AgentId(agent_id),
        role="macro_agent",
        subscriptions=[],
        tools=["macro-data-api"],
        behavior_params={"curiosity": 0.7},
        tags=["macro"],
    )

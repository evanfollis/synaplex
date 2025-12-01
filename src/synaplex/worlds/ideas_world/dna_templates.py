# synaplex/worlds/ideas_world/dna_templates.py

from synaplex.core.dna import DNA
from synaplex.core.ids import AgentId


def make_archivist_agent(agent_id: str = "archivist") -> DNA:
    """
    Archivist agent: Reads markdown idea files and converts them to Experiences.
    
    Subscribes to: none (reads from external markdown files)
    Role: Extract and structure idea atoms from markdown
    """
    return DNA(
        agent_id=AgentId(agent_id),
        role="archivist",
        subscriptions=[],
        tools=[],
        behavior_params={"attention_span": 0.8},
        tags=["ideas", "extraction"],
    )


def make_architect_agent(agent_id: str = "architect") -> DNA:
    """
    Architect agent: Maintains a manifold about the shape of the idea space.
    
    Subscribes to: archivist (receives idea signals)
    Role: Build and maintain conceptual map of ideas, clusters, gaps
    """
    return DNA(
        agent_id=AgentId(agent_id),
        role="architect",
        subscriptions=[AgentId("archivist")],
        tools=[],
        behavior_params={"synthesis_tendency": 0.9},
        tags=["ideas", "synthesis", "structure"],
    )


def make_critic_agent(agent_id: str = "critic") -> DNA:
    """
    Critic agent: Hunts for tensions, duplicates, and low-value ideas.
    
    Subscribes to: archivist (receives idea signals)
    Role: Identify contradictions, redundancies, blind spots
    """
    return DNA(
        agent_id=AgentId(agent_id),
        role="critic",
        subscriptions=[AgentId("archivist")],
        tools=[],
        behavior_params={"skepticism": 0.8, "pattern_detection": 0.9},
        tags=["ideas", "critique", "tensions"],
    )


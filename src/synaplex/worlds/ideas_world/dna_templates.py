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


def make_synaplex_agent(agent_id: str = "synaplex") -> DNA:
    """
    Synaplex agent: Represents the Synaplex idea/concept itself.
    
    Subscribes to: archivist (receives Synaplex idea), all topic agents
    Role: Deep understanding of Synaplex as both a system and an idea
    """
    return DNA(
        agent_id=AgentId(agent_id),
        role="synaplex_idea",
        subscriptions=[
            AgentId("archivist"),
            AgentId("llms"),
            AgentId("world_models"),
            AgentId("agentic_systems"),
            AgentId("cognitive_architectures"),
            AgentId("manifolds"),
            AgentId("message_graphs"),
            AgentId("nature_nurture"),
        ],
        tools=[],
        behavior_params={"synthesis_tendency": 0.95, "depth": 0.9},
        tags=["synaplex", "architecture", "meta"],
    )


def make_llms_agent(agent_id: str = "llms") -> DNA:
    """
    LLMs topic agent: Domain expert on Large Language Models.
    
    Subscribes to: archivist (receives all ideas)
    Role: Expertise in LLMs, transformers, prompting, fine-tuning
    """
    return DNA(
        agent_id=AgentId(agent_id),
        role="llms_expert",
        subscriptions=[AgentId("archivist")],
        tools=[],
        behavior_params={"expertise": 0.9, "breadth": 0.7},
        tags=["llms", "transformers", "nlp", "foundation-models"],
    )


def make_world_models_agent(agent_id: str = "world_models") -> DNA:
    """
    World Models topic agent: Domain expert on foundational world models.
    
    Subscribes to: archivist (receives all ideas)
    Role: Expertise in world models, simulation, prediction, model-based RL
    """
    return DNA(
        agent_id=AgentId(agent_id),
        role="world_models_expert",
        subscriptions=[AgentId("archivist")],
        tools=[],
        behavior_params={"expertise": 0.9, "breadth": 0.7},
        tags=["world-models", "simulation", "prediction", "rl"],
    )


def make_agentic_systems_agent(agent_id: str = "agentic_systems") -> DNA:
    """
    Agentic Systems topic agent: Domain expert on multi-agent systems.
    
    Subscribes to: archivist (receives all ideas)
    Role: Expertise in multi-agent systems, coordination, communication
    """
    return DNA(
        agent_id=AgentId(agent_id),
        role="agentic_systems_expert",
        subscriptions=[AgentId("archivist")],
        tools=[],
        behavior_params={"expertise": 0.9, "breadth": 0.7},
        tags=["multi-agent", "coordination", "communication", "agent-frameworks"],
    )


def make_cognitive_architectures_agent(agent_id: str = "cognitive_architectures") -> DNA:
    """
    Cognitive Architectures topic agent: Domain expert on cognitive architectures.
    
    Subscribes to: archivist (receives all ideas)
    Role: Expertise in cognitive architectures, reasoning systems, knowledge representation
    """
    return DNA(
        agent_id=AgentId(agent_id),
        role="cognitive_architectures_expert",
        subscriptions=[AgentId("archivist")],
        tools=[],
        behavior_params={"expertise": 0.9, "breadth": 0.7},
        tags=["cognitive-architectures", "reasoning", "knowledge-representation"],
    )


def make_manifolds_agent(agent_id: str = "manifolds") -> DNA:
    """
    Manifolds topic agent: Domain expert on internal representations.
    
    Subscribes to: archivist (receives all ideas)
    Role: Expertise in manifolds, internal representations, worldview evolution
    """
    return DNA(
        agent_id=AgentId(agent_id),
        role="manifolds_expert",
        subscriptions=[AgentId("archivist")],
        tools=[],
        behavior_params={"expertise": 0.9, "breadth": 0.7},
        tags=["manifolds", "internal-representations", "worldviews", "embeddings"],
    )


def make_message_graphs_agent(agent_id: str = "message_graphs") -> DNA:
    """
    Message Graphs topic agent: Domain expert on message-passing graphs.
    
    Subscribes to: archivist (receives all ideas)
    Role: Expertise in graph structures, message passing, distributed systems
    """
    return DNA(
        agent_id=AgentId(agent_id),
        role="message_graphs_expert",
        subscriptions=[AgentId("archivist")],
        tools=[],
        behavior_params={"expertise": 0.9, "breadth": 0.7},
        tags=["graphs", "message-passing", "distributed-systems", "topology"],
    )


def make_nature_nurture_agent(agent_id: str = "nature_nurture") -> DNA:
    """
    Nature vs Nurture topic agent: Domain expert on nature/nurture distinction in AI.
    
    Subscribes to: archivist (receives all ideas)
    Role: Expertise in structural constraints vs learned behavior, nature/nurture distinction
    """
    return DNA(
        agent_id=AgentId(agent_id),
        role="nature_nurture_expert",
        subscriptions=[AgentId("archivist")],
        tools=[],
        behavior_params={"expertise": 0.9, "breadth": 0.7},
        tags=["nature-nurture", "structure", "learning", "constraints"],
    )


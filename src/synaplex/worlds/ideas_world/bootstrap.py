# synaplex/worlds/ideas_world/bootstrap.py

from pathlib import Path

from synaplex.core.ids import WorldId, AgentId
from synaplex.core.runtime_inprocess import InProcessRuntime, GraphConfig, EdgeConfig
from synaplex.core.env_state import EnvState

from .dna_templates import (
    make_archivist_agent,
    make_architect_agent,
    make_critic_agent,
    make_synaplex_agent,
    make_llms_agent,
    make_world_models_agent,
    make_agentic_systems_agent,
    make_cognitive_architectures_agent,
    make_manifolds_agent,
    make_message_graphs_agent,
    make_nature_nurture_agent,
)
from .agents import (
    make_archivist_mind,
    make_architect_mind,
    make_critic_mind,
    make_synaplex_mind,
    make_llms_mind,
    make_world_models_mind,
    make_agentic_systems_mind,
    make_cognitive_architectures_mind,
    make_manifolds_mind,
    make_message_graphs_mind,
    make_nature_nurture_mind,
)
from .lenses import (
    IdeasArchitectLens,
    IdeasCriticLens,
    SynaplexLens,
    LLMsLens,
    WorldModelsLens,
    AgenticSystemsLens,
    CognitiveArchitecturesLens,
    ManifoldsLens,
    MessageGraphsLens,
    NatureNurtureLens,
)


def bootstrap_ideas_world(
    ideas_dir: str | Path = "docs/ideas",
    manifold_store_root: str = "manifolds/ideas_world",
    world_id: str = "ideas-world",
) -> InProcessRuntime:
    """
    Bootstrap the Ideas World with multiple agents for idea exploration.
    
    Agents:
    - archivist: Reads markdown idea files and emits idea signals
    - architect: Maintains manifold about idea space structure
    - critic: Hunts for tensions, duplicates, and low-value ideas
    - synaplex: Represents the Synaplex idea/concept itself
    - llms: Domain expert on Large Language Models
    - world_models: Domain expert on foundational world models
    - agentic_systems: Domain expert on multi-agent systems
    - cognitive_architectures: Domain expert on cognitive architectures
    - manifolds: Domain expert on internal representations
    - message_graphs: Domain expert on message-passing graphs
    - nature_nurture: Domain expert on nature/nurture distinction in AI
    
    Graph Topology:
    - All topic agents and synaplex agent subscribe to archivist
    - Synaplex agent subscribes to all topic agents for cross-domain understanding
    - Architect and critic subscribe to synaplex agent to reason about it
    
    Args:
        ideas_dir: Directory containing markdown idea files
        manifold_store_root: Root directory for persistent manifolds
        world_id: World identifier
    
    Returns:
        Configured runtime ready to process ideas and reason about Synaplex
    """
    world_id_obj = WorldId(world_id)
    env_state = EnvState()
    
    # Build graph config with all subscriptions
    # Topic agents subscribe to archivist
    # Synaplex agent subscribes to archivist and all topic agents
    # Architect and critic also subscribe to synaplex agent to reason about it
    graph_config = GraphConfig(
        edges=[
            # Original edges
            EdgeConfig(subscriber=AgentId("architect"), publisher=AgentId("archivist")),
            EdgeConfig(subscriber=AgentId("critic"), publisher=AgentId("archivist")),
            # Topic agents subscribe to archivist
            EdgeConfig(subscriber=AgentId("llms"), publisher=AgentId("archivist")),
            EdgeConfig(subscriber=AgentId("world_models"), publisher=AgentId("archivist")),
            EdgeConfig(subscriber=AgentId("agentic_systems"), publisher=AgentId("archivist")),
            EdgeConfig(subscriber=AgentId("cognitive_architectures"), publisher=AgentId("archivist")),
            EdgeConfig(subscriber=AgentId("manifolds"), publisher=AgentId("archivist")),
            EdgeConfig(subscriber=AgentId("message_graphs"), publisher=AgentId("archivist")),
            EdgeConfig(subscriber=AgentId("nature_nurture"), publisher=AgentId("archivist")),
            # Synaplex agent subscribes to archivist and all topic agents
            EdgeConfig(subscriber=AgentId("synaplex"), publisher=AgentId("archivist")),
            EdgeConfig(subscriber=AgentId("synaplex"), publisher=AgentId("llms")),
            EdgeConfig(subscriber=AgentId("synaplex"), publisher=AgentId("world_models")),
            EdgeConfig(subscriber=AgentId("synaplex"), publisher=AgentId("agentic_systems")),
            EdgeConfig(subscriber=AgentId("synaplex"), publisher=AgentId("cognitive_architectures")),
            EdgeConfig(subscriber=AgentId("synaplex"), publisher=AgentId("manifolds")),
            EdgeConfig(subscriber=AgentId("synaplex"), publisher=AgentId("message_graphs")),
            EdgeConfig(subscriber=AgentId("synaplex"), publisher=AgentId("nature_nurture")),
            # Architect and critic subscribe to synaplex agent
            EdgeConfig(subscriber=AgentId("architect"), publisher=AgentId("synaplex")),
            EdgeConfig(subscriber=AgentId("critic"), publisher=AgentId("synaplex")),
        ]
    )
    
    runtime = InProcessRuntime(
        world_id=world_id_obj,
        env_state=env_state,
        graph_config=graph_config,
    )
    
    # Create DNA templates
    archivist_dna = make_archivist_agent()
    architect_dna = make_architect_agent()
    critic_dna = make_critic_agent()
    synaplex_dna = make_synaplex_agent()
    llms_dna = make_llms_agent()
    world_models_dna = make_world_models_agent()
    agentic_systems_dna = make_agentic_systems_agent()
    cognitive_architectures_dna = make_cognitive_architectures_agent()
    manifolds_dna = make_manifolds_agent()
    message_graphs_dna = make_message_graphs_agent()
    nature_nurture_dna = make_nature_nurture_agent()
    
    # Create lenses
    architect_lens = IdeasArchitectLens(name="architect_lens")
    critic_lens = IdeasCriticLens(name="critic_lens")
    synaplex_lens = SynaplexLens(name="synaplex_lens")
    llms_lens = LLMsLens()
    world_models_lens = WorldModelsLens()
    agentic_systems_lens = AgenticSystemsLens()
    cognitive_architectures_lens = CognitiveArchitecturesLens()
    manifolds_lens = ManifoldsLens()
    message_graphs_lens = MessageGraphsLens()
    nature_nurture_lens = NatureNurtureLens()
    
    # Create and register agents
    archivist = make_archivist_mind(
        agent_id=archivist_dna.agent_id.value,
        ideas_dir=ideas_dir,
    )
    
    architect = make_architect_mind(
        agent_id=architect_dna.agent_id.value,
        store_root=manifold_store_root,
    )
    
    critic = make_critic_mind(
        agent_id=critic_dna.agent_id.value,
        store_root=manifold_store_root,
    )
    
    synaplex = make_synaplex_mind(
        agent_id=synaplex_dna.agent_id.value,
        store_root=manifold_store_root,
    )
    
    llms = make_llms_mind(
        agent_id=llms_dna.agent_id.value,
        store_root=manifold_store_root,
    )
    
    world_models = make_world_models_mind(
        agent_id=world_models_dna.agent_id.value,
        store_root=manifold_store_root,
    )
    
    agentic_systems = make_agentic_systems_mind(
        agent_id=agentic_systems_dna.agent_id.value,
        store_root=manifold_store_root,
    )
    
    cognitive_architectures = make_cognitive_architectures_mind(
        agent_id=cognitive_architectures_dna.agent_id.value,
        store_root=manifold_store_root,
    )
    
    manifolds = make_manifolds_mind(
        agent_id=manifolds_dna.agent_id.value,
        store_root=manifold_store_root,
    )
    
    message_graphs = make_message_graphs_mind(
        agent_id=message_graphs_dna.agent_id.value,
        store_root=manifold_store_root,
    )
    
    nature_nurture = make_nature_nurture_mind(
        agent_id=nature_nurture_dna.agent_id.value,
        store_root=manifold_store_root,
    )
    
    # Register with DNA and lenses
    runtime.register_agent(archivist, dna=archivist_dna)
    runtime.register_agent(architect, dna=architect_dna, lens=architect_lens)
    runtime.register_agent(critic, dna=critic_dna, lens=critic_lens)
    runtime.register_agent(synaplex, dna=synaplex_dna, lens=synaplex_lens)
    runtime.register_agent(llms, dna=llms_dna, lens=llms_lens)
    runtime.register_agent(world_models, dna=world_models_dna, lens=world_models_lens)
    runtime.register_agent(agentic_systems, dna=agentic_systems_dna, lens=agentic_systems_lens)
    runtime.register_agent(cognitive_architectures, dna=cognitive_architectures_dna, lens=cognitive_architectures_lens)
    runtime.register_agent(manifolds, dna=manifolds_dna, lens=manifolds_lens)
    runtime.register_agent(message_graphs, dna=message_graphs_dna, lens=message_graphs_lens)
    runtime.register_agent(nature_nurture, dna=nature_nurture_dna, lens=nature_nurture_lens)
    
    return runtime


# synaplex/worlds/ideas_world/bootstrap.py

from pathlib import Path

from synaplex.core.ids import WorldId, AgentId
from synaplex.core.runtime_inprocess import InProcessRuntime, GraphConfig, EdgeConfig
from synaplex.core.env_state import EnvState

from .dna_templates import make_archivist_agent, make_architect_agent, make_critic_agent
from .agents import make_archivist_mind, make_architect_mind, make_critic_mind
from .lenses import IdeasArchitectLens, IdeasCriticLens


def bootstrap_ideas_world(
    ideas_dir: str | Path = "docs/ideas",
    manifold_store_root: str = "manifolds/ideas_world",
    world_id: str = "ideas-world",
) -> InProcessRuntime:
    """
    Bootstrap the Ideas World with archivist, architect, and critic agents.
    
    Args:
        ideas_dir: Directory containing markdown idea files
        manifold_store_root: Root directory for persistent manifolds
        world_id: World identifier
    
    Returns:
        Configured runtime ready to process ideas
    """
    world_id_obj = WorldId(world_id)
    env_state = EnvState()
    
    # Build graph config
    graph_config = GraphConfig(
        edges=[
            EdgeConfig(subscriber=AgentId("architect"), publisher=AgentId("archivist")),
            EdgeConfig(subscriber=AgentId("critic"), publisher=AgentId("archivist")),
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
    
    # Create lenses
    architect_lens = IdeasArchitectLens(name="architect_lens")
    critic_lens = IdeasCriticLens(name="critic_lens")
    
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
    
    # Register with DNA and lenses
    runtime.register_agent(archivist, dna=archivist_dna)
    runtime.register_agent(architect, dna=architect_dna, lens=architect_lens)
    runtime.register_agent(critic, dna=critic_dna, lens=critic_lens)
    
    return runtime


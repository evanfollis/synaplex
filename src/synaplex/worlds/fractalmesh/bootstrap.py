# synaplex/worlds/fractalmesh/bootstrap.py

from synaplex.core.ids import WorldId
from synaplex.core.runtime_inprocess import InProcessRuntime, GraphConfig
from synaplex.core.env_state import EnvState
from .config import FractalMeshConfig
from .dna_templates import make_macro_agent
from .agents import make_default_mind


def bootstrap_fractalmesh_world() -> InProcessRuntime:
    """
    Skeleton bootstrap that creates an empty world with a single agent.
    """
    world_id = WorldId("fractalmesh-world")
    env_state = EnvState()
    graph_config = GraphConfig()

    runtime = InProcessRuntime(world_id=world_id, env_state=env_state, graph_config=graph_config)

    # Example: register one mind
    macro_dna = make_macro_agent("macro-1")
    mind = make_default_mind(macro_dna.agent_id.value)
    runtime.register_agent(mind)

    return runtime

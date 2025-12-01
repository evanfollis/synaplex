# synaplex/worlds/fractalmesh/bootstrap.py

from synaplex.core.ids import WorldId
from synaplex.core.runtime_inprocess import InProcessRuntime, GraphConfig
from synaplex.core.env_state import EnvState
from synaplex.core.lenses import Lens
from .config import FractalMeshConfig
from .dna_templates import make_macro_agent
from .agents import make_default_mind


def bootstrap_fractalmesh_world() -> InProcessRuntime:
    """
    Bootstrap a FractalMesh world with agents, DNA, and lenses.

    This demonstrates the proper setup for message routing:
    - Agents registered with DNA (defines subscriptions)
    - Agents registered with Lenses (defines perception)
    - Graph config for additional edges
    """
    world_id = WorldId("fractalmesh-world")
    env_state = EnvState()
    graph_config = GraphConfig()

    runtime = InProcessRuntime(world_id=world_id, env_state=env_state, graph_config=graph_config)

    # Example: register one mind with DNA and default lens
    macro_dna = make_macro_agent("macro-1")
    mind = make_default_mind(macro_dna.agent_id.value)
    
    # Register with DNA (defines subscriptions) and default lens
    default_lens = Lens(name="default")
    runtime.register_agent(mind, dna=macro_dna, lens=default_lens)

    return runtime

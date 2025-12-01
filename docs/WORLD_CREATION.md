# Creating a New World in Synaplex

This tutorial walks you through creating a new world (domain-specific configuration) in Synaplex.

## What is a World?

A **world** is a domain-specific configuration of the Synaplex architecture. It defines:
- Agent roles and DNA templates
- Lenses for perception
- Tools available to agents
- Graph topology (who subscribes to whom)
- World-specific data and state

## World Structure

A world typically has this structure:

```
synaplex/worlds/my_world/
├── __init__.py
├── config.py          # World configuration
├── dna_templates.py   # DNA templates for agent roles
├── lenses.py          # Domain-specific lenses
├── agents.py          # World-specific agent implementations
├── tools.py           # World-specific tools
└── bootstrap.py       # Entry point to create the world
```

## Step 1: Create World Directory

```bash
mkdir -p src/synaplex/worlds/my_world
cd src/synaplex/worlds/my_world
```

## Step 2: Create DNA Templates

Define the structural blueprints for your agents:

```python
# dna_templates.py
from synaplex.core.dna import DNA
from synaplex.core.ids import AgentId

def make_researcher_agent(agent_id: str = "researcher") -> DNA:
    """Create DNA for a researcher agent."""
    return DNA(
        agent_id=AgentId(agent_id),
        role="researcher",
        subscriptions=[],  # Who this agent subscribes to
        tools=["search", "analyze"],  # Tools available to this agent
        behavior_params={
            "curiosity": 0.8,
            "patience": 0.6,
        },
        tags=["research", "analysis"],
    )

def make_data_source_agent(agent_id: str = "data-source") -> DNA:
    """Create DNA for a data source agent."""
    return DNA(
        agent_id=AgentId(agent_id),
        role="data_source",
        subscriptions=[],
        tools=[],
        behavior_params={},
        tags=["data"],
    )
```

## Step 3: Create Lenses

Define how agents perceive the world:

```python
# lenses.py
from synaplex.core.lenses import Lens
from typing import Any, Dict

class ResearcherLens(Lens):
    """Lens for researcher agents - filters for research-relevant signals."""
    
    def should_attend(self, signal_payload: Dict[str, Any]) -> bool:
        """Only attend to research-related signals."""
        signal_type = signal_payload.get("type", "")
        return signal_type in ["research", "data", "finding"]
    
    def transform_projection(self, raw_projection: Dict[str, Any]) -> Dict[str, Any]:
        """Transform projection to research-focused view."""
        # Extract research-relevant fields
        return {
            "data": raw_projection.get("data", {}),
            "metadata": raw_projection.get("metadata", {}),
        }
```

## Step 4: Create Tools (Optional)

Define tools that agents can use:

```python
# tools.py
from synaplex.cognition.tools import ToolRegistry, FunctionTool

def create_world_tool_registry() -> ToolRegistry:
    """Create tool registry for this world."""
    registry = ToolRegistry()
    
    def search_tool(query: str) -> Dict[str, Any]:
        """Search for information."""
        # Your search implementation
        return {"results": [], "query": query}
    
    def analyze_tool(data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data."""
        # Your analysis implementation
        return {"analysis": "placeholder"}
    
    registry.register_function(
        name="search",
        description="Search for information in the knowledge base",
        func=search_tool,
    )
    
    registry.register_function(
        name="analyze",
        description="Analyze structured data",
        func=analyze_tool,
    )
    
    return registry
```

## Step 5: Create Agent Implementations

Create world-specific agent classes (optional - can use base `Mind`):

```python
# agents.py
from synaplex.core.ids import AgentId
from synaplex.cognition.mind import Mind
from synaplex.cognition.openai_client import OpenAILLMClient
from synaplex.core.world_modes import WorldMode

def make_researcher_mind(
    agent_id: str,
    tool_registry=None,
    **kwargs
) -> Mind:
    """Create a researcher mind."""
    llm = OpenAILLMClient()
    
    return Mind(
        agent_id=AgentId(agent_id),
        llm_client=llm,
        tool_registry=tool_registry,
        world_mode=WorldMode.MANIFOLD,  # Full cognitive loop
        **kwargs
    )
```

## Step 6: Create Bootstrap Function

Create the entry point that sets up your world:

```python
# bootstrap.py
from synaplex.core.ids import WorldId
from synaplex.core.runtime_inprocess import InProcessRuntime, GraphConfig, EdgeConfig
from synaplex.core.env_state import EnvState
from synaplex.core.lenses import Lens

from .dna_templates import make_researcher_agent, make_data_source_agent
from .agents import make_researcher_mind
from .tools import create_world_tool_registry
from .lenses import ResearcherLens

def bootstrap_my_world(
    world_id: str = "my-world",
    **kwargs
) -> InProcessRuntime:
    """
    Bootstrap the world with agents, DNA, and lenses.
    
    Returns:
        Configured runtime ready to run
    """
    # Create runtime
    world_id_obj = WorldId(world_id)
    env_state = EnvState()
    
    # Define graph topology
    graph_config = GraphConfig(
        edges=[
            # Researcher subscribes to data source
            EdgeConfig(
                subscriber=AgentId("researcher"),
                publisher=AgentId("data-source")
            ),
        ]
    )
    
    runtime = InProcessRuntime(
        world_id=world_id_obj,
        env_state=env_state,
        graph_config=graph_config,
    )
    
    # Create tool registry
    tool_registry = create_world_tool_registry()
    
    # Create DNA templates
    researcher_dna = make_researcher_agent()
    data_source_dna = make_data_source_agent()
    
    # Create agents
    researcher = make_researcher_mind(
        agent_id=researcher_dna.agent_id.value,
        tool_registry=tool_registry,
    )
    
    # Create lenses
    researcher_lens = ResearcherLens(name="researcher_lens")
    default_lens = Lens(name="default")
    
    # Register agents
    runtime.register_agent(researcher, dna=researcher_dna, lens=researcher_lens)
    # Register data source if you have one
    # runtime.register_agent(data_source, dna=data_source_dna, lens=default_lens)
    
    return runtime
```

## Step 7: Use Your World

```python
from synaplex.worlds.my_world.bootstrap import bootstrap_my_world

# Create the world
runtime = bootstrap_my_world()

# Run some ticks
for tick in range(10):
    runtime.tick(tick)
    print(f"Tick {tick} complete")
```

## Best Practices

### 1. Keep Worlds Focused

Each world should represent a specific domain or research question. Don't try to make one world do everything.

### 2. Use DNA for Structure

Put structural information (subscriptions, tools, behavior params) in DNA, not in agent code.

### 3. Leverage Lenses

Use lenses to implement receiver-owned semantics - each agent interprets the world through its own lens.

### 4. Respect Invariants

- Never leak manifold content outside the Mind
- Keep core independent (no LLM/manifold dependencies)
- Don't import meta into worlds
- Maintain nature/nurture separation

### 5. Test Your World

Create tests for your world:

```python
# tests/test_my_world.py
def test_world_bootstrap():
    runtime = bootstrap_my_world()
    assert len(runtime.get_agents()) > 0

def test_world_tick():
    runtime = bootstrap_my_world()
    runtime.tick(0)
    # Verify expected behavior
```

## Example: Ideas World

See `src/synaplex/worlds/ideas_world/` for a complete example of a world implementation.

## Next Steps

- Read `docs/ARCHITECTURE.md` for architectural details
- Check `docs/DESIGN_NOTES.md` for design philosophy
- Explore existing worlds for patterns
- Create tests for your world


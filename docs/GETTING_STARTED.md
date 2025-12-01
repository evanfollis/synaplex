# Getting Started with Synaplex

This guide will help you get started with Synaplex, a research platform for studying distributed AI minds with persistent internal worldviews.

## Installation

### Prerequisites

- Python 3.10 or higher
- pip or poetry for package management

### Install Synaplex

```bash
# Clone the repository
git clone <repository-url>
cd synaplex

# Install with pip
pip install -e .

# Or with poetry
poetry install
```

### Environment Setup

If you plan to use OpenAI LLM clients, create a `.env` file:

```bash
OPENAI_API_KEY=your_api_key_here
OPENAI_LLM_MODEL=gpt-4  # Optional, defaults to gpt-4
```

## Core Concepts

Before diving in, understand these key concepts:

1. **Minds**: Agents with internal worldviews (manifolds) that evolve over time
2. **Nature vs Nurture**: 
   - **Nature**: Structural constraints (DNA, lenses, graph topology)
   - **Nurture**: Internal worldview (manifold) that evolves
3. **Unified Loop**: Perception → Reasoning → Internal Update
4. **World Modes**: 
   - `GRAPH_ONLY`: Deterministic, no LLM
   - `REASONING_ONLY`: LLM reasoning, no persistent worldview
   - `MANIFOLD`: Full loop with persistent worldview

## Quick Start Example

Here's a minimal example to get you started:

```python
from synaplex.core.ids import AgentId, WorldId
from synaplex.core.runtime_inprocess import InProcessRuntime, GraphConfig
from synaplex.core.env_state import EnvState
from synaplex.core.dna import DNA
from synaplex.core.lenses import Lens
from synaplex.cognition.openai_client import OpenAILLMClient
from synaplex.cognition.mind import Mind

# Create a world
world_id = WorldId("my-world")
env_state = EnvState()
runtime = InProcessRuntime(world_id=world_id, env_state=env_state)

# Create an agent with DNA
agent_id = AgentId("agent-1")
dna = DNA(
    agent_id=agent_id,
    role="researcher",
    subscriptions=[],  # No subscriptions yet
    tools=[],  # No tools yet
)

# Create a mind
llm_client = OpenAILLMClient()
mind = Mind(
    agent_id=agent_id,
    llm_client=llm_client,
    world_mode=WorldMode.MANIFOLD,  # Full cognitive loop
)

# Register agent with runtime
lens = Lens(name="default")
runtime.register_agent(mind, dna=dna, lens=lens)

# Run a few ticks
for tick in range(3):
    runtime.tick(tick)
    print(f"Tick {tick} complete")
```

## Running Examples

The repository includes example scripts:

```bash
# Multi-agent interaction example
python examples/multi_agent_example.py

# OpenAI usage example
python examples/openai_usage.py
```

## Next Steps

1. **Read the Architecture**: See `docs/ARCHITECTURE.md` for detailed specifications
2. **Understand Design Philosophy**: See `docs/DESIGN_NOTES.md` for the "why"
3. **Create Your First World**: See `docs/WORLD_CREATION.md` for a tutorial
4. **Explore Examples**: Check out `examples/` directory

## Common Patterns

### Creating Agents with Subscriptions

```python
# Agent B subscribes to Agent A
dna_a = DNA(agent_id=AgentId("agent-a"), role="publisher")
dna_b = DNA(
    agent_id=AgentId("agent-b"),
    role="subscriber",
    subscriptions=[AgentId("agent-a")],  # B subscribes to A
)
```

### Using Manifold Persistence

```python
from synaplex.cognition.manifolds import FileManifoldStore

# Create file-based store
store = FileManifoldStore(root="manifolds/my_world")

# Use with Mind
mind = Mind(
    agent_id=agent_id,
    llm_client=llm_client,
    manifold_store=store,  # Persists across restarts
)
```

### Using Tools

```python
from synaplex.cognition.tools import ToolRegistry, FunctionTool

# Create tool registry
registry = ToolRegistry()

# Register a tool
def calculate_sum(a: float, b: float) -> float:
    return a + b

registry.register_function(
    name="calculate_sum",
    description="Adds two numbers together",
    func=calculate_sum,
)

# Pass to Mind
mind = Mind(
    agent_id=agent_id,
    llm_client=llm_client,
    tool_registry=registry,
)

# Tools are available if listed in DNA
dna = DNA(
    agent_id=agent_id,
    role="calculator",
    tools=["calculate_sum"],  # Tool names from registry
)
```

## Troubleshooting

### LLM Client Errors

If you see LLM-related errors:
- Check your API key is set in `.env`
- Verify the model name is correct
- Ensure you have API credits/quota

### Manifold Store Errors

If manifold persistence fails:
- Check file permissions on the store directory
- Ensure the directory exists or can be created
- Verify disk space is available

### Import Errors

If you see import errors:
- Ensure Synaplex is installed: `pip install -e .`
- Check Python version is 3.10+
- Verify all dependencies are installed

## Getting Help

- **Architecture Questions**: See `docs/ARCHITECTURE.md`
- **Design Questions**: See `docs/DESIGN_NOTES.md`
- **Implementation Details**: See implementation summaries in root directory
- **Examples**: Check `examples/` directory

## Further Reading

- `README.md`: High-level overview
- `docs/ARCHITECTURE.md`: Detailed architecture specification
- `docs/DESIGN_NOTES.md`: Design philosophy and rationale
- `docs/GLOSSARY.md`: Terminology reference


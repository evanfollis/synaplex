# Getting Started with Synaplex

This guide will help you get started with Synaplex, a research platform for **Material Cognition**.

Unlike standard agent frameworks, Synaplex does not treat agents as stateless workers. It treats them as **Geologies** (Minds) that accumulate **Sediment** (Substrate) over time.

## Installation

### Prerequisites

  - Python 3.10 or higher
  - pip or poetry

### Install Synaplex

```bash
# Clone the repository
git clone <repository-url>
cd synaplex

# Install (Editable mode recommended for research)
pip install -e .
```

### Environment Setup

Synaplex needs a backend for the "Biology" layer (the LLM). Create a `.env` file:

```bash
OPENAI_API_KEY=your_api_key_here
OPENAI_LLM_MODEL=gpt-4  # Recommended. Models with low context windows struggle with Frottage.
```

## Core Concepts (The Physics)

Before writing code, understand the material physics:

1.  **Minds are Soil (Substrate `S`)**:

      * Minds do not have "state variables." They have a **Substrate**—a dense, sedimentary text blob that accumulates over time.
      * *Invariant:* The Runtime never parses this blob. It is opaque.

2.  **Communication is Texture (`T`)**:

      * Agents do not send "messages." They project **Textures** (Frottage Dumps).
      * Receivers apply **Lenses** ($L$) to interpret these Textures via **Interference** ($\Phi$).

3.  **The Loop is Unified**:

      * **Interference** (Input) → **Reasoning** (Churn) → **Resurfacing** (Update).
      * Every Mind runs this full loop, every tick. There is no "fast path."

## Quick Start Example

Here is a minimal "Petri dish" setup:

```python
from synaplex.core.ids import AgentId, WorldId
from synaplex.core.runtime_inprocess import InProcessRuntime
from synaplex.core.env_state import EnvState
from synaplex.core.dna import DNA
from synaplex.core.lenses import Lens
from synaplex.cognition.openai_client import OpenAILLMClient
from synaplex.cognition.mind import Mind

# 1. Create the Physics (World & EnvState)
world_id = WorldId("genesis-1")
env_state = EnvState()  # Strictly physical facts (Time, IDs)
runtime = InProcessRuntime(world_id=world_id, env_state=env_state)

# 2. Define Nature (DNA)
# This agent is a "Researcher" with specific hard-coded tools/subs
agent_id = AgentId("agent-1")
dna = DNA(
    agent_id=agent_id,
    role="researcher",
    subscriptions=[],  # No lenses active yet
    tools=[],
)

# 3. Define Nurture (The Mind)
# This initializes an empty Substrate 'S'
llm_client = OpenAILLMClient()
mind = Mind(
    agent_id=agent_id,
    llm_client=llm_client,
)

# 4. Wire them together
# The Lens defines how the Runtime projects data into this Mind
default_lens = Lens(name="broad_spectrum")
runtime.register_agent(mind, dna=dna, lens=default_lens)

# 5. Run the Loop
for tick in range(3):
    print(f"--- Tick {tick} ---")
    # This triggers Interference -> Reasoning -> Resurfacing
    runtime.tick(tick)
```

## Running Examples

The repository includes example scripts that demonstrate specific physical properties:

```bash
# Demonstrates Texture Projection & Interference
python examples/texture_projection.py

# Demonstrates Substrate Viscosity (Resistance to change)
python examples/viscosity_test.py
```

## Common Patterns

### Wiring Lenses (Subscriptions)

Agents do not "subscribe" to topics; they point **Lenses** at other Agents.

```python
# Agent B points a Lens at Agent A
dna_a = DNA(agent_id=AgentId("agent-a"), role="projector")
dna_b = DNA(
    agent_id=AgentId("agent-b"),
    role="observer",
    subscriptions=[AgentId("agent-a")],  # B will perceive A's Texture
)
```

### Persisting the Sediment (Substrate Store)

If you don't persist the Substrate, the Mind gets a lobotomy on every restart.

```python
from synaplex.cognition.substrate import FileSubstrateStore

# Create a geological storage layer
store = FileSubstrateStore(root="sediment/my_world")

# Bind it to the Mind
mind = Mind(
    agent_id=agent_id,
    llm_client=llm_client,
    substrate_store=store,  # Loads previous 'S' on startup
)
```

### Using Tools (Impacts)

Tools in Synaplex are **Sources of Impact** ($P$). They return raw data that acts as a "meteor strike" on the Substrate. The Mind must then "churn" this impact into sediment.

```python
from synaplex.cognition.tools import ToolRegistry

# Register a physical tool
def get_temperature() -> str:
    return "22C"

registry = ToolRegistry()
registry.register_function(
    name="get_temperature",
    description="Returns current physical temp",
    func=get_temperature,
)

# The Mind uses the tool during Reasoning
mind = Mind(
    agent_id=agent_id,
    llm_client=llm_client,
    tool_registry=registry,
)
```

## Troubleshooting

### "The Agent is rambling / Hallucinating"

  * **Diagnosis:** This is a feature, not a bug. Synaplex relies on **Frottage** (high-entropy outputs).
  * **Fix:** If it is *too* incoherent, check if your **Lens** is too broad, or if the Agent's **Viscosity** ($K$) is too low (making it too impressionable).

### "Substrate Store Errors"

  * Ensure your `sediment/` directory is writable. The blobs are opaque text/binary files; do not manually edit them.

## Next Steps

1.  **Study the Physics**: Read `docs/GEOMETRIC_CONSTITUTION.md` to understand $S$, $T$, and $\Phi$.
2.  **Study the Wiring**: Read `docs/ARCHITECTURE.md` to understand how the graph works.
3.  **Build a World**: See `docs/WORLD_CREATION.md`.

## Terminology Check

  * **Substrate:** The Mind's memory. (Not "Manifold").
  * **Texture:** The Mind's output. (Not "Message").
  * **Resurfacing:** The Update step. (Not "Save").
  * **EnvState:** Physical facts. (Not "Shared Memory").
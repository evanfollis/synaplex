# Synaplex

> Synaplex is an architecture for AI systems made of many interacting minds. Each mind maintains its own internal sediment (a **Substrate**) while coordinating through a structured graph of **Textures**.

Synaplex has two inseparable faces:

  * A **Geometric Constitution** (`GEOMETRIC_CONSTITUTION.md`) that treats each mind’s internal state as a **Substrate** `S` with **Basins** `A`, **Viscosity** `K`, **Gradient** `τ`, and material operators like **Interference** `Φ`, **Impact** `P`, and **Resurfacing**.
  * An **Architecture** (`ARCHITECTURE.md`) that turns that physics into concrete loops, messages, runtimes, and modules.

This `README.md` is the **orientation layer**:

  * It gives you the **mental model** for Synaplex (Physics \> Geometry).
  * It explains how the **Substrate view** and the **implementation** fit together.
  * It shows you how the **repo is structured** so you can extend it without breaking the underlying ideas.

If you want formal detail, go to `GEOMETRIC_CONSTITUTION.md`.
If you want to know *what Synaplex is and how to use it*, start here.

-----

## Quick Start

Get up and running with Synaplex in just a few lines:

```python
from synaplex.quick_start import quick_start

# Create a runtime with one agent (Substrate initialized)
runtime = quick_start()

# Run a tick to see the cognitive loop in action
# (Interference -> Reasoning -> Resurfacing)
runtime.tick(0)
```

The `quick_start()` helper sets up:

  * A runtime with one agent.
  * A default **Lens** and **DNA**.
  * An in-memory **Substrate Store**.
  * A dummy LLM client.

**Requirements:**

  * Python 3.10+
  * `pip install -e .`

**Next Steps:**

  * See `examples/quick_start_example.py` for the basics.
  * See `examples/texture_projection.py` to see how Agents generate Frottage Dumps.
  * Read on for the full mental model.

-----

## 1\. What Synaplex Is For

Synaplex exists to be a **substrate for high-density cognition**, not just another "multi-agent framework."

Standard frameworks treat agents as **stateless processors** that exchange clean JSON.
Synaplex treats agents as **stateful geologies** that exchange messy **Textures**.

It is designed for systems where:

  * Each mind maintains a **Substrate** (`S`): A persistent, sedimentary accumulation of context, contradictions, and latent potential.
  * Internal structure evolves via **Resurfacing**: New thoughts are deposited as layers; old thoughts settle into **Basins** (`A`).
  * Minds interact via **Interference**: Communication is the projection of a high-entropy **Texture** (`T`), interpreted by a receiver's **Lens** (`L`).
  * You can run **Nature/Nurture experiments**:
      * Change the wiring/DNA (**Nature**).
      * Change the initial sediment and impact patterns (**Nurture**).

The core question:

> What happens when you give Minds a "messy" memory that accumulates like soil, rather than a "clean" memory that acts like a database?

-----

## 2\. Core Mental Model

At the highest level, Synaplex is:

> A **Landscape of Substrates** interacting via **Optical Interference**.

There are three major pieces:

### 1\. Minds (The Soil)

Each Mind has:

  * **Nature:** DNA, Lenses, Graph Edges, Deterministic `EnvState` (Physics).
  * **Nurture:** A private **Substrate** `S` with Basins `A`, Viscosity `K` (resistance to change), and Gradient `τ` (slope).
  * **Loop:** `Interference → Reasoning → Resurfacing`.

### 2\. Graph (The Light)

A message-passing environment that:

  * Routes **Signals** (cheap broadcasts).
  * Manages **Textures** (rich, noisy projections).
  * Calculates **Interference** (where Textures overlap Lenses).

### 3\. Constitution (The Law)

A conceptual layer (`GEOMETRIC_CONSTITUTION.md`) that says:

  * **$S$** = Substrate (sedimentary memory).
  * **$T$** = Texture (Frottage output).
  * **$\Phi$** = Interference (Receiver-owned meaning).
  * **$K$** = Viscosity (How hard is the mind to change?).

You do **not** need to be a geologist to use Synaplex, but the material metaphors are there to keep the architecture from drifting into "database thinking."

-----

## 3\. The Cognitive Loop

Every Mind runs the same loop:

> **Interference (Input) → Reasoning (Churn) → Resurfacing (Output)**

### 3.1 Interference (World → Mind)

The runtime builds a **Percept** by:

1.  Collecting **Textures** from neighbors.
2.  Overlaying the Mind's **Lenses**.
3.  **Amplifying** the resonance (where Lens matches Texture).
4.  **Preserving** the dissonance (the background noise remains visible).

*No LLM calls. No Substrate modification.*

### 3.2 Reasoning (Mind ↔ World)

The Mind calls an LLM using:

  * The Percept.
  * Its current **Substrate** `S`.
  * Its **Viscosity** `K` and **Basins** `A`.

Here it:

  * Churns the new input against old sediment.
  * Generates **Frottage Dumps** (new Textures) to project outward.
  * Decides whether to trigger **Impacts** (`P`) or **Holonomy** (`H`).

### 3.3 Resurfacing (Mind → Substrate)

Finally, the Mind updates itself:

  * Deposits new sediment (adding to `S`).
  * Adjusts **Viscosity** `K` (did we get surprised? Soften up. Were we right? Harden up).
  * Writes a new `SubstrateEnvelope`.

*This is the only write-path to the Mind's memory.*

-----

## 4\. Communication: Textures & Lenses

Minds never read each other's Substrates. They only see:

  * **Signals:** "I updated."
  * **Textures:** "Here is a messy description of my reality."
  * **EnvState:** "Here is the time and the stock price."

### 4.1 Textures (Frottage)

A Texture is a **Frottage Dump**.

  * **Rich:** It contains the "grain" of the thought, not just the summary.
  * **Noisy:** It includes contradictions and "maybe"s.
  * **Purpose:** To offer maximum surface area for other Minds to latch onto.

### 4.2 Lenses (Observation)

A Lens is a filter owned by the Receiver.

> "Mind B looks at Mind A's Texture through a 'Skeptic' Lens."

  * The Sender does not know how it is being looked at.
  * The Receiver creates the meaning via Interference.

-----

## 5\. Vocabulary Cheat Sheet

  * **Substrate (`S`):** The Mind's private, sedimentary memory.
  * **Texture (`T`):** The noisy, high-entropy output of a Mind.
  * **Frottage:** The act of generating a Texture from a Substrate.
  * **Interference (`Φ`):** The intersection of a Texture and a Lens.
  * **Viscosity (`K`):** The resistance of a Mind to new ideas.
  * **Basins (`A`):** Deep habits or stable concepts in the sediment.
  * **Gradient (`τ`):** The natural "downhill" direction of thought.

-----

## 6\. Invariants (Hard Rules)

1.  **Every Mind has a Substrate.**
2.  **Runtime never parses Substrates.** They are opaque blobs.
3.  **Resurfacing is the only write-path.**
4.  **Texture \> Summary.** Always project the mess.
5.  **Receiver-Owned Meaning.** Sender emits Texture; Receiver applies Lens.
6.  **EnvState is Physics.** No meanings, only facts.
7.  **No Self-Cleaning.** Projections must not strip away context.

-----

## 7\. Repo Layout

```text
.
├── README.md                 # You are here
├── GEOMETRIC_CONSTITUTION.md # The Law of Substrate (Physics)
├── ARCHITECTURE.md           # Implementation Constraints
├── synaplex/
│   ├── core/                 # Physics (Graph, Lenses, EnvState)
│   ├── cognition/            # Biology (Mind Loop, Substrate I/O, LLM)
│   ├── substrate_science/    # Geology (Offline Analysis of Substrates)
│   ├── meta/                 # Tectonics (Evolution & Experiments)
│   └── worlds/               # Domain Implementations
```

-----

## 8\. How to Work With Synaplex

### 8.1 Building a World

1.  Define **DNA** (Roles).
2.  Define **Lenses** (How they see).
3.  Define **Tools** (What they do).
4.  **Do not** try to define the "schema" of their thoughts. Let the Substrate evolve.

### 8.2 Running Experiments

  * Use `synaplex.meta` to evolve the graph.
  * Use `substrate_science` to measure **Viscosity** and **Diversity**.
  * **Never** let the agents know their metrics.

-----

## 9\. Status & Direction

Synaplex is a research platform for **Material Cognition**.
If you keep the physics (Substrate/Texture) intact, you can build systems where intelligence **emerges from the mud**, rather than being forced down a pipeline.
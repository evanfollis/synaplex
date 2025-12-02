# ✅ DESIGN_NOTES.md

**Intent, Philosophy, and Material Physics**

---

## 1. Why Synaplex Exists (The Material Turn)

Most "multi-agent" frameworks are built around **tasks**, **tools**, and **workflows**:
* LLMs are treated as **stateless processors**.
* "State" is a clean JSON cache or vector store.
* Messages are **information packets** (clean signals).
* The goal is **Efficiency**: Get the right answer as fast as possible.

Synaplex steps sideways from that. It is built around **Materiality**, **Sediment**, and **Resistance**:
* LLMs are treated as **Minds** with internal **Substrates** `S`.
* The **Substrate** is a first-class geological object:
    * It has **Basins** `A` (habits).
    * It has **Viscosity** `K` (resistance to change).
    * It has **Gradient** `τ` (slope).
    * It **accumulates** sediment over time; it is never reset.
* The goal is **Density**: Develop a rich, high-entropy worldview that can survive perturbation.

Synaplex is **not** an orchestration engine.
It is a petri dish for studying:
> A landscape of Minds with opaque Substrates `S` that are constantly churned by **Impacts** `P`, illuminated by **Interference** `Φ`, and scarred by **Holonomy** `H`.

---

## 2. The Central Question (Material Version)

Synaplex is a platform for investigating one big family of questions:

> How do Substrates `S` evolve when you embed Minds in a shared world,
> let them project messy **Textures** `T` at each other,
> observe via **Lenses** `L`,
> and occasionally scar the world via Holonomy `H`?

That decomposes into concrete questions:
* How does **Viscosity** `K` change learning? (Does a "hard" agent learn slower but more robustly than a "soft" agent?)
* How does **Interference** `Φ` work? (What happens when a "Skeptic" Lens looks at an "Optimist" Texture?)
* What happens when you force agents to communicate via **Frottage** (high-entropy dumps) rather than summaries?
* Can we measure "Intellectual Maturity" not by benchmarks, but by **Basin Saturation** $A_{sat}$ (depth of conviction) and **Dimensionality** $D$ (richness of context)?

Everything in `ARCHITECTURE.md` is there to make these "physics" experimentable.

---

## 3. Materiality as the Backbone

Synaplex has two explicit layers:

1.  **Geometric Constitution** (`GEOMETRIC_CONSTITUTION.md`)
    * Defines the **Physics**:
        * `S` (Substrate), `A` (Basins), `K` (Viscosity), `τ` (Gradient).
        * `P` (Impact), `T` (Texture), `Φ` (Interference).
        * `Ω` (Tectonics), `Ξ` (Erosion/Dissipation).
    * Defines **Ecological Metrics**:
        * `D` (Dimensionality), `R_div` (Refraction Diversity), `A_sat` (Basin Saturation).
    * **The Invariant:** You cannot smooth out the world. You cannot optimize away the noise.

2.  **Architecture** (`ARCHITECTURE.md`)
    * Maps the physics into code:
        * Minds and the Unified Loop.
        * Substrate Envelopes and Frottage.
        * Graph wiring and Lenses.

**Design Stance:**
If you add a feature, you must explain it in terms of **Substrate Physics**.
* *Bad:* "I added a caching layer for speed." (Drift).
* *Good:* "I added a Viscosity modifier that hardens the Substrate after repeated impacts." (Aligned).

---

## 4. One Cognitive Loop (No "Modes")

Synaplex enforces a **Single Cognitive Ontology**:

> **Interference (Input) → Reasoning (Churn) → Resurfacing (Update)**

1.  **Interference:** The Mind applies Lenses to incoming Textures. It highlights resonance but preserves background noise.
2.  **Reasoning:** The Mind churns the Percept against its Substrate `S`. It generates friction, heat, and new Textures.
3.  **Resurfacing:** The Mind deposits new sediment onto `S`, updates Viscosity `K`, and erodes/deepens Basins `A`.

**CRITICAL:**
* There are **NO** "Graph-Only" or "Reasoning-Only" modes in the Runtime.
* A Mind **always** has a Substrate.
* A Mind **always** runs the full loop.

**"What if I want to run a graph-only simulation?"**
* That is a **Meta-Level Ablation**.
* You build an experiment harness *around* Synaplex that mocks the agents or stubs the Reasoning step.
* You do **not** add a `mode="graph_only"` flag to the `Mind` class.
* *Why?* Because once you add "Fast Paths" to the architecture, developers will use them for optimization, and the emergent material physics will die.

---

## 5. Nature vs Nurture vs Physics

The architecture's split:

* **Nature (Hardware):**
    * Graph Topology (Who talks to whom).
    * DNA (Roles, Lenses, Tools).
    * EnvState (The physics of the world).
* **Nurture (Soil):**
    * Substrate `S`.
    * Basins `A`, Viscosity `K`, Gradient `τ`.

Why this split matters:
1.  **Same Hardware, Different Soil:** Clone an agent's DNA, but give them different starting Substrates. Watch them diverge.
2.  **Same Soil, Different Hardware:** Clone an agent's Substrate, but move them to a different spot in the graph. Watch how context changes the sediment.

---

## 6. Substrates: The Mind's Soil

One of Synaplex's sharpest constraints:

> The Substrate `S` is **for the Mind**, not for you.

Practically:
* The Substrate is **Opaque Sediment** (`SubstrateEnvelope`).
* It is written only during **Resurfacing**.
* It is **Never Parsed** by the runtime.
* It contains contradictions, garbage, and latent patterns.

**Design Consequence:**
* If you want data to be queryable (e.g., "What is the agent's status?"), put it in **EnvState**.
* If you want data to be active (e.g., "What does the agent *believe*?"), it stays in the **Substrate**.

---

## 7. Communication: Texture and Interference

Updated stance:
> Messages are not "Information."
> They are **Textures** (Frottage) projected onto a surface.

### 7.1 Textures (Frottage)
* Agents do not summarize. They **Resurface**.
* They project a **Texture** `T`: A dense, high-entropy description of their reality.
* **"Overloading" is good.** Sending rich, metaphorical, redundant text increases the surface area for connection.

### 7.2 Interference ($\Phi$)
* Communication happens at the **Receiver**.
* The Receiver applies a **Lens** $L$ to the Texture $T$.
* $\Phi = T \cap L$.
* Where they overlap, the signal is amplified (Resonance).
* Where they don't, the signal is background noise (Context).
* **No "Self-Cleaning":** The sender does not clean the message. The receiver does not delete the noise.

---

## 8. Internal Conjecture (Churn)

Internally, a Mind can:
* Spawn multiple **Personas** (The Believer, The Skeptic).
* Let them **Churn** against the Substrate independently.
* **Merge** the results during Resurfacing.

This is not a "Planning Phase." It is simply **Turbulence** inside the Reasoning step.

---

## 9. Meta and Indexers: Geology & Tectonics

We keep three loci cleanly separated:

1.  **Core/Worlds (Biology):** Where Minds live and churn.
2.  **Indexers (Geology):** Offline analysis.
    * They take **Snapshots** of Substrates.
    * They measure Viscosity, Basin Depth, and Temperature.
    * They write **Physics Reports** to EnvState.
    * *They never touch the live Mind.*
3.  **Meta (Tectonics):** Evolution.
    * Reads metrics.
    * Moves the "plates" (Graph wiring, DNA).
    * *Minds are blind to Tectonics.*

---

## 10. Implementation Constraints (The Anti-Drift Rules)

Code is **in-bounds** if:
* **Minds** are always "Nature + Substrate + Loop."
* **Substrates** are opaque and unparsed.
* **Communication** is Texture + Lens.
* **Ablations** (graph-only, etc.) exist only in `synaplex.meta` or `tests`, never in `core`.

Code is **out-of-bounds** if:
* It adds a "summary" field to messages.
* It allows the runtime to regex the Substrate.
* It creates a "Fast Path" that skips Reasoning.

**The North Star:**
We are building a system where intelligence **emerges from the mud** (Substrate), not one where it is **piped through the plumbing** (Workflows).
If your feature cleans up the mud, you are breaking the machine.
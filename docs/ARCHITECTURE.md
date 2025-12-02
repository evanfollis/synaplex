# **ARCHITECTURE.md — Core Spine for Synaplex**

**(Aligned with GEOMETRIC_CONSTITUTION.md — The Law of Substrate)**

Synaplex defines an architecture for AI systems composed of many interacting **Minds**.
Each Mind maintains its own evolving internal sediment (its **Substrate** `S`) while participating in a shared external world structured as a message-passing graph.

This document is the **implementation-facing companion** to `GEOMETRIC_CONSTITUTION.md`.

* The Constitution defines the **material primitives** and operators:
    `S, A, K, P, H, Φ, Ω, Ξ, τ, D, R_div, A_sat, H_rate, T`.
* This Architecture document specifies how those primitives show up as:
    * Minds and their loops,
    * Interference and Textures,
    * Graph wiring and runtime behavior,
    * Code modules and invariants.

If the Constitution and Architecture ever disagree, **the Constitution wins**.

There is:
* **one cognitive ontology** (Interference → Reasoning → Resurfacing),
* **one kind of Mind** (nature + nurture + loop),
* and **every Mind has a Substrate**.

---

## 0. How Materiality Becomes Architecture

Synaplex operates through a **single cognitive loop**:

> **Interference (Input) → Reasoning (Churn) → Resurfacing (Update)**

This is how material operators act over time:

* **Interference (Perception)**
    * Applies **Lenses** to incoming **Textures** to create a resonance pattern (the Percept).
    * Calculates overlap ($S \cap L$).
    * Does **not** touch the Substrate or internal geometry yet.
* **Reasoning**
    * Interprets the Percept through the Mind’s existing Substrate `S`, Basins `A`, Viscosity `K`, and Gradient `τ`.
    * Generates internal friction and potential new sediment.
    * May trigger outward **Impacts** `P` and project new **Textures** `T`.
* **Resurfacing (Internal Update)**
    * Applies dissipation `Ξ`,
    * Deposits new sediment onto `S` (the only time `S` changes),
    * Erodes or deepens Basins `A`,
    * Updates Viscosity `K` (hardening or softening),
    * Writes a new `SubstrateEnvelope`.

All "worlds" are special cases of this ontology.

---

## 1. Minds, Nature, and Nurture

### 1.1 Mind

A **Mind** is the fundamental unit, defined by:

* **Nature** — Wiring (Graph, DNA, Lenses, Tools, EnvState).
* **Nurture** — The accumulated **Substrate** `S` and its properties (`A, K, τ`).
* **Loop** — The application of operators.

Operationally, a Mind is:
> A function from Interference Patterns (plus current Substrate) to new Substrates and outward Textures.

### 1.2 Nature (Outer Structure)

Nature is everything externally visible and structurally constrained.

#### DNA (Design Constraints)
* Role and purpose.
* Tools/APIs.
* **Implicit Gradient Priors**: How `τ` is initially oriented (e.g., "Flow toward conflict," "Flow toward density").

#### Lenses ($L$)
* The mechanism of observation.
* Lenses define **Resonance**: "What patterns trigger a signal in this receiver?"
* **Invariant:** Lenses do not delete noise; they merely highlight signal against the noise.

#### Deterministic State (EnvState)
* **Strictly Physical.**
* Contains: IDs, timestamps, resource counters, external raw data feeds.
* **Forbidden:** Summaries, intents, "meanings," or any semantic derivative of the Substrate.
* *EnvState is Physics; Substrate is Metaphysics.*

### 1.3 Nurture (Inner Substrate)

Nurture is the Mind’s private, evolving material history.

#### Substrate `S` (formerly Manifold)
* Persistent internal sediment.
* Encoded as opaque text in a `SubstrateEnvelope`.
* **Texture-rich:** Contains contradictions, "garbage," and latent potential.
* **Never Parsed:** The runtime treats it as a binary blob.

#### Basins `A` (formerly Attractors)
* Deep grooves or habits in the sediment.
* Where thoughts "settle" when the Mind is tired or un-impacted.

#### Viscosity `K` (formerly Curvature)
* The "hardness" of the Mind.
* **High $K$:** Substrate is stone. Incoming Textures bounce off.
* **Low $K$:** Substrate is mud. Incoming Textures leave deep tracks.

#### Gradient `τ` (formerly Teleology)
* The "slope" of the ground.
* Determines the direction of flow for new sediment.

---

## 2. The Cognitive Loop (Operator Pipeline)

### 2.1 Interference (World → Mind)

The runtime constructs a **Percept** by:
1.  Collecting **Textures** projected by subscribed neighbors.
2.  Overlaying the Mind's **Lenses** onto these Textures.
3.  **Amplifying** regions of overlap (Resonance).
4.  **Preserving** non-overlapping regions as background noise (Context).

**Invariant:** The Percept is "colored-in," not "cropped."

### 2.2 Reasoning (Mind ↔ World)

Reasoning is where the Mind churns.
* Inputs: Percept + Prior Substrate `S₀`.
* Process: The LLM attempts to reconcile the new Interference Pattern with its existing sediment.
* **Frottage Action:** The Mind may rub its own Substrate to generate outward-facing **Textures** (`T`) to send to others.

### 2.3 Resurfacing (Mind → Substrate)

Resurfacing is the only time the Mind changes.
* New thoughts settle as sediment.
* Viscosity `K` is adjusted (did we get surprised? Soften `K`. Were we right? Harden `K`).
* A new `SubstrateEnvelope` is written.

---

## 3. Communication: Textures & Resonance

Communication is the exchange of surfaces, not packets.

### 3.1 Signals
* Lightweight, structured alerts (e.g., "I updated").
* Contains **no semantics**, only pointers.

### 3.2 Projections (Textures)
A **Projection** is the transmission of a **Texture ($T$)**.

* **Definition:** A Texture is a **Frottage Dump** of the sender's current state.
* **Content:** High-entropy, dense, "messy" prose or vector clouds.
* **Purpose:** To offer maximum surface area for the receiver's Lenses to catch onto.
* **Forbidden:** "Summaries," "Briefs," or "Cleaned Notes."
* *The noise is the signal.*

### 3.3 Interference ($\Phi$)
* The Receiver owns the meaning.
* The Receiver applies $L$ to $T$.
* Result: $\Phi(T, L)$ is the "Interference Pattern" — a map of where the Sender's mess resonated with the Receiver's query.

---

## 4. Internal Multiplicity

To maintain density, a Mind may fork:
1.  **Spawn:** Create "Persona Branches" (e.g., The Believer, The Skeptic).
2.  **Churn:** Each branch interacts with the Substrate differently.
3.  **Merge:** Internal Update overlays these branches. The "interference" between the branches becomes the new sediment.

---

## 5. Code-Level Architecture

### 5.1 `synaplex.core` — Physics
* IDs, EnvState, Lenses, Graph Topology.
* **Blind:** Knows nothing of what is inside the Substrates.

### 5.2 `synaplex.cognition` — Biology
* LLM Clients.
* `SubstrateEnvelope` management.
* Implementation of Frottage (Texture generation) and Interference.
* **The only module that reads/writes Substrate text.**

### 5.3 `synaplex.substrate_science` — Geology
* **Offline** analysis.
* Takes snapshots of Substrates.
* Measures Viscosity ($K$), Basin Depth ($A$), and Temperature ($T$).
* Writes **physics-based** analytics to EnvState.
* *Never edits the live Substrate.*

### 5.4 `synaplex.meta` — Tectonics
* Evolutionary algorithms.
* Changes the Graph (subscriptions) and DNA (Roles).
* **Metric-Blind Minds:** Agents never see the meta-metrics.

---

## 6. Invariants (Hard Rules)

Any implementation violating these is **not Synaplex**.

1.  **Every Mind has a Substrate.** It is opaque and sedimentary.
2.  **Runtime is Blind.** No parsing, schema-enforcement, or "cleaning" of Substrates by the core code.
3.  **Resurfacing is the only Write Path.** No external editing of a Mind's memory.
4.  **Texture > Summary.** Agents must project dense, noisy Frottage Dumps. Summarization is considered data loss.
5.  **EnvState is Physics.** It may only contain objective facts (time, ID, resources). It must never contain meanings or intents.
6.  **Receiver-Owned Meaning.** The Sender provides the Texture; the Receiver provides the Lens. The "message" is the interference between them.
7.  **No "Self-Cleaning."** Projections must not strip away noise. The background context must remain attached to the signal.
8.  **Tension Preservation.** Meta-moves ($\Omega$) must not resolve all contradictions. The system dies if it agrees.

---

## Appendix A — Material ↔ Architecture Mapping

| Material Primitive | Architectural Expression |
| :--- | :--- |
| **`S` (Substrate)** | `SubstrateEnvelope` (Opaque, sedimentary text/vector blob) |
| **`T` (Texture)** | **Frottage Dump** (High-entropy output payload) |
| **`A` (Basins)** | Habits/Recurring patterns in the sediment |
| **`K` (Viscosity)** | Resistance parameter (Temperature/Top-p modulation) |
| **`P` (Impact)** | New inputs that force sediment displacement |
| **`Φ` (Interference)** | The result of `Texture` $\cap$ `Lens` |
| **`τ` (Gradient)** | The implicit slope/bias of the agent's reasoning |
| **`EnvState`** | strictly **Physics** (Time, ID, External Data) |

Architecture is Materiality rendered as code constraints.
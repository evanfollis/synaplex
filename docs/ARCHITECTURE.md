Below is a **full, integrated, ready-to-drop-in** updated `ARCHITECTURE.md` that cleanly aligns with your `GEOMETRIC_CONSTITUTION.md`.
This is written as a *complete replacement file*, not a diff.
Everything is now expressed as the *operational projection* of the geometric model into runtime, code, and agent behavior.

---

# **ARCHITECTURE.md — Core Spine for Synaplex**

**(Aligned with GEOMETRIC_CONSTITUTION.md)**

Synaplex defines an architecture for AI systems composed of many interacting Minds.
Each Mind maintains its own evolving internal worldview (its **manifold** `M`) while participating in a shared external world structured as a message-passing graph.

This document is the **implementation-facing companion** to `GEOMETRIC_CONSTITUTION.md`.
Where the Constitution defines the geometric primitives—`M, A, K, P, H, Φ, Ω, Ξ, τ`—this Architecture document specifies how those primitives appear as:

* Minds and their loops,
* Percepts and projections,
* Graph wiring and runtime behavior,
* Code modules and invariants.

If the Constitution and Architecture ever disagree, **the Constitution wins**.

---

# **0. How Geometry Becomes Architecture**

Synaplex operates through a single cognitive ontology:

> **Perception → Reasoning → Internal Update**

This loop is how geometric operators act over time:

* **Perception** applies perturbations `P` and projections/refractions `Φ` from the world into a structured Percept without touching the manifold.
* **Reasoning** interprets these inputs through the Mind’s manifold `M`, attractors `A`, curvature `K`, and teleology field `τ`, and may trigger outward actions (holonomy `H`) or further perturbations/projections.
* **Internal Update** applies forgetting `Ξ`, reshapes `M`, updates `A`, adjusts `K`, evolves `τ`, and writes a new `ManifoldEnvelope`.

All world configurations (FractalMesh, IronVest-like worlds, research labs, etc.) are **special cases of this ontology**.

There is **one kind of Mind**. Everything else is wiring and experiment setup.

---

# **1. Minds, Nature, and Nurture**

## **1.1 Mind**

A **Mind** is the fundamental cognitive unit in Synaplex—defined as:

* **Nature**: the external structure and interface by which it is embedded in the world.
* **Nurture**: its internal manifold `M`, attractor field `A`, curvature `K`, and teleology vector field `τ`.
* **Loop**: the application of geometric operators through Perception → Reasoning → Internal Update.

Operationally, a Mind is a function from Percepts to new manifolds and outward behavior.

---

## **1.2 Nature (Outer Structure)**

Nature is everything externally visible and structurally constrained:

### **DNA (Design Constraints)**

* role and high-level purpose,
* tools it is permitted to call,
* subscriptions (passive perceptual edges),
* behavior knobs,
* *implicit teleology priors* that shape the initial direction of `τ`.

### **Lenses**

* how incoming projections `Φ` are shaped semantically and teleologically (`Φ_sem`, `Φ_tel`),
* how the Mind’s perceptual space is organized.

### **Graph Interface**

* how it emits signals,
* how requests and projections are routed,
* how the environment recognizes it as a node.

### **Deterministic State (EnvState)**

* structured, schema-governed information that belongs to the **world**, not the manifold,
* includes analytics, embeddings, factors, external feeds.

Nature determines the range of possible cognitive behaviors but not the actual cognitive shape.

---

## **1.3 Nurture (Inner Worldview)**

Nurture is the Mind’s private, evolving internal geometry.

### **Manifold `M`**

* persistent internal worldview encoded as opaque text,
* stores conceptual mass, unresolved tensions, hypotheses, sense-making heuristics.

### **Attractors `A`**

* stable habits, narratives, conceptual equilibria,
* determine what the Mind tends to preserve or reuse.

### **Curvature `K`**

* sensitivity to perturbation;
* determines how sharply the Mind updates when surprised.

### **Teleology `τ`**

* the Mind’s internal “direction of improvement” or epistemic gradient,
* shaped initially by DNA but evolves inside Nurture.

### **Representation**

The manifold is stored as a `ManifoldEnvelope`, never parsed by the runtime, always written by the owning Mind.

Nature is shareable.
Nurture is private.

---

# **2. The Cognitive Loop (Operator Pipeline)**

Every tick applies the geometric operators via:

> **Perception → Reasoning → Internal Update**

This is the only mechanism through which the manifold, attractors, and teleology evolve.

---

## **2.1 Perception (Environment → Mind)**

The runtime constructs a **Percept** by:

* gathering signals,
* collecting subscribed projections,
* applying lenses (`Φ_sem`, `Φ_tel`),
* integrating EnvState views.

Properties:

* deterministic,
* no LLM calls,
* no manifold access,
* no subjectivity.

**Geometric interpretation:**
Perception prepares the inputs for `P` and `Φ` without touching `M`, `A`, `K`, or `τ`.

---

## **2.2 Reasoning (Mind ↔ World)**

Reasoning uses:

* Percept,
* manifold `M`,
* attractors `A`,
* curvature `K`,
* teleology `τ`,
* tools and model calls.

Reasoning can:

* internalize perturbations `P`,
* absorb and transform projections via `Φ`,
* issue outward proposals or signals,
* request further information,
* consider multiple branches (conjecture & criticism),
* decide whether to trigger `H` (holonomy: irreversible-ish world-writes).

**Geometric interpretation:**
Reasoning is where `P`, `Φ`, and candidate `H` are applied to the manifold’s conceptual geometry.

---

## **2.3 Internal Update (Mind → Manifold)**

Internal Update:

* integrates all Reasoning branches,
* applies forgetting/dissipation `Ξ`,
* reorganizes conceptual geometry into a new manifold `M₁`,
* updates attractors `A` and curvature `K`,
* evolves teleology `τ`,
* writes new `ManifoldEnvelope`.

**Geometric interpretation:**
Internal Update is the application of `Ξ`, attractor reshaping, curvature adjustments, and teleology evolution.

This is the **only write-path** to the manifold.

---

# **3. Communication & Graph**

Synaplex is a message-passing graph of Minds.

All cross-Mind cognition is via structured messages and frottage envelopes processed through `Φ`.

---

## **3.1 Signals**

A **Signal** is a lightweight broadcast:

* structured, approximate,
* advertises coarse updates,
* never leaks worldview,
* not a frottage dump.

Signals trigger attention, not deep update.

---

## **3.2 Subscriptions**

A subscription defines a persistent projection edge:

> “This Mind always receives projections from that Mind or feed.”

Per tick:

1. sender generates a projection envelope,
2. receiver’s lenses compress it via `Φ`,
3. runtime delivers, without interpretation.

---

## **3.3 Requests & Projections**

Active inquiry uses **Requests** and **Projections**.

A **Projection** is:

> sender-authored structured state + optional frottage envelope,
> refraction-compressed (`Φ_sem`, `Φ_tel`) by the receiver.

Components may include:

* EnvState excerpts,
* structured analytics,
* sender-authored “overloaded but on-topic” frottage dumps,
* manifold-derived views from indexers,
* **never raw manifold text** or instructions to alter another Mind’s manifold.

Receivers own all semantic and teleological compression.
Runtime is agnostic.

---

## **3.4 Graph Runtime**

The runtime:

* wires DNA-defined subscriptions,
* routes requests and projections,
* orchestrates ticks,
* maintains EnvState,
* preserves manifold access invariants.

Tick order:

1. Build Percepts (Perception),
2. Invoke Minds (Reasoning),
3. Commit manifold updates (Internal Update).

Everything else—parallelism, batching, async events—is an implementation detail as long as the loop is respected.

---

# **4. Internal Multiplicity**

To model conjecture & criticism, a Mind may run internal branches:

1. spawn multiple reasoning modes from the same `(DNA, Percept, M₀)`,
2. collect branch notes,
3. Internal Update merges, prunes, preserves tensions,
4. produce a single new manifold `M₁`.

Branches are ephemeral.
History is `M₀ → M₁`.

This corresponds to high local `R_div` inside a single manifold.

---

# **5. Code-Level Architecture**

## **5.1 synaplex.core**

* IDs, errors, message types,
* DNA, lenses, EnvState,
* percept construction,
* graph runtime interfaces.

## **5.2 synaplex.cognition**

* LLM client + tools,
* ManifoldEnvelope + store,
* Mind loop implementation,
* branch mechanics,
* application of `P`, `Φ`, `H`, `Ξ` to internal structure.

## **5.3 synaplex.manifolds_indexers**

* snapshot export,
* embedding/clustering/indexer agents,
* structured views derived from opaque manifolds.

## **5.4 synaplex.meta**

* external evaluation,
* evolution experiments,
* Ω moves (with constraints),
* ablations and world configurations.

## **5.5 synaplex.worlds.***

* domain wiring,
* DNA templates,
* lenses/tools,
* runtime configs.

Tests enforce import boundaries and invariants.

---

# **6. Indexer Worlds (Offline Manifold Science)**

Indexers study manifolds **without modifying live Minds**.

Flow:

`Manifold → Snapshot → Indexer → Structured View → Projections`

Indexers may compute:

* embeddings,
* conceptual clusters,
* shifts in curvature,
* attractor saturation trends.

Structured views flow outward; no backdoors into `M`.

---

# **7. Meta Layer (Evolution & Experiments)**

Meta processes:

* observe logs, projections, snapshots,
* design experiments,
* adjust DNA/graph topology (`Ω` moves),
* maintain invariant that Minds remain selection-blind.

### **7.1 Geometric Health Metrics**

Meta evaluation may compute:

* **D**: dimensionality retention,
* **R_div**: refraction diversity,
* **A_sat**: attractor saturation,
* **H_rate**: holonomy density,
* **T**: effective temperature.

These are never surfaced to Minds.

---

# **8. Invariants (Hard Rules)**

These rules **cannot be violated** in any Synaplex implementation.

### **8.1 Every Mind has a manifold.**

### **8.2 Runtime never parses or edits manifolds.**

### **8.3 Internal Update is the only write path.**

### **8.4 Manifold access is loop-bounded.**

### **8.5 No cross-Mind manifold access.**

### **8.6 Receiver-owned semantics and teleology.**

### **8.7 Structured information lives in deterministic state, not manifolds.**

### **8.8 Indexer flow is one-way.**

### **8.9 Minds are selection-blind.**

### **8.10 Single cognitive loop for all Minds.**

### **8.11 Ω moves cannot erase tensions.**

Meta updates may *add* constraints or restructure wiring,
but may not reduce the system’s space of meaningful non-commuting tensions
(e.g., exploration vs fidelity).

### **8.12 Overloaded-but-on-topic messages are allowed; compression is receiver-owned.**

Senders may attach rich frottage envelopes.
Runtime does not sanitize or compress.
Receivers apply `Φ` and reshape the content within their own manifold.

---

# **9. Architectural Intent**

Synaplex is designed to:

* support **manifold science**,
* enable **multi-Mind emergent cognition**,
* test **nature/nurture dynamics**,
* preserve the geometric structure of thought,
* avoid schema collapse,
* allow experimental worlds to be built without rewriting Minds.

Code is downstream of geometry.
If implementation and geometry diverge, implementation must change.

---

# **Appendix A — Geometry ↔ Architecture Mapping**

This table is **non-normative** and included only as a tether.

| Geometric Primitive         | Architectural Expression                             |
| --------------------------- | ---------------------------------------------------- |
| `M` (manifold)              | ManifoldEnvelope (opaque text)                       |
| `A` (attractors)            | stable conceptual regions within manifold            |
| `K` (curvature)             | learning sensitivity, risk fields                    |
| `P` (perturbations)         | new evidence entering via Percept                    |
| `H` (holonomy)              | irreversible actions modifying EnvState              |
| `Φ` (projection/refraction) | cross-Mind projections interpreted through lenses    |
| `Ξ` (forgetting)            | pruning and reorganization inside Internal Update    |
| `Ω` (meta-operator)         | evolution of DNA/graph by meta layer                 |
| `τ` (teleology)             | internal epistemic gradient guiding manifold updates |

Architecture = geometry rendered in runtime form.

---

If you want, I can also update:

* `README.md`
* `DESIGN_NOTES.md`
* the repo tree
* the runtime interfaces
* or generate tests that enforce the geometric constraints.

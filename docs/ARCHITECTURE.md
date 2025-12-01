# **ARCHITECTURE.md — Core Spine for Synaplex**

**(Aligned with GEOMETRIC_CONSTITUTION.md)**

Synaplex defines an architecture for AI systems composed of many interacting **Minds**.
Each Mind maintains its own evolving internal worldview (its **manifold** `M`) while participating in a shared external world structured as a message-passing graph.

This document is the **implementation-facing companion** to `GEOMETRIC_CONSTITUTION.md`.

* The Constitution defines the **geometric primitives** and operators:
  `M, A, K, P, H, Φ, Ω, Ξ, τ, D, R_div, A_sat, H_rate, T`.
* This Architecture document specifies how those primitives show up as:

  * Minds and their loops,
  * Percepts and projections,
  * Graph wiring and runtime behavior,
  * Code modules and invariants.

If the Constitution and Architecture ever disagree, **the Constitution wins**.

There is:

* **one cognitive ontology** (Perception → Reasoning → Internal Update),
* **one kind of Mind** (nature + nurture + loop),
* and **every Mind has a manifold**.

No layered runtimes, no `WorldMode`s, no graph-only or reasoning-only “worlds” inside Synaplex proper.
Those exist only as external experiments in the meta layer, not as first-class architectures.

---

## 0. How Geometry Becomes Architecture

Synaplex operates through a **single cognitive loop**:

> **Perception → Reasoning → Internal Update**

This is how geometric operators act over time:

* **Perception**

  * Applies perturbations `P` and projections/refractions `Φ` from the world into a structured **Percept**.
  * Does **not** touch the manifold or any internal geometry (`M, A, K, τ`).
* **Reasoning**

  * Interprets the Percept through the Mind’s manifold `M`, attractors `A`, curvature `K`, and teleology field `τ`.
  * May trigger outward actions (holonomy `H`), further perturbations `P`, and new projections `Φ`.
* **Internal Update**

  * Applies forgetting/dissipation `Ξ`,
  * reshapes `M`,
  * updates `A` and `K`,
  * evolves `τ`,
  * writes a new `ManifoldEnvelope`.

All “worlds” (Idea World, FractalMesh-like worlds, lab simulations, personal sandboxes) are **special cases of this ontology**.
They differ only in **wiring and content**, not in cognitive structure.

There is **one kind of Mind**. Everything else is environment and experiment setup.

---

## 1. Minds, Nature, and Nurture

### 1.1 Mind

A **Mind** is the fundamental cognitive unit in Synaplex, defined by:

* **Nature** — how it is wired into the world (graph, DNA, lenses, tools, EnvState hooks).
* **Nurture** — its internal manifold `M` and the evolving fields `A` (attractors), `K` (curvature), `τ` (teleology).
* **Loop** — the application of geometric operators via Perception → Reasoning → Internal Update.

Operationally, a Mind is:

> a function from Percepts (plus its current manifold)
> to new manifolds and outward behavior.

All Minds share this shape. There are no “dumber” or “simpler” mind types at the architecture level.

---

### 1.2 Nature (Outer Structure)

Nature is everything externally visible and structurally constrained.

#### DNA (Design Constraints)

* role and high-level purpose,
* tools it may call,
* subscriptions (passive perceptual edges),
* behavior parameters/knobs,
* **implicit teleology priors**: how `τ` is initially oriented (e.g., “seek structure”, “seek tension”, “seek actionability”).

#### Lenses

* define how incoming projections are:

  * **semantically** shaped (`Φ_sem`),
  * and **teleologically** prioritized (`Φ_tel`),
* determine what gets into the Percept and how it is framed.

#### Graph Interface

* how the Mind:

  * emits signals,
  * sends requests,
  * produces projections for subscribers,
* how the runtime addresses and routes to it.

#### Deterministic State (EnvState)

* shared, schema-governed information in the **world**, not inside the manifold:

  * analytics, factors, embeddings,
  * external data feeds,
  * explicit experiment flags or configs.

Nature constrains **what can be seen and done**, but not **how it is understood**.
Understanding lives in Nurture.

---

### 1.3 Nurture (Inner Worldview)

Nurture is the Mind’s private, evolving internal geometry.

#### Manifold `M`

* persistent internal worldview,
* encoded as opaque text in a `ManifoldEnvelope`,
* written by the Mind for its own future selves,
* never parsed or schema-enforced by the runtime.

#### Attractors `A`

* stable-ish habits, explanations, conceptual equilibria,
* determine where the Mind tends to “fall back” when uncertain.

#### Curvature `K`

* sensitivity field: how much small perturbations matter,
* controls when the Mind radically reweights priors vs. shrugging off anomalies.

#### Teleology `τ`

* internal “direction of improvement” / epistemic gradient,
* initially seeded by DNA + lenses,
* evolves through Internal Update based on success/failure patterns.

The architecture **never** requires you to explicitly represent `A, K, τ` as separate structures.
They are **geometric interpretations** of how the manifold behaves over time.

Nature is shareable and inspectable.
Nurture is private and opaque.

---

## 2. The Cognitive Loop (Operator Pipeline)

Every tick applies the geometric operators through:

> **Perception → Reasoning → Internal Update**

This is the only path for evolutions in `M`, `A`, `K`, and `τ`.

There are no alternate loops, sub-loops, or “mode-dependent” loops in Synaplex.

---

### 2.1 Perception (Environment → Mind)

The runtime constructs a **Percept** by:

* collecting **signals** broadcast on the graph,
* assembling **projections** from subscribed agents and feeds,
* applying lenses to both:

  * semantic shaping (`Φ_sem`),
  * relevance / teleological bias (`Φ_tel`),
* integrating relevant **EnvState** views.

Properties:

* deterministic and side-effect free,
* no LLM calls,
* no manifold reads or writes,
* no branching or speculation.

**Geometric view:** Perception prepares structured inputs where `P` (perturbations) and `Φ` (refractions) can act, but it does not operate directly on `M`, `A`, `K`, or `τ`.

---

### 2.2 Reasoning (Mind ↔ World)

Reasoning is where the Mind thinks.

Inputs:

* Percept (shaped by nature: DNA + lenses + graph),
* prior manifold `M₀`,
* and implicitly, the evolving geometry (`A, K, τ`).

Within Reasoning, the Mind may:

* interpret and internalize perturbations `P`,
* translate incoming projections under its own `Φ`,
* spawn **internal branches** (conjecture & criticism),
* draft outward actions and signals,
* plan or decide whether to trigger holonomy moves `H` (irreversible-ish world writes),
* prepare notes and candidate updates for Internal Update.

**Geometric view:** Reasoning is where `P` and `Φ` are applied to the manifold’s conceptual geometry, and candidate `H` moves are proposed.

---

### 2.3 Internal Update (Mind → Manifold)

Internal Update is the Mind’s checkpoint ritual.

Inputs:

* prior manifold `M₀`,
* notes from Reasoning (including all branches),
* current Percept, if needed for context.

Responsibilities:

* merge or contrast branch notes,
* apply forgetting/dissipation `Ξ`,
* reorganize and rewrite `M` into `M₁`,
* implicitly update `A` (attractors) and `K` (curvature) as the manifold’s geometry changes,
* adjust `τ` based on what “seemed to work” epistemically,
* emit a new `ManifoldEnvelope` to the store.

**Geometric view:** Internal Update applies `Ξ`, adjusts attractors, curvature, and teleology, and commits the new internal geometry.

> **Internal Update is the only write path to the manifold.**

---

## 3. Communication & Graph

Synaplex is a **message-passing graph of Minds**.

All cross-Mind cognition flows through structured messages and receiver-owned refractions `Φ`.
No one ever reads or writes another Mind’s manifold.

---

### 3.1 Signals

A **Signal** is a lightweight broadcast:

* small, structured, approximate,
* advertises coarse updates (“something changed over here”),
* never includes manifold text or frottage dumps,
* designed to **trigger attention**, not to transmit worldview.

Receivers decide—via their lenses—whether a given signal matters.

---

### 3.2 Subscriptions

A **subscription** defines a persistent perceptual edge:

> “This Mind always receives projections from that Mind or data feed.”

On each tick:

1. the publisher produces a projection for the subscriber,
2. the runtime routes it,
3. the subscriber’s lens shapes it into part of its Percept.

Subscriptions define each Mind’s **baseline perceptual field**.

---

### 3.3 Requests & Projections

Active information-seeking uses **Requests** and **Projections**.

* A **Request** expresses what kind of information a Mind wants from another Mind.
* A **Projection** is:

  > a structured, sender-authored external view
  > that the receiver will compress and reinterpret via its own `Φ`.

Projection payloads may include:

* EnvState features,
* structured analytics,
* sender-authored “overloaded but on-topic” **frottage-like blobs** (rich text, multiple frames, tensions),
* manifold-derived **views** produced by indexers,
* **never raw manifold text**,
* **never direct instructions to change another Mind’s manifold**.

The sender chooses what to expose in structured form.
The receiver owns all semantic and teleological compression.

---

### 3.4 Graph Runtime

The runtime:

* manages world IDs, agents, and graph configuration,
* wires subscriptions and routes signals/requests/projections,
* executes ticks in the canonical order:

  1. Perception — build Percepts,
  2. Reasoning — invoke Minds,
  3. Internal Update — commit manifolds.

It also:

* maintains EnvState,
* enforces manifold access invariants (no cross-Mind manifold access, no runtime parsing, etc.).

Implementation details—async scheduling, batching, distributed routing—are free to vary as long as they respect:

* the logical Perception → Reasoning → Internal Update ordering,
* manifold access boundaries,
* message type semantics.

---

## 4. Internal Multiplicity (Conjecture & Criticism)

To support internal conjecture & criticism, a Mind may run multiple **branches** inside one tick:

1. From `(DNA, Percept, M₀)`, spawn several reasoning branches:

   * e.g., “explorer”, “skeptic”, “structuralist”.
2. Each branch:

   * processes the Percept + `M₀` differently,
   * produces internal notes and candidate outward behavior.
3. Internal Update:

   * sees all branch notes as “prior self-notes” (branch identities are optional),
   * decides what to preserve, contrast, or explicitly keep as unresolved tension,
   * writes a single new `ManifoldEnvelope` `M₁`.

Branches are **ephemeral**.
The Mind’s history, geometrically, is just `M₀ → M₁ → M₂ → ...`.

This corresponds to **high local `R_div`** inside a single manifold: multiple ways of seeing the same Percept before consolidation.

---

## 5. Code-Level Architecture

The codebase mirrors the geometric architecture so that cognitive and structural boundaries are hard to violate.

### 5.1 `synaplex.core` — External Structure

Responsibilities:

* IDs and errors,
* message types (signals, requests, projections, Percepts),
* DNA and lenses,
* EnvState abstractions,
* graph runtime interfaces and in-process implementations.

Constraints:

* knows nothing about LLM specifics,
* does not know how manifolds are represented or written,
* treats Minds through an abstract interface that exposes loop entry points, not internal geometry.

---

### 5.2 `synaplex.cognition` — Internal Mind Dynamics

Responsibilities:

* LLM client and tool invocation,
* `ManifoldEnvelope` and `ManifoldStore` (opaque snapshots),
* Mind implementation of Perception → Reasoning → Internal Update,
* branching strategies and consolidation mechanisms,
* application of operators `P, Φ, H, Ξ` **inside** a Mind’s reasoning and update process.

Constraints:

* imports from `synaplex.core` (DNA, lenses, messages, EnvState) but not vice versa,
* is the **only** place where manifolds are constructed, read, and written,
* knows nothing about experiment-level metrics or evolution (that lives in `meta`).

---

### 5.3 `synaplex.manifolds_indexers` — Offline Manifold Science

Responsibilities:

* snapshot export from live manifolds (opaque text + metadata),
* indexer “worlds” that:

  * compute embeddings,
  * cluster manifolds,
  * detect attractor changes, curvature shifts, etc.,
* write manifold-derived **structured views** back into their own EnvState.

Constraints:

* operate on **snapshots**, never on live manifolds,
* never edit or overwrite a Mind’s manifold,
* communicate results back only via structured data (EnvState, projections).

Flow:

> `Manifold → Snapshot → Indexer → Structured View → (optional) Projections to worlds`

---

### 5.4 `synaplex.meta` — Evaluation, Evolution, Ablations

Responsibilities:

* compute metrics over:

  * projections,
  * logs,
  * EnvState snapshots,
  * DNA and graph configs,
  * manifold snapshots,
* design and run evolution experiments:

  * Ω moves = changes to DNA, graph structure, lenses, or tool sets,
* run **ablations / counterfactuals** that *simulate*:

  * graph-only behavior,
  * “no-manifold” reasoning,
  * other degraded configurations.

Constraints:

* never imported by `synaplex.worlds.*`,
* affects Minds only via changes to DNA/config/graph between runs (Ω moves),
* keeps Minds **selection-blind**: Minds never see their scores or meta objectives.

Important:
Graph-only, reasoning-only, or no-manifold configurations live **here** as ablations—
they are **not** canonical Synaplex worlds.

---

### 5.5 `synaplex.worlds.*` — Domain-Specific Worlds

Responsibilities:

* define DNA templates for roles (e.g., Archivist, Architect, Critic),
* define domain-specific lenses and tools,
* wire agent sets and graph topology,
* provide world-specific bootstrap code and scripts.

Constraints:

* import `synaplex.core` and `synaplex.cognition`,
* may consume structured views from `manifolds_indexers`,
* do **not** import `synaplex.meta`,
* do **not** define alternate cognitive loops or “modes”.

A world is **just** a configuration of the one Synaplex ontology.

---

## 6. Indexer Worlds (Offline Manifold Science)

Indexer worlds let you study manifolds offline without touching live agents.

Pipeline:

1. **Export** `ManifoldSnapshot`s:

   * opaque text,
   * metadata (agent_id, world_id, timestamps, tags).
2. **Index** with dedicated agents:

   * embeddings,
   * clusters,
   * conceptual neighborhoods,
   * detect shifts in `A` or `K` at the population level.
3. **Write** structured views into the indexer’s own EnvState.
4. Optionally expose these views via projections back into other worlds.

The key invariant:

> No indexer ever edits a live manifold.
> Worldviews are observed, not over-written.

---

## 7. Meta Layer (Evolution & Experiments)

The meta layer is for **system-level science**, not cognition.

Meta agents:

* read:

  * projections,
  * logs,
  * EnvState snapshots,
  * DNA and graph configs,
  * manifold snapshots,
* design experiments:

  * which Ω moves to apply (e.g., new subscription edges, new roles, modified lenses),
  * which ablations to run (e.g., “what if this Mind had no access to its manifold?”),
* record outcomes for analysis.

Minds are never told:

* that they’re in an experiment,
* what metrics are being used,
* how Ω moves are chosen.

### 7.1 Geometric Health Metrics

Meta may compute health scalars like:

* **D** — dimensionality / diversity of active conceptual directions,
* **R_div** — refraction diversity (how differently different Minds respond to the same perturbation),
* **A_sat** — attractor saturation (overcommitment vs healthy plasticity),
* **H_rate** — holonomy rate (how often irreversible-ish changes happen),
* **T** — effective temperature (how deformable the system is under perturbation).

These scalars are **evaluation tools**, not runtime parameters. Minds never see them.

---

## 8. Invariants (Hard Rules)

These are **non-negotiable**. Any implementation that violates them is **not Synaplex**.

1. **Every Mind has a manifold.**

   * A `ManifoldEnvelope` always exists (may be “thin”, but never absent).

2. **Runtime never parses or edits manifolds.**

   * No schema, no AST, no pattern mining in core/worlds code.
   * Only `synaplex.cognition` knows how to serialize/deserialize.

3. **Internal Update is the only write path.**

   * All manifold writes happen inside the Mind’s Internal Update step.
   * No “fix agent” APIs, no external patches.

4. **Manifold access is loop-bounded.**

   * No manifold reads/writes during Perception.
   * Reasoning may read the manifold.
   * Internal Update reads and writes the manifold.
   * Indexers/meta operate only on snapshots, never live references.

5. **No cross-Mind manifold access.**

   * Minds never read or write other Minds’ manifolds.
   * All cross-Mind perception is via projections and signals over structured state.

6. **Receiver-owned semantics (and teleology).**

   * Lenses define how projections are interpreted.
   * Senders do not control how receivers see them.
   * Teleological bias `Φ_tel` lives with the receiver, not the sender.

7. **Structured information lives in deterministic state, not manifolds.**

   * If it must be queriable, diffable, or globally interpretable, it goes into EnvState or similar.
   * Manifolds are for the Mind’s **own** cognitive geometry.

8. **Indexer flow is one-way.**

   * `Manifold → Snapshot → Indexer → Structured View`.
   * No loop back into live manifolds.

9. **Minds are selection-blind.**

   * `synaplex.worlds.*` does not import `synaplex.meta`.
   * Meta feedback only via Ω moves on DNA/config/graph, never via direct metrics to Minds.

10. **Single cognitive loop.**

    * All Minds follow the same Perception → Reasoning → Internal Update loop.
    * No runtime “graph-only” or “reasoning-only” modes inside Synaplex proper.
    * Ablations that simulate such modes live in `meta` or tests, not in core/worlds.

11. **Ω moves cannot erase tensions.**

    * Meta may add constraints or restructure wiring,
    * but Ω moves must not deliberately destroy all non-commuting tensions (e.g., by collapsing all disagreement channels).
    * In practice: avoid changes that drive `D` and `R_div` to degenerately low values across the whole system.

12. **Overloaded-but-on-topic messages are allowed; compression is receiver-owned.**

    * Agents may send rich, messy, but on-topic “frottage-like” payloads in projections.
    * Runtime does not sanitize or compress these.
    * Receivers apply `Φ` to decide what to keep, what to ignore, and how to integrate into `M`.

---

## 9. Architectural Intent

Synaplex is designed to be:

* a platform for **manifold science**,
* a substrate for **multi-Mind emergent cognition**,
* a lab for **nature/nurture experiments**,
* and a geometry-faithful foundation for building domain-specific worlds without collapsing thought into brittle schemas.

Code is downstream of geometry.

* If implementation and geometry diverge, implementation must change.
* If a new idea demands a different geometry, update `GEOMETRIC_CONSTITUTION.md` first, then this Architecture, and only then the code.

---

## Appendix A — Geometry ↔ Architecture Mapping

This table is **non-normative**—a tether between mathy talk and code.

| Geometric Primitive            | Architectural Expression                                       |
| ------------------------------ | -------------------------------------------------------------- |
| `M` (manifold)                 | `ManifoldEnvelope` (opaque text, stored via `ManifoldStore`)   |
| `A` (attractors)               | stable conceptual patterns inferred from manifold trajectories |
| `K` (curvature)                | effective sensitivity to perturbations / surprise              |
| `P` (perturbations)            | new evidence entering via Percepts and signals                 |
| `H` (holonomy)                 | irreversible-ish changes to EnvState / graph / external world  |
| `Φ` (projection/refraction)    | receiver-owned interpretation of projections via lenses        |
| `Ξ` (forgetting)               | pruning, re-weighting, reorganization during Internal Update   |
| `Ω` (meta-operator)            | meta layer changes to DNA, graph, lenses, tools                |
| `τ` (teleology)                | Mind’s internal epistemic gradient over manifold updates       |
| `D` (dimensionality)           | diversity of active conceptual directions across Minds         |
| `R_div` (refraction diversity) | heterogeneity in responses to the same perturbation            |
| `A_sat` (attractor saturation) | degree of over-commitment vs plasticity                        |
| `H_rate` (holonomy rate)       | frequency of irreversible-ish changes in EnvState              |
| `T` (temperature)              | effective malleability of the system under perturbation        |

Architecture is geometry rendered as runtime and code constraints.

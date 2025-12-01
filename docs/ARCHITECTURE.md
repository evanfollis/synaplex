# **ARCHITECTURE.md — Core Spine for Synaplex**

Synaplex defines an architecture for AI systems composed of many interacting Minds.
Each Mind maintains its own evolving internal worldview (its manifold) while participating in a shared external world structured as a message-passing graph.

This document specifies the **ontology**, **loop shape**, and **hard invariants** that all Synaplex implementations must respect.

The central object of study is:

> How a Mind’s **nature** (outer structure) and **nurture** (inner manifold) co-evolve over time in a graph of other Minds.

---

## 0. Unified Ontology

Synaplex has **one cognitive ontology**:

> **Perception → Reasoning → Internal Update**

Every Mind:

1. receives a structured **Percept** from the environment (Perception),
2. thinks about it using an LLM + tools + its manifold (Reasoning),
3. revises its manifold (Internal Update).

All “world configurations” are variations in wiring, roles, and experiment setup.
They do **not** introduce new cognitive layers or alternative mind types.

There is one kind of Mind (nature + manifold + loop). Everything else is environment and experiment.

---

## 1. Minds, Nature, and Nurture

### 1.1 Mind

A **Mind** is the core cognitive unit in Synaplex.

Conceptually it consists of:

* **Nature** — how it is wired into the world.
* **Nurture** — its private internal worldview and reasoning habits.
* **Loop** — the Perception → Reasoning → Internal Update cycle it runs each tick.

In code, Minds implement a unified interface (see Section 5).

---

### 1.2 Nature (Outer Structure)

Nature is everything about the Mind that is externally visible and structurally constrained:

* **DNA**

  * role and high-level purpose,
  * subscriptions (which agents/data feeds it sees),
  * tools it can call,
  * behavior parameters and knobs.

* **Lenses**

  * how it attends to signals,
  * how it requests and interprets projections,
  * how it shapes its percept space.

* **Graph Interface**

  * how it emits signals,
  * how it responds to requests,
  * how it is wired into the message-passing graph.

* **Deterministic State (EnvState / other structured state)**

  * structured, interpretable, schema-governed information that belongs to the **world**, not any one Mind’s manifold,
  * includes features, analytics, vendor data, indexer-derived embeddings, etc.

Nature determines what the Mind *could* see and do, but not what it *does* in fact treat as important.

---

### 1.3 Nurture (Inner Worldview)

Nurture is the Mind’s private, evolving internal life.

* **Manifold**

  * persistent internal worldview,
  * represented as opaque text in a `ManifoldEnvelope`,
  * written by the Mind for its own future self,
  * never parsed or schema-enforced by the runtime.

* **Reasoning Patterns**

  * branching styles (explorer, skeptic, structuralist, etc.),
  * how it reconciles conflicting evidence,
  * how it manages unresolved questions and tensions,
  * how it develops an internal sense of “what matters”.

Over time, the manifold trajectory encodes:

* what the Mind has come to care about,
* how its explanations have deepened or shifted,
* where it still feels confused or unsatisfied.

Nature is shared and inspectable.
Nurture is private and opaque.

---

## 2. The Cognitive Loop

Each tick is one run of:

> **Perception → Reasoning → Internal Update**

This loop is the **only** way manifolds and outward behavior change.

### 2.1 Perception (Environment → Mind)

The **environment** (graph runtime) constructs a **Percept** for each Mind based on Nature:

* gather **signals** broadcast on the graph,
* collect **projections** from subscribed agents,
* read relevant data feeds / EnvState views,
* apply the Mind’s lenses to filter/select/shape these inputs,
* assemble a structured `Percept`.

Properties:

* deterministic,
* no LLM calls,
* no manifold access,
* no subjective interpretation.

Perception is the distilled view of “what is visible to this Mind right now,” given its Nature.

---

### 2.2 Reasoning (Mind ↔ World)

The Mind then performs **Reasoning**, using:

* the `Percept`,
* its prior manifold,
* tools,
* internal branching styles.

Reasoning is where:

* the Mind interprets what it sees,
* explores hypotheses and counterfactuals,
* requests more information,
* forms outward commitments.

Concretely, Reasoning can:

* issue **signals** (lightweight broadcasts),
* send **requests** for projections from other agents,
* respond to inbound requests with **projections** of its state,
* update deterministic state when allowed by DNA,
* produce an internal trace that will feed Internal Update.

Reasoning is the only place where a Mind uses the manifold **for thinking in the moment**.

---

### 2.3 Internal Update (Mind → Manifold)

Internal Update is where the Mind revises its manifold.

Inputs:

* prior `ManifoldEnvelope` (M₀),
* reasoning output (including internal branches),
* current Percept and relevant deterministic state.

Responsibilities:

* integrate new evidence into the worldview,
* choose what to preserve, amplify, or discard,
* maintain or explicitly preserve tensions and contradictions if useful,
* grow or reshape latent conceptual structure.

Output:

* new `ManifoldEnvelope` (M₁),
* persisted via `ManifoldStore`.

Internal Update is the **only write path** to the manifold.
No other code or process is allowed to modify `ManifoldEnvelope`.

---

## 3. Communication & Graph

Synaplex is a **message-passing graph of Minds**.

### 3.1 Signals

A **Signal** is a cheap, broadcast-level message:

* structured, approximate,
* advertises “what’s happening here” in a coarse way,
* never includes raw manifold text.

Receivers use their own lenses to decide whether to care.

Signals are attentional hooks, not worldview leaks.

---

### 3.2 Subscriptions

A **subscription** is a long-lived perceptual edge defined in DNA:

> “This Mind always wants a projection from that Mind / data feed.”

For each tick:

* sender produces a projection suitable for the receiver,
* receiver’s lens shapes how that projection is represented in its Percept,
* sender does not know how its state is interpreted.

Subscriptions define each Mind’s passive perceptual field.

---

### 3.3 Requests & Projections

Active information-seeking happens via **requests** and **projections**.

* A **request** expresses what kind of information a Mind wants from another Mind.
* A **projection** is:

  > sender’s externally visible structured state, as seen through the receiver’s lens.

Projection payloads may contain:

* EnvState features,
* analytics/factors,
* manifold-derived views produced by indexers (embeddings, clusters, etc.),
* never raw manifold text.

All cross-Mind perception flows through projections.

---

### 3.4 Graph Runtime

The runtime:

* manages the agent set and DNA configs,

* wires subscriptions and routes requests/responses,

* orchestrates ticks:

  1. build Percepts (Perception),
  2. call Minds (Reasoning),
  3. commit manifold updates (Internal Update),

* integrates outward behavior into EnvState and signals.

The runtime can be in-process or distributed, but it must:

* respect message types (Signal, Request, Projection, Percept),
* respect manifold access rules,
* preserve the unified loop semantics.

Ticks are the conceptual unit of time.
Asynchronous events can be modeled as finer-grained or agent-local ticks that still honor the same loop.

---

## 4. Internal Multiplicity (Conjecture & Criticism)

To model internal conjecture and criticism, a Mind may run **multiple reasoning branches** in a single tick.

Mechanism:

1. From the same starting point `(DNA, Percept, manifold M₀)`, the Mind spawns several branches:

   * e.g., explorer, skeptic, structuralist, etc.
   * each branch runs a full reasoning pass.

2. Each branch produces:

   * its outward proposals (optional),
   * its own candidate internal notes.

3. Internal Update then:

   * sees all branch notes as prior self-notes,
   * is not told about “branch identities”,
   * runs a fresh reasoning pass to reconcile, merge, and selectively preserve contradictions or tensions,
   * commits a single new `ManifoldEnvelope` (M₁).

Branches are ephemeral.
From the Mind’s perspective, history is `M₀ → M₁`.

Conjecture and criticism happen **inside** a single Mind, anchored to its own manifold, not as free-floating multi-agent banter.

---

## 5. Code-Level Mapping

The codebase mirrors this architecture so the boundaries are hard to violate.

### 5.1 Core Modules

* `synaplex.core`

  * IDs, errors, message types.
  * DNA, lenses, and EnvState.
  * Percept construction.
  * Agent interface and runtime interface.

* `synaplex.cognition`

  * LLM client + tool invocation.
  * ManifoldEnvelope + ManifoldStore.
  * Mind implementation of the Perception → Reasoning → Internal Update loop.
  * Branching and Internal Update strategies.

* `synaplex.manifolds_indexers`

  * Snapshot export from live manifolds.
  * Indexer agents that compute manifold-derived views.

* `synaplex.meta`

  * evaluation over logs, projections, snapshots, DNAs, and graph configs.
  * evolution and experiment harnesses.

* `synaplex.worlds.*`

  * domain-world configs (agents, DNA templates, graph wiring).
  * domain-specific lenses, tools, and agent factories.

Tests in `tests/` act as **tripwires** to guard import directions and invariants (see Section 8).

(See README’s repo layout for detailed file tree.)

---

## 6. Indexer Worlds (Offline Manifold Science)

Indexers let you study manifolds **without touching live Minds**.

Pipeline:

1. Export **ManifoldSnapshots** from live runs:

   * opaque text,
   * metadata (agent_id, world_id, timestamps, tags).

2. Indexer worlds ingest these snapshots and compute manifold-derived views:

   * embeddings,
   * clusters,
   * topic factors,
   * other latent structure.

3. Indexers store their results in **structured state** (their own EnvState).

4. Core worlds may then read indexer outputs through projections, as structured data.
   They never receive “edit your manifold” commands.

Information flow is one-way:

> **Manifold → Snapshot → Indexer → Structured View**

No code edits a live manifold outside a Mind’s Internal Update step.

---

## 7. Meta Layer (Evolution & Experiments)

The meta layer is where **research** and **evolution** live.

Meta:

* reads:

  * projections, logs, EnvState snapshots,
  * DNA, graph configs,
  * manifold snapshots,

* designs experiments and evolution strategies:

  * modify DNA templates,
  * adjust graph topology,
  * seed populations with different initial manifolds,
  * define evaluation metrics externally,

* writes back only via:

  * new or modified DNA/configs,
  * new runtime/graph wiring for subsequent runs.

Minds are **selection-blind**:

* they never see meta metrics or evolution objectives,
* they are never directly told that they are being graded.

Experiments like “graph-only” or “stateless reasoning” are treated as **ablations and counterfactual runs**, not alternative ontologies:

* in those runs, you may *disable* Internal Update or manifold access,
* the core spec still treats “Mind = nature + manifold + loop” as the baseline cognitive object.

---

## 8. Invariants (Hard Rules)

These are non-negotiable. Any implementation that violates them is not Synaplex.

1. **Every Mind has a manifold.**

   * A Mind always has a `ManifoldEnvelope`, even if initially empty.

2. **Manifold is opaque to the runtime.**

   * No parsing, schema enforcement, or structural edits in core/runtime.
   * Manifold text is never treated as structured data.

3. **Internal Update is the only write path to manifolds.**

   * All manifold writes occur inside a Mind’s Internal Update step.
   * No other module or process may create or modify `ManifoldEnvelope`.

4. **Manifold access is loop-bounded.**

   * No manifold reads/writes during Perception.
   * Only the owning Mind, during Reasoning/Internal Update, may touch its manifold.
   * Indexer/meta contexts may read manifold snapshots; they never edit live manifolds.

5. **No cross-Mind manifold access.**

   * Minds never read or write other Minds’ manifolds.
   * All cross-Mind perception is via projections/signals over structured state.

6. **Receiver-owned semantics.**

   * Projections are interpreted via the receiver’s lens.
   * No globally enforced schema overrides lens semantics.

7. **Structured information lives in deterministic state, not manifolds.**

   * If you want it structured, queryable, and shareable, it belongs in EnvState or similar—not in the manifold.

8. **Indexer flow is one-way.**

   * Manifolds → snapshots → indexers → structured views.
   * No “edit manifold” or “fix agent” API.

9. **Meta isolation and selection blindness.**

   * Domain worlds do not import `synaplex.meta`.
   * Meta influences Minds only via DNA/config/graph changes.
   * Minds never see their global scores or objectives.

10. **Single cognitive loop.**

    * All Minds follow the same Perception → Reasoning → Internal Update loop.
    * Engineering sub-phases are allowed, but they must respect Perception/Reasoning/Internal Update boundaries and manifold access rules.

These invariants preserve the distinction between Nature and Nurture, protect manifold purity, and keep Synaplex a platform for studying Minds rather than a thin wrapper around prompt orchestration.

---

## 9. Architectural Intent

Synaplex is designed to be:

* a platform for **manifold science**,
* a substrate for **multi-Mind cognition**,
* a lab for **nature/nurture experiments**,
* a foundation on which domain-specific worlds (like FractalMesh) can be built without collapsing internal worldviews into schemas or dashboards.

Code should be treated as an implementation detail of this architecture, not the other way around.

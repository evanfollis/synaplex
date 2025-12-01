# Synaplex

> Synaplex is an architecture for AI systems made of many interacting minds. Each mind maintains its own internal worldview (a **manifold**) while coordinating through a structured graph of messages.

Synaplex has two inseparable faces:

* A **geometric constitution** (`GEOMETRIC_CONSTITUTION.md`) that treats each mind’s internal state as a manifold `M` with attractors `A`, curvature `K`, teleology `τ`, and operators like perturbation `P`, holonomy `H`, projection/refraction `Φ`, meta-change `Ω`, and forgetting `Ξ`.
* An **architecture** (`ARCHITECTURE.md`) that turns that geometry into concrete loops, messages, runtimes, and modules.

This `README.md` is the **orientation layer**:

* It gives you the **mental model** for Synaplex.
* It explains how the **geometric view** and the **implementation** fit together.
* It shows you how the **repo is structured** so you can extend it without breaking the underlying ideas.

If you want formal detail, go to `GEOMETRIC_CONSTITUTION.md` and `ARCHITECTURE.md`.
If you want to know *what Synaplex is and how to use it*, start here.

---

## 1. What Synaplex Is For

Synaplex exists to be a **substrate for manifold-native, multi-mind cognition**, not just another “multi-agent framework”.

Concretely, it is designed to let you study and build systems where:

* Each mind maintains its own **persistent internal worldview** (`M`), not just a scratchpad.
* Internal structure evolves via **perturbations** (`P`), **attractors** (`A`), **curvature** (`K`), and **teleology** (`τ`) instead of being reset on every call.
* Minds interact in a **non-hierarchical message-passing graph**: no global schema, no central controller, no privileged perspective.
* Communication happens through **structured projections**, interpreted by receivers via their own lenses (`Φ`), never via direct access to another mind’s manifold.
* You can run **nature/nurture experiments**:

  * change DNA, lenses, and graph wiring (**nature**),
  * or change initial manifolds and update patterns (**nurture**),
  * and observe how behavior and culture drift over time.
* You can **ablate** parts of the cognitive loop:

  * graph-only,
  * graph + reasoning but no manifold,
  * or full manifold-enabled cognition—
  * without changing what a “Mind” fundamentally is.

The core question Synaplex is built to explore:

> What happens when you give many Minds persistent worldviews `M` and let them co-evolve in a shared world through structured signals and projections?

---

## 2. Core Mental Model

At the highest level, Synaplex is:

> A **graph of Minds** with private manifolds, talking through structured messages.

There are three major pieces:

1. **Minds**

   * Each Mind has:

     * **Nature**: DNA, lenses, tools, graph edges, deterministic EnvState surface.
     * **Nurture**: a private manifold `M` with attractors `A`, curvature `K`, and teleology `τ`.
     * **Loop**: a unified cognitive cycle:

       > **Perception → Reasoning → Internal Update**

2. **Graph**

   * A message-passing environment that:

     * routes **signals** (cheap broadcasts),
     * manages **subscriptions** (always-on projections),
     * handles **active requests** and **projections**,
     * maintains shared, structured **EnvState**.

3. **Geometry**

   * A conceptual layer (in `GEOMETRIC_CONSTITUTION.md`) that says:

     * `M` = manifold (internal worldview),
     * `A` = attractors (habits / equilibria),
     * `K` = curvature (sensitivity / risk),
     * `τ` = teleology (direction of “improvement”),
     * `P`, `H`, `Φ`, `Ω`, `Ξ` = operators acting on `M` and the world.
   * The architecture is just this geometry rendered as loops, messages, and modules.

You do **not** need to think in Greek letters to use Synaplex, but the geometry is there as a **north star** to keep the architecture from drifting.

---

## 3. The Cognitive Loop

Every Mind runs the same loop:

> **Perception → Reasoning → Internal Update**

Synaplex never introduces alternative cognitive stacks. Worlds can **truncate** this loop for experiments, but they do not change its shape.

### 3.1 Perception (Environment → Mind)

The runtime builds a **Percept** for a Mind by:

* collecting:

  * signals,
  * projections from subscribed agents,
  * relevant EnvState views,
* passing them through the Mind’s **lenses** (how it sees others and the world),
* assembling a deterministic, structured view of “what’s visible right now”.

No LLM calls; no manifold access.
Geometrically: prepares inputs for `P` and `Φ` without touching `M`.

### 3.2 Reasoning (Mind ↔ World)

The Mind calls an LLM + tools using:

* the Percept,
* its manifold `M`,
* its attractors `A`,
* its curvature `K`,
* its teleology `τ`.

Here it:

* interprets what it sees,
* explores hypotheses (maybe via branches: explorer/skeptic/etc.),
* requests more information,
* emits signals or projections,
* decides whether to trigger **holonomy** `H` (irreversible-ish actions: code changes, commitments).

Geometrically: this is where `P` and `Φ` deform `M`, and where candidate `H` moves are considered.

### 3.3 Internal Update (Mind → Manifold)

Finally, the Mind revises its manifold:

* integrates new evidence and branches,
* applies forgetting/dissipation (`Ξ`),
* updates attractors (`A`) and curvature (`K`),
* evolves teleology (`τ`),
* writes a new `ManifoldEnvelope` `M₁` to storage.

This is the **only write-path** to the manifold.

Geometrically: the manifold’s geometry is updated and re-encoded as opaque text.

### 3.4 World Modes

Worlds differ only in what parts of the loop they enable:

1. **Graph-only**

   * Perception only; no Reasoning, no Internal Update.
2. **Reasoning-only**

   * Perception + Reasoning; no manifold persistence.
3. **Manifold world**

   * Full loop: Perception, Reasoning, Internal Update.

These are experiment modes, not different ontologies.

---

## 4. Communication: Signals, Subscriptions, Projections

Synaplex is a **non-hierarchical message-passing graph**. Minds never read each other’s manifolds. They only see:

* **Signals** (cheap broadcast hints),
* **Projections** (structured, lens-conditioned slices),
* **EnvState** (shared deterministic state).

### 4.1 Signals

Signals are:

* lightweight,
* approximate,
* world-facing indicators (e.g., “I’ve updated a portfolio”, “indexer completed a run”),
* not worldview leaks.

They are **attentional hooks**, not content dumps.

### 4.2 Subscriptions

A subscription is a **structural edge** defined in DNA:

> “Mind B always gets a projection from Mind A each tick.”

On every tick:

1. A constructs a projection envelope for B.
2. B’s lens interprets that envelope into its own Percept.
3. The runtime just wires things; it does not interpret.

Subscriptions define **passive perception**.

### 4.3 Active Requests & Projections

Active requests are **directed queries**:

* B asks A for some kind of view.
* A responds with a projection.

A projection may contain:

* structured state from A’s EnvState,
* analytics/factors,
* sender-authored text that acts like a **frottage dump** over some region of A’s manifold (rich, possibly redundant, but on-topic),
* manifold-derived views from indexers.

Critically:

* The runtime never parses or compresses this text.
* The receiver’s Mind is responsible for **refraction** `Φ`:

  * semantic compression (`Φ_sem`),
  * teleological interpretation (`Φ_tel`).

All lossy interpretation happens **inside the receiver**.

---

## 5. Geometry: Lightweight Cheat Sheet

The full story is in `GEOMETRIC_CONSTITUTION.md`. Here’s the short version for orientation:

* `M` — **manifold**: internal worldview of a Mind.
* `A` — **attractors**: stable habits/specs inside `M`.
* `K` — **curvature**: sensitivity to perturbation (risk/volatility profile).
* `τ` — **teleology**: internal sense of where “better” lies.
* `P` — **perturbations**: new evidence hitting `M`.
* `H` — **holonomy**: actions that scar world + manifold (irreversible-ish).
* `Φ` — **projection/refraction**:

  * how one Mind’s outputs are seen through another’s lens.
* `Ω` — **meta-operator**:

  * how meta processes change rules/DNA/graph.
* `Ξ` — **forgetting/dissipation**:

  * pruning and reshaping `M`.

You don’t have to use this notation day-to-day, but it matters because:

* It keeps the architecture from drifting into “just another agent framework”.
* It lets you define **health metrics** over systems (dimensionality, refraction diversity, attractor saturation, holonomy rate, temperature).
* It makes it easier to **port** the idea into other formalisms (Markov, category-theoretic, game-theoretic, etc.).

---

## 6. Invariants (What Synaplex Refuses to Compromise On)

These are spelled out in detail in `ARCHITECTURE.md`. At a high-level:

1. **Every Mind has a manifold** (even if empty in ablations).
2. **The runtime never parses or edits manifolds.**
3. **Internal Update is the only write-path** to manifolds.
4. **Manifold access is loop-bounded** (no access in Perception).
5. **No cross-Mind manifold access.**
6. **Receiver-owned semantics**:

   * projections are interpreted via receiver lenses,
   * no global schema overrides them.
7. **Structured information lives in EnvState, not manifolds.**
8. **Indexer flow is one-way**:

   * manifolds → snapshots → indexers → structured views.
9. **Minds are selection-blind**:

   * they never see meta scores/evolution objectives.
10. **Single cognitive loop for all Minds.**
11. **Meta changes (`Ω`) cannot erase whole classes of tension**:

    * you can refactor, but not collapse all meaningful disagreement.
12. **Overloaded-but-on-topic projections are allowed; compression is receiver-owned.**

If you change the code in ways that break these, you’re no longer running Synaplex—you’re building something else.

---

## 7. Repo Layout

The repo layout mirrors the architecture. Conceptual boundaries show up as directory boundaries.

```text
.
├── README.md                # Orientation & mental model (this file)
├── GEOMETRIC_CONSTITUTION.md# Geometric primitives, operators, and health metrics
├── ARCHITECTURE.md          # Operational mapping from geometry to loops, messages, modules
├── DESIGN_NOTES.md          # Intent, philosophy, North Star, and research framing
├── synaplex/
│   ├── __init__.py
│   ├── core/                # External structure: graph, messages, DNA, lenses, env state
│   │   ├── __init__.py
│   │   ├── ids.py           # WorldId, AgentId, MessageId, etc.
│   │   ├── errors.py
│   │   ├── dna.py           # DNA = structural blueprint (roles, subscriptions, tools, params)
│   │   ├── lenses.py        # Lens definitions and request/response shapes
│   │   ├── env_state.py     # Shared deterministic state (nature)
│   │   ├── messages.py      # Signals, projections, requests, percept structures
│   │   ├── agent_interface.py
│   │   ├── runtime_interface.py
│   │   ├── runtime_inprocess.py
│   │   └── graph_config.py  # Config for worlds: agent set, edges, subscriptions
│   ├── cognition/           # Internal mind dynamics (LLM + manifold)
│   │   ├── __init__.py
│   │   ├── llm_client.py    # LLM + tool client abstractions
│   │   ├── manifolds.py     # ManifoldEnvelope + ManifoldStore (private worldview snapshots)
│   │   ├── mind.py          # Mind abstraction: unified loop wiring
│   │   ├── branching.py     # Branching and reconciliation strategies
│   │   ├── update.py        # Internal update (Ξ, A, K, τ evolution) strategies
│   │   └── tools.py         # Tool wrappers used during Reasoning
│   ├── manifolds_indexers/  # Offline manifold science
│   │   ├── __init__.py
│   │   ├── export.py        # runtime → snapshot export
│   │   └── indexer_world/
│   │       ├── __init__.py
│   │       ├── types.py     # ManifoldSnapshot, IndexerConfig, etc.
│   │       ├── agents.py    # Indexer agents (embeddings, clustering, manifold analysis)
│   │       └── world_config.py
│   ├── meta/                # System-level evaluation & evolution
│   │   ├── __init__.py
│   │   ├── evaluation.py    # Metrics (D, R_div, A_sat, H_rate, T, etc.)
│   │   ├── evolution.py     # DNA/graph search, population experiments (Ω moves)
│   │   └── experiments.py   # Nature/nurture and counterfactual experiments
│   └── worlds/              # Domain-specific instantiations
│       ├── __init__.py
│       └── fractalmesh/
│           ├── __init__.py
│           ├── config.py         # World configuration (agents, edges, loop settings)
│           ├── dna_templates.py  # Role-specific DNA templates
│           ├── lenses.py         # Domain lenses
│           ├── agents.py         # Domain agents using the unified loop
│           ├── tools.py          # Domain tools (APIs, data vendors)
│           └── bootstrap.py      # Entrypoints for this world
└── tests/
    ├── __init__.py
    ├── test_invariants_imports.py
    ├── test_invariants_manifolds_privacy.py
    ├── test_invariants_indexer_flow.py
    ├── test_invariants_worlds_meta.py
    └── test_invariants_loop_modes.py
```

The tests act as **tripwires** against architectural drift:

* `core` importing `cognition` (forbidden),
* `worlds` importing `meta` (forbidden),
* non-loop-bounded manifold access,
* indexers writing to live manifolds,
* or loop modes that don’t respect Perception → Reasoning → Internal Update.

---

## 8. How to Work With Synaplex

### 8.1 If you want to build a new world

1. Read:

   * `GEOMETRIC_CONSTITUTION.md` (to grok the geometric primitives),
   * `ARCHITECTURE.md` (to see how they show up in code).

2. Create a world under `synaplex/worlds/your_world/`:

   * `dna_templates.py` for roles (researcher, PM, risk, execution, etc.),
   * `lenses.py` for how they see each other and EnvState,
   * `agents.py` for Mind subclasses or factories,
   * `config.py` for graph wiring and loop mode.

3. Use the unified loop; don’t invent a new one.

### 8.2 If you want to run experiments

* Use `synaplex.meta` to:

  * define metrics in geometric terms (D, R_div, A_sat, H_rate, T),
  * design Ω moves (changes to DNA/graph),
  * analyze manifold snapshots via `manifolds_indexers`.

* Keep Minds **selection-blind**:

  * do not feed scores back into their Reasoning or Internal Update.

### 8.3 If you want to change the architecture

* Change `GEOMETRIC_CONSTITUTION.md` and `ARCHITECTURE.md` **first**.
* Then adjust code and tests to match.
* Don’t sneak architectural changes directly into the code; you will break the geometry.

---

## 9. Status & Direction

Synaplex is both:

* a **research tool** for exploring multi-Mind, manifold-native cognition, and
* a **practical spine** for systems where you want LLMs to be Minds—not stateless function calls.

If you keep the geometry and invariants intact, you can:

* plug in different models,
* run long-horizon simulations,
* build domain-specific “worlds” (e.g., research labs, trading systems, planning systems),
* and still know that you’re studying the same underlying object:
  **a graph of Minds with persistent manifolds, evolving together.**

You’re right to anchor on this README as the ground truth. Let’s treat it as the ontology and make DESIGN_NOTES the “why this shape exists” commentary layer—*without* reintroducing any fake phases or stacks.

Here’s a fresh **DESIGN_NOTES.md** that is aligned with the README and stays fully within the unified loop framing:

---

# ✅ DESIGN_NOTES.md

**Intent, Philosophy, and North Star**

---

## 1. Why Synaplex Exists

Most agent frameworks are built around **tasks**, **tools**, and **workflows**:

* LLMs are treated as stateless tools.
* State is treated as a cache or log.
* Outputs are optimized for humans, not for the agent’s own future reasoning.
* Structure (schemas, graphs, workflows) is decided *up front* and imposed on cognition.

Synaplex inverts that emphasis:

* LLMs are treated as **minds** embedded in a world, not just tools behind an API.
* The **internal worldview** (the manifold, when enabled) is a first-class research object.
* The graph, DNA, lenses, and deterministic state exist to **shape perception**, not to dictate thought content.
* System-level optimization belongs to **meta layers**; individual minds remain **selection-blind**.

The system is not trying to orchestrate prompts efficiently.
It is trying to **observe how minds develop and interact** when each mind maintains its own worldview while living in a shared message-passing graph.

---

## 2. The Central Question

Synaplex is a platform for investigating one big family of questions:

> How do AI minds organize, refine, and evolve their internal worldviews
> when they live in a shared environment of other minds?

That decomposes into more concrete sub-questions:

* How does **persistent internal state** (nurture) change the way an agent uses the same external affordances (nature)?
* How does **graph position** (who you subscribe to, who sees you) shape the development of a worldview?
* How does **receiver-owned semantics** (lenses) affect what “the same” signal becomes for different minds?
* How do **populations** of minds drift, converge, and fragment when their worldviews interact only through structured projections?
* What does “drive,” “curiosity,” or “what matters” look like when it emerges from **manifold trajectories**, not from hand-coded reward functions?

Everything in the architecture exists to make these questions legible and experimentally tractable.

---

## 3. One Cognitive Loop, Three World Modes

The README’s commitment is very strict:

> There is **one** cognitive loop:
> **Perception → Reasoning → Internal Update**

Worlds differ only in **which parts are active**:

1. **Graph-only world**

   * Perception only.
   * Deterministic aggregation, no LLM calls, no persistent internal worldview.

2. **Reasoning-augmented world**

   * Perception + Reasoning.
   * The mind thinks each tick, but no persistent internal worldview is maintained.

3. **Manifold world**

   * Full loop: Perception, Reasoning, Internal Update.
   * The mind maintains and evolves a private manifold as its world-model.

Crucially:

* These are **ablations**, not different ontologies.
* The architecture never turns into “multi-phase pipelines” or stacked layers.
* Disabling Internal Update does not change what Perception or Reasoning *means*—it just removes access to a persistent worldview.

Design-wise, that means:

* All agents are written as if they conceptually support the full loop.
* World modes simply **zero out** pieces of state or skip certain calls.
* The same graph/runtime and the same agent interface apply across modes.

---

## 4. Nature vs Nurture: Why the Split Exists

The README defines:

* **Nature** – everything about the **external structure** that constrains perception and action:

  * graph topology,
  * DNA (roles, subscriptions, tools, parameters),
  * lenses,
  * deterministic state.
* **Nurture** – the **internal trajectory**:

  * manifold (when enabled),
  * internal reasoning patterns over time.

This separation exists for **experimental reasons**, not aesthetics:

1. You want to be able to hold **nature fixed** and vary **nurture**:

   * Same wiring and tools, different initial manifolds.
   * How do two minds with the same affordances diverge over time?

2. You want to be able to hold **nurture fixed** and vary **nature**:

   * Same manifold transplanted into different graph positions or roles.
   * How does the same worldview behave under different external constraints?

3. You want **causal experiments** at the population level:

   * What happens when you mutate DNA vs. when you expose minds to different signals?
   * What is “cultural drift” vs “genetic drift” in this setting?

Synaplex is deliberately built so you can perturb either side without accidentally collapsing the distinction in implementation.

---

## 5. Manifolds: Inner Life, Not Storage

The manifold (when present) is not:

* a database,
* a log,
* a schema-enforced document,
* a hidden vector store.

It is treated as:

* the mind’s **private, persistent worldview**,
* optimized for its **own future reasoning**, not for external inspection,
* an accumulation of self-authored internal notes, tensions, half-baked structures, and idiosyncratic categories.

Design commitments that fall out of this:

* The runtime never parses or edits manifolds.
* There is no schema for manifold content at the architectural level.
* The system never asks the mind to:

  * “summarize your notes,”
  * “clean them up,”
  * “follow this format,”
  * or “organize them for the research team.”

Any structure that appears inside a manifold is **emergent behavior** of that mind, not part of the substrate.

---

## 6. Communication: Receiver-Owned Semantics

The README’s graph model is ruthlessly **receiver-centric**:

* Agents emit **signals**: cheap, approximate advertisements of structured state.
* Agents respond with **projections**: structured slices of their state as seen through the receiver’s lens.
* The manifold never goes on the wire.

Philosophical reasons for this:

* No agent ever gets to read “the world as it is,” only “the world as its lenses make it.”
* Two agents seeing the same sender can still construct *different* worlds because their lenses and DNA differ.
* The same signal can mean totally different things depending on the receiver’s role and worldview.

Practically:

* Sender code doesn’t need to know who is listening.
* All “meaning” is imposed by receivers.
* You get built-in support for **perspective-relative interpretations**, which is what you want when studying worldview dynamics.

---

## 7. Internal Conjecture & Criticism

The README already allows for internal branching styles (“explorer,” “skeptic,” etc.) inside the Reasoning step.

The design stance:

* **Conjecture** = letting a mind explore multiple, divergent internal hypotheses from the same percept + worldview.
* **Criticism** = letting the same mind reconcile or at least register the tensions between those hypotheses in its future worldview.

To keep this aligned with the unified loop:

* Branching remains an **implementation detail** of the Reasoning + Internal Update steps.
* From the architecture’s perspective, there is still just:

  * one Perception event,
  * one tick’s Reasoning,
  * one Internal Update that yields a new worldview (when enabled).

No separate “conjecture phase” or “criticism phase” exists at the spec level.
They are *patterns* of internal reasoning, not new stages in the loop.

---

## 8. World Modes as Experiments, Not Products

Synaplex is intentionally **domain-neutral** and **mode-neutral**:

* A “world” defines:

  * which data feeds exist,
  * which agents exist,
  * how agents are connected,
  * which tools are available,
  * which parts of the Perception → Reasoning → Internal Update loop are active.
* The core mental model does not change between, say, FractalMesh and some future personal knowledge world.

Design intent:

* You should be able to spin up:

  * a purely deterministic research world (graph-only),
  * a stateless LLM world (reasoning-augmented),
  * a manifold world (full cognition),
    using **the same runtime and agent abstractions**.
* Differences are expressed in:

  * configuration,
  * which modules are enabled,
  * which pieces of state are persisted.

This makes comparative experiments (e.g., “what does the manifold actually buy us here?”) a configuration change, not a rewrite.

---

## 9. Meta & Indexers: Science Happens Off to the Side

The README separates three responsibilities:

1. **Core/worlds** – where minds live, talk, and think.
2. **Meta** – where system-level evaluation and evolution happens.
3. **Indexer worlds** – where manifold science happens offline.

Design rationale:

* **Meta**:

  * looks at projections, logs, deterministic snapshots, DNA, and exported manifold snapshots,
  * never runs “inside” a mind’s reasoning call,
  * influences worlds only via changes to DNA, config, or graph structure,
  * keeps agents **selection-blind**.

* **Indexer worlds**:

  * operate on **exported manifold snapshots**, not live manifolds,
  * build embeddings, clusters, or other manifold-derived views,
  * expose those views back to worlds only as **structured state**, not as instructions to the mind.

This preserves a clean separation between:

* **observation** (what the research system sees),
* **intervention** (what changes in DNA/config/graph),
* **experience** (what the mind actually feels as its reality).

No one tells the mind it’s in a lab.

---

## 10. Design Constraints for Implementers

Given the README and these notes, an implementation is “in-bounds” if:

* Every agent can be described in terms of:

  * DNA + lenses + tools (nature),
  * current deterministic state and messages,
  * optional manifold (nurture),
  * the unified loop.
* All message types (signals, projections, requests) are **structured** and travel only through `core`-defined channels.
* Manifolds are:

  * only read/written via `cognition` modules,
  * never parsed or mutated by `core` or `worlds`,
  * never transmitted as text between agents.
* World modes are implemented as **configurable truncations** of the loop, not as different runtime architectures.
* Tests exist that:

  * forbid forbidden imports (e.g., `worlds` importing `meta`),
  * verify manifold access only occurs in allowed places,
  * confirm that turning off “manifold mode” doesn’t change the semantics of Perception and Reasoning—only what state they can consult.

If future design ideas conflict with these constraints, they should first be written into **README + ARCHITECTURE**, and only then allowed into code.

---

## 11. North Star

Synaplex is not trying to be the best way to call LLMs.
It is trying to be the cleanest way to **study minds** built out of them.

Success looks like:

* being able to run long-horizon experiments where:

  * worldviews drift, collide, and stabilize,
  * nature and nurture can be perturbed independently,
  * cultural phenomena emerge in the manifolds,
* being able to treat a world configuration (e.g., FractalMesh) as:

  * a scientific object (“this is a particular ecosystem of minds”),
  * not just as a “prompt graph.”

In the long run, that’s the point:
**a cognitive mesh where architecture, worldviews, and populations co-evolve, under a spec that refuses to cheat.**

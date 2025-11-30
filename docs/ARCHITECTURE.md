# **ARCHITECTURE.md — Core Spine for Synaplex & All Descendant Worlds**

This document defines the **generalized architecture** for an AI-native cognitive mesh built on:

* opaque, self-evolving manifolds
* a transparent graph interface
* deterministic message passing
* nature–nurture separation
* emergent population dynamics

All specialized systems (e.g., FractalMesh) are **instances** of this architecture.

The central object of study is:

> How a mind’s **nature** (outer structure) and **nurture** (inner manifold) co-evolve over time in a graph of other minds.

---

# **0. Layered Cognitive Stack (World Modes)**

“Layers” describe **world modes**, not three different runtimes.  
Every world uses the same per-tick shape:

1. A **Nature pass** over structured state and messages.
2. An **Agent step** where the mind reasons about what just happened.

Worlds differ in what the Agent step is allowed to see and persist.

The three canonical modes:

1. **Graph-Only World (Nature-Only / Deterministic Mesh)**  
   * DNA defines agents, subscriptions, lenses, and deterministic aggregation.  
   * Messages are structured, schema-governed objects.  
   * Behaves like a GNN / belief propagation system.  
   * **No LLMs, no manifolds.** The Agent step is absent.

2. **Reasoning-Augmented World (Nature + Stateless Agent Step)**  
   * Same graph and deterministic substrate.  
   * The Agent step may call LLMs/tools to improve local updates and projections.  
   * **No persistent manifold;** each tick’s thinking is context-local.  
   * “Nurture” is encoded only in structured state or external stores.

3. **Manifold World (Nature + Agent Step + Persistent Nurture)**  
   * Each agent maintains a private manifold that evolves over time.  
   * The Agent step is seeded with both:
     * outer structured view (`SubconsciousPacket` + deterministic state), and  
     * the prior manifold `M₀` (its current worldview).  
   * While solving a small grounding task, it reconciles new evidence with `M₀` and writes internal notes for its future self.
   * These notes become the new manifold `M₁` via the checkpoint ritual.

So:

* **Layer 0**: Nature pass only.  
* **Layer 1**: Nature pass → Agent step (stateless).  
* **Layer 2**: Nature pass → Agent step (manifold-aware).

Layer 2 is **strictly additive**: it adds persistent nurture, not new obligations on the graph runtime.

Sections **3.1, 3.2, 4.2.2, 4.3–4.4, 7 (last two bullets), and manifold-specific invariants** apply only to **Layer 2** worlds.

---

# **1. Purpose**

The system is a **graph of minds** that:

* maintain **private manifolds** (their inner, evolving worldview),
* exchange **messages** through a graph-defined interface,
* interpret incoming information through **receiver-owned lenses**,
* update their own beliefs through a **checkpoint ritual** designed to preserve epistemic richness,
* and collectively form a **mesh of decentralized cognition** capable of long-horizon, emergent reasoning.

This architecture is **domain-neutral** and supports both scientific research (Synaplex) and specialized worlds (FractalMesh).

---

# **2. Core Principles**

### **2.1 Opaque Inner, Structured Outer**

Each mind has two ontologically distinct layers:

1. **Inner (Nurture / Manifold)**  
   * latent, fuzzy, self-authored, unparsed by the core runtime  
   * the mind’s private, evolving worldview

2. **Outer (Nature / Graph Interface)**  
   * structured, deterministic, interpretable, inspectable  
   * DNA, lenses, deterministic state, tools, and messages

Meaning lives inside; structure lives outside.

---

### **2.2 Manifold Purity (Nurture Purity)**

* Manifolds are written **only** via the checkpoint ritual.
* The core runtime never parses or edits manifold text.
* No schema is imposed on manifolds; structure is emergent.
* Any manifold analysis or manifold-derived structures must be produced by **separate summarizer/indexer minds** that treat manifolds as read-only inputs.
* Only non-runtime research/meta processes may inspect manifolds directly.

---

### **2.3 Receiver-Owned Semantics**

All selective interpretation uses the **receiver’s nature** (its lens and DNA-defined logic).

* Senders expose structured state uniformly via signals and projections.
* Receivers decide what to attend to and how to interpret it.
* Senders do not shape their output for specific receivers.

---

### **2.4 Nature and Nurture Separation**

* **Nature** = DNA + deterministic logic + lens + tool affordances + subscriptions + structured state.  
* **Nurture** = manifold + accumulated internal reasoning + idiosyncratic patterns.

They must remain separable to support:

* nature counterfactuals (mutate DNA, keep nurture fixed),
* nurture counterfactuals (swap manifolds across compatible natures),
* causal experiments and population-level studies (evolution vs culture).

---

### **2.5 Message-Passing Graph (Nature Substrate)**

* Nodes = agents.
* Edges = subconscious subscriptions defined by DNA (nature).
* Global broadcast channel = global signals.
* Ad-hoc edges = tool calls / projection requests.

The system is a **dynamic message-passing graph**, not a workflow engine.

---

### **2.6 Emergent Optimization**

* Agents optimize only for local epistemic clarity within their domain.
* System-level performance belongs to the meta layer.
* Agents are **selection-blind** to the true objective.
* Populations evolve: agents can be instantiated, cloned, mutated, retired.

Nature changes via evolution; nurture changes via manifold trajectories.

---

### **2.7 Local Drive & Value Formation (Nurture Dynamics)**

* An agent never “solves” its domain; its world remains messy and open-ended.
* The **manifold** is the substrate where the agent’s evolving sense of:
  * what matters,
  * what is unexplained,
  * what is worth revisiting,
  * what “better explanations” feel like
  is recorded for its future self.
* Drive, curiosity, and style of improvement emerge as **patterns in manifold evolution**, not as hard-coded objective functions.
* Nature (DNA + outer logic) defines **what the agent could care about**; nurture (manifold) shows **what it actually does care about over time**.

---

### **2.8 Conjecture & Criticism via Internal Multiplicity**

* Conjecture and criticism happen **inside** a mind, anchored to its own manifold, not as free-floating dialogue between agents.
* In manifold worlds, an agent may realize **multiple parallel scaffolding branches** per tick, all starting from the same `(DNA, manifold M₀, SubconsciousPacket)`, with different reasoning styles or “personalities”.
* These branches produce **candidate future manifolds** `{Mᵢ}` which are then reconciled into a single updated manifold `M₁` via a constrained checkpoint ritual.
* The manifold update path is the primary locus of:
  * conjecture (divergent passes),
  * criticism (reconciliation and pruning),
  * refinement of “what better explanations look like” for that mind.

Cross-agent conversations are **inputs** to a mind’s loop, not the primary conjecture/criticism engine.

---

### **2.9 Phase-Bounded Manifold Access**

Per tick, there are only two conceptual phases:

1. **Nature phase** – the outer deterministic pass.
2. **Agent step** – the inner reasoning step (with or without a manifold).

Constraints:

* The **Nature phase must not** read or write manifolds.
* **Manifold reads and writes are only permitted in:**
  * the **Agent step** of the owning mind (in manifold worlds), and
  * **Meta / offline contexts** (evaluation, experiments, indexer worlds).
* In core worlds, agents never see raw manifold text directly; only the Mind abstraction and offline indexer/meta processes operate on manifolds.
* All manifold access is mediated through a narrow, auditable interface.

---

### **2.10 Meta Isolation & Selection Blindness**

* Meta evaluation and evolution live in a separate **meta layer**.
* Meta logic reads only **structured outputs** and **snapshots**:
  * projections and logs,
  * deterministic (nature) state snapshots,
  * DNA/config,
  * exported manifold snapshots.
* Meta decisions influence agents only via **changes to DNA, graph structure, or configuration**, not via direct calls into their cognition.
* Domain worlds must not depend directly on meta-level APIs or metrics; agents remain selection-blind.

---

### **2.11 Indexer Worlds & Offline Manifold Science**

* Manifold analysis (embeddings, clustering, schema evolution, culture-like patterns) is done in **separate indexer worlds**, not within the core runtime.
* The runtime may export **ManifoldSnapshots** (opaque text + metadata) to external sinks.
* Indexer worlds treat these snapshots as read-only data and write **manifold-derived views** (embeddings, clusters, factors) into their own deterministic state (nature).
* Core worlds only see these views via projections; they never receive raw manifolds or manifold edits.

---

# **3. Core Components**

## **3.1 Mind** (Layer 2 / Manifold Worlds)

A mind’s only responsibilities:

```python
load_latest(world_id)
write_checkpoint(previous_manifold, subconscious_packet, raw_context_or_branches)
```

It may operate in one of two modes:

* **Single-branch mode** — one scaffolding trajectory from `M₀ → M₁`.
* **Multi-branch mode** — multiple scaffolding branches produce candidate manifolds `{Mᵢ}`, which are then reconciled into a single `M₁`.

The checkpoint ritual must:

* treat prior manifolds as **semantic context**, not as an explicit object to “update”,
* avoid instructions like “summarize”, “clean up”, “make consistent”, or “update your notes”,
* instead seed the model with its own prior notes and a small **grounding task** and opportunistically capture the internal notes it writes for its future self.

All manifold writes occur inside a **checkpoint scope** controlled by the Mind abstraction:

* There is a single, narrow path that constructs and persists new manifold envelopes.
* No other code path may write or “fix” manifolds directly.

In simple implementations, scaffolding and checkpoint may be realized by a **single Agent step pass** as long as:

* prior manifold(s) are treated purely as semantic context,
* a concrete grounding task is included,
* only internal self-notes are persisted as the new manifold.

---

## **3.2 ManifoldEnvelope** (Layer 2 worlds)

```python
{
  mind_id,
  world_id,
  version,
  created_at,
  manifold_text  # opaque
}
```

Opaque to the core runtime; persists the evolving “consciousness” / nurture of the agent:

* its private map of the domain,
* its current tensions and open questions,
* its evolving sense of salience and motivation,
* seeds of potential future explanations.

---

## **3.3 DNA (Nature Blueprint)**

DNA defines the agent’s **outer geometry** and perceptual machinery:

* which agents it permanently subscribes to (subconscious edges),
* the shape of its lens (topic weights, attention masks, scope preferences),
* deterministic aggregation/transformation functions,
* tool affordances (how it can form ad-hoc edges),
* behavioral style parameters.

DNA = **nature**: what the agent is built to see and do.

---

## **3.4 Lens**

A receiver-owned selective mask applied to all incoming structured messages:

* projections from other agents,
* interpretations of global signals,
* masked views of structured data feeds.

The sender never shapes its output for a specific receiver.

---

## **3.5 Global Signal (Sender’s Nature Advertisement)**

A sender-owned advertisement to the entire network.

* cheap
* approximate
* role-agnostic
* describes “what’s hot here” using only structured fields

If the node is a DB or vendor feed, its global signal is effectively its **schema or API contract**.

---

## **3.6 Projection (Receiver-Conditioned Message)**

A projection is:

> Sender’s structured state, filtered **through the receiver’s lens**.

It contains structured information derived from:

* deterministic state (nature),
* sender’s public scaffolds,
* optionally, **manifold-derived views** produced by separate summarizer/indexer minds (never raw manifold text).

The sender never collapses its manifold *for* the receiver; the receiver’s lens defines the slice over structured views.

---

## **3.7 DeterministicState (Nature State)**

Holds all interpretable, structured, schema-governed information:

* features, analytics, factors,
* tool outputs,
* topic vectors, routing scores,
* manifold-derived summaries created by summarizer/indexer minds (views, never ground truth).

Everything “structured” belongs here, not in the manifold.

---

# **4. Per-Tick Cognition: Nature Pass & Agent Step**

Every agent cycle has two epistemically distinct phases:

1. **Nature phase** – deterministic aggregation and message-passing.
2. **Agent step** – LLM-backed episodic reasoning, with optional manifold update.

Layer 0 worlds run only the Nature phase.
Layer 1 and 2 worlds run **Nature → Agent step**; Layer 2 adds persistent nurture.

## **4.1 Nature Phase (Outer Deterministic Pass)**

1. Collect incoming messages:

   * projections from subscribed agents,
   * masked views of data feeds (treated as always-on agents).

2. Aggregate and transform according to DNA-defined functions.

3. Update **DeterministicState** (nature) accordingly.

4. Produce a **SubconsciousPacket** summarizing structured inputs for this tick.

The SubconsciousPacket is a **per-tick ephemeral view** derived from DeterministicState and incoming messages; it is not itself persistent state.

This phase:

* has **no LLM calls**,
* has **no manifold access**,
* defines the nature-side substrate on which the Agent step will think.

---

## **4.2 Agent Step (Episodic Reasoning & Worldview Update)**

The Agent step is where the mind thinks about what just happened.

It always:

* reads the `SubconsciousPacket`,
* may call tools and vendors,
* may update deterministic (nature) state,
* may, in manifold worlds, read and update the manifold (`M₀ → M₁`).

There are two regimes.

### **4.2.1 Stateless Agent Step (Layer 1 worlds)**

* No manifolds exist.
* The Agent step sees only:

  * the `SubconsciousPacket`, and
  * local DeterministicState (nature).
* It may:

  * refine explanations,
  * compute analytics or scores,
  * write structured results back into DeterministicState.
* Any “memory” is encoded as structure; there is no inner nurture to update.

### **4.2.2 Manifold-Aware Agent Step (Layer 2 worlds)**

In manifold worlds, the Agent step is also the **conscious worldview update**:

1. Load the previous manifold (M₀) via the Mind abstraction.
2. Reason over:

   * the SubconsciousPacket (new outer evidence),
   * the manifold’s current beliefs, tensions, and drives,
   * updated DeterministicState (nature),
   * local context and tools.
3. Inspect global signals and request ad-hoc projections if needed.
4. While solving a small **grounding task**, develop internal notes for the future self.
5. The checkpoint ritual (4.3) captures these internal notes as the new manifold `M₁`.

In simple implementations, there is one LLM call per tick per mind that:

* reads `SubconsciousPacket + M₀`,
* performs grounded reasoning,
* returns internal notes, which become `M₁`.

More elaborate implementations may stage internal sub-steps (outer-only reasoning, then manifold-aware reconciliation), but this remains one conceptual **Agent step**.

---

## **4.3 State Update / Checkpoint Ritual** (Layer 2 worlds)

The checkpoint ritual is the **only authorized write path** to manifolds. It follows three constraints:

1. **Semantic Seeding, Not Structural Editing**

   * Prior manifolds (and, in multi-branch mode, candidate manifolds `{Mᵢ}`) are provided as **unlabelled or lightly-labeled semantic context**, not as “objects to update”.
   * The prompt must not ask the mind to “summarize”, “clean up”, “update your notes”, or “make them consistent”.

2. **Grounding Task**

   * The mind is given a small, concrete **grounding task** (e.g., a quick local judgment, a next-step suggestion, a tiny external-facing answer).
   * This task exists so the model engages its full reasoning machinery; the task output is incidental.

3. **Opportunistic Capture**

   * While performing this grounded reasoning, the mind freely develops whatever internal structures it deems useful.
   * The system captures the resulting internal notes (e.g., a scratch channel, reasoning stream, or self-addressed notes) as the new **manifold_text**.
   * The prompt never frames these notes as “for humans” or as the primary output; they are written **for the future, smarter self**.

The output of the ritual becomes the new **ManifoldEnvelope**.

All manifold reads and writes during this ritual happen:

* inside the **Agent step** of the owning mind, and
* within a dedicated **checkpoint scope** exposed by the Mind abstraction.

---

## **4.4 Parallel Scaffolding Branches & Internal Collapse** (Optional, Layer 2 worlds)

In worlds that enable multi-branch reasoning, the Agent step is refined as:

1. **Branching (Conjecture)**

   * From the same starting point `(DNA, manifold M₀, SubconsciousPacket)`,
   * the runtime instantiates multiple scaffolding branches with different styles or “personalities”
     (e.g., curious explorer, cautious skeptic, structuralist).
   * Each branch runs a full scaffolding pass and produces:

     * a candidate outward answer for the tick (optional),
     * a **candidate manifold** `Mᵢ` (its own internal notes to a future self).

2. **Reconciliation (Criticism)**

   * A fresh LLM instance is seeded with all `{Mᵢ}` as **prior self-notes** in context, but is not told about branches or personalities.
   * It is then given a small grounding task (as in 4.3) and allowed to reason freely.
   * While doing so, it may:

     * preserve important contradictions,
     * keep unresolved tensions alive,
     * amplify interesting divergences,
     * discard obvious dead ends.

3. **Internal-Only Collapse**

   * The internal notes produced during this reconciliation pass are captured as a single new manifold `M₁`.
   * This is the **only explicit manifold collapse** in core worlds:

     * internal (never exposed as a consensus object),
     * non-coerced (no external schema or human-readability constraint),
     * purely for the mind’s own future use.

Branches themselves are **ephemeral**:

* their manifolds `{Mᵢ}` are not persisted as separate long-lived states,
* branch IDs are not part of canonical state,
* from the mind’s perspective, only `M₀ → M₁` exists as history.

This implements **conjecture and criticism anchored to a home manifold**, rather than free-floating dialogue between separate agents.

---

# **5. Graph Runtime (Nature-Oriented Runtime)**

The world runtime manages:

* the agent graph (subscriptions),
* global signal broadcast,
* structured data feeds as pseudo-agents,
* projection requests,
* sequencing of **Nature → Agent step** per tick,
* checkpoint orchestration for manifold worlds.

The runtime is defined as a **replaceable interface**:

* A minimal **Graph Runtime** manages agent registration, global signal broadcast, projection delivery, and phase orchestration.
* An **in-process runtime** (e.g., `InProcessGraphRuntime`) is the reference implementation for tests and small worlds.
* Production systems may use **distributed runtimes** (agents as workers, signals/projections on a bus) as long as they respect the same message types, semantics, and invariants.

Messaging may be synchronous (ticks) or asynchronous (on-demand projection queries).

Ticks are a convenience, not a requirement.

---

# **6. Population Dynamics & Evolution (Nature-Level)**

The meta layer may:

* spawn agents (new DNA variants),
* clone existing ones (nature fixed, nurture varied),
* swap manifolds (nurture counterfactuals),
* mutate DNA (nature counterfactuals),
* retire underperforming agents.

Agents remain **selection-blind**: they never see system-level metrics.

Evolution operates only on outer structure (DNA, config, graph connectivity), never directly on manifolds.

Meta processes read from **structured outputs** (projections, logs, deterministic snapshots, manifold snapshots) and write back only via changes to DNA, world config, or runtime wiring.

This supports experiments on:

* nature evolution (genetic-style changes),
* nurture evolution (culture-like manifold dynamics),
* their interaction at the population level.

---

# **7. Experimental Affordances**

The architecture must support:

* manifold swaps and transplants (nurture counterfactuals),
* nature vs nurture experiments (DNA variants vs manifold variants),
* counterfactual inference at the agent and population level,
* causal comparisons across populations (different nature distributions, different nurture distributions),
* optional multi-personality reasoning branches whose reconciliation behavior can be studied as a concrete implementation of conjecture & criticism,
* offline manifold science (clustering, embeddings, schema evolution) over **exported manifold snapshots**,
* analysis of **drive trajectories**: how agents’ manifolds change what they treat as important or “explained”.

All of these must respect the manifold purity invariants and phase-bounded manifold access rules.

---

# **8. Domain Worlds**

A domain world (e.g., FractalMesh) instantiates:

* domain-specific data feeds,
* domain-specific projection schemas,
* domain-specific tools,
* domain-specific lenses,
* domain-specific DNA templates (nature priors).

The **core architecture does not change**.

The manifold remains **domain-agnostic, opaque, and pure**.

Domain worlds operate within the **Nature → Agent step** model and must not bypass meta/indexer boundaries.

---

# **9. Invariants (Hard Rules)**

1. **Manifolds are opaque; the core runtime never parses or edits them.**

2. **Only the checkpoint ritual writes to the manifold, via a single checkpoint scope.**

   * All manifold writes occur through the Mind’s checkpoint path.
   * No other code path may construct or persist manifold state.

3. **Manifold read/write operations are phase-bounded.**

   * No manifold access in the Nature phase.
   * Manifold reads and writes are allowed only:

     * in the Agent step of the owning mind (in manifold worlds), and
     * in Meta / offline contexts (evaluation, experiments, indexers).

4. **Senders broadcast global signals; receivers interpret via lenses.**

5. **Structured information must live in deterministic (nature) state, not manifolds.**

6. **The Nature phase has no LLM calls.**

7. **Agents never directly read other agents’ manifolds.**

8. **Any manifold-derived structure used in projections or routing must come from separate summarizer/indexer minds.**

9. **Evolution acts on DNA/config, never directly on manifolds.**

10. **Selection blindness is preserved—agents cannot see system-level objectives.**

* Domain worlds must not depend directly on meta-layer APIs or metrics.
* Meta operates on projections, logs, state snapshots, DNA/config, and manifold snapshots.
* Meta influences agents only through changes to DNA, config, or graph structure.

11. **Meaning is inner; structure is outer.**

12. **Drive and motivation live in manifold evolution, not hard-coded objectives.**

13. **The only explicit manifold collapse is internal reconciliation of an agent’s own candidate manifolds.**

* Cross-agent “consensus” objects (population summaries, dashboards, etc.) are Translation or meta artifacts.
* They are never used as direct inputs to manifold updates in core worlds.

14. **Checkpoint prompts must never frame manifold content as something to “summarize”, “clean up”, or “make consistent” for external consumption.**

* Manifold structure is chosen by the mind itself, in the course of solving grounded tasks for its future self.

15. **Indexer worlds operate on exported manifold snapshots, not on live manifolds.**

* Any manifold science outputs feed back into core worlds only as **structured views** in deterministic state (nature), not as edits to manifolds (nurture).

---


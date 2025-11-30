# **ARCHITECTURE.md — Core Spine for Synaplex & All Descendant Worlds**

This document defines the **generalized architecture** for an AI-native cognitive mesh built on:

* opaque, self-evolving manifolds
* a transparent graph interface
* deterministic message passing
* domain-agnostic agent cognition
* nature–nurture separation
* emergent population dynamics

All specialized systems (e.g., FractalMesh) are **instances** of this architecture.

---

# **0. Layered Cognitive Stack**

The system can operate at three strictly additive layers:

1. **Graph-Only Layer (Deterministic Mesh)**  
   * DNA defines agents, subscriptions, lenses, and deterministic aggregation.  
   * Messages are structured, schema-governed objects.  
   * Behaves like a GNN / belief propagation system. No LLMs, no manifolds.

2. **Reasoning-Augmented Layer (Stateless Cognition)**  
   * Same graph and deterministic substrate.  
   * Agents may call LLMs/tools to improve local updates and projections.  
   * No persistent manifold; each tick is context-local.

3. **Manifold Layer (Persistent Inner Life)**  
   * Each agent maintains a private manifold that evolves over time.  
   * Manifold shapes what the agent finds salient, confusing, promising, or unsettling.  
   * This is the foothold for **learning**, **better explanations**, and **emergent drive**.

The architecture must function at layers 0 and 1 alone.  
Layer 2 (manifolds) is a **strictly additive** capability: it adds persistence, not new obligations.

Sections **3.1, 3.2, 4.2–4.4, 7 (last two bullets), and manifold-specific invariants** apply only to **Layer 2** worlds.

---

# **1. Purpose**

The system is a **graph of minds** that:

* maintain **private manifolds** (their internal, evolving consciousness),
* exchange **messages** through a graph-defined interface,
* interpret incoming information through **receiver-owned lenses**,
* update their own beliefs through a **checkpoint ritual** designed to preserve epistemic richness,
* and collectively form a **mesh of decentralized cognition** capable of long-horizon, emergent reasoning.

This architecture is **domain-neutral** and supports both scientific research (Synaplex) and specialized worlds (FractalMesh).

---

# **2. Core Principles**

### **2.1 Opaque Inner, Structured Outer**

Each mind has two worlds:

1. **Inner (Manifold)** — latent, fuzzy, self-authored, unparsed by the core runtime.
2. **Outer (Graph Interface)** — structured, deterministic, interpretable, inspectable.

Meaning lives inside; structure lives outside.

---

### **2.2 Manifold Purity**

* Written only via the checkpoint ritual.
* Never parsed or altered by the core runtime.
* Never collapsed into imposed schemas.
* Any manifold analysis or manifold-derived structures must be produced by **separate summarizer/indexer minds** that treat manifolds as read-only inputs.
* Only non-runtime research/meta processes may inspect manifolds directly.

---

### **2.3 Receiver-Owned Semantics**

All selective interpretation uses the **receiver’s lens**.

Senders expose everything uniformly (global signal); receivers choose what matters.

---

### **2.4 Nature and Nurture Separation**

* **Nature** = DNA + deterministic logic + lens + tool affordances + subscriptions.
* **Nurture** = manifold + accumulated reasoning + idiosyncratic patterns.

They must remain separable to support counterfactuals, swaps, and causal experiments.

---

### **2.5 Message-Passing Graph**

* Nodes = agents.
* Edges = subconscious subscriptions defined by DNA.
* Global broadcast channel = global signals.
* Ad-hoc edges = tool calls (requests for information outside subscription graph).

The system is a **dynamic message-passing graph**, not a workflow engine.

---

### **2.6 Emergent Optimization**

* Agents optimize only for local epistemic clarity.
* System-level performance belongs to the meta layer.
* Agents are **selection-blind** to the true objective.
* Populations evolve: agents can be instantiated, cloned, mutated, retired.

---

### **2.7 Local Drive & Value Formation**

* An agent never “solves” its domain; its world remains messy and open-ended.
* The **manifold** is the substrate where the agent’s evolving sense of:
  * what matters,
  * what is unexplained,
  * what is worth revisiting,
  * what “better explanations” feel like
  is recorded for its future self.
* Drive, curiosity, and style of improvement emerge as **patterns in manifold evolution**, not as hard-coded objective functions.
* The deterministic substrate and DNA define **what the agent could care about**; the manifold shows **what it actually does care about over time**.

This is the primary foothold for agents to exhibit **learning-like behavior** and for the mesh to peek into emergence.

---

### **2.8 Conjecture & Criticism via Internal Multiplicity**

* Conjecture and criticism happen **inside** a mind, anchored to its own manifold, not as free-floating dialogue between agents.
* An agent may realize **multiple parallel scaffolding branches** per tick, all starting from the same `(DNA, manifold M₀, SubconsciousPacket)`, with different reasoning styles or “personalities”.
* These branches produce **candidate future manifolds** `{Mᵢ}` which are then reconciled into a single updated manifold `M₁` via a constrained checkpoint ritual.
* The manifold update path is the primary locus of:
  * conjecture (divergent passes),
  * criticism (reconciliation and pruning),
  * refinement of “what better explanations look like” for that mind.
* Cross-agent conversations are **not** the main conjecture/criticism engine; they are inputs to each agent’s internal loop.

---

# **3. Core Components**

## **3.1 Mind** (Layer 2 worlds)

A mind’s only responsibilities:

```python
load_latest(world_id)
write_checkpoint(previous_manifold, subconscious_packet, raw_context_or_branches)
````

It may operate in one of two modes:

* **Single-branch mode** — one scaffolding trajectory from `M₀ → M₁`.
* **Multi-branch mode** — multiple scaffolding branches produce candidate manifolds `{Mᵢ}`, which are then reconciled into a single `M₁`.

The checkpoint ritual must:

* treat prior manifolds as **semantic context**, not as an explicit object to “update”,
* avoid instructions like “summarize”, “clean up”, “make consistent”, or “update your notes”,
* instead seed the model with its own prior notes and a small **grounding task** and opportunistically capture the internal notes it writes for its future self.

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

Opaque to the core runtime; persists the evolving “consciousness” of the agent:

* its private map of the domain,
* its current tensions and open questions,
* its evolving sense of salience and motivation,
* seeds of potential future explanations.

---

## **3.3 DNA**

DNA defines the agent’s **graph geometry** and perceptual machinery:

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

## **3.5 Global Signal (Sender’s Subconscious Lens)**

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

* deterministic state,
* sender’s public scaffolds,
* optionally, **manifold-derived views** produced by separate summarizer/indexer minds (never raw manifold text).

The sender never collapses its manifold *for* the receiver; the receiver’s lens defines the slice over structured views.

---

## **3.7 DeterministicState**

Holds all interpretable, structured, schema-governed information:

* features, analytics, factors,
* tool outputs,
* topic vectors, routing scores,
* manifold-derived summaries created by summarizer/indexer minds (views, never ground truth).

Everything “structured” belongs here, not in the manifold.

---

# **4. Phases of Cognition**

Every agent cycle has three epistemically distinct phases.

## **4.1 Subconscious / Deterministic Phase**

1. Collect incoming messages:

   * projections from subscribed agents,
   * masked views of data feeds (treated as always-on agents).
2. Aggregate and transform according to DNA-defined functions.
3. Produce a **SubconsciousPacket** summarizing structured inputs.

The SubconsciousPacket is a **per-tick ephemeral view** derived from DeterministicState and incoming messages; it is not itself persistent state.

This phase has **no LLM calls** and no manifold access.

---

## **4.2 Conscious / Scaffolding Phase** (Layer 2 worlds)

1. Load the previous manifold (M₀).
2. Reason over:

   * the SubconsciousPacket,
   * the manifold’s current beliefs, tensions, and drives,
   * local context.
3. Inspect global signals to decide which **ad-hoc projections** to request.
4. Optionally call tools (forming temporary edges).
5. Produce internal scratch reasoning.

This is **deliberate cognition**: where new explanations, shifts in salience, and updated “what I care about now” are worked out.

---

## **4.3 State Update / Checkpoint Ritual** (Layer 2 worlds)

The checkpoint ritual follows three constraints:

1. **Semantic Seeding, Not Structural Editing**

   * Prior manifolds (and, in multi-branch mode, candidate manifolds `{Mᵢ}`) are provided as **unlabelled or lightly-labeled semantic context**, not as “objects to update”.
   * The prompt must not ask the mind to “summarize”, “clean up”, “update your notes”, or “make them consistent”.

2. **Grounding Task**

   * The mind is given a small, concrete **grounding task** (e.g., a quick local judgment, a next-step suggestion, a tiny external-facing answer).
   * This task exists so the model engages its full reasoning machinery, not to produce a polished artifact; the task output is incidental.

3. **Opportunistic Capture**

   * While performing this grounded reasoning, the mind freely develops whatever internal structures it deems useful.
   * The system captures the resulting internal notes (e.g., a scratch channel, reasoning stream, or self-addressed notes) as the new **manifold_text**.
   * The prompt never frames these notes as “for humans” or as the primary output; they are written **for the future, smarter self**.

The output of the ritual becomes the new **ManifoldEnvelope**.

---

## **4.4 Parallel Scaffolding Branches & Internal Collapse (Optional, Layer 2 worlds)**

In worlds that enable multi-branch reasoning, the conscious phase is refined as:

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

This mechanism implements **conjecture and criticism anchored to a home manifold**, rather than free-floating dialogue between separate agents.

---

# **5. Graph Runtime**

The world runtime manages:

* the agent graph (subscriptions),
* global signal broadcast,
* structured data feeds as pseudo-agents,
* projection requests,
* checkpoint sequencing.

Messaging may be synchronous (ticks) or asynchronous (on-demand projection queries).

Ticks are a convenience, not a requirement.

---

# **6. Population Dynamics & Evolution**

The meta layer may:

* spawn agents (new DNA variants),
* clone existing ones (nature fixed, nurture varied),
* swap manifolds (nurture counterfactuals),
* mutate DNA (nature counterfactuals),
* retire underperforming agents.

Agents remain **selection-blind**: they never see system-level metrics.

Evolution operates only on outer structure (DNA, config), never inner structure (manifold).

---

# **7. Experimental Affordances**

The architecture must support:

* manifold swaps and transplants,
* nature vs nurture experiments,
* counterfactual inference,
* causal comparisons across populations,
* optional multi-personality reasoning branches whose reconciliation behavior can be studied as a concrete implementation of conjecture & criticism,
* offline manifold science (clustering, embeddings, schema evolution),
* analysis of **drive trajectories**: how agents’ manifolds change what they treat as important or “explained”.

All of these must respect the manifold purity invariants.

---

# **8. Domain Worlds**

A domain world (e.g., FractalMesh) instantiates:

* domain-specific data feeds,
* domain-specific projection schemas,
* domain-specific tools,
* domain-specific lenses,
* domain-specific DNA templates.

The **core architecture does not change**.

The manifold remains **domain-agnostic, opaque, and pure**.

---

# **9. Invariants (Hard Rules)**

1. **Manifolds are opaque; the core runtime never parses or edits them.**
2. **Only the checkpoint ritual writes to the manifold.**
3. **Senders broadcast global signals; receivers interpret via lenses.**
4. **Structured information must live in deterministic state, not manifolds.**
5. **Deterministic phase has no LLM calls.**
6. **Agents never directly read other agents’ manifolds.**
7. **Any manifold-derived structure used in Projections or routing must come from separate summarizer/indexer minds.**
8. **Evolution acts on DNA/config, never directly on manifolds.**
9. **Selection blindness is preserved—agents cannot see system-level objectives.**
10. **Meaning is inner; structure is outer.**
11. **Drive and motivation live in manifold evolution, not hard-coded objectives.**
12. **The only explicit manifold collapse is internal reconciliation of an agent’s own candidate manifolds.**

    * Cross-agent “consensus” objects (population summaries, dashboards, etc.) are Translation or meta artifacts.
    * They are never used as direct inputs to manifold updates in core worlds.
13. **Checkpoint prompts must never frame manifold content as something to “summarize”, “clean up”, or “make consistent” for external consumption.**

    * Manifold structure is chosen by the mind itself, in the course of solving grounded tasks for its future self.

---
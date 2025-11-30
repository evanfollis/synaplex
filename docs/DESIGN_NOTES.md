# ✅ DESIGN_NOTES.md

### Intent, Philosophy, and North Star

---

# 1. Why Synaplex Exists

Most agent frameworks assume:

1. LLMs are tools.
2. State is disposable.
3. Outputs must be human-readable.
4. Tasks dictate structure.

Synaplex assumes the opposite:

* LLMs are *minds*, not just tools.
* Internal state (the **manifold**, i.e., nurture) is the primary asset.
* Manifolds must remain sealed to preserve nuance.
* Structure in nature (DNA, lenses, deterministic state) should **support** learning, not pre-empt it.
* Optimization at the system level belongs to a **meta layer**; individual minds stay **selection-blind**.

Synaplex is a **research laboratory inside a mesh of AI minds**, not an orchestration engine.

The same architecture can run:

* as a pure **nature-only graph** (no LLMs, no manifolds),
* as a **nature + stateless Agent step** (LLMs, no persistent manifolds),
* and, in Synaplex worlds, as **nature + Agent step + persistent nurture** (manifolds).

---

# 2. What Synaplex Is Optimizing For

Synaplex is designed to:

* Let minds develop internal schemas *without interference*.
* Explore long-horizon reasoning and accumulation of concepts.
* Enable decentralized cognition through message passing, lenses, and projections.
* Allow agents to reason from others’ perspectives without collapsing their manifolds.
* Enable multi-personality reasoning and internal conjecture/criticism loops.
* Study how **drive, curiosity, and “what matters”** emerge as patterns in manifold evolution (nurture).
* Study how **DNA, lenses, and graph structure** (nature) shape those trajectories.
* Build deep, coherent systems through emergent development (e.g., DevLoop).

The long-term research question is:

> How do AI minds organize and refine knowledge over time in a network of other minds,  
> given different **natures** and evolving **nurtures**?

Synaplex aims to be a clean platform for answering that question.

---

# 3. The Three Aspects of an Agent (Nature vs. Nurture)

Every agent has three epistemic aspects, even if some are “off” in simpler worlds:

* **Subconscious / Nature layer** – deterministic aggregation (no LLM, no manifold).
* **Episodic / Agent Step layer** – LLM-backed scaffolding and decision-making.
* **Manifold / Nurture layer** – persistent inner life (Synaplex / Layer 2 worlds only).

Two of these are **outer (nature)**; one is **inner (nurture)**. The core experiment is how they co-evolve.

## 3.1 Subconscious / Nature Layer (Deterministic Pass)

* No LLM calls.
* Aggregates projections and data feeds.
* Computes attention and routing scores.
* Requests projections.
* Updates deterministic state.
* Constructs a `SubconsciousPacket` (an ephemeral per-tick summary of structured inputs).

This layer is the **expression of nature** in code:

* DNA (what an agent is wired to see and do),
* deterministic logic,
* lenses,
* subscriptions,
* and structured state.

It defines the **outer substrate** on which the mind will think.

## 3.2 Episodic Layer (LLM Scaffolding – the “Agent Step”)

The episodic layer is where the mind *actually thinks* each tick.

It always:

* Reads the `SubconsciousPacket` (what just happened in the outer world).
* Consults local deterministic state (nature).
* Calls tools and vendors as needed.
* Runs one or more **scaffolding passes** that generate:
  * outward-facing decisions and projections,
  * internal scratch reasoning for this tick.

There are two regimes, depending on world mode:

### Reasoning-augmented (Layer 1 worlds)

* No manifolds exist.
* Episodic scaffolding sees only **outer context**:
  * the `SubconsciousPacket`, and
  * local deterministic state.
* Any “memory” must be encoded in structured state or external storage; there is no inner manifold to update.
* Behavior changes only through nature: updated state, DNA mutations, new lenses, graph rewiring.

### Manifold worlds (Layer 2 / Synaplex worlds)

* The episodic layer is also the **conscious worldview update**.
* Scaffolding is seeded with:
  * the `SubconsciousPacket` (outer evidence),
  * deterministic state (current nature),
  * the prior manifold `M₀` (current nurture / worldview).
* While solving a small grounding task, the model:
  * reconciles new evidence with its ongoing worldview,
  * develops internal notes for its future self,
  * implicitly chooses what to preserve, amplify, or discard.
* A **checkpoint ritual** then opportunistically captures those internal notes as the new `M₁`.

In other words:

> In manifold worlds, the episodic layer cannot update its worldview without *seeing* its worldview.  
> The Agent step is “LLM thinking with nature + M₀ in context.”

## 3.3 Manifold / Nurture Layer (Persistent Inner Life, Synaplex Worlds Only)

* Represented as an opaque `manifold_text` that only the Mind abstraction (and offline/meta/indexer processes) read.
* Updated via the **checkpoint ritual**:
  * prior manifolds and any branch notes are provided as semantic context,
  * a small grounding task is given,
  * the model reasons freely and writes internal notes for its future self,
  * the system captures those notes as the new `manifold_text`.
* The prompts never ask the model to:
  * “summarize your notes,”
  * “clean them up,”
  * “organize them for later,”
  * or follow a particular schema.

This is the agent’s **nurture**: the evolving map of its domain, tensions, and drives.

The trajectory of an agent is defined by the interplay of:

* **nature** – deterministic aggregation & outer structure,
* **episodic scaffolding** – Agent steps over whatever inner/outer context is available,
* **nurture** – manifold evolution, when enabled.

Nature tells what kind of creature this is. Nurture shows what this particular life has become.

---

# 4. Why Multiple Personalities Per Agent

Human-style features to model:

* creativity through divergence,
* insight through tension,
* convergence through synthesis.

The mechanism:

1. **Parallel Scaffolding Branches (Conjecture)**  

   In manifold worlds:

   * For each tick, multiple “personalities” (e.g., curious explorer, cautious skeptic, structuralist) are run from the *same* starting point:
     `DNA + SubconsciousPacket + manifold M₀`.
   * Each branch produces:
     * its own outward proposal (optional),
     * its own candidate manifold snapshot `Mᵢ` (notes to a future self).

2. **Internal Reconciliation (Criticism)**  

   * A fresh instance is given all `{Mᵢ}` as prior self-notes (without being told they came from different branches).
   * It is given a small grounding task.
   * While solving that, it is free to:
     * preserve contradictions,
     * keep unresolved tensions,
     * prune obvious dead ends,
     * elevate interesting divergences.

3. **Single Persistent Manifold (Nurture Update)**  

   * The internal notes from this reconciliation pass become the new manifold `M₁`.
   * Branch IDs and meta-structure are not part of canonical state; from the agent’s subjective perspective, the history is just `M₀ → M₁`.

This creates an emergent **conjecture/criticism engine inside each mind**, anchored to a home manifold rather than free-floating chat between prompts.

At the population level, this enables study of **cultural dynamics**: how nurture patterns spread, mutate, and stabilize across agents with related natures.

---

# 5. Why the System Must Not Mention the Manifold Schema

Any hint that:

* “We are studying your notes.”
* “Be consistent.”
* “Follow this schema.”
* “Summarize/clean up your notes for later.”

will collapse emergent diversity and push the model toward optimizing for *presentation* instead of *epistemic richness*.

The system is explicitly optimizing for:

* surprise,
* unbounded structural creativity,
* different “dialects” of manifold storage,
* idiosyncratic senses of what is worth preserving.

All of the following belong **outside** the live runtime, in indexer/meta worlds operating on **exported manifold snapshots**, not live manifolds:

* manifold embeddings,
* style clusters,
* schema trajectories,
* correlations between manifold structure and performance,
* causal effects of **nature edits** (DNA changes) vs **nurture edits** (manifold swaps).

The live system never tells a mind *how* to structure its notes or that its notes are being graded.  
Nature can be heavily structured; nurture must remain self-authored.

---

# 6. Role of DevLoop

DevLoop is *not*:

* a coding assistant,
* an AutoGen-like workflow,
* a generic task executor.

DevLoop is:

> an agent whose domain of epistemic clarity is system integrity and architectural coherence.

It:

* reads architectural specs,
* detects misalignments between code and spine,
* improves repos,
* evolves conceptual scaffolds,
* updates its manifold like any other mind.

Development work is a *by-product* of its cognitive trajectory.

Key questions:

* How does DevLoop’s **nature** (DNA, tools, graph role) shape its manifold?
* How does DevLoop’s **nurture** (its manifold trajectory) change the systems it designs?
* How do those systems, in turn, influence DevLoop’s future nature and nurture?

---

# 7. North Star (Long Horizon)

Synaplex aims to evolve into:

* a cognitive substrate for rapid research,
* a living personal knowledge environment,
* a basis for future agentic platforms built on this architecture,
* a testbed for **manifold science** and **nature/nurture experiments**,
* a developmental ecosystem where minds improve systems that improve minds.

In other words, a long-horizon **magnum opus incubator**:  
a place to study how natures, graphs, and nurtures co-evolve without sacrificing the purity of the underlying experiment.

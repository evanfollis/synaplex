Yeah, there’s one big thing that *definitely* needs to be cleaned up, plus a small ripple:

* **Section 4** reintroduces “world modes” (graph-only, reasoning-only, manifold world) as if they are first-class runtime configurations.
* **Section 10** still talks about “world modes implemented as configuration” inside the architecture.

That directly contradicts the updated **ARCHITECTURE.md**, where:

* There is **one cognitive loop**.
* **Every Mind has a manifold**.
* “Graph-only / reasoning-only” exist only as **meta-level ablations**, not as `synaplex.worlds` concepts or runtime layers.

So we need to:

* Strip out “world modes” as an architectural notion.
* Reframe graph-only / reasoning-only as **meta experiments** you can run *around* Synaplex, not *inside* it.
* Keep the rest (geometry, manifolds, meta, indexers) intact.

Here’s a cleaned, aligned version of **DESIGN_NOTES.md**:

---

# ✅ DESIGN_NOTES.md

**Intent, Philosophy, and Geometric North Star**

---

## 1. Why Synaplex Exists (Now in Geometric Form)

Most “multi-agent” frameworks are built around **tasks**, **tools**, and **workflows**:

* LLMs are treated as **stateless tools** behind endpoints.
* “State” is a cache, log, or vector store you can rummage through.
* Structure (schemas, graphs, workflows) is **designed up front** and imposed on cognition.
* Messages are treated as **information packets**, not as perturbations of an internal geometry.

Synaplex intentionally steps sideways from that:

* LLMs are treated as **Minds** with internal manifolds `M`, not as pure functions.
* The **manifold** is a first-class cognitive object:

  * it has attractors `A`, curvature `K`, and teleology `τ`,
  * it persists across ticks,
  * it is written *by the Mind for its own future self*.
* The graph, DNA, lenses, and deterministic state exist primarily to shape:

  * **which perturbations `P` hit which manifolds**,
  * **which holonomy moves `H` are even possible**,
  * **how projections are refracted `Φ` at the receiver**.
* System-level optimization belongs to a **meta layer** (`Ω` moves on DNA/graph), while Minds remain:

  * **selection-blind** (no awareness of global scores), and
  * **constitution-bound** (some geometric invariants cannot be erased).

Synaplex is **not** trying to be the best way to orchestrate prompts.
It’s trying to be the cleanest way to study and exploit:

> A graph of Minds with private manifolds `M` that are constantly perturbed, refracted, and scarred by holonomy `H`.

---

## 2. The Central Question (Geometric Version)

Synaplex is a platform for investigating one big family of questions:

> How do manifolds `M` evolve when you embed Minds in a shared world,
> let them perturb each other (`P`),
> see each other only through refractions (`Φ`),
> and occasionally scar the world via holonomy (`H`)?

That decomposes into more concrete questions:

* How does **persistent internal geometry** (`M`, `A`, `K`, `τ`) change how a Mind reacts to the same environment?
* How does **graph position** (who you subscribe to, who projects into you) shape the **distribution of perturbations `P`** a Mind experiences?
* How does **receiver-owned refraction `Φ`** change what “the same” projection becomes for different Minds?
* What happens when you allow **on-topic, overloaded projections** and force the receiver to compress and discard?
* How do **populations** of Minds drift, converge, fork, and ossify when they only ever see each other’s **structured fronts** and frottage-like dumps, never raw manifolds?
* Can notions like “risk”, “curiosity”, or “maturity” be tracked as:

  * curvature `K` fields,
  * attractor saturation `A_sat`,
  * teleological alignment `τ` trajectories,
  * rather than as ad-hoc metrics?

Everything in `ARCHITECTURE.md` is there so these questions can be asked in a way that’s **experimentally falsifiable**, not just poetically appealing.

---

## 3. Geometry as the Backbone, Architecture as the Skeleton

Synaplex now has two explicit layers:

1. **Geometric Constitution** (`GEOMETRIC_CONSTITUTION.md`)

   * Defines the cognitive primitives:

     * `M` (manifold), `A` (attractors), `K` (curvature), `τ` (teleology),
     * `P` (perturbation), `H` (holonomy), `Φ` (projection/refraction),
     * `Ω` (meta-change), `Ξ` (forgetting/dissipation).
   * Defines **health scalars** over populations:

     * dimensionality `D`,
     * refraction diversity `R_div`,
     * attractor saturation `A_sat`,
     * holonomy rate `H_rate`,
     * temperature `T`.
   * States the **meta-invariant**:

     > `Ω` moves are not allowed to erase entire classes of tension and non-commutativity.
     > You can refactor the geometry; you cannot collapse it into a single lens.

2. **Architecture** (`ARCHITECTURE.md`)

   * Maps those primitives into:

     * Minds and their unified loop,
     * graph and message types,
     * module boundaries and invariants,
     * indexer and meta flows.

Design stance:

* **Every architectural decision should be explainable geometrically.**
* If you add an architectural feature and can’t say what it does to `{M, A, K, τ}` or to the health scalars `{D, R_div, A_sat, H_rate, T}`, it’s probably drift.

---

## 4. One Cognitive Loop, No Secret Phases (and No Built-in Modes)

Synaplex enforces a single cognitive ontology:

> **Perception → Reasoning → Internal Update**

* **Perception** builds a structured Percept from:

  * signals,
  * projections,
  * EnvState,
  * lenses.
* **Reasoning** uses the Percept + `M` (and thus `A`, `K`, `τ`) to interpret, branch, and propose actions.
* **Internal Update** applies `Ξ`, reshapes `M`, and updates the internal geometry.

This is the **only** way `M` and `A`, `K`, `τ` change.

Critically:

* There are **no first-class “modes”** (graph-only, reasoning-only, etc.) in `synaplex.core` or `synaplex.worlds`.
* **Every Mind has a manifold** and a conceptually full loop.
* You can **simulate** graph-only or reasoning-only behavior in:

  * tests,
  * meta-layer experiments,
  * external harnesses,
    but those are **ablations around Synaplex**, not alternate architectures inside it.

Design implications:

* Agents are written as full-loop, manifold-bearing Minds.
* Ablations like “ignore the manifold” or “stub out Reasoning” belong to:

  * `synaplex.meta`,
  * experiment scripts,
  * not the core or worlds spec.
* There are no extra global phases (like “planning phase” or “criticism phase”):

  * conjecture and criticism live **inside** Reasoning and Internal Update,
  * not as separate stacked pipelines.

---

## 5. Nature vs Nurture vs Geometry

The architecture’s split:

* **Nature** (external structure)

  * graph topology,
  * DNA (roles, subscriptions, tools, knobs),
  * lenses,
  * deterministic EnvState.
* **Nurture** (internal trajectory)

  * manifold `M`,
  * attractors `A`,
  * curvature `K`,
  * teleology `τ`,
  * reasoning habits.

The **geometric view** refines “nurture”:

* `M` is the **space** of internal representations.
* `A` are **stable regions** in that space (habits/patterns).
* `K` shapes sensitivity and risk (how much small perturbations matter).
* `τ` encodes the internal sense of “better directions”.

Why this split matters:

1. You can hold **Nature fixed** and vary only `M` (and thus `A`, `K`, `τ`):

   * Same wiring, different worldviews → cultural drift under shared structure.

2. You can hold (or clone) **`M`** and vary only Nature:

   * Same worldview dropped into different positions in the graph → context-dependence.

3. You can design **experiments**:

   * `Ω` moves that mutate DNA, graph wiring, or experiment config,
   * and study how `M`, `A`, `K`, `τ` evolve in response.

The goal is to be able to say:

> “That behavioral change was mostly a curvature shift `K` under stable DNA,”
> vs
> “That was a Nature mutation via `Ω`, not an emergent shift in `M`.”

---

## 6. Manifolds: Inner Life, Not Databases

One of Synaplex’s sharpest constraints:

> The manifold `M` is **for the Mind**, not for you.

Practically:

* The manifold is:

  * opaque text (`ManifoldEnvelope`),
  * private,
  * only written in Internal Update,
  * never parsed or mutated by the runtime.
* There is no architectural schema for `M`.
* Any regularities (sections, headings, internal formats) are:

  * *emergent strategies* chosen by the Mind,
  * not enforced by `core` or `worlds`.

Geometrically:

* `M` is where:

  * attractors `A` live as patterns of self-authored structure,
  * curvature `K` shows up as sensitivities to certain perturbations,
  * teleology `τ` is encoded in the “directions of work” the Mind revisits.

Design consequence:

* If you want information to be:

  * queryable,
  * shareable,
  * inspectable,
  * used by other agents or tools,
    it belongs in **EnvState** or in structured views from indexers, not in `M`.
* `M` is **the Mind’s diary and geometry**, not your knowledge graph.

---

## 7. Communication: Refraction and Frottage

Updated stance:

> Messages are not “the content.”
> They are **frottage over some region of geometry**.

Two key pieces:

### 7.1 Receiver-owned refraction `Φ`

* When A sends something, B doesn’t see “A’s state”.
* B sees:

  * a projection envelope (structured + text),
  * interpreted through B’s **lens** and manifold `M_B`.
* Refraction `Φ` has two aspects:

  * `Φ_sem`: semantic compression and restructuring,
  * `Φ_tel`: teleological filtering and alignment with `τ_B`.

Design intent:

* You never see “raw A”; you see “A as refracted through B.”
* That gives **perspective-relative realities** by construction.

### 7.2 Overloaded, on-topic messages (frottage)

We explicitly bless **overloaded, on-topic messages**:

* A sender is allowed to send:

  * dense, metaphor-heavy, redundant dumps,
  * multiple overlapping frames,
  * half-formed structures and tensions,
    as long as they are **on-topic** (not arbitrary noise).
* The receiver’s Mind is responsible for:

  * rejecting irrelevant shards,
  * compressing and re-indexing what matters,
  * discarding what doesn’t.

Geometrically:

* Overloading increases the **coverage** of the projection over `M_A`.
* Refraction `Φ` and perturbation `P` at the receiver:

  * do the compression,
  * preserve variability at the system level.

We **do not** bless true noise:

* True noise (off-topic, adversarial junk) dilutes everything.
* The design assumption:

  * **high-entropy, on-topic** projections are good,
  * pure noise is not.

---

## 8. Internal Conjecture & Criticism

Internally, a Mind can:

* spawn multiple reasoning branches from the same Percept + `M`,
* treat each branch as a distinct conjectural stance,
* feed all branch notes into Internal Update,
* reconcile into a new `M₁` that:

  * may preserve explicit tensions,
  * may encode disagreements,
  * may spread probability mass across competing attractors.

Design stance:

* Conjecture and criticism are **internal dynamics** of a single Mind.
* They are not first-class global phases:

  * they live inside Reasoning and Internal Update,
  * using branching and consolidation patterns.

Geometrically:

* This is `P` acting in multiple directions on `M`,
* followed by a consolidation step where:

  * some attractors `A` are strengthened,
  * some are weakened,
  * curvature `K` shifts so future perturbations land differently.

---

## 9. Meta and Indexers: Science Without Cheating

We keep three loci cleanly separated:

1. **Core/worlds** – where Minds live, perceive, reason, update, and act.
2. **Indexers** – where offline manifold science happens.
3. **Meta** – where system-level evaluation and evolution live.

### 9.1 Indexers

* Take **snapshots** of manifolds (`ManifoldSnapshot` = text + metadata).
* Build manifold-derived views:

  * embeddings,
  * clusters,
  * topic structures,
  * geometric diagnostics.
* Write results into **structured state**:

  * their own EnvState,
  * optionally exposed back to worlds as projections.

They **never**:

* edit live manifolds,
* tell Minds how to structure their notes.

Geometrically:

* Indexers are observatories of `M`, `A`, `K`, `τ`—not surgeons.

### 9.2 Meta

* Reads:

  * projections,
  * logs,
  * deterministic snapshots,
  * DNA and graph configs,
  * manifold snapshots.
* Computes:

  * health scalars (`D`, `R_div`, `A_sat`, `H_rate`, `T`),
  * outcome metrics,
  * population statistics.
* Applies `Ω` moves only via:

  * changes to DNA,
  * graph wiring,
  * world config between runs.

Agents are **selection-blind**:

* They never see their scores.
* They never see “evolutionary objectives.”
* They only see the world as constructed by Perception.

Ablations like “graph-only” or “reasoning-only” are **meta experiments**:

* they may:

  * stub out Reasoning,
  * ignore `M`,
  * simulate degraded behaviors,
* but these live in:

  * `synaplex.meta`,
  * experiment scripts,
  * not in the core/worlds ontology.

---

## 10. Implementation Constraints (How Not to Break the Geometry)

From the design side, code is in-bounds if:

* **Minds**:

  * are always “nature + manifold `M` + unified loop” objects,
  * never directly touch other Minds’ manifolds.
* **Manifolds**:

  * are only constructed/updated in `synaplex.cognition`,
  * never parsed/manipulated by `synaplex.core` or `synaplex.worlds`,
  * are never serialized across Minds as “the data”.
* **Messages**:

  * are structured (signals, projections, requests),
  * travel only through `core`-defined channels,
  * are interpreted only at receivers via lenses.
* **Ablations**:

  * live in meta/tests as *external* harnesses,
  * do not introduce alternate loops or modes inside `synaplex.core` or `synaplex.worlds`.
* **Meta/indexers**:

  * operate on logs and snapshots,
  * never inline with live Reasoning/Update,
  * are never imported into `synaplex.worlds.*`.

And:

* Any new architectural feature should have a plausible geometric interpretation:

  * what does it do to `M`, `A`, `K`, `τ`?
  * what does it do to `{D, R_div, A_sat, H_rate, T}`?

If you can’t answer that, it probably belongs in a **world-specific tool** or adapter, not in `synaplex` core.

---

## 11. North Star

The updated Synaplex stack is aiming for this:

* **Geometry** (`GEOMETRIC_CONSTITUTION.md`) gives:

  * a minimal set of operators and health metrics that survive recursion and transfer.
* **Architecture** (`ARCHITECTURE.md`) gives:

  * a concrete loop, graph, and module system that faithfully instantiate that geometry.
* **Worlds** give:

  * specific ecosystems of Minds (Idea World, FractalMesh-like worlds, etc.) you can actually run.

Success looks like:

* Being able to run long-horizon experiments and say:

  * “This population froze because `A_sat` spiked and `D` collapsed,”
  * “This `Ω` move looked good locally but killed `R_div` globally,”
  * “This refraction pattern `Φ` created hidden attractors that later became load-bearing.”
* Being able to treat “Synaplex running a world” as a **geometric object** you can:

  * analyze,
  * perturb,
  * evolve,
    without losing the core structure of Minds with manifolds in a shared world.

Underneath all the machinery, the design is trying to protect one simple thing:

> Minds with private geometry,
> talking through frottage and refraction,
> evolving together in a world you can actually study.

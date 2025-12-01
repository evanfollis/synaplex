# IDEA_WORLD — A Synaplex World for Evolving Ideas

> **Idea World** is a Synaplex world whose sole purpose is to scale and refine a single human’s ideas over time.
> It is both:
>
> * a *real world* you can run, and
> * a *template* for building other Synaplex worlds.

Idea World treats your cognitive life as a population of Minds that:

* metabolize your **brain dumps** into evolving manifolds,
* generate and refine **attractors** (themes, specs, patterns),
* explore and reframe ideas under different **curvatures**,
* and, when permitted, trigger **holonomy** via execution tools (e.g., Cursor, scripts) to produce concrete artifacts.

It is explicitly a **strange loop**:
Idea World is implemented in Synaplex *and* serves as the canonical example for how to build any Synaplex world.

---

## 1. Geometric View

Idea World is defined directly in terms of the geometric primitives:

* **M (Manifold)** – each Mind’s evolving internal worldview about your ideas.
* **A (Attractors)** – stable-ish patterns:

  * recurring themes,
  * proto-theories,
  * reusable design moves,
  * concrete specs that keep resurfacing.
* **K (Curvature)** – where your conceptual space is:

  * highly sensitive and generative (high K),
  * vs. crystallized and robust (low K).
* **P (Perturbations)** – all the ways the world kicks the manifolds:

  * your raw notes (phone dumps, frottage blobs),
  * external resources,
  * contradictions, failures, and surprises,
  * feedback from executed experiments.
* **H (Holonomy)** – irreversible-ish moves:

  * code written or modified,
  * repos reshaped,
  * docs committed,
  * scripts run, experiments launched.
* **Φ (Projection / Refraction)** – how Minds see each other’s state:

  * “Architect Mind’s view of Explorer Mind,”
  * “Executor Mind’s distillation of Architect’s plan,”
  * always transformed through the receiver’s lens.
* **Ω (Meta-operators)** – edits to:

  * DNA templates,
  * which Minds exist,
  * how they are wired,
  * which execution channels are enabled.
* **Ξ (Forgetting / Dissipation)** – intentional decay:

  * pruning stale ideas,
  * compressing dead branches,
  * freeing capacity in the manifolds.

Everything in Idea World is a statement about how these primitives are instantiated and interact.

---

## 2. What Idea World Is For

Idea World has one job:

> Turn your messy, ongoing stream of thought into
> a living geometry of ideas **plus** empirical feedback loops.

Concretely, it aims to:

* capture your ideas in **M** (across multiple Minds, not just one),
* let different Minds form and test **A** under different **K** regimes,
* use **Φ** to cross-pollinate perspectives (PM ↔ Research ↔ Critic),
* and use **H** to move from “epistemic poetry” to “concrete artifacts.”

Success criteria (informal):

* Ideas become *sharper* when they circulate.
* More ideas reach an executable form without your direct micromanagement.
* The system can be used as a **template** for other domains (e.g., research orgs, product design, etc.).

This world is intentionally **non-financial** and **personal**:
no client, no PnL, no external KPI. The only metric is epistemic reach + meaningful execution.

---

## 3. Mind Types (DNA Classes)

Idea World defines a small cast of role patterns. Each is a distinct **DNA template**; nurture (M) evolves over time.

### 3.1 IdeaPMMind

> Treats your long-horizon goals and projects as a portfolio of ideas.

* **M** – tracks:

  * active “idea threads,”
  * their maturity,
  * dependencies,
  * and perceived importance.
* **A** – attractors are:

  * “this idea has legs,”
  * “this is a core primitive,”
  * “this belongs in X project.”
* **K** – curvature modulates:

  * how quickly it reweights projects when new perturbations arrive.
* **P** – main inputs:

  * your brain dumps,
  * projections from ResearchMinds,
  * CriticMind’s red flags,
  * execution results (H feedback).
* **H** – triggers:

  * “promote idea to spec,”
  * “spawn execution task,”
  * “merge idea into project X documentation.”

This is your “Idea Portfolio Manager.”

---

### 3.2 ResearchMind

> Explores the local neighborhood of an idea, hunts for structure, analogies, and missing operators.

* **M** – holds:

  * variations on a theme,
  * references,
  * attempted formalisms,
  * partial taxonomies.
* **A** – attractors are:

  * recurring decompositions,
  * candidate operator sets,
  * stable metaphors that keep working.
* **K** – tuned relatively high:

  * quick to deform its M when a new perturbation suggests a better framing.
* **P** – main inputs:

  * fragments around a theme,
  * cross-projections from IdeaPMMind and CriticMind,
  * your external reading.
* **H** – triggers:

  * “produce a more formal, geometric description,”
  * “draft a GEOMETRIC_CONSTITUTION revision proposal,”
  * “sketch a minimal operator basis for this sub-domain.”

Multiple ResearchMinds may exist (e.g., “geometry,” “agent orchestration,” “execution frameworks”).

---

### 3.3 CriticMind

> Specializes in collapse detection and bullshit filtration.

* **M** – models:

  * common failure modes,
  * previous illusions (“too good to be true” episodes),
  * patterns of overreach.
* **A** – attractors:

  * “this is unfalsifiable,”
  * “this is aesthetic but empty,”
  * “this overfits an anecdote.”
* **K** – high around:

  * claims of inevitability,
  * global priors (“geometry is the *only* language”).
* **P** – inputs:

  * specs from ResearchMind,
  * enthusiasm spikes from IdeaPMMind,
  * past failures.
* **H** – triggers:

  * “flag idea as high-risk epistemically,”
  * “demand a minimal experiment,”
  * “downgrade idea until we get evidence.”

CriticMind doesn’t kill ideas; it **bends** their trajectory toward tests.

---

### 3.4 ExecutionMind (Executor Shim)

> Bridges from ideas to Cursor/scripts/notebooks. It is the main **H**-emitter.

* **M** – tracks:

  * what has been attempted,
  * success/failure patterns,
  * execution environments, constraints.
* **A** – attractors:

  * reusable execution patterns,
  * “safe” scaffolds for experiments,
  * templates for repos, scripts, tests.
* **K** – higher for:

  * cheap, reversible experiments,
  * lower for:
  * destructive or high-cost operations.
* **P** – inputs:

  * “execution-ready” attractors from IdeaPMMind,
  * test plans from ResearchMind,
  * guardrails from CriticMind.
* **H** – triggers:

  * cursor/other execution calls,
  * code edits,
  * test runs,
  * artifact creation (e.g., new docs, notebooks).

**Important:** ExecutionMind is *not* allowed to invent its own high-level goals. It serves IdeaPMMind + ResearchMind + CriticMind.

---

### 3.5 GeometryStewardMind (Optional but Powerful)

> Guards the **GEOMETRIC_CONSTITUTION** and Ω moves.

* **M** – holds:

  * the evolving understanding of your geometry,
  * past Ω moves and their consequences.
* **A** – attractors:

  * “this change preserves commutators/tensions,”
  * “this change reduces expressivity or diversity.”
* **K** – very high near:

  * changes that reduce the number of meaningful tensions,
  * collapsing multiple operators into one vague blob.
* **P** – inputs:

  * proposed spec changes,
  * observed drift in worlds,
  * cross-world comparisons (later).
* **H** – triggers:

  * accepted constitutional changes,
  * spawning new Minds (Ω that add DNA templates),
  * deprecating roles or lenses.

This is where the **Synaplex strange loop** is anchored: the world that builds worlds.

---

## 4. Perception, Reasoning, Internal Update in Idea World

All Minds obey the unified loop; Idea World only configures how `P` and `H` behave.

### 4.1 Perception

Percept construction uses:

* your new dumps (P),
* other Minds’ projections (Φ),
* logs of H moves (execution history),
* deterministic state (e.g., doc indexes, repo summaries).

Each Mind’s *lens* selects and shapes:

* which ideas are “foreground,”
* how confidence is represented,
* how risk/novelty is exposed.

No manifold access happens here.

---

### 4.2 Reasoning

Each Mind:

* uses `Percept + M` (if enabled) to:

  * explore hypotheses,
  * spawn internal branches (explorer/skeptic),
  * propose `P` to other Minds (requests),
  * propose `H` candidates to ExecutionMind.
* may generate:

  * new attractors in its internal picture,
  * new tensions (“this contradicts X”).

Reasoning is where “epistemic poetry” lives—but with GeometrySteward + CriticMind ensuring it doesn’t detach from testability forever.

---

### 4.3 Internal Update

Each Mind writes to its manifold:

* updates weights on existing A,
* changes local curvature K,
* records new tensions to revisit,
* archives or prunes via Ξ.

This is the only write path to M.

The implementation should treat this as a **sacred ritual**: short, explicit, well-tested.

---

## 5. Holonomy & Execution

Holonomy in Idea World is wired to concrete substrate(s):

* Cursor-like agents (code edits, file creation),
* local scripts,
* notebook execution,
* API calls for experiments.

Rules of thumb:

* **H moves must be observable.**

  * logged, diff-able, replayable.
* **H moves are downstream of A.**

  * we act on attractors, not random sparks.
* **H moves feed back as P.**

  * Execution results become perturbations to all relevant Minds.

In other words:

> H closes the loop from idea → world → new idea.

---

## 6. Ω and Ξ in Idea World

### Ω — Meta changes

In this world, Ω moves include:

* adding/removing DNA templates,
* changing which Minds exist,
* changing allowed H channels,
* tuning Ξ rates (aggressiveness of forgetting),
* adjusting branching strategies.

Ω should be:

* proposed by Minds (esp. Research + GeometrySteward),
* approved by you or by GeometrySteward rules,
* logged as first-class events.

### Ξ — Forgetting

Ξ is implemented as:

* manifold pruning policies,
* “fadeout” of low-energy attractors,
* periodic compression passes.

Idea World needs Ξ to avoid turning into an unstructured idea graveyard.

---

## 7. Logging & Documentation as First-Class Holonomy

Because this world is also the **template for Synaplex worlds**, we treat documentation as holonomy:

* Changes to:

  * `GEOMETRIC_CONSTITUTION.md`
  * `ARCHITECTURE.md`
  * `README.md`
  * `docs/worlds/IDEA_WORLD.md`
  * `docs/worlds/WORLD_TEMPLATE.md`
* are themselves **H moves initiated and justified by Minds**.

This gives us:

* a live audit trail of the strange loop,
* a way to see which ideas made it all the way from:

  * spark → attractor → spec → code → doc.

---

## 8. File Layout (Idea World)

Recommended structure:

```text
docs/
  worlds/
    IDEA_WORLD.md        # This file: spec + rationale
    WORLD_TEMPLATE.md    # General template for Synaplex worlds

synaplex/
  worlds/
    idea_world/
      __init__.py
      config.py          # Wiring: which Minds, edges, loop configuration
      dna_templates.py   # IdeaPMMind, ResearchMind, CriticMind, ExecutionMind, GeometryStewardMind
      lenses.py          # Percept/projection shapes for each Mind type
      agents.py          # Concrete Mind classes using core/cognition primitives
      tools.py           # Execution shims (Cursor, scripts, notebooks)
      bootstrap.py       # Entry points to spin up Idea World
```

Idea World should be the first “golden” world that all future worlds can look at.

---

## 9. How Idea World Becomes a Template

The companion `WORLD_TEMPLATE.md` (below) generalizes this pattern:

* same geometric primitives,
* same Mind taxonomy pattern,
* but filled in for arbitrary domains (finance, org design, research labs, etc).

Idea World = “reference implementation”
World Template = “copy this, replace the nouns, keep the geometry.”

---

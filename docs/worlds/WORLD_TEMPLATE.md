# WORLD_TEMPLATE — Skeleton for a Synaplex World

> This document is a template for defining a Synaplex world.
> Replace domain-specific nouns, keep the geometric structure.

---

## 1. Domain & Purpose

* **World name:** `YOUR_WORLD_NAME`
* **Domain:** e.g., research org, product development, personal knowledge, etc.
* **Primary objective:** e.g., “evolve research programs,” “stabilize product bets,” “amplify a person’s thinking.”

---

## 2. Geometric Instantiation

For this world:

* **M (Manifolds)** = what are Minds’ internal worldviews *about*?
* **A (Attractors)** = what kinds of stable patterns matter here?
* **K (Curvature)** = where is the system brittle vs flexible?
* **P (Perturbations)** = what counts as a “kick” (events, data, inputs)?
* **H (Holonomy)** = what are irreversible-ish actions in this domain?
* **Φ (Projection)** = how do Minds see each other? lens semantics.
* **Ω (Meta)** = how can the rules of the world change?
* **Ξ (Forgetting)** = how do we decay/prune internal structures?

Fill these in with domain-specific answers.

---

## 3. Mind Types (DNA Templates)

List the primary Mind roles:

For each Mind type:

* **Name** – e.g., `ProgramPMMind`, `ResearchMind`, `RiskMind`, `ExecutionMind`, `StewardMind`.
* **M** – what its manifold tracks.
* **A** – its main attractors.
* **K** – regions of high vs low curvature.
* **P** – what perturbations it primarily ingests.
* **H** – what actions it is allowed to trigger.
* **Φ patterns** – who it listens to and how it refracts them.

---

## 4. Loop Configuration

Describe how the unified loop is realized:

* **Perception:**

  * What structured inputs exist (signals, data feeds, logs)?
  * How do lenses shape them?
* **Reasoning:**

  * How do Minds branch (if at all)?
  * Are there canonical reasoning styles?
* **Internal Update:**

  * How is M revised each tick?
  * Are there special Ξ/pruning rules?

Specify which world modes are supported:

* graph-only,
* reasoning-augmented,
* manifold-enabled.

---

## 5. Holonomy & Execution

Define:

* what counts as H in this world (deployments, policies, trades, docs, etc),
* how H is triggered,
* how results feed back as P.

---

## 6. Ω and Ξ Policies

* **Ω:** who/what can:

  * add/remove Mind types,
  * change DNA templates,
  * alter graph structure,
  * change execution permissions?

* **Ξ:** forgetting rules:

  * when and how manifolds are pruned,
  * how attractors decay or compress.

---

## 7. File Layout

Document where this world lives in the repo:

```text
synaplex/worlds/YOUR_WORLD_NAME/
  config.py
  dna_templates.py
  lenses.py
  agents.py
  tools.py
  bootstrap.py
docs/worlds/YOUR_WORLD_NAME.md
```

---
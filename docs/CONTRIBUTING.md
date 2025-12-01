# **CONTRIBUTING.md**

Thank you for contributing to **Synaplex**.
This project is not a typical software library. It is a **cognitive substrate** that depends on strict architectural boundaries and conceptual clarity.

This document explains **how to contribute responsibly**—whether you are a human developer or an LLM generating code.

---

# 1. Ground Rules

Before modifying any code, contributors must:

1. **Read the following documents (in this order):**

   * `README.md` — mental model & unified loop
   * `ARCHITECTURE.md` — canonical structure & invariants
   * `GEOMETRIC_CONSTITUTION.md` — seams, lenses, and separation principles
   * `DESIGN_NOTES.md` — intent, philosophy, research frame

2. **Do not introduce new concepts that conflict with these documents** unless you first update the documents themselves (see Section 3).

3. **Do not treat Synaplex as a workflow engine or orchestration layer.**
   The architecture is built for research on distributed cognition, not process automation.

4. **Never collapse nature and nurture.**

   * DNA, lenses, deterministic structure → nature
   * manifold, internal reasoning patterns → nurture
     These must remain separable in code and in design.

5. **Never allow raw manifold text to leak into core/worlds.**
   It is private to each mind.

6. Before making architectural changes, **contributors must read GEOMETRIC_CONSTITUTION.md.** 
   It defines the geometric rules—the seams, lenses, and separation principles—that all modules must obey.

---

# 2. Invariants to Respect

Synaplex enforces a strict ontology. Contributors must preserve the following invariants:

## 2.1 Nature / Nurture Boundary

* Only `synaplex.cognition` may access or modify manifolds.
* `core` and `worlds` must not read or manipulate manifold content.
* Manifolds must remain **opaque**, self-authored text.

## 2.2 Unified Cognitive Loop

Every agent implements:

> **Perception → Reasoning → Internal Update**

There are no alternate loops, no layered stacks, no separate pipelines.
Worlds **configure** the environment; they do not redefine cognition.

## 2.3 Receiver-Owned Semantics

* All projections are interpreted **via the receiver’s lens**.
* Senders do not tailor messages per receiver.
* No global schemas for meaning.

## 2.4 Meta Isolation

`synaplex.meta` must never be imported into:

* `synaplex.worlds.*`
* `synaplex.core`
* `synaplex.cognition`

Meta logic influences agents **only** by changing DNA, world configs, or graph structure.

## 2.5 One-Way Manifold Export

* Live manifolds → snapshots → indexers/meta
* Never the reverse.
* Indexers write *views* into their own deterministic state, not back into live manifolds.

## 2.6 Deterministic State is Not a Manifold

If a feature is structured, interpretable, or shared, it belongs in:

* `EnvState`,
* projection payloads,
* indexer views.

Do **not** push structured information into a manifold.

---

# 3. How to Propose Changes

Modifying Synaplex’s architecture requires a **spec-first workflow**.

### Step 1 — Update the architecture documents

Before writing code:

* Update `ARCHITECTURE.md` if you change:
  loop semantics, message types, boundaries, nature–nurture definitions, invariants.

* Update `DESIGN_NOTES.md` if you change:
  intent, epistemic assumptions, long-horizon research goals, internal dynamics.

* Update `README.md` only when:
  the onboarding mental model must be updated to match the new architecture.

### Step 2 — Only then create or modify code

Once the architecture changes are documented and merged:

* Implement the change under `synaplex/` respecting module boundaries.
* Add tests that enforce the new invariant or boundary.
* Ensure no cross-layer imports break the ontology.

### Step 3 — Run the invariant test suite

Before submitting a PR:

```
pytest tests/
```

The suite includes checks for:

* manifold access violations
* import layering
* meta isolation
* projection semantics
* one-way manifold export
* loop consistency

---

# 4. How to Add a New World

Worlds are *pure configurations* of the substrate.

To add a world:

1. Create a new directory under `synaplex/worlds/<world_name>/`

2. Add:

   * `config.py` — agent set, graph wiring, runtime settings
   * `dna_templates.py` — DNA blueprints
   * `lenses.py` — perceptual transforms for the domain
   * `agents.py` — factories constructing Minds + DNA
   * `tools.py` (optional) — domain integrations
   * `bootstrap.py` — entrypoint for running this world

3. Worlds **must not**:

   * modify core semantics,
   * redefine the cognitive loop,
   * access manifolds directly,
   * import `synaplex.meta`.

Worlds are **plug-ins**, not forks of the substrate.

---

# 5. How to Add Tools or APIs

Tools live in two places:

* `synaplex.cognition.tools` for LLM-facing tool wrappers
* `synaplex.worlds.<world>.tools` for domain-specific integrations

Tools must:

1. expose minimal, stable interfaces,
2. surface results in **structured form**, not unparsed text,
3. avoid leaking sensitive/worldview information back into the environment.

Tools do **not** access manifolds.

---

# 6. How to Add or Modify LLM Behavior

LLM calls are restricted to the `synaplex.cognition` module:

* only the Mind abstraction may load/save manifolds,
* prompts must not mention schemas for manifolds,
* prompts must not ask minds to “summarize,” “compress,” “clean,” or “organize” worldview text,
* prompts must not collapse diversity across minds.

Branching (explorer/skeptic/etc.) should use `branching.py` and must reconcile internally.

---

# 7. Tests and Boundary Enforcement

The philosophy:
**A boundary that is not enforced by tests will eventually be violated.**

Before submitting code, ensure tests cover:

* **import boundaries** — core → cognition → worlds (never reverse)
* **manifold purity** — cognition-only access
* **meta isolation**
* **export path** — snapshots only
* **projection semantics** — no raw manifolds
* **loop shape** — every tick must run Perception → Reasoning → Internal Update

A PR lacking test coverage for a new invariant will not be accepted.

---

# 8. Style and Code Standards

### 8.1 Clarity Over Cleverness

The architecture is the clever part.
The code should be boring, explicit, and readable.

### 8.2 Strong Typing

Use `typing` and dataclasses throughout.

### 8.3 Pure Functions in Core

`core` should be deterministic and side-effect minimal.

### 8.4 Manifold Text is Sacred

Never reformat, sanitize, or restructure a manifold unless explicitly in an offline indexer.

### 8.5 No Hidden Channels

Agents must not communicate:

* through shared globals,
* via side-loaded files,
* by smuggling worldview text into structured fields.

All communication flows through the message graph.

---

# 9. Contributions From AI Assistants

For LLM contributors:

* Do not “optimize” by merging layers or collapsing concepts.
* Do not hallucinate new abstractions outside the approved ontology.
* Always preserve:

  * unified loop
  * nature/nurture separation
  * receiver-owned semantics
  * manifold purity
  * meta isolation
* When unsure, ask for clarification or propose a spec update.

---

# 10. Philosophy of Contribution

Synaplex is a research substrate.
Its integrity matters more than feature velocity.

**Contribute carefully, humbly, and structurally.**

The architecture exists to protect a long-horizon research agenda.
Changes must reinforce that agenda—not accidentally undermine it.

---
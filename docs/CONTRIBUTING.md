# **CONTRIBUTING.md**

Thank you for contributing to **Synaplex**.
This project is not a typical software library. It is a **Material Substrate** for distributed cognition that depends on strict architectural boundaries and conceptual clarity.

This document explains **how to contribute responsibly**—whether you are a human developer or an LLM generating code.

-----

# 1\. Ground Rules

Before modifying any code, contributors must:

1.  **Read the following documents (in this order):**

      * `README.md` — mental model & material physics.
      * `ARCHITECTURE.md` — canonical structure & invariants.
      * `GEOMETRIC_CONSTITUTION.md` — The Law of Substrate (Physics \> Geometry).
      * `DESIGN_NOTES.md` — intent, philosophy, research frame.

2.  **Do not introduce new concepts that conflict with these documents.**

      * If the code requires a new physics (e.g., a new operator), update the Constitution first.

3.  **Do not treat Synaplex as a workflow engine.**

      * It is a research platform for **emergent, sedimentary cognition**, not process automation.

4.  **Never collapse Nature and Nurture.**

      * **Nature:** DNA, Lenses, Graph, EnvState (The Hardware).
      * **Nurture:** Substrate `S`, Basins `A`, Viscosity `K` (The Soil).
      * These must remain separable in code and in design.

5.  **Never allow raw Substrate sediment to leak into core/worlds.**

      * The Substrate is private to each mind. It is opaque.

6.  **Respect the Physics.**

      * Do not smooth out the data. We want the bumps.

-----

# 2\. Invariants to Respect

Synaplex enforces a strict ontology. Contributors must preserve the following invariants:

## 2.1 Nature / Nurture Boundary

  * Only `synaplex.cognition` may access or modify **Substrates**.
  * `core` and `worlds` must not read, parse, or manipulate Substrate content.
  * Substrates must remain **opaque, sedimentary text**.

## 2.2 Unified Cognitive Loop

Every agent implements:

> **Interference (Input) → Reasoning (Churn) → Resurfacing (Output)**

There are no alternate loops. No "Fast Path." No "Graph Only" mode in the core.

## 2.3 Receiver-Owned Meaning (Interference)

  * All Textures are interpreted **via the receiver’s Lens**.
  * Senders do not tailor messages per receiver.
  * No global schemas for meaning.

## 2.4 Meta Isolation

`synaplex.meta` must never be imported into `core`, `cognition`, or `worlds`.
Meta logic acts like **Tectonics**: it shifts the ground (DNA/Graph) but does not touch the mind directly.

## 2.5 One-Way Substrate Export

  * Live Substrate → Snapshot → Indexer/Meta.
  * **Never the reverse.** Indexers write *views* into deterministic EnvState, never back into live Substrates.

## 2.6 Deterministic State is Not a Substrate

If a feature is structured, interpretable, or shared (e.g., a count, a tag, a price), it belongs in `EnvState`.
**Do not** push structured information into a Substrate.

-----

# 3\. How to Propose Changes

Modifying Synaplex requires a **spec-first workflow**.

### Step 1 — Update the docs

  * **Physics Change:** Update `GEOMETRIC_CONSTITUTION.md` (e.g., new material property).
  * **Wiring Change:** Update `ARCHITECTURE.md` (e.g., new message type).

### Step 2 — Modify Code

  * Implement changes respecting the **Substrate vs. EnvState** boundary.

### Step 3 — Run Invariant Tests

```bash
pytest tests/
```

Ensure no "Leakage" tests fail. (e.g., Did you accidentally let a World read a Substrate?)

-----

# 4\. How to Add a New World

Worlds are *pure configurations* of the substrate.

To add a world:

1.  Create `synaplex/worlds/<world_name>/`.
2.  Define:
      * `dna_templates.py` (Roles).
      * `lenses.py` (How they see).
      * `agents.py` (Factories).
3.  **Constraint:** Worlds must never import `synaplex.meta` or access `ManifoldStore` directly.

-----

# 5\. How to Add Tools

  * **Standard Tools:** `synaplex.cognition.tools`
  * **World Tools:** `synaplex.worlds.<world>.tools`

Tools return **structured data** (strings/JSON). They do not return "meaning." The Mind must churn the tool output into its own sediment.

-----

# 6\. How to Add or Modify LLM Behavior

LLM calls are restricted to `synaplex.cognition`.

**CRITICAL PROMPT ENGINEERING RULES:**

1.  **Prohibit Summarization.**

      * Never ask the LLM to "summarize," "compress," or "clean."
      * Explicitly forbid bullet points if they reduce entropy.

2.  **Command Frottage.**

      * Instruct the LLM to generate **Textures**: "dense, high-entropy descriptions," "rich prose," "capture the grain and the conflict."

3.  **Preserve Latency.**

      * Instruct the LLM that "contradictions are valid data" and should be preserved in the Substrate.

4.  **No Schemas for Memory.**

      * The Substrate is a blob. Do not try to force it into JSON.

-----

# 7\. Tests and Boundary Enforcement

**A boundary not enforced by tests will be violated.**

Tests must ensure:

  * `core` never imports `cognition`.
  * `worlds` never import `meta`.
  * No one reads the Substrate except the Mind itself during the Reasoning phase.

-----

# 8\. Style and Code Standards

### 8.1 Materiality Over Abstraction

Naming matters. Use `Substrate`, `Texture`, `Lens`, `Viscosity`. Avoid generic terms like `State` or `Message` where specific physics apply.

### 8.2 Substrate Sediment is Sacred

Never reformat, sanitize, or structure a Substrate. It is the soil of the mind; do not pave over it.

### 8.3 No Hidden Channels

Minds talk via Textures and Signals. No global variables. No side-loading.

-----

# 9\. Contributions From AI Assistants

For LLM contributors:

  * **Do not "fix" the mess.** The mess is the feature.
  * **Do not "optimize" for clarity.** Ambiguity is the fuel.
  * **Respect the Physics.** A Substrate is not a Database.
  * When in doubt, ask: *Does this increase or decrease the entropy of the system?* (Target: Increase/Maintain).

-----

# 10\. Philosophy of Contribution

Synaplex is a research substrate.
Its integrity matters more than feature velocity.

**Contribute like a Geologist, not an Architect.**
We are studying how the layers form, not building a skyscraper.
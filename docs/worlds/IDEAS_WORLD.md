# IDEA\_WORLD — A Synaplex World for Evolving Ideas

> **Idea World** is a Synaplex world whose sole purpose is to scale and refine a single human’s ideas over time.
> It is both:
>
>   * A **Material Simulation** you can run.
>   * A **Reference Implementation** for building other Synaplex worlds.

Idea World treats your cognitive life as a **Landscape of Substrates** that:

  * **Metabolize** your brain dumps into evolving sediment.
  * **Churn** latent ideas against each other to create friction and heat.
  * **Resurface** insights as deep Basins (habits) or new Layers.
  * Trigger **Impacts** (tools/execution) to leave permanent scars on the real world.

It is explicitly a **strange loop**:
Idea World is built on Synaplex to evolve the ideas *about* Synaplex.

-----

## 1\. Material View (The Physics)

Idea World is defined directly in terms of the material primitives:

  * **S (Substrate)** – Each Mind’s evolving internal sediment. A dense, opaque history of thoughts.
  * **A (Basins)** – Deep grooves in the sediment:
      * Recurring themes.
      * Proto-theories that refuse to die.
      * "Sticky" metaphors.
  * **K (Viscosity)** – The resistance of the sediment:
      * High $K$ (Granite): The "Critic" who demands hard proof.
      * Low $K$ (Mud): The "Explorer" who adopts every new idea.
  * **P (Impact)** – External forces striking the sediment:
      * Your raw notes (Frottage blobs).
      * Execution results (Compiler errors, test logs).
  * **H (Holonomy)** – Scars on the World:
      * Code committed to git.
      * Files written to disk.
      * Real-world APIs invoked.
  * **$\Phi$ (Interference)** – How Minds see each other:
      * The **Texture** $T$ projected by a Sender.
      * The **Lens** $L$ applied by a Receiver.
      * The resulting pattern of Resonance and Noise.
  * **$\Xi$ (Erosion)** – The natural decay of unvisited paths.

-----

## 2\. What Idea World Is For

Idea World has one job:

> Turn your messy stream of thought into a **Self-Organizing Geology**.

Concretely:

  * Capture your ideas in **S** (across multiple specialized Minds).
  * Let Minds generate friction via **Interference** (The Critic churns against the Explorer).
  * Use **Holonomy** to turn "Epistemic Sediment" into "Artifacts" (Code, Docs).

Success Criteria:

  * Ideas become **denser** (more connected) over time.
  * The system generates **surprising** connections (high Refraction Diversity).
  * The system produces artifacts without you holding the pen.

-----

## 3\. Mind Types (DNA Classes)

Idea World defines a cast of roles. Each is a distinct DNA template with different **Lenses** and **Viscosity**.

### 3.1 The Synthesizer (PM)

> *Role:* The Gardener. *Viscosity:* Medium.

  * **Lens:** Tuned for "Coherence" and "Actionability."
  * **Substrate ($S$):** Tracks maturity, dependencies, and "heat" of ideas.
  * **Basins ($A$):** "This is a project," "This is a core primitive."
  * **Impact ($P$):** Absorbs your brain dumps and projections from Explorers.
  * **Action:** Triggers "Promote to Spec" or "Request Critique."

### 3.2 The Explorer (Research)

> *Role:* The Scout. *Viscosity:* Low (Mud).

  * **Lens:** Wide-angle, tuned for "Novelty" and "Analogy."
  * **Substrate ($S$):** A chaotic mix of half-baked theories, references, and "what ifs."
  * **Basins ($A$):** Recurring metaphors, candidate taxonomies.
  * **Impact ($P$):** Absorbs fragments, random reading, and cross-projections.
  * **Action:** Generates high-entropy **Textures** (Frottage) to inspire others.

### 3.3 The Critic (Risk)

> *Role:* The Geologist. *Viscosity:* High (Granite).

  * **Lens:** Narrow, tuned for "Contradiction," "Failure Modes," and "Overreach."
  * **Substrate ($S$):** A catalog of fallacies, past failures, and rigour constraints.
  * **Basins ($A$):** "This is unfalsifiable," "This is just aesthetics."
  * **Action:** Projects **Resistance Textures** that force other minds to harden their arguments.

### 3.4 The Executor (Shim)

> *Role:* The Hand. *Viscosity:* Variable.

  * **Lens:** Tuned for "Instructions" and "Specs."
  * **Substrate ($S$):** Execution logs, error patterns, environment constraints.
  * **Holonomy ($H$):**
      * Writes code (Cursor).
      * Runs scripts.
      * Commits docs.
  * **Invariant:** It never invents goals. It manifests the sediment of others.

### 3.5 The Steward (Meta)

> *Role:* The Tectonic Shift.

  * **Lens:** Tuned for "System Health" (Diversity, Stagnation).
  * **Action:** Triggers $\Omega$ moves (e.g., "Spawn a new Explorer," "Kill this edge").
  * **Goal:** Prevent the system from calcifying into a single worldview.

-----

## 4\. The Loop in Idea World

All Minds obey the Unified Loop.

### 4.1 Interference (Input)

  * Minds project **Textures** (messy dumps).
  * Receivers apply **Lenses**.
  * Result: A Percept where "signal" is highlighted but "noise" is visible.

### 4.2 Reasoning (Churn)

  * The Mind grinds the Percept against its current Sediment.
  * The Explorer might branch into "Optimist" and "Abstract" personas to widen the search space.
  * The Critic might branch into "Pedantic" and "Structural" personas to find weak points.

### 4.3 Resurfacing (Update)

  * New thoughts settle.
  * Viscosity adjusts (Surprise softens; Confirmation hardens).
  * A new **Substrate Envelope** is written.

-----

## 5\. Holonomy & Execution

Holonomy connects the Dream to the Real.

  * **Input:** A dense, high-agreement Basin in the Synthesizer's substrate.
  * **Action:** The Executor fires a tool (e.g., `write_file`).
  * **Feedback:** The result (Success/Error) hits the system as a massive **Impact ($P$)**.

> $H$ closes the loop: Idea $\to$ Artifact $\to$ New Reality $\to$ New Idea.

-----

## 6\. $\Omega$ and $\Xi$ (Tectonics & Erosion)

### $\Omega$ (Tectonics)

  * Meta-level changes to the graph.
  * *Example:* "The Critic is ignoring the Explorer. I will force a Subscription edge between them."

### $\Xi$ (Erosion)

  * Natural decay.
  * If a Basin (Idea) isn't visited (referenced) for N ticks, it fills up with silt and disappears.

-----

## 7\. Documentation as Holonomy

Since Idea World is a template:

  * Changes to `IDEA_WORLD.md` or `GEOMETRIC_CONSTITUTION.md` are **Holonomy Events**.
  * The system can write its own manual.

-----

## 8\. File Layout

```text
docs/
  worlds/
    IDEA_WORLD.md         # This spec
    WORLD_TEMPLATE.md     # Generalizable version

synaplex/
  worlds/
    idea_world/
      __init__.py
      config.py           # Wiring (Tectonics)
      dna_templates.py    # Role definitions
      lenses.py           # Optical definitions
      agents.py           # Mind implementations
      tools.py            # Sources of Holonomy
      bootstrap.py        # Big Bang
```

-----

## 9\. How Idea World Becomes a Template

Idea World is the **Reference Implementation**.
To build a new world (e.g., "Finance World"):

1.  Copy `idea_world`.
2.  Keep the Physics ($S, T, \Phi, K$).
3.  Change the Nouns (Roles, Lenses, Tools).
4.  Run.
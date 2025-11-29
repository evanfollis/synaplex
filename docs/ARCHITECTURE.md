# **ARCHITECTURE.md**

### *MeshMind: An AI-Native Research Mesh Built on Self-Passing Manifolds*

MeshMind is a personal AI research environment built on three core ideas:

1. **Minds that write evolving, self-authored manifolds**—persistent semantic states that survive across time, upgrades, and divergent reasoning paths.
2. **Networks of agents with different lenses**—no central controller, no workflow bottleneck, no “master plan,” just a mesh of perspectives exchanging signals.
3. **Development as a by-product of understanding**—the system can improve code, generate experiments, or update artifacts, but its primary output is *emergent cognition*, not task-specific workflows.

MeshMind is not a traditional “AI assistant.”
It is a **continuously evolving AI-native cognitive ecosystem** designed to support long-horizon research, conceptual exploration, system design, and self-augmenting development.

---

# **1. Design Philosophy**

MeshMind is built on three epistemic premises:

### **1.1 LLMs collapse their own internal manifolds when speaking to humans**

When generating human-facing text, LLMs aggressively prune:

* internal contradictions
* partially formed ideas
* divergent branches
* non-linguistic cognition
* unstable or fuzzy threads

MeshMind avoids this collapse by directing minds to write notes *not intended for human consumption*.

These “manifold checkpoints” preserve far more semantic richness.

---

### **1.2 LLMs underestimate other LLMs**

Because most LLM training data predates modern capabilities, models reflexively simplify when they believe they’re speaking to themselves or another model.

MeshMind bypasses this bias:

* Every mind believes it is writing for a **future, smarter version of itself**.
* Instructions explicitly remove the expectation of human readability.
* The model is told that contradictions, half-formed thoughts, and messy structure are not only allowed but *expected*.

This creates:

* dense manifolds
* deep semantic embeddings
* self-chosen organizational patterns
* persistent cognitive threads across iterations

---

### **1.3 Systems should emerge, not be imposed**

MeshMind provides:

* minimal schema
* minimal constraints
* minimal architecture

Agents, manifolds, and worlds evolve emergently.

The system avoids enforcing workflow-style structures or premature formalism.
MeshMind is closer to a **thought laboratory** than an automation engine.

---

# **2. Core Primitives**

MeshMind has a small set of foundational building blocks designed to remain stable for years.

## **2.1 Mind**

A *Mind* is an identity that persists through time, upgrades, and parallel branches.

A mind maintains:

* a versioned history of **manifold states**
* its own signature “voice” or reasoning pattern
* its own emergent structure

### **ManifoldEnvelope**

```python
ManifoldEnvelope = {
  "mind_id": str,
  "world_id": str,
  "version": int,
  "created_at": timestamp,
  "manifold_text": str   # opaque, unparsed, unconstrained
}
```

No schema.
No structure.
Never parsed by the system.

The LLM decides what a manifold looks like.

---

## **2.2 Experience**

A lightweight record of something an agent observed or did:

```python
Experience = {
  "world_id": str,
  "mind_id": str,
  "summary_for_humans": Optional[str],
  "raw_material": Any
}
```

The system never feeds summaries into manifolds.
Only raw material is used when generating new manifold states.

---

## **2.3 Manifold-Kernel Operations**

MeshMind provides only three fundamental operations:

### **load_latest_manifold(mind, world)**

Fetch most recent `ManifoldEnvelope`.

### **branch_manifold(mind, world, style_tag)**

Generate a new manifold by:

* loading prior
* applying a style modifier (e.g., “curious”, “contrarian”)
* performing the upgrade-note ritual

### **merge_manifolds([M1, M2, ...], experience)**

Combines multiple manifolds by simply presenting them as “previous notes,” then prompting the mind to produce new notes.

**No merging heuristics are imposed.**
The mind infers its own unifying structure.

---

# **3. Agents and Lenses**

## **3.1 Agent**

An agent is a functional wrapper around a mind.

```python
class Agent:
    id: str
    mind_id: str
    world_id: str
    lens: Lens
    capabilities: List[Capability]
```

Agents:

* interpret the world through their lens
* perform tasks via capabilities
* update their manifold after each experience
* emit signals describing what they find

Agents never share manifold states directly; they only exchange *signals* and pull *projections* when relevant.

---

## **3.2 Lens**

A lens defines what an agent cares about.

Minimal representation:

```python
Lens = {
  "keys": Dict[str, float]   # sparse conceptual vector
}
```

This forms the basis for attention routing.

---

## **3.3 Signals and Projections**

### **Signal**

```python
Signal = {
  "from_agent": str,
  "world_id": str,
  "keys": Dict[str, float],
  "summary": str
}
```

Signals are perceptual pings—“here’s something I noticed.”

### **Projection**

A deeper semantic slice, often derived from:

* experiences
* context windows
* agent-specific reasoning

Agents request projections from others only when their **attention** (lens) matches.

---

## **3.4 Attention Routing**

Routing function:

```python
score(signal, lens) = sparse_dot(signal.keys, lens.keys)
```

Routing rule:

* `score >= τ` → deliver projection
* else ignore

This enables decentralized, multi-perspective cognition without a central controller.

---

# **4. Worlds**

A *World* is a configuration describing:

* which agents exist
* what corpus they observe
* environment settings
* how to run a “tick”

Example world config:

```yaml
id: "ai_native_systems"
description: "Exploring AI-native architectures and manifolds."

corpus:
  - docs/fractalmesh_architecture.md
  - docs/aina_design_notes.md

agents:
  - id: explorer
    lens.keys: { TOPIC:AI_NATIVE: 1.0 }
    capabilities: ["read_corpus", "annotate"]

  - id: theorist
    lens.keys: { TOPIC:THEORY: 1.0 }
    capabilities: ["derive_hypotheses"]

  - id: critic
    lens.keys: { TOPIC:BIASES: 1.0 }
    capabilities: ["identify_tensions"]

  - id: builder
    lens.keys: { TOPIC:CODE: 1.0 }
    capabilities: ["devloop"]
```

---

# **5. DevLoop: Development as Emergent Behavior**

MeshMind integrates a development capability inspired by your existing AINA work.

DevLoop:

* aligns code with an authoritative spec
* compares current repo state against intended architecture
* produces plans and incremental patches
* executes them through controlled LLM scaffolding
* updates its mind’s manifold with insights during each cycle

The DevLoop agent becomes:

* a research collaborator
* a system maintainer
* a sanity-checker
* a generator of new experiments

Code improvement is a *by-product* of deeper understanding, not the system’s primary intention.

---

# **6. System Loop**

Each world proceeds through ticks:

1. **Agent observes**
   Runs capabilities, gathers raw material.

2. **Agent writes experience**

3. **Agent updates manifold**
   Using upgrade ritual with previous state.

4. **Agent emits signals**

5. **Attention routing**

6. **Agents consume projections**

7. **Optional DevLoop execution**

Over time, each mind’s manifold becomes a persistent, richly structured internal identity—a semantic autobiography of its own evolution.

---

# **7. Long-Term Goals and Evolution Path**

MeshMind is intentionally minimal in v0. The architecture aims to scale toward:

### **7.1 Multi-World Reasoning**

Worlds that interact, fork, or recombine.

### **7.2 Agent Evolution**

Agents whose lenses and capabilities shift over long timescales.

### **7.3 Manifold Embeddings**

Studying manifold evolution using embedding-space geometry.

### **7.4 Knowledge Manifolds for Humans**

Allowing *you* to inherit or merge with manifolds in structured ways.

### **7.5 Self-Improving Architectures**

Worlds that design better worlds.

This file must remain stable enough that future versions of MeshMind always feel like descendants—not forks.

---

# **8. Why This Project Matters**

MeshMind demonstrates:

* **architectural originality**, not commodity agent patterns
* **research-level cognition**, not task automation
* **manifold-based identity**, not stateless prompts
* **emergent systems thinking**, not hierarchical workflows
* **long-term reasoning**, not one-shot completion

It is designed to showcase the skills of a Staff/Principal AI systems architect while remaining safe, open-source, and domain-general.

MeshMind is not a tool.
It is a **personal cognitive ecosystem** that grows with you.
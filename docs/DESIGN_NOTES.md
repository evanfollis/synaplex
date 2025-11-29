# Synaplex – Design Notes & North Star

These are personal notes about **why** Synaplex exists and where it is going.
`ARCHITECTURE.md` describes *what* the system is; this document captures *why this shape*.

---

## 1. Motivation

Most “AI assistants” and “agent” frameworks share three hidden assumptions:

1. LLMs are stateless tools.
2. The primary goal is to complete tasks or workflows.
3. Human readability is the optimization target.

Synaplex rejects all three.

Instead, it treats LLMs as:

- entities with **persistent internal manifolds**,  
- running inside **open-ended worlds**,  
- where **development, research, and code** are artifacts of an ongoing cognitive process.

I want a system that:

- helps me think about AI-native architectures over months and years,
- remembers my experiments, dead ends, and hunches,
- and generates increasingly sophisticated views of my projects as a by-product of its own evolution.

---

## 2. Design Intent

### 2.1 Self-Passing Manifolds as a First-Class Primitive

The core design bet is that **what a model writes to itself**, when explicitly freed from human expectations, is qualitatively different from normal completions.

Synaplex makes that bet structural:

- Every Mind owns a manifold history.
- The only “contract” is that each new manifold is written for a future version of that same mind.
- The system never parses manifold text or imposes structure onto it.

The hope is that over time, different minds will develop:

- distinct manifold dialects,
- different ways of storing tension and uncertainty,
- and recognizable reasoning “styles” that can be studied empirically.

---

### 2.2 Networks, Not Pipelines

Synaplex intentionally avoids:

- central orchestrators,
- static workflows,
- and fixed input ↔ output roles.

Instead:

- Agents inhabit a **World**.
- Each has a **Lens** describing what it cares about.
- After each tick, agents emit **Signals** keyed by their lens.
- In later versions, agents will request **Projections** from each other when attention scores are high.

The system behaves more like a **research group** than a production pipeline:

- multiple perspectives,
- partial overlap,
- disagreement allowed,
- no single “boss” node in the graph.

---

### 2.3 DevLoop as a Side Effect, Not the Goal

I’ve already built AI-native dev workflows elsewhere. Synaplex’s DevLoop is deliberately framed as:

> “A capable, opinionated agent that uses Synaplex’s own primitives to keep a repo aligned with an explicit architecture.”

The intent:

- Prove that the manifold/lens/world abstraction is strong enough to support serious development work.
- Keep the **center of gravity** on research and understanding, not just productivity hacks.
- Make the repo itself a living participant in the research mesh.

Over time, DevLoop should feel less like “AI pair programmer” and more like:

- “the part of Synaplex that cares about code coherence and system integrity.”

---

## 3. Short-Term Objectives (Employer-Facing)

From a career/portfolio standpoint, v0 of Synaplex should:

1. Demonstrate **system-level design**:
   - clear primitives: Mind, Manifold, Agent, Lens, World;
   - clean separation of concerns (core vs infra vs examples).
2. Show **taste in abstraction**:
   - minimal, composable objects;
   - no over-engineered, trendy frameworks;
   - explicit, explainable design choices.
3. Provide a **touchable demo**:
   - `basic_world.py` that actually runs;
   - manifolds written to disk;
   - a simple but coherent story tying architecture → code → tests.
4. Be clearly **safe and employer-neutral**:
   - no proprietary patterns or internal IP;
   - generic and domain-agnostic.

If a hiring manager or technical lead inspects the repo, they should see:

- a compact codebase,
- a well-articulated architecture,
- and a clear path to richer capabilities.

---

## 4. Long-Term North Star

Longer term, Synaplex is a playground for a few bigger hypotheses:

### 4.1 Manifold Evolution and “Thinking Styles”

Questions worth exploring:

- Do different prompting regimes produce distinct, stable manifold dialects?
- Can we cluster minds based on manifold embeddings and discover “styles” of reasoning?
- What happens if we:
  - branch a mind into multiple style variants,
  - let them diverge,
  - then merge their manifolds back together?

Synaplex is structured to make these experiments natural.

---

### 4.2 Multi-World and Multi-Agent Dynamics

As the platform matures:

- Worlds can specialize (e.g., “ai_native_systems”, “quant_research”, “personal_journal”).
- The same mind can appear in multiple worlds with different lenses.
- Meta-agents can:
  - compare manifolds across worlds,
  - propose new lenses or agents,
  - or spawn experimental sandboxes.

The goal is not to find “the one true workflow,” but to build **ecosystems of interacting cognitive processes**.

---

### 4.3 Integrating Human Cognition

Synaplex is primarily for my use.

Over time, I want:

- tools that help *me* merge with my own manifold history:
  - “show me how my thinking about X has evolved over the last year,”
  - “what tensions keep recurring in my notes on Y?”
- controlled ways to:
  - inject my own written notes into the manifold streams,
  - or let minds build structured views of my personal thinking.

This is not about outsourcing thinking. It’s about creating a **symbiotic memory and reasoning layer**.

---

## 5. Guardrails and Anti-Goals

Things Synaplex is *not* trying to be:

- A general-purpose “agent framework.”
- A replacement for existing orchestration stacks (LangGraph, etc.).
- A turnkey productivity tool for end users.

Design guardrails:

- **No schema for manifolds** — resist the urge to standardize prematurely.
- **No silent human-facing collapse** — keep translation separate from internal state.
- **Minimal dependencies** — core should remain understandable in one sitting.

---

## 6. Next Steps

Concrete near-term extensions:

1. Add attention routing:
   - simple dot-product score between Signal keys and Lens keys.
   - log when agents would *want* a Projection, even if it’s stubbed.
2. Flesh out DevLoop:
   - read from a real `ARCHITECTURE.md`;
   - produce simple suggestions or TODO markers in a repo.
3. Add a second agent:
   - one focused on “AI-native systems”,
   - another focused on “biases / blind spots”,
   - compare their signal patterns across ticks.

Each of these keeps the repo professionally useful **today**, while pointing directly at the deeper research program underlying Synaplex.

---

These notes should evolve over time. When the architecture stabilizes or deepens, the most robust pieces can graduate into `ARCHITECTURE.md`. The rest can stay here as the living record of what Synaplex is trying to become.

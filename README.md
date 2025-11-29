# Synaplex

**Synaplex** is an AI-native research environment built around one core idea:

> Minds that pass rich, self-authored manifold states to their future selves — not collapsed, human-optimized summaries.

Where most systems treat LLMs as disposable stateless tools, Synaplex treats them as **persistent minds** with:

- evolving internal manifolds,
- different lenses and roles,
- and a shared world they co-inhabit.

Development, codegen, and workflow automation are *by-products* of this research ecosystem — not the primary goal.

---

## ✨ Project Goals

Synaplex is designed to:

- Explore **self-passing manifold states** as a primitive for long-horizon AI cognition.
- Build a **network of agents** (minds + lenses) with no central controller.
- Use **attention routing** (keys/lenses/values) instead of fixed workflows.
- Provide a **DevLoop agent** that continuously aligns a repo with an explicit architecture, as a side effect of the research loop.

The long-term north star: a personal AI research mesh that grows with its user and produces **ever-richer internal models of the world**, not just answers.

---

## 🧠 Core Ideas

### Self-Passing Manifolds

Each mind maintains a sequence of opaque, LLM-authored checkpoints:

- Written explicitly **for a future, smarter version of itself**.
- Not optimized for human readability.
- Free to keep contradictions, fuzzy threads, and half-baked ideas.
- Reloaded each time the mind “wakes up” in a world tick.

The platform never imposes a schema on these notes. The structure emerges from the model itself.

---

### Agents, Lenses, and Worlds

- **Mind** – an identity with a manifold history.
- **Agent** – a mind + a lens + capabilities in a particular world.
- **Lens** – a sparse conceptual vector of what an agent cares about.
- **World** – a configuration that wires agents to corpora, tools, and each other.

Agents broadcast **Signals** keyed by what they’re seeing, and request deeper **Projections** from each other when their lens aligns.

No single agent is “the center” of Synaplex. The system is a **mesh**, not a pipeline.

---

### DevLoop (AI-Native Development)

Synaplex includes an optional **DevLoop agent** that:

1. Reads a repo snapshot + architecture spec.
2. Identifies misalignment between design and implementation.
3. Plans and applies incremental patches under strict safeguards.
4. Updates its manifold with what it learned each cycle.

The goal isn’t to auto-complete tasks; it’s to create a **self-aware development loop** that learns how the codebase *should* evolve.

---

## 🏗️ Repository Layout

```text
synaplex/
  README.md
  pyproject.toml             # or setup.cfg/requirements.txt if you prefer
  src/
    synaplex/
      __init__.py
      core/
        __init__.py
        types.py             # Lens, Signal, Projection, ManifoldEnvelope
        mind.py              # Mind abstraction & manifold operations
        agent.py             # Agent base class (mind + lens + capabilities)
        world.py             # World runtime & tick loop
      infra/
        __init__.py
        storage.py           # File-based storage for manifolds & worlds
        llm.py               # LLM client interface (pluggable backends)
      examples/
        __init__.py
        basic_world.py       # Minimal demo world with a single agent
  docs/
    ARCHITECTURE.md          # High-level system architecture
    DESIGN_NOTES.md          # Intent, north star, and roadmap
    diagrams/
      synaplex_overview.mmd  # Mermaid diagram: system overview
      agent_interaction.mmd  # Mermaid diagram: agent/world tick
  tests/
    test_smoke.py            # Basic import/run smoke test
````

---

## 🔧 Quickstart (Dev)

> These are suggestions; adjust to your preferred tooling.

```bash
# Clone your repo
git clone https://github.com/<your-username>/synaplex.git
cd synaplex

# Create a venv
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install in editable mode
pip install -e .

# Run the basic example
python -m synaplex.examples.basic_world
```

You should see logs showing:

* a world being constructed,
* a single agent loading/creating its manifold,
* a “tick” where it writes a new checkpoint envelope.

---

## 📚 Documentation

* `docs/ARCHITECTURE.md` – canonical architecture description.
* `docs/DESIGN_NOTES.md` – personal intent, philosophy, and roadmap.
* `docs/diagrams/*.mmd` – Mermaid diagrams for architecture and interactions.

---

## 🧪 Testing

```bash
pytest
```

Initial tests are intentionally minimal (import & smoke). The plan is to grow a test suite that:

* enforces invariants around manifolds,
* ensures phase separation (storage vs routing vs reasoning),
* validates basic world+agent behavior.

---

## ⚖️ License

Choose what fits your goals (MIT, Apache-2.0, etc.). For now, this file assumes you’ll add a proper `LICENSE` once you publish.

---

## 🗺️ Roadmap (Sketch)

* v0.1 – Core primitives: Mind, Agent, World, basic manifold IO.
* v0.2 – Multiple agents + attention routing + simple signals/projections.
* v0.3 – DevLoop agent integrated against `ARCHITECTURE.md`.
* v0.4+ – Multi-world experiments, manifold analysis, and more advanced research tooling.

Synaplex is intentionally small at the start. The goal is to **grow a deep spine**, not a bloated surface area.

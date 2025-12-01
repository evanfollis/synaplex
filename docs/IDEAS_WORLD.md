# Ideas World: Bringing Half-Formed Ideas to Life

The Ideas World is a Synaplex world designed to turn your half-formed ideas into living objects that evolve through agent cognition.

## Concept

Instead of ideas sitting dormant in markdown files, they flow through Synaplex agents:
- **Archivist** reads your markdown ideas and emits signals
- **Architect** builds a manifold about the shape of your idea space
- **Critic** identifies tensions, duplicates, and blind spots

Your ideas become **Experiences** that agents think about, and agents maintain evolving worldviews (manifolds) about your ideas.

## Quick Start

1. **Add ideas to markdown**:
   ```bash
   # Edit or create ideas
   vim docs/ideas/00_inbox.md
   ```

2. **Process ideas through Synaplex**:
   ```bash
   python scripts/process_ideas.py
   ```

3. **Check evolved manifolds**:
   ```bash
   # Manifolds are in manifolds/ideas_world/
   ls manifolds/ideas_world/architect/
   cat manifolds/ideas_world/architect/v1.json
   ```

## Architecture

### Agents

**Archivist** (`archivist`)
- Reads `docs/ideas/*.md` files
- Extracts idea atoms (sections starting with `## Idea:`)
- Emits signals with idea metadata (domain, tags, status, question)
- Subscribed to by: architect, critic

**Architect** (`architect`)
- Maintains manifold about "the shape of my idea space"
- Receives idea signals from archivist
- Builds conceptual maps, clusters, identifies gaps
- Uses `IdeasArchitectLens` to focus on structural elements

**Critic** (`critic`)
- Hunts for tensions, duplicates, low-value ideas
- Receives idea signals from archivist
- Identifies contradictions, redundancies, blind spots
- Uses `IdeasCriticLens` to focus on tensions

### Message Flow

```
Markdown Files
    ↓
Archivist (extracts ideas, emits signals)
    ↓
    ├─→ Architect (builds structure manifold)
    └─→ Critic (identifies tensions manifold)
```

### Idea Format

Ideas in markdown should follow this structure:

```markdown
## Idea: Your Idea Title

- Domain: domain_name
- Tags: [tag1, tag2]
- Status: seed | in_progress | hot | defer
- Question: What question does this address?

Freeform notes...
- rough sketches
- contradictions
- connections
```

The archivist parses this and creates signals like:
```json
{
  "type": "idea",
  "title": "Your Idea Title",
  "domain": "domain_name",
  "tags": ["tag1", "tag2"],
  "status": "seed",
  "question": "What question...",
  "content_preview": "...",
  "source_file": "00_inbox.md"
}
```

## Usage

### Basic Processing

```bash
# Process ideas once
python scripts/process_ideas.py

# Process multiple ticks (let agents think more)
python scripts/process_ideas.py --ticks 5

# Custom directories
python scripts/process_ideas.py \
  --ideas-dir ./my_ideas \
  --store-root ./my_manifolds
```

### Workflow

1. **Dump ideas** into `docs/ideas/00_inbox.md` as they come
2. **Process regularly**: Run the script to let agents think
3. **Organize periodically**: Move ideas to domain files when inbox gets full
4. **Review manifolds**: Check `manifolds/ideas_world/` to see what agents learned

### Programmatic Usage

```python
from synaplex.worlds.ideas_world.bootstrap import bootstrap_ideas_world

# Bootstrap world
runtime = bootstrap_ideas_world(
    ideas_dir="docs/ideas",
    manifold_store_root="manifolds/ideas_world",
)

# Run ticks
for tick in range(10):
    runtime.tick(tick)
    
# Manifolds have evolved!
```

## Extending

### Adding New Agents

Add to `dna_templates.py` and `bootstrap.py`:

```python
# In dna_templates.py
def make_planner_agent(agent_id: str = "planner") -> DNA:
    return DNA(
        agent_id=AgentId(agent_id),
        role="planner",
        subscriptions=[AgentId("architect"), AgentId("critic")],
        tags=["ideas", "planning"],
    )

# In bootstrap.py - create and register planner
```

### Custom Idea Processing

Extend `IdeasArchivistMind` to add custom parsing or signal generation.

### Multi-Personality Exploration

For high-value ideas, you can use branching:

```python
from synaplex.cognition.branching import BranchingStrategy

# Create mind with branching
mind = Mind(
    agent_id=AgentId("explorer"),
    llm_client=llm,
    branching_strategy=BranchingStrategy(
        llm_client=llm,
        default_styles=["explorer", "skeptic", "structuralist"],
    ),
)
```

## Philosophy

The Ideas World embodies key Synaplex principles:

- **Ideas as Experiences**: Not stored text, but flowing through agent cognition
- **Persistent Worldviews**: Agents maintain evolving manifolds about ideas
- **Multi-Perspective**: Architect and critic see ideas differently (lens-based)
- **Emergent Structure**: Schema emerges from agent manifolds, not imposed

Your ideas become **alive** because agents think about them over time, not just store them.

## Next Steps

1. **Reactivation Loop**: Periodically re-process old ideas to keep them active
2. **Idea Index**: Build `ideas_index.json` to track which ideas need attention
3. **Multi-Personality Merges**: For high-value ideas, use branching + merge
4. **Domain Files**: Organize ideas into `ai_native_systems.md`, etc.

## Example

After running `process_ideas.py`, your architect's manifold might contain:

> "The idea space clusters around three domains: AI-native systems (most active), Synaplex evolution (growing), and investment research (seed). There's a tension between wanting to explore many possibilities (archivist signals many seeds) and needing to commit to concrete experiments. The lens market idea connects to attention routing patterns I've seen in other signals..."

This is the agent's evolving worldview about your ideas, not a summary for you - it's for the agent's future self to reason better next time.


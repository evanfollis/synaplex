# Ideas Directory

This directory contains your half-formed ideas that are being processed by Synaplex Ideas World.

## Structure

- `00_inbox.md` - New ideas go here first
- `ai_native_systems.md` - Ideas about AI-native systems, agents, Synaplex
- `synaplex_evolution.md` - Ideas about evolving Synaplex itself
- `investment_research.md` - Financial/research ideas (future)
- `personal_meta.md` - Life rules, career strategy, frameworks (future)

## Idea Format

Each idea should follow this minimal structure:

```markdown
## Idea: Your Idea Title

- Domain: domain_name
- Tags: [tag1, tag2, tag3]
- Status: seed | in_progress | hot | defer
- Question: What question does this idea address?

Your freeform notes here...
- rough sketches
- contradictions
- "this might be dumb but..."
- connections to other ideas
```

## Workflow

1. **Dump ideas** into `00_inbox.md` as they come
2. **Process regularly**: Run `python scripts/process_ideas.py` to let agents think about your ideas
3. **Organize periodically**: Move ideas from inbox to domain files when you have 10-20 accumulated
4. **Let agents evolve**: The architect and critic agents will build manifolds about your idea space

## Status Values

- `seed` - Just planted, not yet explored
- `in_progress` - Actively thinking about this
- `hot` - High priority, needs attention
- `defer` - Good idea but not now

## Processing

To process ideas through Synaplex:

```bash
# Process ideas once
python scripts/process_ideas.py

# Process multiple ticks
python scripts/process_ideas.py --ticks 5

# Use custom directories
python scripts/process_ideas.py --ideas-dir ./my_ideas --store-root ./my_manifolds
```

After processing, check `manifolds/ideas_world/` to see how agents have evolved their worldviews about your ideas.


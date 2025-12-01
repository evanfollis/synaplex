"""
IDEA_WORLD — A geometric Synaplex world for evolving, prioritizing,
and enacting half-formed ideas.

This world is explicitly shaped around the geometric primitives:

- P:   perturbations (idea blobs, execution feedback)
- M:   manifolds (agent worldviews)
- A:   attractors (idea portfolios / focal clusters)
- K:   curvature (sensitivity / volatility of priorities)
- H:   holonomy (irreversible-ish actions / executions)
- Φ:   refraction (lenses, projections, message interpretation)
- Ω:   meta updates to rules / configs (out of band)
- Ξ:   forgetting / decay (handled in agent prompts / Update logic)

Core roles:

- IdeaIngestMind (P-heavy): turns messy text into idea perturbations.
- IdeaArchitectMind (M/A): builds structure over idea space.
- IdeaCriticMind (M/A): hunts tensions, contradictions, redundancies.
- IdeaPMMind (A/K): manages idea portfolio and readiness for execution.
- ExecutionMind (H): owns action plans and logs H into EnvState.
- GeometryStewardMind (M/Φ/Ω): keeps IDEA_WORLD aligned with the
  geometric constitution and proposes Ω moves (spec/config changes).

This module doesn’t define behavior; it just names the world.
"""

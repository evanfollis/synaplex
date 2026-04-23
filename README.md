# synaplex

**synaplex.ai is the system** — a self-learning, self-evolving feedback
system for uncovering the structure of AI systems.

Not a publication. Not a portfolio. The system itself, with a public face
at `synaplex.ai` and an operator face at `command.synaplex.ai`. Pods (atlas
for systematic crypto, skillfoundry for commercial discovery) are
bidirectional exploratory probes; the canon, knowledge system, lab,
publication, and command surfaces are the load-bearing layers.

This repo is the codebase for the system — publication machinery,
evaluation lab, and (in progress) the five-layer operational pipeline that
ingests external signal, converts it into candidate canon envelopes,
validates them, and publishes accepted claims as reader-facing writeups.

## What gets published

- **Editorial**: topology-not-timeline deep-dives on agent platforms, memory
  systems, context infrastructure, orchestration, and the broader structure
  of AI systems. New pieces refine the latent shape; old pieces become
  foundations. Backed by the same canon envelopes the lab emits.
- **Lab**: systematic third-party evaluations, pre-registered as canon
  `Claim`s, executed against bounded task suites, recorded as typed
  `Evidence`, decided via canon `Decision`s that cite all contradictory
  evidence. Replayable and hash-bound.
- **Directory**: quality-graded (not star-count-graded) catalog of agent
  platform components, curated from the lab's evaluation corpus.

## Canon

Every envelope this repo emits conforms to the discovery-framework spec at
`context-repository/spec/discovery-framework/` (v0.1.0, frozen). Object
types: Claim, Evidence, Decision, Promotion, Realization, Policy,
EventLogEntry, ArtifactPointer.

See `CLAUDE.md` for operating principles; `CURRENT_STATE.md` for live
status; `supervisor/decisions/0027-synaplex-is-the-system.md` for the
framing.

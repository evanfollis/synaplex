# Agentstack

Publication + evaluation lab for engineers building agent platforms.

Sibling to `atlas` (crypto research) and `skillfoundry` (commercial discovery).
The third canon instance of the workspace epistemic system.

## What gets published

- **Editorial**: daily news scan + weekly synthesis covering agent harnesses
  (Claude Code, Codex, Aider, OpenDevin, Cline), context systems, memory
  systems (Letta, mem0, MemGPT), integrations (MCP, function calling),
  orchestration (LangGraph, CrewAI).
- **Lab**: systematic third-party evaluations. Every eval is pre-registered as
  a canon `Claim`, executed against a bounded task suite, recorded as typed
  `Evidence`, decided via a canon `Decision` that cites all contradictory
  evidence. Replayable.

## Canon

This repo emits envelopes conforming to the discovery-framework spec at
`/opt/workspace/projects/context-repository/spec/discovery-framework/`. Object
types: Claim, Evidence, Decision, Promotion, Realization, Policy,
EventLogEntry, ArtifactPointer. Spec version `0.1.0`.

See `CLAUDE.md` for operating principles; `CURRENT_STATE.md` for live status.

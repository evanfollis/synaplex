---
name: Agentstack current state
description: Front door for the agentstack publication + evaluation lab. Read first every session.
updated: 2026-04-19
owner: executive (principal: evan)
phase: scaffold
---

# Agentstack — current state

## One-line status

Project approved and scaffolded 2026-04-19; canon adapter work in flight; site + first eval pre-registration pending.

## Strategic context (why this project exists)

Approved plan: `/root/.claude/plans/calm-squishing-peacock.md`.

Third canon instance (after atlas crypto + skillfoundry commercial). Publication + evaluation lab serving engineers building agent platforms. The ~400k-addressable AI-engineer audience has no systematic third-party eval site covering agent harnesses, context systems, memory, integrations, and orchestration. ~12-month window before a labs-backed competitor claims the surface.

Dual purpose: evaluations (a) are differentiated content backed by replayable canon envelopes, (b) feed Evan's own engineering insight, (c) exercise the epistemic layer across a third domain — which is itself the most defensible IP.

## What's done

- 2026-04-19: project approved in plan mode.
- 2026-04-19: agentstack skeleton (CLAUDE.md, CURRENT_STATE.md, README.md, directory layout, git init) — commit `61aa752`.
- 2026-04-19: supervisor governance landed — ADR-0026 + `supervisor/projects/products/agentstack.md`, commit `78a88ae`.
- 2026-04-19: **atlas canon adapter landed** — `src/atlas/adapters/discovery/{emit.py, migrate.py, MAPPING.md}` with 16 pytest cases. Migration backfilled 47 Claims + 123 Evidence + 82 phase-transition EventLogEntries + 1 Policy (tier-mapping). All 0 validation failures against canon v0.1.0 schemas. Atlas regression clean (97/97 tests passing, was 81/81). Commit `<atlas-head>` on atlas/main.
- 2026-04-19: **first lab Claim pre-registered** — `lab/.canon/claims/b7ff216f4eec6e58.json` for the memory-systems-v1 evaluation. Methodology at `lab/evals/memory-systems-v1/methodology.md` hash-bound into the Claim's ArtifactPointer. Validated against canon v0.1.0.

## What's in flight

- **Track 2 (skillfoundry canon adapter)**: next up. Adapter pattern proven by atlas; skillfoundry's markdown → canon mapping is the mirror.
- **Track 3 (editorial launch)**: Astro site scaffold pending. Domain registration (`agentstack.dev`, ~$12/yr CF Registrar) pending principal confirmation of cost. Site can first deploy to `agentstack.pages.dev` without the custom domain.
- **Eval execution (Week 6 per plan)**: memory-systems-v1 is pre-registered; actual runs against Letta / mem0 / MemGPT / Claude-memory APIs are the Week 6 action.

## What's next (blocking / unblocking path)

1. Finish atlas canon adapter + unit tests + dry-run migration (Track 1). Unblocks: skillfoundry adapter pattern, lab adapter pattern.
2. Scaffold Astro site locally (Track 3). Unblocks: domain registration decision, first editorial publish.
3. Pre-register first lab eval (memory systems) as a canon Claim envelope. Unblocks: actual eval run in Week 6.
4. Domain registration for `agentstack.dev` — pending principal cost confirmation (~$12/yr CF Registrar). Site can deploy to `<name>.pages.dev` without this.

## Gates (from plan)

- **Week 4**: atlas adapter valid on all 47 hypotheses; editorial daily scan running ≥10 consecutive days; ≥300 newsletter subs.
- **Week 8**: first eval published with canon ledger entry; ≥1000 subs; ≥3 editorial pieces live.
- **Week 12**: 2 evals published; ≥2000 subs; ≥5 sponsor conversations opened.
- **Week 26**: ≥5000 subs; ≥6 evals; ≥$3k/mo revenue; L2 extraction evaluation complete.

## Active risks

- **Canon adapter surfaces L1 spec gaps** — budget 1 week for spec v0.2.0 via context-repository adversarial review; fallback is thin compatibility layer if more.
- **Editorial-launch timing slippage** — competitors could claim "serious eval" slot during infrastructure weeks. Mitigation: daily scan goes live Week 3 regardless of adapter completion.
- **Methodology credibility** — every eval pre-registered + raw artifacts hash-bound + adversarial review before publish. Invite external review openly.

## Truth sources (non-transcript)

- Canon L1: `/opt/workspace/projects/context-repository/spec/discovery-framework/`
- Approved plan: `/root/.claude/plans/calm-squishing-peacock.md`
- Governance ADR: `supervisor/decisions/0026-agentstack-lab-third-canon-instance.md`
- Project shaping: `supervisor/projects/products/agentstack.md`

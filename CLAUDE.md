# Agentstack — publication + evaluation lab for agent platform systems

context-always-load:
  - CURRENT_STATE.md

## What This Is

The workspace's third canon instance (after atlas for crypto and skillfoundry for
commercial discovery). Two tracks under one brand at `agentstack.dev`:

- **Editorial** — daily news scan + weekly synthesis on agent harnesses, context
  systems, memory, integrations, orchestration. Reader audience: engineers
  building agent platforms.
- **Lab** — systematic third-party evaluations emitted as canon envelopes
  (Claim → Evidence → Decision) per the L1 discovery-framework spec at
  `/opt/workspace/projects/context-repository/spec/discovery-framework/`.
  Each eval has a reader-facing writeup AND an auditable replayable ledger.

## Operating Principles

- **Every lab eval ships as a canon envelope first, writeup second.** The ledger
  entry in `lab/.canon/` is primary; the MDX writeup in `site/src/content/lab/`
  renders from it. No prose-first evals.
- **Pre-register everything.** Claim + falsification_criteria + thresholds land
  in `.canon/` BEFORE any eval run begins. Hash-pinned.
- **Raw artifacts hash-bound.** Every piece of evidence references an
  `ArtifactPointer{content_hash, version, uri}`. Post-hoc edits produce new
  records, not silent overwrites.
- **Adversarial review before every lab publish.** Route to Codex via
  `supervisor/scripts/lib/adversarial-review.sh`. Findings either addressed or
  explicitly accepted in the writeup.
- **No 1:1 services.** Revenue is commoditized only: sponsorships, affiliate,
  paid tier, directory listings, benchmark-as-a-service with
  `Policy.provenance.sponsor` attestation. Per `user_revenue_preference_commoditized.md`.
- **Agentic content generation; human click-send for outreach.** Evan does not
  do outbound personally (FINRA). Daily scan and draft synthesis are
  agent-generated; sponsor emails are agent-drafted with Evan-click-send gate.
- **L1 canon is frozen at v0.1.0.** If a lab eval exposes a canon gap, escalate
  via context-repository adversarial review to bump the spec, not a local
  workaround.

## Structure

```
agentstack/
├── CLAUDE.md            (this file)
├── CURRENT_STATE.md     front door
├── README.md            public README
├── site/                Astro MDX + Tailwind, deploys to CF Pages
│   └── src/content/{editorial,lab,directory}/
├── scan/                daily news harvester (agentic)
├── editorial/           weekly synthesis drafting
└── lab/
    ├── evals/memory-systems-v1/   first eval: memory systems comparison
    ├── canon_emit.py              emits claim/evidence/decision envelopes
    └── .canon/                    canon envelope store (append-only, hash-pinned)
```

## Truth Sources (in descending authority)

1. **L1 canon** at `context-repository/spec/discovery-framework/` — the obligations
   model every envelope conforms to.
2. **Canon envelopes** in `lab/.canon/` — hash-pinned, validated, replayable.
3. **Git history** of this repo.
4. **ADRs** at `supervisor/decisions/`.
5. **Reader-facing writeups** (`site/src/content/`) — derivative, not primary.
   If writeup and canon envelope disagree, canon wins.

Do not treat prior session transcripts or tick-generated narratives as truth.

## Session Model

- **Unit**: an editorial cycle (daily scan + weekly synthesis) OR a lab
  evaluation (pre-register → execute → review → publish).
- **Durable state**: `lab/.canon/`, `site/src/content/`, commits in git.
- **Session transcript** (JSONL) is not durable. Promote load-bearing content
  to canon envelopes or writeups before session end.

## Governance

- **Project tier**: Product (external-facing, commercial-compounding) per
  ADR-0023.
- **Governance ADR**: `supervisor/decisions/0026-agentstack-lab-third-canon-instance.md`.
- **Reflection loop**: 12h per-project reflection (added to `projects.conf`
  after Week 4 gate).
- **Tick cadence**: `workspace-project-tick@agentstack.timer` (to be installed).
- **Adversarial review**: required before every lab eval publish and before
  acceptance of canon-schema bumps.

## Review Standard

A meaningful change is incomplete if it cannot answer:
- which canon obligation it satisfies or improves,
- what evidence or decision surface it affects,
- whether the ArtifactPointer hashes are reproducible,
- what adversarial review said about the methodology.

## Tech Stack

- Site: Astro 4+ with MDX, Tailwind, deployed to CF Pages via Wrangler
- Lab: Python 3.12, src layout, depends on local-editable atlas `StateStore`
  pending L2 `discovery-runtime` extraction (see ADR-0026).
- Scan + editorial generation: Claude Sonnet API, orchestrated via scripts in
  `scan/` and `editorial/`.
- Newsletter: Buttondown (API-driven, free tier).
- Canon validation: Python `jsonschema` + a small in-repo validator that
  enforces the 7 canon.md rules beyond plain JSON Schema.

## What NOT to Do

- Don't publish an eval writeup without the matching canon envelope passing
  validation.
- Don't accept principal statements as "done" without capturing them into ADRs
  or `paid-services.md` in-turn (per `feedback_capture_principal_decisions_in_turn.md`).
- Don't propose 1:1 audits or per-customer services. Pivot to self-serve.
- Don't retry the "MCP-as-brand" positioning. The durable topic is agent
  platform systems — harnesses, context, memory, integrations, orchestration.
- Don't fork atlas's models into a diverged local copy. Use them via local-
  editable install. L2 extraction is deferred but the lab must not bake in
  incompatibilities.

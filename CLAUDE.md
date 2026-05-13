# synaplex — the system

context-always-load:
  - CURRENT_STATE.md

## What This Is

synaplex.ai **is the system** (per ADR-0027, superseding ADR-0026). Not a
parent brand, not a publication, not a portfolio surface. The system itself —
with a public face at `synaplex.ai` (reader + agent-addressable surface) and
an operator face at `command.synaplex.ai`. This repo is the codebase for that
system: publication + lab machinery + (in progress) the five-layer operational
pipeline defined in ADR-0029.

Load-bearing layers (ADR-0027):
1. **Canon** — obligations model at
   `context-repository/spec/discovery-framework/` (v0.1.0, frozen).
2. **Knowledge system** — validated invariants with bidirectional provenance to
   pods (atlas, skillfoundry) and lab reviews.
3. **Lab** — methodology engine. Pressures canon. Validates pod claims.
   Reviews external AI systems. Produces reusable review methodologies that
   re-enter the knowledge system as first-class assets.
4. **Publication + education** — topology (not timeline) projection of the
   knowledge system. New pieces refine latent structure; old pieces become
   foundations.
5. **Command** — operator surface. Internal view of the same system the
   public sees externally.

**Pods** (atlas, skillfoundry) are bidirectional exploratory probes with
lifecycles (emerge → explore → contribute → graduate/deprecate). They are
not sibling products; they are domain applications of the same methodology
this codebase runs.

### Operating pipeline (ADR-0029, proposed)

Five layers, one circulatory system:
- **Layer 1 — Intake**: external-signal ingestion (RSS / arxiv / HN / Reddit /
  GitHub / Substack / podcasts) → content-hash dedup → per-beat scoring → daily
  digests + weekly synthesis. Beats: `agent-platforms`, `systematic-trading`,
  `venture-discovery`. Lives under `intake/`.
- **Layer 2 — Reasoning**: daily per-beat job that loads pod canon state +
  intake synthesis → runs conjecture/criticism → writes candidate Claim /
  Evidence / Decision envelopes to the relevant pod's `.canon/candidates/`.
  Lives under `reasoning/` (not yet built).
- **Layer 3 — Validation**: woven throughout. Adversarial review + counter-
  search + canon integrity. Lives under `validation/` (not yet built).
- **Layer 4 — Presentation**: accepted claims → agent-drafted MDX writeups
  under `site/src/content/`. Principal approve-to-publish gate for brand-
  facing output. Canon envelope primary; writeup derivative.
- **Layer 5 — Friction + self-reflection**: cross-cutting typed events to
  `runtime/friction/events.jsonl`. Classes promote to FR candidates.
  Infrastructure friction and research friction captured the same way.

## Operating Principles

- **Every lab eval ships as a canon envelope first, writeup second.** The
  ledger entry in `lab/.canon/` is primary; the MDX writeup in
  `site/src/content/lab/` renders from it. No prose-first evals.
- **Pre-register everything.** Claim + falsification_criteria + thresholds
  land in `.canon/` BEFORE any eval run begins. Hash-pinned and immutable.
- **Raw artifacts hash-bound.** Every piece of evidence references an
  `ArtifactPointer{content_hash, version, uri}`. Post-hoc edits produce new
  records, not silent overwrites.
- **Adversarial review before every lab publish.** Route to Codex via
  `supervisor/scripts/lib/adversarial-review.sh`. Findings either addressed
  or explicitly accepted in the writeup.
- **No 1:1 services.** Revenue is commoditized only: sponsorships, affiliate,
  paid tier, directory listings, benchmark-as-a-service with
  `Policy.provenance.sponsor` attestation.
- **Agentic content generation; human click-send for outreach.** Evan does
  not do outbound personally (FINRA). Intake + synthesis + draft generation
  are cron-agentic; sponsor emails are agent-drafted with Evan-click-send
  gate.
- **L1 canon is frozen at v0.1.0.** If a lab eval exposes a canon gap,
  escalate via context-repository adversarial review to bump the spec, not
  a local workaround.
- **Intake dedup contract.** Every adapter uses the shared
  `intake.hashing.content_id(...)` helper — no adapter-local dedup schemes.
  Divergent ID schemes across write paths silently corrupt cross-path
  queries (workspace rule S1-P3).
- **Every layer emits typed friction events.** A silent layer is
  indistinguishable from a stuck one (S3-P2, generalized by ADR-0029).
- **Session-startup CURRENT_STATE commit hygiene.** Every synaplex
  session, as its first repo-touching action of the turn, commits any
  pending `CURRENT_STATE.md` edits before proceeding to other work.
  Reason: the 12h reflection job writes load-bearing updates to
  `CURRENT_STATE.md` between sessions but is propose-only by design
  (workspace CLAUDE.md §"Automated Self-Reflection Loop": "Read-only
  and propose-only — never commits project code"). If no session
  runs for 24h+, the reflection edits accumulate uncommitted and
  agents opening new sessions read stale state from git HEAD. Closes
  the carry-forward escalation pattern that produced
  `URGENT-synaplex-current-state-commit-policy.md` at 4 cycles. The
  alternative (Option A — letting reflect.sh commit `CURRENT_STATE.md`)
  was rejected because the read-only invariant is load-bearing across
  every project the reflection loop touches, not just synaplex;
  loosening it for one file invites scope creep, and the existing
  `URGENT-supervisor-reflection-dirty-tree.md` safety-net handoff
  already exists for the case where reflect.sh exceeds its scope.
  The hygiene rule lives here (project-local) rather than in
  workspace CLAUDE.md because the discipline is the session's, not
  the framework's.

## Structure

```
synaplex/
├── CLAUDE.md            (this file)
├── CURRENT_STATE.md     front door
├── README.md            public README
├── site/                Astro + Tailwind, deploys to CF Pages (→ synaplex.ai)
│   └── src/content/{editorial,lab,directory}/
├── intake/              Layer 1: adapters, scoring, digest, friction
│   └── adapters/        rss, arxiv, hackernews (reddit/github/substack/podcast queued)
├── reasoning/           Layer 2: per-beat daily jobs (not yet built)
├── validation/          Layer 3: counter-search, canon integrity (not yet built)
├── editorial/           Layer 4: draft synthesis surface
├── scan/                legacy surface; collapsing into intake/
└── lab/
    ├── evals/memory-systems-v1/   first eval: memory systems comparison
    ├── canon_emit.py              emits claim/evidence/decision envelopes
    └── .canon/                    canon envelope store (append-only, hash-pinned)
```

## Truth Sources (in descending authority)

1. **L1 canon** at `context-repository/spec/discovery-framework/` — the
   obligations model every envelope conforms to.
2. **Canon envelopes** in `lab/.canon/` — hash-pinned, validated, replayable.
3. **Git history** of this repo.
4. **ADRs** at `supervisor/decisions/` — ADR-0027 (system framing) and
   ADR-0029 (pipeline) are the current load-bearing ones; ADR-0026 is
   superseded.
5. **Reader-facing writeups** (`site/src/content/`) — derivative, not
   primary. If writeup and canon envelope disagree, canon wins.

Do not treat prior session transcripts or tick-generated narratives as
truth.

## Session Model

- **Unit**: a layer execution (intake cycle / reasoning pass / validation
  job / publication draft) OR a lab evaluation (pre-register → execute →
  review → publish).
- **Durable state**: `lab/.canon/`, `runtime/intake/`, `runtime/friction/`,
  `site/src/content/`, commits in git.
- **Session transcript** (JSONL) is not durable. Promote load-bearing content
  to canon envelopes, writeups, or typed friction events before session end.

## Governance

- **Project tier**: synaplex is the system itself (ADR-0027); atlas and
  skillfoundry are pods — the ADR-0023 two-tier framing is superseded at the
  workspace level.
- **Governance ADRs**:
  - `supervisor/decisions/0027-synaplex-is-the-system.md` (accepted)
  - `supervisor/decisions/0029-synaplex-loop-five-layer-pipeline.md`
    (proposed)
  - `supervisor/decisions/0026-agentstack-lab-third-canon-instance.md`
    (superseded by ADR-0027, retained for context)
- **Shaping surface**: `supervisor/projects/products/synaplex.md`.
- **Reflection loop**: 12h per-project reflection.
- **Adversarial review**: required before every lab eval publish and before
  acceptance of canon-schema bumps.

## Review Standard

A meaningful change is incomplete if it cannot answer:
- which canon obligation it satisfies or improves,
- what evidence or decision surface it affects,
- whether the ArtifactPointer hashes are reproducible,
- what adversarial review said about the methodology.

## Tech Stack

- Site: Astro 5 + Tailwind 3 + MDX, deployed to CF Pages via Wrangler
  (pinned to Astro 5 for Node-20 compatibility; Astro 6 requires Node 22+).
- Intake + lab: Python 3.12, src layout. Intake depends on `feedparser`,
  `httpx`, `anthropic`. Lab depends on atlas's `StateStore` (local-editable
  install) pending L2 `discovery-runtime` extraction.
- Scoring: Claude Sonnet API with prompt caching on the system prompt and
  beat definitions (per the `claude-api` skill).
- Transcription (future): Groq `whisper-large-v3` for podcast ingestion.
- Newsletter: Buttondown (API-driven).
- Canon validation: `jsonschema` + a small in-repo validator enforcing the
  canon.md obligations beyond plain JSON Schema.

## What NOT to Do

- Don't publish an eval writeup without the matching canon envelope
  passing validation.
- Don't rehash a pre-registered Claim to fix metadata drift — document
  the drift in the completion report. Pre-registration immutability is
  the whole point; the id binds the scientific content, not the author
  metadata.
- Don't fork atlas's models into a diverged local copy. Use them via
  local-editable install. L2 extraction is deferred but the lab must not
  bake in incompatibilities.
- Don't propose 1:1 audits or per-customer services. Pivot to self-serve.
- Don't reshape the site IA in one pass. Per ADR-0027 §Open question 2,
  IA reshaping is incremental; ship a minimum-viable shape that is
  explicitly not default-blog, iterate.
- Don't conflate infrastructure friction and research friction into
  separate systems. ADR-0029 §Layer 5: one system.
- Don't bolt intake onto the reflection job. ADR-0029 §Alternatives
  considered §1: rejected; different concerns at different cadences.

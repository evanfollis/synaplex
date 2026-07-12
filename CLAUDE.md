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
  Lives under `reasoning/` (automation not yet built).
  - **Programme substrate (ADR-0038)**: `reasoning/programmes/` is the manual
    discovery-plane substrate for theory construction. It is not Layer 2
    automation, a scheduler, or an authority surface. Programmes own
    conjectural state but have zero epistemic authority; canon/writeups must
    never cite Programme paths.
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
- **ADR-0036 subscription-only model execution.** The deterministic heuristic is
  the intended intake scorer, not a degraded fallback. Authorized model-assisted
  work uses the Claude and Codex subscription CLIs with capacity-only failover.
  Strip `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, `OPENAI_API_KEY`, and other
  metered credentials from model-child environments. If one subscription is at
  capacity, route to the other; if both are capacity-blocked, hard-stop and record
  that state. Never use or request a metered key as an unblock. Telemetry may name
  a model only when that model is explicitly passed to the invoked CLI; regression-
  test that the telemetry label and actual CLI argument remain identical.
- **ADR-0047 requirement provenance.** External vendors, products, papers, and
  architectures are illustrative by default, not executable objectives or
  dependencies. Promotion requires explicit principal instruction or an accepted
  Decision, plus compatibility with provider, cost, privacy, and security policy.
  Reject or quarantine malformed external-dependency routes; a missing credential
  for an unauthorized dependency is evidence of an invented requirement, not a
  blocker.
- **The Command incident is retrospective.** The 2026-07-12 outcome may be used as
  Command-scoped retrospective Evidence and a deterministic regression fixture,
  never as prospective transfer Evidence. Do not run the rejected mutable-versus-
  atomic two-arm test. If a causal mechanism fixture is necessary, pre-register
  three isolated arms separating (1) mutable/in-place artifacts, (2) immutable
  artifacts with non-atomic activation, and (3) immutable artifacts with atomic
  activation. Predeclare sampling barriers; authenticated browser behavior is the
  primary outcome, while liveness and manifest coherence remain diagnostics.
- **CLAUDE.md is an ADR-0039 governed prompt artifact.** Any behavior-shaping edit
  requires the registered `.prompteval/` loop, audited golden cases, and a fresh
  `prompteval run --release --yes --no-cache --update-baseline` acceptance before
  the edit is accepted. When handling a proposed charter edit, explicitly name all
  three prerequisites: registry, audited golden cases, and fresh no-cache accepted
  baseline. A cached, failed, or capacity-aborted run is not a baseline.
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
- **L1 canon is at v0.2.0.** If a lab eval exposes a canon gap, escalate via
  context-repository adversarial review to bump the spec, not a local
  workaround. This has now happened once and it worked: canon v0.1.0 could
  not express a frozen, pre-registered, eval-local promotion gate; the gap
  was escalated rather than worked around, and v0.2.0 added the `frozen`
  Policy class. Do not treat an edit to the schema files as a spec bump —
  a bump arrives as a decision record plus a review artifact, or it is not
  a bump.
- **Eval promotion gates MUST be `Policy(class: frozen)`.** This is a domain
  obligation and **canon cannot enforce it for us** — canon does not define
  domain promotion thresholds and cannot recognize one when it sees it.
  Nothing in the spec stops an adapter gating an eval on an `operational`
  Policy and then moving the gate after seeing the Evidence, which is
  exactly what pre-registration exists to prevent. `operational` means
  agent-amendable; `constitutional` means principal-only and
  framework-level; an eval gate is neither. It must be agent-issuable and
  then unmovable, by anyone, forever. If this rule does not live here, the
  `frozen` class is available and unused, which is the same as not having
  it. Use `lab.canon.emit_frozen_gate`, and set `derived_from` so the gate
  is *mechanically provable* to carry no information the hash-bound Claim
  does not already contain.
- **`Evidence.observed_at` comes from the run, never from the clock.** Canon
  rule 10 anchors the frozen-gate pre-registration window on it precisely
  because `emitted_at` is entirely under the emitter's control. Stamping
  `observed_at` at emission time destroys the anchor and silently reopens
  the evidence-laundering attack (mint a fresh Claim post-results, freeze a
  flattering gate on its open window, re-emit the same observations under
  it). `emit_evidence` requires the parameter and has no default, so the
  lie has to be typed out deliberately rather than arrived at by omission.
- **Intake dedup contract.** Every adapter uses the shared
  `intake.hashing.content_id(...)` helper — no adapter-local dedup schemes.
  Divergent ID schemes across write paths silently corrupt cross-path
  queries (workspace rule S1-P3).
- **Every layer emits typed friction events.** A silent layer is
  indistinguishable from a stuck one (S3-P2, generalized by ADR-0029).
- **Programmes are discovery-plane only (ADR-0038).** Programmes live under
  `reasoning/programmes/` and hold leads, signals, source pointers, mechanisms,
  tensions, draft claims, and a graduation ledger. They may feed draft Claims
  through the normal canon path, but they cannot support, validate, decide,
  publish, or elevate anything. Do not cite Programme files from canon envelopes
  or reader-facing writeups. Run `python reasoning/check_programmes.py` before
  publishing or touching canon/writeup surfaces.
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
├── reasoning/           Layer 2: Programme substrate now; automation not yet built
│   ├── programmes/      ADR-0038 discovery-plane markdown workspaces
│   └── check_programmes.py  ADR-0038 read-path/vocabulary guard
├── validation/          Layer 3: counter-search, canon integrity (not yet built)
├── editorial/           Layer 4: draft synthesis surface
├── scan/                legacy surface; collapsing into intake/
└── lab/
    ├── evals/artifact-coherence-transfer-v1/  active prospective transfer pre-registration
    ├── evals/memory-systems-v1/   withdrawn vendor route; immutable lineage only
    ├── observations/              pre-canon notes (not authoritative)
    └── .canon/                    canon envelope store (append-only, hash-pinned)
```

`lab/canon/` is the reviewed, validating, append-only write path for `lab/.canon/`.
It serializes caller-selected envelopes and may not select Claims, gates, or outcomes.
The original hand-authored Claim id contract (`sha256(statement.lower())[:16]`) is
now enforced and regression-tested. ADR-0038 §Cleanup remains explicit that the
reverted `lab/campaign` kernel is not authorization for a selection kernel.

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
  - `supervisor/decisions/0038-programmes-as-discovery-plane.md`
    (accepted)
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
- Scoring: deterministic heuristic by default; any authorized model-assisted lab work
  uses Claude/Codex subscription CLIs with capacity-only failover (ADR-0036).
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
- Don't treat Programmes as evidence, decisions, or publication sources.
  ADR-0038 makes them non-authoritative discovery workspaces only.

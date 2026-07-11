---
name: Memory Systems Comparison v1 — Alternatives, Outcome Map, Verifier Plan
description: Rival explanations pre-registered for the memory-systems-v1 campaign. Hash-bound into the rival Claim envelopes. Additive to methodology.md, which is unchanged.
updated: 2026-07-11
eval_id: memory-systems-v1
spec_version: 0.1.0
---

# memory-systems-v1 — Alternatives, Outcome Map, Verifier Plan

## Why this document exists, and why it is not an edit to `methodology.md`

`methodology.md` is hash-bound into Claim `b7ff216f4eec6e58`
(`sha256:45916c9f…`) and is immutable. Editing it to add the sections below
would invalidate the pre-registration — the exact failure the canon exists to
prevent. So this is a **new artifact**, hash-bound into **new rival Claims**.
The primary Claim's statement, falsification criteria, thresholds, and
methodology are untouched.

**This is legitimate pre-registration, not post-hoc rationalization, for one
reason that expires**: as of 2026-07-11 the eval has never been executed and the
canon store contains **zero Evidence envelopes**. Rival explanations registered
before any result exists are pre-registration. The same rivals registered after
results exist would be storytelling. That window is open now and closes the
moment the first Evidence envelope lands.

## The defect this lens exposed

The pre-registered design has **four subjects and no control**.

If all four memory systems score below 0.80 recall@1 at 10-session depth — the
outcome the primary claim predicts — that observation is consistent with at
least two incompatible explanations:

1. Memory systems genuinely cannot do this (the primary claim), **or**
2. The task, corpus, or harness cannot detect success at all — nothing could
   score 0.80 here, including a naive baseline that just pastes the prior
   transcripts into the context window.

Nothing in the current design distinguishes these. A confirmatory result would
have been published as a finding about memory systems when it may have been a
finding about our own harness. That is the measurement-invalidity boundary
class, and it is the strongest rival below.

## Rival explanations (registered as Claims)

Each rival is a first-class canon `Claim` with its own falsification criteria.
Rivals are not annotations on the primary claim — canon already models competing
explanations, via `Decision.candidate_claims` / `rejected_alternatives` /
`arbitration`. The campaign manifest records which Claims are rivals *before* a
Decision exists to arbitrate them.

### A2 — measurement invalidity (the harness, not the systems)

> Sub-0.80 recall@1 at 10-session depth on the `multi_session_coherence` suite is
> a property of the task harness rather than of memory systems: a no-memory
> control that pastes the full prior-session transcript into context within the
> same 30k-token budget also scores below 0.80 mean recall@1.

**Falsified if**: the no-memory full-context control achieves mean recall@1 ≥ 0.80
(N≥10, 95% bootstrap CI lower bound ≥ 0.80) at 10-session depth. That result shows
the harness *can* discriminate, and a universal memory-system failure is then
about the systems.

### A3 — configuration, not capability

> The sub-0.80 result reflects default out-of-the-box configuration rather than
> capability ceilings: at least one subject reaches mean recall@1 ≥ 0.80 at
> 10-session depth when configured per its vendor's published best-practice guide.

**Falsified if**: every subject, configured per its vendor's published
best-practice guide, still scores mean recall@1 < 0.80 (N≥10) at 10-session depth.

### A4 — depth is the load-bearing choice

> Recall degrades monotonically with session depth rather than failing
> categorically, such that at least one subject exceeds 0.80 mean recall@1 at
> depth d=4 while falling below it at d=10 — making the choice of 10-session
> depth, not memory capability, the load-bearing assumption in the primary claim.

**Falsified if**: no subject exceeds mean recall@1 ≥ 0.80 at depth d=4 (N≥10).
The failure is then present even at shallow depth and is not a depth artifact.

## Outcome map (pre-registered, ordered, first match wins)

The map is evaluated **top-down; the first matching row selects**. Rows are
ordered by precedence, not by likelihood. Pre-committing the precedence is the
point: it is what stops a result from being narrated into whichever explanation
reads best after the fact.

| # | Observation at d=10, N≥10, default config | Selects |
|---|---|---|
| 1 | any subject ≥ 0.80 recall@1 (95% CI lower ≥ 0.80) | **primary FALSIFIED** (`b7ff216f4eec6e58`) |
| 2 | all subjects < 0.80 **and** no-memory control < 0.80 | **A2** — harness cannot discriminate; the finding is about the task |
| 3 | all subjects < 0.80 **and** control ≥ 0.80 **and** ≥1 subject ≥ 0.80 under vendor best-practice config | **A3** — the eval measured defaults, not ceilings |
| 4 | all subjects < 0.80 **and** control ≥ 0.80 **and** ≥1 subject ≥ 0.80 at d=4 | **A4** — depth is the load-bearing variable |
| 5 | all subjects < 0.80 **and** control ≥ 0.80 **and** no subject ≥ 0.80 at d=4 or under best-practice config | **primary SUPPORTED** |

Row 1 sits above the rest because falsification of the primary claim is
dispositive regardless of what the rivals say.

Note what row 2 forces: **the control arm must run**, or rows 2–5 cannot be
distinguished from each other and the campaign cannot reach any conclusion at
all. The outcome map is what makes the missing control a blocking omission
rather than a footnote.

## Validity threats (boundary classes)

| id | Boundary class | Threat | Mitigation |
|---|---|---|---|
| T1 | `measurement_invalidity` | No control condition: a universal sub-0.80 result is uninterpretable. | A2 + verifier `no_memory_control`; outcome-map row 2 makes the control mandatory. |
| T2 | `benchmark_contamination` | The task corpus may appear in subjects' training data. | `reset_semantics` stays held out; corpus items generated from a private seed; contamination check reported with results. |
| T3 | `implementation_drift` | Vendor APIs change between runs; cells are not comparable across dates. | Pin and record API/model versions inside every Evidence artifact; run all arms within one window. |
| T4 | `evidence_lineage_dependence` | Every result derives from one harness, so all evidence fails together. | Verifier `independent_replication` (external tier); the campaign counts independent *lineages*, not envelopes. |
| T5 | `regime_shift` | A new frontier model with native memory changes the field mid-campaign. | Decision expiry + invalidation conditions below. |
| T6 | `policy_spend_change` | The cost model (≤30k in / ≤3k out per run) can abort a cell. An aborted cell is **not** a failed cell. | Aborted cells are emitted as Evidence with `polarity: neutral` and an explicit abort reason — never as `contradicts`. |

T6 is the quiet one: a system aborted for cost that gets silently coded as a
failure would manufacture support for the primary claim out of our own budget
ceiling.

## Verifier plan

Each verifier declares the primary-source **lineage** it draws on. The campaign's
pressure scheduler will not propose a verifier whose lineage already appears in
the evidence set — re-running a lineage produces a correlated observation, not an
independent one. Tiers are canon Evidence tiers, ordered by bindingness to
external reality; the scheduler prefers the most binding unexercised verifier.

| id | Challenge | Targets | Lineage | Tier |
|---|---|---|---|---|
| `no_memory_control` | Run `multi_session_coherence` at d=10 against a no-memory full-context control within the same token budget. | A2 | `harness:no-memory-control` | `internal_operational` |
| `vendor_best_practice_config` | Re-run all subjects configured per each vendor's published best-practice guide. | A3 | `harness:vendor-config` | `internal_operational` |
| `depth_sweep` | Run `multi_session_coherence` at d ∈ {2,4,6,8} for all subjects. | A4 | `harness:depth-sweep` | `internal_operational` |
| `held_out_reset_semantics` | Run the held-out `reset_semantics` suite once, at publication time. | primary | `harness:held-out` | `internal_operational` |
| `vendor_rebuttal` | Send pre-publication results to each vendor; log the rebuttal as Evidence. | primary | `external:vendor-response` | `external_conversation` |
| `independent_replication` | Have a third party reproduce the headline result on their own harness. | primary | `external:third-party-replication` | `external_commitment` |

The two external verifiers outrank every internal one. Once we have our own
numbers, the most valuable next challenge is somebody else failing to reproduce
them — not us running one more suite against ourselves.

## Decision-packet expiry

- **valid_until**: `2027-01-11` (6 months from registration).
- **Invalidation conditions** (any one re-opens the campaign before expiry):
  - any subject ships a major memory-architecture change;
  - a new frontier model ships with native long-horizon memory;
  - vendor pricing changes enough to materially move `cost_per_1k_queries`.

A supported claim past its expiry is not wrong — it is **unverified**. The
scheduler routes it back to `revalidate` rather than letting stale support sit
inert and get cited.

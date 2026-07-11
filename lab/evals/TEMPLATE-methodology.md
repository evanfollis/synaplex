---
name: <eval-id> — Methodology
description: Pre-registered methodology for a synaplex lab evaluation. Hash-bound via canon ArtifactPointer.
updated: <YYYY-MM-DD>
eval_id: <eval-id>
spec_version: 0.1.0
---

# <eval-id> — Methodology

> Copy this file to `lab/evals/<eval-id>/methodology.md` and fill it in **before**
> emitting the Claim. Once the Claim is emitted, this document is hash-bound and
> immutable — every section below has to be right the first time, because the only
> way to change it afterward is a successor Claim.
>
> The four sections marked **[required by the alternatives gate]** did not exist in
> the first eval's methodology, and their absence let a design with four subjects
> and zero controls reach pre-registration. `python -m lab.campaign gate <eval-id>`
> now refuses to publish without them. Delete this blockquote when you copy the file.

## Subjects under test

<What is being evaluated, at what version, accessed how, as of what date. Pin
versions: `implementation_drift` is a real boundary class and undated subjects
make cells incomparable across runs.>

## Task suites

| # | Name | What it measures | Held-out? |
|---|---|---|---|
|  |  |  |  |

<At least one suite is held out and run exactly once, at publication time. It is
the out-of-sample check that the other suites were not tuned into.>

## Pre-registered thresholds

<Every number that a result will be compared against: effect sizes, significance
levels, N per cell, bootstrap iterations, cost ceilings. A threshold chosen after
seeing data is not a threshold.>

## Alternatives — rival explanations **[required by the alternatives gate]**

<The single most important section, and the one the first eval lacked.>

For the outcome this eval predicts: **what else could produce that same
observation?** Each rival explanation is registered as its own canon `Claim`, with
its own falsification criteria, and listed in `campaign.json` under
`alternative_claim_ids`. Rivals are not annotations on the primary claim — canon
already models competing explanations through `Decision.candidate_claims` /
`rejected_alternatives` / `arbitration`.

Ask specifically:
- **Measurement invalidity** — could the harness be incapable of detecting the
  effect at all? Is there a **control** that establishes the instrument can
  discriminate? (Four subjects and no control cannot distinguish "the subjects are
  weak" from "the task is undiscriminating.")
- **Configuration** — are we measuring defaults rather than ceilings?
- **Arbitrary parameter** — is some chosen constant (depth, k, N, window) doing the
  work that we are attributing to the subject?

A claim with no rivals does not publish. It can be waived — by a
`Decision(kind=continue)` whose `policies_in_force` names `lab.alternatives_required`
— but not quietly.

## Outcome map **[required by the alternatives gate]**

<Ordered, first-match-wins. Which observation selects which claim. Pre-committing
the precedence is what stops a result from being narrated after the fact into
whichever explanation reads best.>

| # | Observation | Selects |
|---|---|---|
| 1 |  | primary FALSIFIED |
| 2 |  | rival A2 |
| … |  |  |

Check the map for a row that no verifier can ever fill. If the map needs an
observation nothing in the verifier plan produces, the eval cannot conclude —
that is the moment to add the missing arm, not after the runs come back.

## Validity threats **[required by the alternatives gate]**

<Boundary classes worth naming: `measurement_invalidity`, `benchmark_contamination`,
`implementation_drift`, `evidence_lineage_dependence`, `verifier_conflict`,
`regime_shift`, `policy_spend_change`. Each gets a mitigation.>

| id | Boundary class | Threat | Mitigation |
|---|---|---|---|
|  |  |  |  |

Name the one about spend explicitly: a cell aborted for cost is **not** a failed
cell, and coding it as one manufactures support for your own claim out of your own
budget ceiling. Aborted cells emit Evidence with `polarity: neutral`.

## Verifier plan **[required by the alternatives gate]**

<Every challenge available to this campaign, each declaring the primary-source
**lineage** it draws on and the canon Evidence **tier** its result would carry.>

| id | Challenge | Targets | Lineage | Tier |
|---|---|---|---|---|
|  |  |  |  |  |

`lineage` is the anti-laundering key. The pressure scheduler will not propose a
verifier whose lineage already appears in the evidence set — re-running a lineage
yields a correlated observation, not an independent one. Three writeups of one
benchmark run are one result, not three.

Tiers rank by bindingness to external reality: `external_transaction` >
`external_commitment` > `external_conversation` > `internal_operational`. Once you
have your own numbers, the most valuable next challenge is usually somebody else
failing to reproduce them — not you running one more suite against yourself.

## Decision-packet expiry

- **valid_until**: `<YYYY-MM-DD>`
- **Invalidation conditions**: <what re-opens this campaign before the date>

A supported claim past its expiry is not wrong — it is **unverified**. The
scheduler routes it to `revalidate` rather than letting stale support sit inert
and get cited.

## Data capture

<Where runs log, what each record contains, how transcripts get hash-bound into
Evidence envelopes. Post-hoc edits produce a new content_hash and a new Evidence
record — never a silent overwrite.>

## Adversarial review trail

- Methodology review (pre-execution): route via
  `supervisor/scripts/lib/adversarial-review.sh`
- Results review (pre-publication): second pass over the complete evidence set

## Pre-registration integrity

Changes to thresholds, suite definitions, subjects, held-out identity, or the
primary/secondary designation invalidate the Claim and require a successor
emission. `lab/campaign/test_campaign.py` asserts this file's hash still matches
what the Claim was bound to; editing it in place fails that test loudly.

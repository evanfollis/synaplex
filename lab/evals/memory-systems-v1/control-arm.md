---
name: memory-systems-v1 — control arm (rival pre-registration)
description: Separately pre-registered rival Claim. A no-memory full-context control, scored by an independent oracle, that determines whether the harness can detect success at all.
updated: 2026-07-12
eval_id: memory-systems-v1
spec_version: 0.2.0
---

# memory-systems-v1 — the control arm

## Why this exists, and why it is not an edit to `methodology.md`

`methodology.md` is hash-bound into Claim `b7ff216f4eec6e58` and is immutable. This is a
**new artifact** bound into a **new, separate Claim**. The primary Claim's statement,
falsification criteria, thresholds, methodology, and frozen promotion gate are all
untouched.

The eval as pre-registered has **four subjects and no control**. If every memory system
scores below 0.80 recall@1 at 10-session depth — the outcome the primary Claim predicts —
that observation is consistent with two incompatible explanations, and nothing in the
original design separates them:

1. **Memory systems genuinely cannot do this.** (The primary Claim.)
2. **The harness cannot detect success at all.** Nothing would reach 0.80 on this corpus,
   including a naive baseline that simply pastes the prior sessions into the context window.

A confirmatory result would have published as a finding about memory systems when it may
have been a finding about our own harness. That is the **measurement-invalidity** boundary
class, and it is the one failure mode a comparison of four subjects against each other
structurally cannot see.

**This is legitimate pre-registration for exactly one reason, and it expires.** As of
2026-07-12 the canon store holds zero `Evidence` envelopes and the eval has never entered
probe. A rival registered before any result exists is a pre-registration. The same rival
registered after results exist is storytelling. The window closes on the first Evidence
emission, which is why this lands *before* the runner does.

## The rival Claim

> Sub-0.80 recall@1 at 10-session depth on the `multi_session_coherence` suite is a
> property of the task harness rather than of memory systems: a no-memory control that
> pastes the full prior-session transcript into context within the same 30,000-token input
> budget also scores below 0.80 mean recall@1.

**Falsified if** the no-memory full-context control achieves mean recall@1 ≥ 0.80
(N ≥ 10 runs, 95% bootstrap CI lower bound ≥ 0.80) at 10-session depth.

Falsifying this rival is the *good* outcome for the primary eval: it proves the instrument
can discriminate, which is what makes a universal memory-system failure a finding about
memory systems rather than about us.

## The control condition

One additional arm, exercised identically to the four subjects:

| Property | Value |
|---|---|
| Memory system | **none** — no store, no retrieval, no summarisation |
| Context construction | prior-session transcripts concatenated verbatim, most-recent-first, truncated at the budget |
| Input budget | **≤ 30,000 tokens** — identical to the per-run ceiling in `methodology.md` |
| Output budget | ≤ 3,000 tokens — identical |
| Prompts | byte-identical to the subject arms |
| Temperature | 0.2, identical |
| Session depth | 10, identical |
| Runs per cell | N ≥ 10, identical |

Most-recent-first truncation is declared here rather than decided at run time. It is the
**strongest honest** baseline: a memory system that cannot beat "just paste the recent
transcript" is not earning its complexity, and truncating oldest-first would hand the
control a corpus systematically missing the facts probed at depth. Choosing the truncation
order after seeing which order flatters the result is exactly the post-hoc freedom this
pre-registration exists to close.

If the transcripts fit inside the budget without truncation, the control is a *ceiling*,
not a baseline, and the comparison is stronger still. That is a fact about the corpus and
is recorded in the run manifest.

## The independent scoring oracle

The oracle is the load-bearing part, and it must not be borrowed from anything under test.

**Ground truth is generated with the corpus, before any run.** Each session carries a set of
probe facts with canonical answers, generated from a private seed and never shown to any
subject. Scoring compares a subject's answer to the canonical answer.

**The oracle is deterministic.** Exact match after a fixed, pre-registered normalisation
(casefold, strip punctuation and articles, collapse whitespace, numerals to digits). It is
**not** an LLM judge.

That last constraint is not fastidiousness. An LLM judge for a memory-systems eval is the
detector confound wearing a lab coat: the instrument that decides whether recall succeeded
would share failure modes, training data, and context-length behaviour with the systems
being scored — and it would score the no-memory control with the same model whose
in-context recall the control is measuring. **The treatment cannot be the detector.** A
deterministic oracle is weaker at judging paraphrase and stronger at being trustworthy, and
for this question that trade is not close.

Pre-registered consequence of that weakness: a semantically correct answer that fails
normalisation counts as a **miss**, for every arm equally. The oracle is blunt in the same
direction for everyone, so it cannot manufacture a difference between arms — it can only
compress one. If the compression is severe enough that all arms floor at zero, that is
itself a harness failure and this rival is *supported*, which is the honest reading.

## Thresholds (pre-registered, frozen)

| | |
|---|---|
| `recall_at_1` | 0.80 |
| `alpha` | 0.05 |
| `bootstrap_iterations` | 1000 |
| `runs_per_cell` | 10 |
| `session_depth` | 10 |
| `max_tokens_per_run_input` | 30000 |
| `max_tokens_per_run_output` | 3000 |

Bound into a `Policy(class: frozen)` with `derived_from: /thresholds`, so canon can prove
mechanically that the gate carries no information this pre-registration does not already
contain. Amendable by nobody.

## Aborted cells are not failed cells

A cell that aborts on the cost ceiling emits `Evidence(polarity: neutral)` with an explicit
abort reason. It never emits `contradicts`. Coding a budget ceiling as a failed result would
manufacture support for the primary Claim out of our own spending limit — a way of
"discovering" that memory systems fail by declining to pay for them to succeed.

## What this rival cannot do

It cannot rescue the eval from a corpus that is simply too easy. If the control scores ≥
0.80 **and** every subject also scores ≥ 0.80, the harness discriminates nothing at the
ceiling instead of nothing at the floor. That case falsifies both this rival and the primary
Claim, and the honest report is that the task was uninformative. It is recorded here so that
outcome is a pre-registered possibility rather than a post-hoc excuse.

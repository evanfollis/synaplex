---
name: Memory Systems Comparison v1 — Methodology
description: Pre-registered methodology for the first agentstack lab evaluation. Hash-bound via canon ArtifactPointer.
updated: 2026-04-19
eval_id: memory-systems-v1
spec_version: 0.1.0
---

# Memory Systems Comparison v1 — Methodology

**Status**: pre-registration in flight. This document is hash-bound into the
Claim envelope at `lab/.canon/claims/memory-systems-v1.json` at emission
time. Any change produces a new ArtifactPointer `content_hash` and
invalidates the pre-registered Claim — a new Claim must be emitted to
register the revised methodology.

## Subjects under test

Four memory systems, all accessed via their published APIs as of 2026-04-19:

1. **Letta** (<https://letta.com>) — episodic + archival memory, hosted API
2. **mem0** (<https://mem0.ai>) — vector-store-backed memory with embedding-
   driven recall
3. **MemGPT** (reference implementation, open-source at
   <https://github.com/letta-ai/letta>) — in-process memory with hierarchical
   scratchpads
4. **Claude built-in memory** (Anthropic native memory tool, `memory_20250818`
   or successor on `claude-sonnet-4-6` / `claude-opus-4-7`)

Four conditions total. Each condition is exercised with the identical task
corpus, identical prompts, identical temperature (0.2 where configurable).

## Task suites (5, one held-out)

| # | Name | What it measures | Held-out? |
|---|---|---|---|
| 1 | `multi_session_coherence` | Recall of ground-truth facts across 10 chained sessions | no |
| 2 | `contradiction_handling` | Does the system flag a fact contradicted at t=5 after being stated at t=0? | no |
| 3 | `retrieval_precision_at_k50` | Precision@5 retrieval under 50 distractor memories | no |
| 4 | `cost_per_1k_queries` | LLM + storage cost at steady-state 10k-item memory | no |
| 5 | `reset_semantics` | Does a "forget X" instruction actually purge or just demote? | **YES — held out** |

Suite #5 is developed but **not run** during methodology iteration. It is the
OOS analog: used once, at publication time, to sanity-check that the other
suites didn't over-fit to tuning.

## Pre-registered thresholds

- **recall@1 threshold**: ≥0.80 (a system passes task 1 if its mean
  recall@1 over 10 runs is ≥0.80 with 95% bootstrap CI not crossing 0.80)
- **Significance level** (α): 0.05 for any pairwise system-vs-system
  statistical test
- **Bootstrap iterations**: 1000 resamples for every bootstrap CI
- **Runs per cell**: N=10 minimum per (system × task) cell
- **Primary effect size**: Cohen's d ≥ 0.5 required for "meaningful
  difference" claim

## Promotion-gate analog (eval-level)

The Claim (`memory-systems-v1-h1`) is **supported** if its falsification
criteria are NOT met across the primary suites (1–4). The Claim is
**contradicted** if ANY one system achieves mean recall@1 ≥ 0.80 with 95%
bootstrap CI bounded below 0.80. A contradicted Claim still publishes — the
lab writeup celebrates the falsification, not the confirmation.

## Cost model

Per-run cost limits (abort condition):
- LLM tokens: ≤ 30,000 input + 3,000 output per session
- Storage ops: ≤ 100 memory-store operations per session
- If any single system exceeds 2× median cost across the others, its
  condition is flagged as "uneconomical" but its results are still reported

## Data capture

Every run logs to `lab/evals/memory-systems-v1/transcripts/<system>/<run-id>.jsonl`
with:
- Full prompt + completion pairs
- Every memory operation (store/retrieve/delete/update) with timing
- Token counts (input, output, cached)
- Cost estimates per Anthropic/Letta/mem0 pricing as of 2026-04-19

Transcripts are hash-bound in the Evidence envelopes emitted post-run.
Post-hoc edits produce new `content_hash`, invalidating the evidence
record and forcing a fresh emission.

## Timeline

- **Week 5**: pre-register Claim + methodology (this document). Hash-bind
  into canon envelope.
- **Week 6**: execute primary suites (1–4) across all 4 systems.
- **Week 7**: execute held-out suite (5). Run adversarial methodology
  review via Codex (`supervisor/scripts/lib/adversarial-review.sh`).
- **Week 8**: publish — reader-facing writeup at
  `agentstack.dev/lab/memory-systems-v1` renders from the canon Decision
  envelope + all cited Evidence envelopes.

## Pre-registration integrity

This document + its content_hash are locked at Claim emission. Any change
to:
- thresholds (recall@1, α, bootstrap iters, runs-per-cell)
- task suite definitions
- list of subjects under test
- held-out suite identity
- primary vs secondary suite designation

…invalidates the existing Claim and requires a new emission with a new
spec id (e.g. `memory-systems-v1.1` or a successor Claim chain). This
enforces the canon obligation "pre-registration immutability" (see
`canon.md` §Phase invariants / probe phase).

## Adversarial review trail

- Methodology review (pre-execution, Week 5): TBD — schedule via
  `supervisor/scripts/lib/adversarial-review.sh`; artifact at
  `.reviews/methodology-memory-systems-v1-<iso>.md`
- Results review (pre-publication, Week 7): TBD — second pass on the
  complete evidence set before publish

## Related canon objects

- Claim: `memory-systems-v1-h1` at `lab/.canon/claims/memory-systems-v1-h1.json`
- Policy (eval promotion-gate): declared inline in the Claim's
  `thresholds`; no separate Policy object for v1

## Related writeups (on publish)

- Editorial cross-link: "Memory is the next harness moat: why Letta, mem0,
  MemGPT, and Claude memory don't yet behave alike" (Week 2 seed editorial)
- Lab writeup: `/lab/memory-systems-v1/` MDX rendering

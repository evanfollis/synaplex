# intake — Layer 1 of the synaplex loop

Per ADR-0029, intake is external-signal ingestion. It is the system's sense
organs: the layer that fills the intake log with what the outside world
produced today, so Layer 2 (reasoning) has new evidence to pressure-test
accumulated canon against.

## Scope of the first pass

Three adapters, one beat, one digest:

- `adapters/rss.py` — blogs + newsletters via RSS/Atom (`feedparser`).
- `adapters/arxiv.py` — cs.AI / cs.CL / cs.LG / q-fin via the arxiv API.
- `adapters/hackernews.py` — top + new + Show HN + Ask HN via Firebase.
- `score.py` — deterministic per-beat relevance scoring with the intended
  keyword + regex heuristic. It has no metered model path.
- `digest.py` — daily per-beat markdown.
- `friction.py` — typed events emitted to `runtime/friction/events.jsonl`
  (ADR-0029 §Layer 5).
- `friction_classifier.py` — deterministic incremental Layer-5 promotion into
  content-addressed runtime candidates and locked supervisor FR records.
- `hashing.py` — the one shared dedup contract (S1-P3).
- `beats.py` — beat definitions. First pass ships `agent-platforms`;
  `systematic-trading` + `venture-discovery` follow in subsequent waves.

Reddit, GitHub, Substack, and podcast transcription are explicitly out
of scope for the first pass. They queue behind text-first adapters and
ship once the pipeline is proven.

## Dedup contract (S1-P3)

Every adapter emits raw items with an `id` field equal to
`intake.hashing.content_id(canonical_url, normalized_title)`. This is the
single rule — no adapter may invent its own hash scheme, because divergent
IDs across write paths silently corrupt cross-path queries in `runtime/`.
`hashing.content_id` is intentionally tiny and documented so a reviewer can
check the contract in one glance.

## Data layout

```
runtime/intake/
├── raw/
│   ├── rss-2026-04-24.jsonl        # one line per item, post-dedup
│   ├── arxiv-2026-04-24.jsonl
│   └── hackernews-2026-04-24.jsonl
├── scored/
│   └── agent-platforms/
│       └── 2026-04-24.jsonl        # raw items + score + rationale
├── digests/
│   └── agent-platforms-2026-04-24.md
└── synthesis/                      # Week 2+: weekly synthesis per beat
```

`runtime/friction/events.jsonl` is append-only across layers.

## How to run (manual)

```bash
# From /opt/workspace/projects/synaplex
.venv/bin/python -m intake ingest --source rss --beat agent-platforms
.venv/bin/python -m intake ingest --source arxiv --beat agent-platforms
.venv/bin/python -m intake ingest --source hackernews --beat agent-platforms
.venv/bin/python -m intake score --beat agent-platforms --date 2026-04-24
.venv/bin/python -m intake digest --beat agent-platforms --date 2026-04-24
```

Or the convenience target that runs the full daily pipeline:

```bash
.venv/bin/python -m intake run-daily --beat agent-platforms
```

## How to run (systemd)

Unit files live under
`supervisor/systemd/synaplex-intake.{service,timer}` (authored, NOT enabled
in the first-pass commit; enable is coordinated with supervisor per
handoff constraint). When enabled:

- `synaplex-intake.timer` runs raw ingestion every 4h.
- `synaplex-score.timer` runs scoring hourly.
- `synaplex-digest.timer` renders the daily digest at 06:57 UTC.

## Scoring

`score.py` always uses the keyword + regex heuristic against the beat's
keyword bank. This is the intended provider: deterministic, token-free, and
independent of ambient API keys. ADR-0036 forbids metered model APIs; an
`ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in the parent environment neither
changes scoring nor represents a blocker. Authorized model-assisted lab work,
when needed elsewhere, uses the Claude/Codex subscription CLIs with metered
credentials removed from child environments.

Every scored item records `score_provider: heuristic`; downstream layers do
not have a runtime provider switch to interpret.

## Operational controls (ADR-0029 §Adversarial review response)

The accepted ADR-0029 attaches eight operational controls to the loop,
authorized by the 2026-04-23T18:00Z handoff. Which ones are live in
this package today, and which are deferred to Layer 2:

**Live (Layer 1 scope):**

- **§6 Layer 1 rate limit (per-fetch, NOT per-day — see deviation
  note below).** Each adapter caps at `intake.limits.layer1_cap()`
  (200) per fetch — i.e., per cron firing. The cap is soft (truncate
  past-cap items + emit `eventType: throttled`) and protects against
  a runaway feed dumping its full archive into one run's output.
  Because the no-clobber/union-merge in `merge_jsonl_by_id` adds new
  items to the existing daily file, multiple cron firings per day can
  push the daily file past 200. **This deviates from the literal
  ADR-0029 §6 wording** ("max 200 raw items per source per day"),
  which would require post-merge truncation. See `intake/limits.py`
  module docstring for the three reconciliation options (A score-
  truncate, B recency-truncate, C ratify per-fetch + reword ADR);
  the choice is principal-only and routed via the cap-policy handoff.
- **§7 Reasoning/Validation boundary semantics (documented below).**
- **§8 Integrity job stub** lives at `projects/synaplex/integrity/` and
  runs via `synaplex-integrity.timer` (04:37 UTC daily). First pass
  walks `lab/.canon/candidates/` (currently empty — Layer 2 not built)
  and emits a summary friction event. The TTL sweep logic is in place;
  it becomes load-bearing when candidates start flowing.

**Deferred to the Layer 2 handoff:**

- §1 Per-source trust tracking (needs promotion data from Layer 2).
- §2 Scoring-accuracy tracking (needs validation outcomes from L3).
- §3 `reasoning_note` required field (Layer 2 candidate write path).
- §4 Bootstrap throttle (Layer 2 candidate emission).
- §5 Candidate TTL + quarantine paths (the TTL sweep logic is here;
  quarantine populates from Layer 2's validation-failure path).

### §7 Boundary semantics

Layer 2 (reasoning) performs: schema validation on candidate envelopes,
referential integrity (candidate references to intake items resolve),
cross-canon dedup against existing envelopes, basic well-formedness
(no null-required-fields).

Layer 3 (validation proper) performs: adversarial review (Codex),
counter-search against the intake corpus for strongest disagreement,
canon integrity (hash, refint, schema consistency across `.canon/`
trees).

The distinction is amplitude, not kind. If Layer 2 implementation grows
Layer-3-shaped validation logic, pause and write a follow-on ADR
proposing to collapse them. Do not silently accumulate validation in
L2 while keeping the naming distinct — that's the failure mode the
ADR-0029 adversarial review called out.

## Friction events

Every adapter call emits at least one friction event:

```json
{"ts":"2026-04-24T06:57:00Z","layer":"intake","source":"rss","eventType":"success","reason":"42 items, 3 deduped","ref":"runtime/intake/raw/rss-2026-04-24.jsonl","sourceType":"cron"}
```

Failure paths emit `eventType=failure` with the exception summary.
Empty-result paths emit `eventType=stuck` per S3-P2 (a silent layer is
indistinguishable from a stuck one).

The classifier is inspectable and has no model or network path:

```bash
.venv/bin/python -m intake.friction_classifier
```

It preserves an atomic watermark at `runtime/friction/classifier-state.json`,
keeps a rolling seven-day projection capped at 256 source references per class
under `runtime/friction/candidates/`, and never rewrites the append-only source.
Three matching `failure` events promote;
`stuck` and `escalated` promote immediately; `success` and designed `throttled`
events remain non-promoting evidence. Every source reference carries the exact
byte range and line hash needed to recover the raw event.

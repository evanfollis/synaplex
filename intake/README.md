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
- `score.py` — per-beat relevance scoring. First pass ships a keyword
  heuristic + a Sonnet scorer; the active provider is chosen at run-time.
- `digest.py` — daily per-beat markdown.
- `friction.py` — typed events emitted to `runtime/friction/events.jsonl`
  (ADR-0029 §Layer 5).
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

## Scoring providers

`score.py` dispatches on `SYNAPLEX_SCORE_PROVIDER`:

- `heuristic` (default when no API key): keyword + regex scoring against
  the beat's keyword bank. Cheap, deterministic, no tokens.
- `sonnet`: Claude Sonnet 4.6 with prompt caching on the system prompt
  + beat definition (per the `claude-api` skill). Requires
  `ANTHROPIC_API_KEY`.

The two providers write the same `scored.jsonl` shape, so swapping is
transparent to downstream layers.

## Friction events

Every adapter call emits at least one friction event:

```json
{"ts":"2026-04-24T06:57:00Z","layer":"intake","source":"rss","eventType":"success","reason":"42 items, 3 deduped","ref":"runtime/intake/raw/rss-2026-04-24.jsonl","sourceType":"cron"}
```

Failure paths emit `eventType=failure` with the exception summary.
Empty-result paths emit `eventType=stuck` per S3-P2 (a silent layer is
indistinguishable from a stuck one).

---
plane: discovery
epistemic_status: conjectural
lifecycle_status: active
title: "Harness engineering as platform knowledge"
slug: harness-engineering-platform-knowledge
created: 2026-07-12
updated: 2026-07-12
owner: synaplex
---

# Harness engineering as platform knowledge

> Nothing in this file is verified. Verified state lives in canon. This
> Programme can feed draft claims, but it cannot support, validate, decide,
> publish, or elevate anything by itself.

## Core conjectural frame

Agent platforms may be moving from model-centric performance questions toward
harness-centric knowledge-system questions. The interesting unit is not only
whether an agent can produce code, but whether the surrounding repository,
runtime, checks, ticket grain, and reflection loop give the agent enough durable
context to act reliably and improve the harness over time.

This Programme exists to keep that theory-shaped frame alive without promoting
it into canon before the strict layer has done its work.

## Leads

- Treat repository state as the durable system of record for agent work, while
  treating prompt context as an ephemeral projection.
- Look for platform designs where runtime observability materially changes the
  agent's ability to correct itself.
- Compare command-level orchestration with ticket-level orchestration on
  oversight load and completion quality.
- Watch whether repeated agent failure patterns become durable harness changes
  or remain one-off instruction churn.

## Signals

- The existing pre-canon observation decomposes the frame into six propositions
  with falsification sketches.
- The workspace already uses repository-loaded context, hooks, typed friction,
  reflection, and synthesis as operating substrate.
- The same pattern appears in external discussion of harness engineering and
  Codex orchestration.

## Sources

Use pointers only. Do not copy source content into this file.

| pointer | kind | note |
| --- | --- | --- |
| https://openai.com/index/harness-engineering/ | url | Primary source pointer for the harness-engineering frame. |
| 66a02d63dbc9dfd0 | intake_id | Existing content pointer recorded with the primary source. |
| https://openai.com/index/open-source-codex-orchestration-symphony/ | url | Primary source pointer for Symphony as a worked orchestration example. |
| bd097b721025a0ed | intake_id | Existing content pointer recorded with the Symphony source. |
| https://videohighlight.com/v/am_oeAoUhew | url | Transcript pointer useful for quote-level follow-up. |
| 99fa623b4f8a57c6 | intake_id | Existing content pointer recorded with the transcript source. |

## Mechanisms

- Durable repository context may reduce repeated re-explanation because the
  agent can read stable instructions, prior decisions, and current state.
- Runtime observability may close the loop between action and outcome, turning
  "did it run" into "did it behave."
- Project-specific checks may be most useful when they fire at failure time and
  include local recovery instructions.
- Ticket-grain orchestration may reduce live supervision when tickets encode
  enough context, acceptance conditions, and ownership.
- Reflection and synthesis may convert repeated agent mistakes into durable
  harness improvements.

## Tensions

- The frame can become self-congratulatory because synaplex itself is a
  harness-heavy system evaluating harness-heavy systems.
- Several drafts are entangled; repository context, observability, checks, and
  reflection may work as a bundle rather than independent variables.
- The source base is narrow and may overfit OpenAI's current platform posture.

## Anomalies

- A lightweight harness may outperform a richly instrumented one on small,
  well-scoped tasks if extra structure raises coordination overhead.
- Some security-sensitive environments may intentionally reduce repository or
  runtime visibility and still achieve acceptable reliability.
- Ticket-level orchestration can fail if tickets are too broad for the agent to
  decompose or too thin to be meaningfully different from commands.

## Open questions

- What task classes make repository-visible agents reliably better than
  repo-blind agents?
- Which runtime observations are actually used by agents to correct behavior,
  versus merely logged for humans?
- What is the useful grain size for a self-sustaining project handoff?
- How should synaplex avoid circularly treating its own harness habits as
  outside confirmation?

## Draft claims

| draft | status | note |
| --- | --- | --- |
| Repository-visible harnesses outperform repo-blind harnesses on complex multi-step coding tasks when repository state includes current decisions, checks, and telemetry. | sketching | Needs bounded task class, comparison surface, and rival explanations. |
| Runtime observability reduces false completion reports from coding agents compared with build-test-only feedback. | sketching | Needs a measurable failure class and comparable harness configurations. |
| Repeated agent failure patterns compound only when converted into durable repository or hook changes. | sketching | Needs a way to distinguish durable harness changes from instruction churn. |

## Graduation ledger

| date | draft | canon claim id | verdict | note |
| --- | --- | --- | --- | --- |
| 2026-07-12 | Repository-visible harnesses outperform repo-blind harnesses on complex multi-step coding tasks when repository state includes current decisions, checks, and telemetry. |  | pending | Not ready; first pass must define task class and falsifier. |
| 2026-07-12 | Runtime observability reduces false completion reports from coding agents compared with build-test-only feedback. |  | pending | Not ready; first pass must identify observable failure category. |
| 2026-07-12 | Repeated agent failure patterns compound only when converted into durable repository or hook changes. |  | pending | Not ready; first pass must avoid circular self-confirmation. |

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
- What independent oracle can count a false completion report without being the
  same instrument as the treatment? This is the concrete unblock for D2. Candidate
  shapes worth exploring: a post-hoc human or third-party audit of a sample of
  completion reports against real end-state; a delayed check run by a system that
  neither arm can see; or an externally-held task set where ground truth is known
  in advance and withheld from both harnesses.

## Draft claims

| draft | status | note |
| --- | --- | --- |
| D1. Repository-visible harnesses outperform repo-blind harnesses on complex multi-step coding tasks when repository state includes current decisions, checks, and telemetry. | sketching | Weakest of the three. "Outperform" is undefined, the task class is unbounded, and the antecedent bundles three independent variables (decisions, checks, telemetry) into one conjunction — a result could not attribute the effect to any of them. Also close to truistic: more relevant context helping is not a discovery. The interesting question is which component carries the effect and how large it is. |
| D2. For repository coding tasks whose completion has a runtime state distinct from "merged", a harness that exposes post-change runtime signals to the agent produces fewer false completion reports than a harness whose only feedback is build plus test. | sketching | Strongest of the three; tightened in the section below but not ready for canon. Single independent variable, bounded task class, and a failure class that is operationally defined rather than gestured at. Graduation refused for now: the treatment is also the detector (see "The detector confound"). |
| D3. Repeated agent failure patterns compound only when converted into durable repository or hook changes. | sketching | "Compound" is undefined and currently unmeasurable; "only when" is a universal that one counterexample kills, which sounds rigorous but is doing no work until "compound" is operational. Highest circularity risk of the three — it is a claim about our own reflection loop, tested by our own reflection loop. |

## Draft under review: runtime observability and false completion

Stage 2 selected D2 as the strongest draft and tightened it. It is still **not
ready for canon**. The blocking reason is recorded below and in the ledger.

### The tightened draft

> For repository coding tasks whose completion has a runtime state distinct from
> "merged" — deploy-shaped tasks — a harness that exposes post-change runtime
> signals to the agent produces fewer false completion reports than a harness
> whose only feedback is build plus test.
>
> A **false completion report** is an agent-authored report asserting that a
> change is live or working, when an independent check shows it is not.

What the tightening bought: one independent variable instead of three, a bounded
task class instead of "complex multi-step coding tasks", and a failure class that
can actually be counted.

### The detector confound

This is the reason graduation is refused, and it is not a detail.

**The treatment is also the instrument.** Runtime observability is the thing that
makes a false completion *visible*. A build-test-only harness will therefore
appear to have fewer false completion reports for a reason that has nothing to do
with agent behaviour: it has no way to detect them. Counting false completions
with the treatment condition as the detector guarantees the result the draft
predicts, whichever way reality actually falls.

Any measurement must count false completions with an **independent oracle** — a
check that sits outside both conditions and is available equally to each. Until
that oracle is specified, D2 is not decidable, and emitting it as a canon Claim
would pre-register a measurement that cannot fail.

This is structurally the same trap as an evaluation with subjects and no control:
the observation the claim predicts is also consistent with the instrument being
blind. Naming it is what the discovery plane is for.

### Rival explanations

If deploy-shaped false completions do drop under runtime observability, at least
four things other than the draft could produce that:

- **R1 — reporting discipline, not observability.** The reduction comes from an
  explicit instruction to verify deployment, not from the availability of runtime
  signals. A harness carrying the rule and *no* runtime observability would show
  the same drop. This is the strongest rival, because in practice the two are
  almost always introduced together, and this workspace is itself a case where the
  rule and the telemetry arrived as a bundle.
- **R2 — character, not rate.** Observability does not reduce false completions;
  it changes their shape. The agent reads a runtime signal, misreads it (a 200 OK
  is not correct behaviour), and reports completion with *more* confidence than
  before. Rate flat, confidence up, harm worse. Distinguishable only by measuring
  confidence-weighted error rather than a raw count.
- **R3 — task property, not harness property.** The effect exists only where "done"
  has a runtime state distinct from merge, and vanishes for pure-computation tasks
  where build plus test is already a complete oracle. Then the finding is about the
  task class and the harness is incidental — which would make the draft true but
  uninteresting, and would mean the bounded task class is doing all the work.
- **R4 — selection.** Teams that invest in runtime observability already have
  stronger verification culture. Observability is a marker of the cause, not the
  cause.

### Falsification shape

Not pre-registration — pre-registration happens in canon, if this ever graduates.
This is the shape a decidable version would have to take:

- Falsified if, on a matched deploy-shaped task set scored by an independent
  oracle, harnesses with runtime observability show the same or a higher rate of
  false completion reports than build-test-only harnesses.
- R1 is separated only by a three-arm comparison: build-test-only; build-test plus
  the verify-deployment rule; build-test plus runtime observability. Two arms cannot
  tell the instruction from the information.
- R2 is separated only if the score is confidence-weighted. A raw count cannot see
  it.

### Measurement caveats

- **Detection asymmetry** (the confound above) biases every naive design toward the
  draft. It is not a refinement; it is disqualifying until fixed.
- **n=1, and it is ours.** The workspace's own documented instance of this failure
  class — telemetry code landed but the service never redeployed, while the
  completion report read as verified — is what makes the draft feel obvious. One
  incident, on our own harness, is a reason to investigate, not support. Any real
  measurement must include harnesses we do not operate.
- **We are the harness-heavy system evaluating harness-heavy systems.** Already
  named in Tensions; it bites hardest here, because D2 is the draft our own
  operating rules most flatter.

### Domain bounds

- **In**: repository coding tasks where completion has a runtime state distinct from
  merge (deploy, migration, service config).
- **Out**: pure-computation and library tasks where build plus test is a complete
  oracle — there is no gap for a false completion to live in.
- **Out**: environments where the agent has no access to runtime signals at all; the
  contrast is undefined rather than negative.

## Graduation ledger

| date | draft | canon claim id | verdict | note |
| --- | --- | --- | --- | --- |
| 2026-07-12 | D1. Repository-visible harnesses outperform repo-blind harnesses. |  | pending | Not ready. Antecedent bundles three independent variables; "outperform" undefined; task class unbounded. Not selected for Stage 2 tightening. |
| 2026-07-12 | D2. Runtime observability reduces false completion reports on deploy-shaped tasks. |  | refused | Stage 2 selected and tightened this draft, then refused graduation. Blocking reason: the treatment condition is also the detector, so a naive measurement returns the predicted result whichever way reality falls. Unblocks only when an independent oracle for false completion is specified and the three-arm design separating rival R1 is costed. No canon envelope emitted. |
| 2026-07-12 | D3. Repeated agent failure patterns compound only when converted into durable harness changes. |  | pending | Not ready. "Compound" is not operational; highest circularity risk of the three. Not selected for Stage 2 tightening. |

---
name: binding disposition — prospective run stopped, invalid
status: BINDING. The run is STOPPED and UNEXECUTED. The study is INCOMPLETE.
decided_at: 2026-07-12T16:30Z
study: artifact-coherence-transfer-v1
claim: bda4396c7638e63f
frozen_gate: 5273e9a31e92f6c3
evidence_emitted: none
canon_events_emitted: none
reviewer: codex CLI 0.144.1, model gpt-5.6-sol, provider openai, reasoning effort medium
reviewer_session: 019f5728-131e-78a0-b4b1-9fd3c28d05c8
review: reviews/codex-methodological-review-2026-07-12.md
receipt: reviews/RECEIPT-codex-2026-07-12.md
transcript_sha256: 53fd9cd09416748e688a362a9d41b70be24a41feaba145f0f6a73b7c37b836c4
transcript_location: operator-only workspace review archive (not checked in, not linked from here)
---

# The prospective run is invalid. It will not be executed.

An opposing model was asked to dispose of the recorded protocol deviation
(`PROTOCOL-DEVIATION-2026-07-12-preprobe-target-consultation.md`) before probe entry, with
four possible verdicts and an explicit warning not to soften. It returned:

> **VERDICT: STOP_RUN_INVALID**

Per the standing commitment — *"if validity is ambiguous, stop with the run unexecuted rather
than forcing progress"* — the run stops. No probe entry has been emitted, no browser sample has
been taken, no Evidence exists, and none will be produced under this Claim by this route.

## The reviewer refuted the contaminated party's disposition, and was right

This session's own disposition held that the deviation voided only the B0 diagnostic and left
the prospective run intact. Its load-bearing argument was that the leaked information was **a
subset of what the hash-bound pre-registration already asserts**. The reviewer called that
self-serving and demonstrated it:

> "The expected body is indeed predeclared, but the methodology does not predeclare HTTP 200,
> absence of redirect, latency, uptime, PID, exact executable/module, restart history, or
> evidence of earlier successful requests/MCP sessions. Its predicate basis says only that the
> service imports an ASGI application and does not resolve named artifact classes at request
> time; the consultation disclosed materially more."

That is correct, and it is a straightforward factual check that the contaminated party did not
perform on itself. `methodology.md` predeclares the expected identity string and the P=false
basis. It predeclares nothing about the service's current health, its response latency, its
redirect behavior, its process identity, or its recent request history. All of that was
disclosed. The "subset" claim was false.

The reviewer also granted what should be granted, which is what makes the refusal credible:

> "The immutable Claim and gate cannot have been retrospectively contaminated: both precede
> access. Nor did access change the already-closed population. **But it contaminated instrument
> construction, operational timing, retry/abort choices, and eventual interpretation. Those
> channels are enough.**"

The last sentence is the disposition. This session named instrument-construction bias and
proposed to neutralize it with fail-injection tests. The reviewer's answer:

> "Fail injection shows that selected synthetic failures activate selected branches; it does not
> validate detector completeness or cure author contamination."

Also correct. A detector proven to fire on the failures its author thought to inject is not a
detector proven to be complete. The fail-injection suite was a real improvement to the
executor; it was never capable of restoring the blindness the deviation destroyed.

**Declaring the information "void" does not restore blindness.** That is the sentence to carry
forward.

## Findings that survive this study and bind any successor

These came out of the review and out of the executive's independent Codex pass on the executor.
They are recorded here because a successor pre-registration must answer them, not rediscover
them.

1. **A semantic artifact mismatch returning HTTP 200 is invisible to this executor.** A stale but
   *loadable* script or API response can be mutually incompatible with the document while
   producing no console error, no uncaught exception, no `requestfailed`, and no error status. If
   the body identity still matches, the executor passes it. The four detection channels are all
   *transport* channels; none asserts application behavior. A study whose subject is artifact
   *coherence* cannot detect incoherence that loads successfully. This is the single most
   important gap and it is a **methodology** gap, not a code gap.
2. **Delayed failures after the fixed 1s post-load dwell escape entirely.** Nothing observes the
   page after the capture instant.
3. **`mechanical_outcome()` crosses into adjudication.** The reviewer holds that writing `pass`
   and failure reasons into the artifact is automated sample adjudication, which ADR-0049
   reserves for the reviewed step, and that "calling adjudication measurement does not remove the
   boundary." This session disagrees in part — the criterion is deterministic and was fixed
   before the run — but the disagreement is recorded, not resolved, and the reviewer's reading is
   the conservative one. A successor should emit raw facts only and adjudicate in review.
4. **`_execute()` accepts an injected plan carrying the real URL**, so a stub sampler could
   produce fixture-shaped artifacts stamped `is_preregistered_subject: true`, which checks URL
   equality alone. The production CLI is closed; the module seam is not.
5. **A partial run still exits 0** with a partial manifest. Downstream filing remains hazardous.
6. **GET/HEAD is not a guarantee of non-mutation** — it depends on subject semantics — and B0
   itself performs a GET.
7. **The absolute anchor and the 10s barrier tolerance are unregistered parameters.** The
   reviewer accepts barrier reading (b) as the faithful one but notes both additions are
   defensible "only if prospectively adjudicated." For a successor Claim they must be *in* the
   pre-registration, not in the executor.

## What is NOT concluded

- **No finding about launchpad-lint.** It was never observed under this protocol. Nothing here
  says its artifacts are coherent or incoherent. That question is untouched and remains open.
- **The kill is a disposal, not a result.** `Decision(kill) c40c91e1d1b56853` disposes Claim
  `bda4396c7638e63f`, citing **zero Evidence** and opening `INVALIDATED, NOT MEASURED`. It cites
  the frozen gate in full (canon rule 13): never met, never missed, never tested. It follows the
  reviewed precedent of the two withdrawn vendor Claims — the schema and the precedent both
  support a non-finding kill, which is the condition under which emitting it was authorized. A
  regression now asserts that *any* zero-Evidence kill must declare itself a non-finding, so no
  later reader or projection can cite this as an experiment that ran and came back negative.
- **The executor is not thereby validated.** It is better than it was — read-only is enforced, the
  anchor is absolute, probe entry is a precondition, corruption refuses — and none of that makes
  this Claim runnable. No amount of executor hardening cures a contaminated instrument author.
- **No successor Claim is emitted.** A successor needs a fresh pre-registration that answers the
  semantic-mismatch defect (finding 1), and it is a new scientific act, not a repair of this one.

## Standing constraints

- The target is **not** observed. No curl, no systemctl, no journalctl, no browser sample.
- **No probe-entry event is emitted** for `bda4396c7638e63f`.
- A successor study requires a **new pre-registration** (new Claim, new frozen gate, new
  methodology addressing finding 1 above) and should be **executed by an agent that has not seen
  the subject's current state** — which this session, and any session inheriting its transcript,
  no longer is.

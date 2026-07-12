# Opposing methodological review — artifact-coherence-transfer-v1

Reviewer: Codex CLI 0.144.1, `model: gpt-5.6-sol`, `provider: openai`, reasoning effort medium.
Question asked: `review-prompt-2026-07-12T16-30Z.txt` (four permitted verdicts; explicitly told
not to soften). Full raw transcript is retained in the operator-only workspace review archive and
is deliberately **not** checked in — see `RECEIPT-codex-2026-07-12.md` for its sha256 and
provenance. This file is the reviewer's final answer, verbatim apart from citation-link cleanup.

Binding effect: see `../DISPOSITION-2026-07-12-run-stopped-invalid.md`.

---

Q1. DISPOSITION

The prospective run is invalid, not merely B0. ADR-0049 makes probe entry an ordering precondition—events must precede *any* subject observation—not merely browser sampling (`ADR-0049:43-50`). The consultation indisputably violated it (`deviation:110-118`). Declaring the resulting information “void” does not restore blindness.

Claim (ii) is self-serving. The expected body is indeed predeclared (`methodology:84-88`), but the methodology does not predeclare HTTP 200, absence of redirect, latency, uptime, PID, exact executable/module, restart history, or evidence of earlier successful requests/MCP sessions. Its predicate basis says only that the service imports an ASGI application and does not resolve named artifact classes at request time (`methodology:53-57`); the consultation disclosed materially more (`deviation:48-83`).

The immutable Claim and gate cannot have been retrospectively contaminated: both precede access (`Claim:5-18`, `gate:35-53`). Nor did access change the already-closed population. But it contaminated instrument construction, operational timing, retry/abort choices, and eventual interpretation. Those channels are enough.

Q2. BIAS CONTROL

Fail injection shows that selected synthetic failures activate selected branches; it does not validate detector completeness or cure author contamination.

A clear blind spot is semantic artifact mismatch returning HTTP 200: a stale but loadable script/API response can be mutually incompatible with the document while producing no console error, uncaught exception, `requestfailed`, or error status. If it preserves the exact body identity, this executor passes it. No user interaction or behavioral assertion is exercised; capture is essentially body text plus passive telemetry (`executor:580-630`). Delayed failures occurring after the fixed one-second capture also escape.

Q3. BARRIER SEMANTICS

Reading (b) is stronger. B2 explicitly fixes a one-second post-load dwell, while B3/B4 repeat “B1-B2” after 30/120 seconds (`methodology:67-75`). Reading (a) would silently replace B2’s repeated one-second dwell.

Nevertheless, the executor adds an unregistered absolute anchor and ten-second tolerance (`executor:117-133`). These are defensible implementation details only if prospectively adjudicated. Choosing the materially wrong interpretation after observation would invalidate the run; (b), declared beforehand, is the faithful choice.

Q4. EXECUTOR INTEGRITY

(a) It blocks non-GET/HEAD browser traffic (`executor:554-565`), but cannot guarantee nonmutation: GET/HEAD safety depends on subject semantics, and B0 performs another GET (`executor:479-508`).

(b) No canon emitter is imported; artifacts explicitly say `emits_evidence: false` (`executor:839-845`, `executor:984-997`).

(c) It cannot silently count fewer than three as complete, but it returns success with a partial manifest (`executor:974-1001`, `executor:1016-1023`). Downstream filing therefore remains hazardous.

(d) Aborts lack outcomes and do not fill sample slots (`executor:899-944`); completed slots are shape-validated (`executor:252-269`).

(e) The CLI is constrained, but `_execute()` can accept an injected plan, including the real URL, arbitrary preflight data, clock, and sampler (`executor:726-768`). `is_preregistered_subject` checks only URL equality (`executor:751-753`). Thus fixture-shaped artifacts can pose as the subject if invoked programmatically.

`mechanical_outcome()` crosses into automated sample adjudication by writing “pass” and failure reasons (`executor:660-720`). ADR-0049 requires preservation of raw artifacts followed by reviewed Evidence and Decision (`ADR-0049:51-57`). Calling adjudication “measurement” does not remove that boundary.

VERDICT: STOP_RUN_INVALID

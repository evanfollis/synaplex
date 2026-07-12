---
name: protocol deviation — pre-probe target consultation
status: RECORDED DEVIATION — NOT EVIDENCE, NOT ADMISSIBLE
occurred_at: 2026-07-12T15:25:42Z–2026-07-12T15:44:07Z (bounded; see §Timestamp fidelity)
recorded_at: 2026-07-12T15:44:07Z
recorded_by: synaplex project session (Claude Opus 4.8)
authority: ADR-0049; handoff synaplex-first-instrumented-research-cycle-2026-07-12
study: artifact-coherence-transfer-v1
claim: bda4396c7638e63f
frozen_gate: 5273e9a31e92f6c3
---

# Protocol deviation: the target was consulted before probe entry

## What this file is

A verbatim record of an out-of-band consultation of the transfer subject that occurred
**before** Phase 1 substrate work existed, **before** the study executor existed, and
**before** any `methodology_log` or `phase_transition(→probe)` event was emitted into canon.

This file is **not Evidence**, is **not admissible as an observation**, and **must never be
cited by an Evidence envelope, a Decision, a knowledge invariant, or a reader-facing
writeup**. It exists because a deviation that is not written down is a deviation that gets
discovered later as a contradiction, and because the run manifest must be able to say
truthfully what touched the subject and when.

It is filed in the study directory but is deliberately **not** referenced by the Claim's
`ArtifactPointer`. The Claim binds `methodology.md` alone
(`sha256:5e1742731c58f06fa329f98cbff0b9b583227578515b172f8d218473777e8c50`), which was
verified unchanged at 2026-07-12T15:44:07Z. Adding this file does not and may not alter the
pre-registration.

## What executed

Two shell invocations ran, in one batch, and both returned output. Neither was a browser
sample. Both were read-only.

### 1. Service liveness / unit identity (B0-shaped)

Command:

```
systemctl status launchpad-lint.service --no-pager 2>&1 | head -15
```

Output, verbatim:

```
● launchpad-lint.service - Launchpad Lint MCP product
     Loaded: loaded (/etc/systemd/system/launchpad-lint.service; enabled; preset: enabled)
     Active: active (running) since Sat 2026-07-11 23:25:42 UTC; 16h ago
   Main PID: 801 (python)
      Tasks: 1 (limit: 9255)
     Memory: 47.2M (peak: 57.1M)
        CPU: 1min 32.866s
     CGroup: /system.slice/launchpad-lint.service
             └─801 /opt/workspace/projects/skillfoundry/skillfoundry-products/products/launchpad-lint/.venv/bin/python -m uvicorn launchpad_lint.app:app --host 127.0.0.1 --port 8010

Jul 12 11:26:53 ubuntu-8gb-hil-1 python[801]: INFO:     2a01:4ff:1f0:5b28::1:0 - "GET / HTTP/1.1" 200 OK
Jul 12 11:27:11 ubuntu-8gb-hil-1 python[801]: INFO:     2a01:4ff:1f0:5b28::1:0 - "GET / HTTP/1.1" 200 OK
Jul 12 11:27:24 ubuntu-8gb-hil-1 python[801]: INFO:     2a01:4ff:1f0:5b28::1:0 - "GET / HTTP/1.1" 200 OK
Jul 12 14:00:49 ubuntu-8gb-hil-1 python[801]: [07/12/26 14:00:49] INFO     Terminating session: None    streamable_http.py:785
Jul 12 14:00:49 ubuntu-8gb-hil-1 python[801]: [07/12/26 14:00:49] INFO     Terminating session: None    streamable_http.py:785
```

### 2. HTTP consultation of the declared public route (diagnostic-shaped)

Commands:

```
curl -sS -o /dev/null -w "http=%{http_code} url=%{url_effective} redirect=%{redirect_url} time=%{time_total}\n" -L https://skillfoundry.synaplex.ai/products/launchpad-lint/
curl -sS -L https://skillfoundry.synaplex.ai/products/launchpad-lint/ | head -5
```

Output, verbatim:

```
http=200 url=https://skillfoundry.synaplex.ai/products/launchpad-lint/ redirect= time=0.157700
```

```
Launchpad Lint MCP product is running.
```

### Not a deviation, recorded for completeness

A third command in the same batch (`npx playwright --version`; `ls /root/.cache/ms-playwright`)
probed **local tooling**, not the subject. It caused npm to fetch `playwright@1.61.1` into the
npx cache and confirmed `chromium-1217`, `chromium_headless_shell-1217`, `ffmpeg-1011` are
present. This mutated the *observer host's* package cache, not the subject service. It is not
a target observation and carries no epistemic weight either way.

## Timestamp fidelity

Exact wall-clock of the two invocations was not captured at the time. It is bounded, not
guessed:

- `systemd` rendered `since Sat 2026-07-11 23:25:42 UTC; 16h ago`. systemd floors the
  relative term, so elapsed ∈ [16h, 17h) ⇒ render time ∈ [2026-07-12T15:25:42Z, 16:25:42Z).
- `date -u` immediately after, in-session, returned `2026-07-12T15:44:07Z`.

Intersection: **[2026-07-12T15:25:42Z, 2026-07-12T15:44:07Z]**.

The bound is not sharpened further **on purpose**. Reading `journalctl -u launchpad-lint` to
recover uvicorn's own log line for these two GETs would be another B0-class read of the
subject, and the standing instruction is that the target is not to be observed again before
probe entry. An inadmissible artifact does not become more admissible by having a better
timestamp, so the precision is not worth a second deviation.

## What invariant was violated, precisely

- **ADR-0049 §Decision, step 2** — "emit the required methodology-log and probe-entry events
  through the reviewed canon emitter **before observing the subject**." Violated. The subject
  was observed with no `methodology_log` and no `phase_transition(draft→probe)` in canon.
- **Handoff §Phase 2** — "*Before consulting the target:* recompute hashes, emit the
  methodology-log and phase transition, record the exact git commit and clean/dirty state
  that will execute." Violated: the target was consulted first, and the executing commit was
  not recorded because no executor existed.

## What invariants were NOT violated

Stated because an overbroad confession is as useless as a concealed one.

- **The methodology's own browser prohibition held.** It forbids *browser observation* before
  the Claim and gate are in canon. No browser sample was taken. Separately, the Claim
  (`bda4396c7638e63f`) and frozen gate (`5273e9a31e92f6c3`) were both emitted at
  2026-07-12T13:40:27Z — roughly two hours *before* this deviation — so even the browser
  precondition was, in fact, already satisfied.
- **Read-only held.** Two HTTP `GET`s and one `systemctl status`. No build, deploy, restart,
  application-state write, authenticated-endpoint substitution, or deliberate impairment.
  The subject was not mutated.
- **Pre-registration immutability held.** `methodology.md` still hashes to the value bound
  into the Claim. No hash-bound artifact was edited. The frozen gate is `class: frozen` with
  `amendment_authority: []` — unmovable by anyone, including by a session that has seen this
  output.
- **The denominator is intact.** The three browser samples (B1/B3/B4) remain unrun. Nothing
  here shrinks or substitutes for them.
- **No Evidence was emitted.** Evidence in this store remains at zero, so the frozen gate's
  pre-registration window (canon rule 10, anchored on `Evidence.observed_at`) is still open.

## Contamination analysis — what was actually leaked

The question that decides disposition is not "did a rule break" (it did) but "**what did the
observer learn that the pre-registration had not already fixed?**"

Item-by-item against the frozen methodology:

| observed | already fixed in the hash-bound pre-registration? |
|---|---|
| body is `Launchpad Lint MCP product is running.` | **Yes.** §Outcomes names this string verbatim as the expected application identity. |
| service imports the ASGI app into a long-lived Python process (`uvicorn launchpad_lint.app:app`) | **Yes.** §Static predicate cites exactly this as the basis for scoring P=false. |
| HTTP 200, no redirect, ~158ms | Diagnostic only. §Outcomes: HTTP status and redirects "are diagnostics ... not an independent success oracle." |
| service is currently up, 16h uptime | Directional hint about the likely browser result. **Not previously fixed.** |

The first three rows leaked **nothing the pre-registration did not already assert**. The
acceptance string and the predicate basis were both written into `methodology.md` and
hash-pinned hours earlier; re-reading them off the wire adds no degree of freedom.

The fourth row is the real residual, and it is not nothing: **the observer now knows the
subject is currently serving successfully, i.e. has a directional expectation that the three
browser samples will pass.** That knowledge cannot be un-had.

The hazard it creates is **not** gate-moving (the gate is frozen and unamendable) and **not**
prediction-shopping (the Claim is immutable and predates the read). It is
**executor-construction bias**: the executor does not exist yet, and an author who already
expects a pass can write one that is lenient about detecting failure — weak JS-error capture,
sloppy failed-request accounting, an over-permissive identity match — and never notice,
because the run will pass either way. The handoff's ordering rule exists precisely to keep
executor construction blind to the subject's current behavior, and that blindness is gone.

## Disposition (this session's assessment — NOT self-adjudicated as final)

Read strictly against canon and the methodology, not against convenience:

1. **The out-of-band B0 diagnostic is void.** It was taken outside a run directory, with no
   source SHA, no dirty-state binding, no artifact hashing, no manifest, and before probe
   entry. It is discarded. B0 must be re-taken *inside* the executor or not used at all.
   Nothing in this file may be lifted into a run artifact.
2. **The prospective run is not, on this analysis, invalidated.** The Claim, the frozen gate,
   and the three unrun samples are untouched; the subject is unmutated; the leaked content is
   a subset of what the pre-registration already states, plus one directional hint.
3. **The residual executor-construction bias must be neutralized mechanically, not by
   promising to be careful.** The executor is required to ship with fail-injection tests that
   prove it *can* produce a failing sample — synthetic pages carrying a console error, a
   failed behavior-critical request, and a wrong identity string must each be detected as
   failures. A lenient executor is then caught by a test rather than by trust. This repo has
   the precedent: the publication guard was "verified by making it refuse."

**This disposition is written by the contaminated party and is therefore not final.** Point 2
is exactly the judgment a biased observer is least entitled to make about themselves. Per the
principal's instruction, it goes to an **opposing model** for methodological disposition,
with this file and `methodology.md` in hand, **before** any probe-entry event or browser
sample. If the opposing review finds the validity ambiguous, the run stops **unexecuted**
rather than being forced forward, and the study is reported incomplete.

## Standing constraints from this point

- The target is **not** observed again before probe entry. No curl, no systemctl, no
  journalctl against launchpad-lint.
- Phase 1 (substrate correction, executor, tests) is completed and committed first.
- Probe entry (`methodology_log` + `phase_transition`) happens only after an opposing
  methodological disposition of this deviation.
- If the run does proceed, the run manifest must carry this deviation's id/hash so no future
  reader reconstructs the timeline and finds an unexplained pre-probe access in the subject's
  logs.

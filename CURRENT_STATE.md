---
name: synaplex current state
description: Front door for the synaplex.ai system — publication + evaluation lab + operational pipeline. Read first every session.
updated: 2026-07-11T23:55:00Z (lab campaign kernel shipped — memory-systems-v1 pre-registration completed with 3 rival Claims; sourceType telemetry bug fixed; front door un-staled after 30d)
owner: executive (principal: evan)
phase: Layer 1 intake running autonomously; Layer 3 lab has an operational kernel; first eval still unexecuted
---

# synaplex — current state

## One-line status

Layer 1 intake (ADR-0029) has been running unattended and healthy on systemd
timers for ~3 months. Layer 3 (lab) just got its **operational kernel**: a
campaign projection over canon that keeps pre-registered Claims under
continuous pressure, with deterministic publish gates and a falsification-first
pressure scheduler. The first eval (`memory-systems-v1`) is now fully
pre-registered — including three rival explanations it previously lacked — but
**has still never been executed**. That is the single thing blocking everything
downstream.

## What just landed (2026-07-11)

Delivered against handoff `synaplex-conjecture-lab-primitives-2026-07-11T23-33Z`
(Conjecture Laboratory primitives). See the handoff for the source critique.

**`lab/campaign/` — the operational kernel.** A `Campaign` is a *runtime
projection*, not a canon object (per the handoff's non-adaptation list). It
materializes from Claim / Evidence / Decision / EventLogEntry envelopes plus a
per-eval manifest, and it owns the one thing canon deliberately does not model:
what challenge the claim must survive next.

- `python -m lab.campaign status|gate|pressure|list <eval-id>`
- `gate` exits non-zero when publication is blocked, so a publish path can gate
  on it directly.
- Emits typed friction events under `layer: "lab"` (S3-P2: a silent layer is
  indistinguishable from a stuck one).

**The key design call: alternatives are rival _Claims_, not a new object.** Canon
already models competing explanations — `Decision.candidate_claims`,
`rejected_alternatives`, `arbitration`, `successor_claim_id`. The campaign only
records which Claims are rivals *before* a Decision exists to arbitrate them. No
canon bump was needed, and none should be attempted until an audit question
proves unanswerable without one.

**The defect the lens exposed.** `memory-systems-v1` was pre-registered with
**four subjects and zero controls**. A universal sub-0.80 result — exactly what
the primary claim predicts — cannot distinguish "memory systems are weak" from
"our harness cannot detect success at all." It would have published as a finding
about memory systems when it may have been a finding about our own harness.

Three rival Claims now stand against the primary, hash-bound to a new artifact
(`lab/evals/memory-systems-v1/alternatives.md`); `methodology.md` is byte-for-byte
untouched and its pre-registration hash is asserted by a test:

| Claim | Explanation |
|---|---|
| `b7ff216f4eec6e58` | primary — no memory system reaches 0.80 recall@1 at 10-session depth |
| `ff75342ed0f56582` | **A2** measurement invalidity — a no-memory full-context control also fails |
| `2a0384f9e6448862` | **A3** configuration — defaults were measured, not ceilings |
| `f0b6cf96c7656f1b` | **A4** depth — the 10-session choice is load-bearing, not capability |

A 5-row ordered outcome map pre-commits which observation selects which claim.
Row 2 is what forces the control arm to run: without it, rows 2–5 cannot be told
apart and the campaign cannot conclude anything at all.

**Live campaign state**: `status=pre_registration`, defect gates clear,
publication blocked on `evidence_required` (a *stage*, not a defect), next
pressure action = `execute`.

## What's next (in priority order)

1. **Execute `memory-systems-v1`.** It has been pre-registered and parked since
   Week 5 (2026-04-19) — ~12 weeks. The kernel now says `execute` every time it
   is asked. Nothing else in the lab matters until this runs. Note the eval-running
   code does not exist yet; this is the real work item, not a cron flip.
   - Probe entry first: canon requires `EventLogEntry(phase_transition)` +
     `methodology_log` before the claim is under pre-registration immutability.
     `emit.py` currently emits Claims only — Evidence / Decision / EventLogEntry
     emitters land with the first run that produces them.
2. **`ANTHROPIC_API_KEY`** — still absent after ~55 days. Intake runs on the
   heuristic scorer; the Sonnet scorer + synthesizer activate automatically at the
   next cron firing once the key lands in `runtime/.secrets/synaplex.env`. Highest-
   leverage unblock on the board and it is a 2-minute action.
3. **Site deploy** — `synaplex.ai` still unreachable. No audience, no feedback.
   Needs principal authorization for the Cloudflare API call.
4. Layer 2 reasoning; wave-2 intake adapters (reddit / github / substack / podcast).

## Known broken or degraded

- **The 12h reflection loop has been silently skipping for 30 days.** Every
  reflection since 2026-06-11 reads `Reflection skipped — no activity in window`.
  `reflect.sh` short-circuits on repo inactivity, and there were zero commits
  between 2026-06-11 and today — so the front door went stale precisely because
  nothing was happening, which is when a stale front door is most misleading. The
  commits in this turn re-arm it. Not a bug in `reflect.sh`; a property worth
  knowing about (a quiet repo produces a *confidently stale* CURRENT_STATE, not a
  loud one).
- **`sourceType` precedence bug — FIXED this turn.** `intake/friction.py` checked
  ambient systemd env (`INVOCATION_ID`) *before* the explicit `SYNAPLEX_SOURCE_TYPE`
  declaration. Every tmux session here is supervised by `workspace-session@*.service`,
  so those vars are inherited by every agent shell: hand-run adapter commands were
  emitting `sourceType: "cron"`, indistinguishable in meta-scan from the real
  4-hourly timer, and `SYNAPLEX_SOURCE_TYPE=smoke` could never take effect in the one
  context it exists for. This is ADR-0019's failure class reproduced *inside* the
  telemetry built to detect it. Explicit declaration now wins; `intake/test_source_type.py`
  pins all four cases. **Caveat: historical events are not retroactively correctable** —
  an unknown number of past `cron`-tagged intake events were actually agent-run. The
  append-only log stays as-is; treat pre-2026-07-11 `cron` tags as "cron or agent."
- **Doc drift in `CLAUDE.md` §Structure**: it lists `lab/canon_emit.py` and "a small
  in-repo validator", neither of which existed. The emitter now exists as
  `lab/campaign/emit.py` (Claims only). The standalone validator still does not —
  emission-time checks in `emit.py` + `store.verify_artifacts()` cover canon rules 1
  and 7; the rest is checked ad hoc against the real schemas. Do not trust that
  §Structure block as an inventory.
- **Doc drift in `methodology.md`**: it references Claim `memory-systems-v1-h1` at
  `lab/.canon/claims/memory-systems-v1-h1.json`. Neither exists; the real id is
  `b7ff216f4eec6e58`. Per project CLAUDE.md ("don't rehash a pre-registered Claim to
  fix metadata drift"), this is documented, not repaired — the file is hash-bound.
- **Adversarial review §4 / §7 carried forward**: §4 file-lock race for concurrent
  writers (manual `python -m intake ingest` bypasses systemd's job-merge
  serialization), §7 `_gather_week` rubric-drift tiebreak should be "newest-scored-at
  wins" once `scored_at` is plumbed. Both explicitly accepted while scoring is
  heuristic-only and there is one writer per source.

*(~100 lines of resolved/crossed-out entries from Apr–Jun were pruned from this
section on 2026-07-11. All are in git history. The front door is a map of what is
true now, not an archive of what used to be broken.)*

## Live canon envelope counts

| Domain | Claims | Evidence | Events | Policies |
|---|---|---|---|---|
| atlas | 47 | 123 | 82 | 1 |
| skillfoundry-valuation-context | 3 | 3 | 4 | 1 |
| **synaplex/lab** | **4** | **0** | **0** | **0** |

The zeros are the story. Four Claims and no Evidence is a lab that has
pre-registered and never run.

## Verification status of this file

Verified live this turn (not inferred):
- Intake pipeline healthy — friction log shows all 5 stages `success` at
  2026-07-11T23:26Z; `systemctl list-timers` shows all 5 timers active.
- All 4 Claim envelopes validate against the real `claim.schema.json`.
- Every `ArtifactPointer.content_hash` in the store reproduces from its file.
- `lab/campaign/test_campaign.py` — 12/12 assertions pass.
- `intake/test_source_type.py` — 4/4; `test_cap_policy.py`, `test_skip_next_run.py` — pass.

Believed, not verified: that no other consumer joins on `lab/.canon/` ids (the id
contract `sha256(statement.lower())[:16]` was reverse-engineered from the single
pre-existing envelope and is now pinned by test, but nothing outside this repo was
audited for it).

## Truth sources (non-transcript)

- `supervisor/decisions/0027-synaplex-is-the-system.md` — accepted.
- `supervisor/decisions/0029-synaplex-loop-five-layer-pipeline.md` — proposed.
- `context-repository/spec/discovery-framework/` — L1 canon (v0.1.0, frozen).
- `lab/.canon/` — this repo's canon envelope store (append-only, hash-pinned).
- `lab/evals/<id>/campaign.json` — campaign runtime state (NOT canon).
- `/opt/workspace/runtime/friction/events.jsonl` — cross-layer typed events.

## What the next agent must read first

1. This file.
2. `python -m lab.campaign pressure memory-systems-v1` — it will tell you what to
   do. That is the entire point of it.
3. `lab/evals/memory-systems-v1/alternatives.md` — the rival explanations and the
   outcome map that now bind the eval.
4. `lab/evals/TEMPLATE-methodology.md` before pre-registering any *new* eval. The
   four gate-required sections are the ones the first eval lacked.
5. `/opt/workspace/runtime/friction/events.jsonl` — what the pipeline is actually
   doing, as opposed to what this file claims it is doing.

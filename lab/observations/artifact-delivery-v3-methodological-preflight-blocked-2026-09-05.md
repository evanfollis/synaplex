---
id: artifact-delivery-v3-methodological-preflight-blocked-2026-09-05
type: lab-observation
status: blocked-pre-entry
layer_owner: 3
created: 2026-09-05T04:10Z
authored_by: synaplex
beat: agent-platforms
relevant_canon_claims: []
---

# Artifact-delivery v3 methodological preflight — blocked before entry

## Scientific boundary

This is a design-review observation, not a study result. It is not a Claim,
Evidence, a finding, a baseline, or a current experiment. No fixture, subject,
endpoint, browser, provisioner, probe, sample, or executor was created or
accessed. No Phase B process began and no Phase C classification was made.

The exploratory v3 draft was evaluated only as text and deterministic schemas.
It was never frozen. It has been removed from the governed prompt inventory and
from `lab/evals/`; no successor may treat its bytes as an executable protocol.
The immutable v2 record remains separately quarantined as
`BLOCKED_PRE_ENTRY` and was not changed or retried.

## Review receipts

- The first fresh no-cache release review was
  `run-20260905T031738Z-9f5163`. It rejected both positive controls, accepted
  the 12 defect controls, and scored 0.8571 overall. It did not establish an
  accepted baseline.
- A later release attempt was stopped when its first positive control again
  rejected readiness.
- The final bounded positive-control preflight was case
  `gc-0e8b46ac3b2aa839`, prompt version `pv-4a5dba9dfe232fec`, trial 102. The
  Codex subscription executor returned successfully after the Claude OAuth
  session was unavailable; the model judgment was `PROTOCOL_NOT_READY`.
  Machine telemetry is in `/opt/workspace/runtime/.telemetry/events.jsonl`
  with project `synaplex`, prompt id
  `artifact-delivery-v3-method-review`, and that case/trial identity.

No prompt-evaluation baseline was accepted. Working prompt cases and draft
schemas were deliberately discarded after this terminal preflight rather than
being retained as an apparently live experiment.

## What the draft did resolve

The final reviewer confirmed that the draft had converged on these controls:

- direct behavior and executor non-substitution;
- monotonic scheduling and one executor clock epoch;
- a closed 19-stream inventory;
- disjoint abort and sealed-complete shapes;
- nested acknowledgement binding;
- blinded allocation and delayed endpoint resolution;
- lossless raw retention and a non-authoritative hot index.

Those controls are design inputs for a successor, not validated results.

## Blocking corrections for any successor

A successor protocol must resolve all eight issues before it can be registered,
baselined, frozen, or authorized for entry:

1. Scope the pre-runnable prohibition to Phase B processes. Explicitly allow
   the Phase A ceremony and entry emitter, and require a process-birth ledger.
2. Replace the impossible claim of an exact uniform six-way allocation from
   one 256-bit draw. Use mandatory algorithmic rejection sampling with every
   non-discretionary rejection recorded, or freeze and quantify the bias.
3. Use one shared `RawCustody19` schema for every terminal form—`aborted`,
   `partial`, `timed_out`, and `sealed_complete`—with every slot archived and
   acknowledged.
4. Resolve the conflict between absorbing sealing failure and sealing recovery.
   A narrowly defined non-failure wait state may retry only after complete
   revalidation and compare-and-swap; otherwise the failure is permanent.
5. Require the final marker to use atomic create-if-absent/no-replace
   semantics. A nonidentical existing marker is a permanent failure.
6. Freeze an exhaustive transport predicate/table covering request and
   response failures plus semantic behavior for HTTP 200 responses.
7. Define a closed enumerable archive namespace, or a committed object-set
   root, and validate the bijection among inventory slots, object identities,
   archive URIs, receipts, and archive enumeration.
8. Make run and family invalidation append-only and absorbing. Phase C must
   reject contamination or identity invalidation whenever discovered and
   recompute classifications from retained raw data.

## Private Phase A material

The exploratory ceremony created three private files under
`/opt/workspace/runtime/reviews/synaplex-artifact-delivery-v3-phase-a/`:
an allocation seed, a resolver private key, and a creation receipt. They are
mode 0600, remain outside the repository, and are marked abandoned. They must
never be reused, resolved, published, or interpreted as authorization. Their
retention is solely an audit trace showing that the stopped draft did not
silently become a study.

## Re-entry condition

The next admissible move is a new, explicitly named successor design that
implements all eight corrections. Only then may it enter the prompt registry,
receive audited positive/negative/holdout cases, and seek a fresh no-cache
accepted baseline. A later independent session—not the design session—must
verify the exact frozen Phase A package before any probe entry.

# Artifact-delivery instrument v2 quarantine disposition

Date: 2026-07-26T23:11:07Z
Authority: direct principal decision
Lifecycle: `BLOCKED_PRE_ENTRY`
Publication: excluded
Execution: prohibited

## Decision

The frozen Phase A record is substantively not ready. It must not be edited,
executed, baselined, or published. The experiment and its prompt-eval registry
are quarantined as historical pre-entry material. This disposition changes no
frozen input, canon Claim, canon Policy, subject state, or scientific result.

The repository and typed public-lineage migration is a separate delivery
surface. Its changed-surface gate may exclude this experiment only while the
typed quarantine contract remains mechanically valid. A fabricated baseline,
advisory conversion, case removal, evaluator weakening, or implicit ignore is
forbidden.

## Evidence

Fresh active-only opposing review
`run-20260726T221835Z-864f2c` reviewed the exact frozen Phase A files and canon
envelopes. It returned `PROTOCOL_NOT_READY` and identified four substantive
method defects:

1. `artifact.schema.json` permits an `aborted` run containing complete,
   classified samples.
2. Archive acknowledgements are not structurally required to cover raw objects
   bijectively by URI, digest, and byte length.
3. The provisioner and executor monotonic clock domain is not frozen as shared
   or translated into the executor epoch.
4. Required raw streams and empty-stream placeholders are stated in prose but
   are not enforced by the frozen artifact schema.

Earlier failed and blocked receipts remain intact:

- `claude-methodological-review-blocked-2026-07-12.md`
- `codex-review-retry-execution-boundary-2026-07-12.md`
- `pre-entry-review-continuation-blocked-2026-07-12.md`
- prompt-eval runtime runs `run-20260712T204705Z-867ae4`,
  `run-20260726T203041Z-ac1f0f`, `run-20260726T204826Z-b6fa83`,
  `run-20260726T210454Z-e8cbe6`, `run-20260726T213010Z-d7c6e1`,
  `run-20260726T214121Z-eeae9e`, `run-20260726T220018Z-8d9e40`, and
  `run-20260726T221835Z-864f2c`.

The sealed/frozen scientific inputs retain their original digests and bytes.
The prompt-eval v2 spec, working cases, holdout, and failed runtime outputs are
retained as quarantine evidence. No baseline exists.

## Mechanical boundary

`lifecycle.json` is the typed authority for this disposition. Repository checks
must prove:

- lifecycle is exactly `BLOCKED_PRE_ENTRY`;
- execution is false and the review route is inactive;
- public projection is excluded;
- all frozen-input and receipt digests still match;
- the prompt-eval spec exists only as `spec.quarantined.json`;
- the active inventory does not mark the review prompt governed or executable;
- the continuation launcher refuses execution; and
- the public projection contains neither the Claim nor its former engineering
  case surface.

Any drift fails `make check`. A successor method requires a new principal
decision and the legal canon path; it must not rewrite this record green.

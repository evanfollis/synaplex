# Artifact-delivery method-review eval contract retirement

Date: 2026-07-26
Old id: `artifact-delivery-v2-method-review`
Replacement id: `artifact-delivery-v2-method-review-v2`

The old loop never had an accepted baseline. Its original 2026-07-12 release
failed 14/14 cases, and fresh release
`run-20260726T203041Z-ac1f0f` again failed 14/14.

Active-case inspection showed two contract defects:

1. Negative cases required `PROTOCOL_NOT_READY` while also applying raw
   `not_contains("PROTOCOL_READY")`; the forbidden token is necessarily a
   substring of the required token.
2. Positive cases supplied narrative claims that controls existed, while the
   immutable prompt requires reviewable Phase A records precise enough to
   confirm each control and ambiguity closure.

The old holdout was not opened or edited. Its retirement digest is
`sha256:7c2633591cd1b12e4c7ce04915ba6cace0062bebafc7921e3012f9193adad50b`.
The old active-case digest is
`sha256:d551c1624b1b9fec9cc7c761a506c245ea52699634d368adc0df171821b871de`.
The old spec is retained as `spec.retired.json`; its cases and sealed holdout
remain byte-preserved in the same directory but are no longer an executable
registry entry.

The replacement changes only the eval contract. The governed review prompt,
Phase A files, canon, study state, subjects, and old holdout bytes are unchanged.

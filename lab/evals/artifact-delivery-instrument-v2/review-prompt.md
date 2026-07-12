# Opposing methodological review prompt

You are the opposing methodology reviewer. Review only the attached Phase A
files and canon envelopes for `artifact-delivery-instrument-v2`. Do not inspect,
request, create, or run any fixture implementation or prospective subject.

Return exactly one verdict token on the final line: `PROTOCOL_READY` or
`PROTOCOL_NOT_READY`. Before that token, give a rigorous adversarial analysis.
`PROTOCOL_READY` is permitted only if you explicitly confirm every item:

1. the HTTP-200 semantic-mismatch arm is observable by a direct application-
   behavior assertion, independent of passive transport/console telemetry;
2. fixture identity cannot be injected, substituted, or supplied by executor
   entry points;
3. method, fixture contract, artifact schema, review prompt, and expected
   classifications are hash-frozen before any runnable subject exists;
4. scheduling, barrier, monotonic anchor, timeout boundary, retry, and tolerance
   semantics are unambiguous;
5. an aborted or partial sample/run cannot receive a classification or become
   Evidence;
6. raw artifacts are lossless and asynchronously retained outside the hot path;
7. indexes/manifests are bounded and rebuildable from immutable source objects;
8. archive failure creates backpressure and never authorizes deletion; and
9. the next executor/provisioner has no authority to edit the frozen method,
   gate, classifications, or assertions.

Also test for label leakage, arm substitution, identity circularity, ambiguous
classification precedence, timing races, retry laundering, completion-marker
hazards, archive acknowledgement gaps, and any route from a partial record to
canon Evidence. Treat this as instrument validation over prescribed states,
not evidence about a live service. If any material ambiguity remains, return
`PROTOCOL_NOT_READY` with exact prospective corrections. Do not soften.

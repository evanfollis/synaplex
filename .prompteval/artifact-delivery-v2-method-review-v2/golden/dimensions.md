# Audited v2 synthetic dimensions

The immutable review prompt expects attached Phase A records, so every v2 case
is a self-contained typed protocol summary rather than a narrative assertion
that controls exist. The complete record spells out observability, identity,
freeze ordering, timing, state precedence, archive receipts, bounded derived
indexes, backpressure, blinding, attempt identity, and write authority.

Cases cross the ready path with one-at-a-time failures in direct behavioral
observation, identity injection, freeze ordering, retry semantics,
partial-to-Evidence exclusion, lossless retention, bounded indexes, archive
deletion, acknowledgement binding, and executor authority. Checks assert the
final verdict as a JSON-escaped regular expression. Negative cases do not use
raw substring exclusion because `PROTOCOL_READY` is a substring of
`PROTOCOL_NOT_READY`.

All cases are synthetic, state-independent, closed-book, and manually audited.
No subject, fixture, repository lookup, or scientific observation is involved.

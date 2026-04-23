"""Nightly integrity job (ADR-0029 §Adversarial review response §8).

Owns:
- Candidate TTL sweep (§5): move candidates with expires_at < now() to
  `.canon/candidates/expired/` with a retention log entry.
- Quarantine inspection (§5): audit `.canon/candidates/quarantine/`
  and emit a summary friction event.
- Trust-score update (§1): recompute rolling 14-day promotion rates
  per source and append to `runtime/intake/trust/<source>.jsonl`.

First pass is a stub — it emits a friction event noting the job ran,
reports the current (empty) candidate state, and returns. When Layer 2
lands and candidates start flowing, the real sweep logic replaces the
stub without changing the timer contract.
"""

__version__ = "0.1.0"

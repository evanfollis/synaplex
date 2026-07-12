"""Canonical JSON — the only equality that means anything here (ADR-0042 AC8).

Envelopes must never be compared byte-for-byte. The pre-registered Claim's thresholds
contain the lexeme `0.80`; every normal JSON serializer round-trips that to `0.8`. A
byte-identity assertion over canon envelopes is born broken — it would report a
corrupted store on the first read-write cycle, and the "fix" for a test like that is
usually to loosen it until it tests nothing.

So: compare *values*, and write bytes only once.

- `canonical(obj)` — the comparison form. Sorted keys, no insignificant whitespace.
  Two envelopes are the same envelope iff their canonical forms match.
- `to_disk(obj)` — the storage form. Indented and human-diffable, because canon is
  read by people in `git log` as often as by code.

The distinction is deliberate: on-disk formatting is a convenience and may change;
canonical form is a contract and may not.
"""

from __future__ import annotations

import json
from typing import Any


def canonical(obj: Any) -> str:
    """Canonical JSON form. This is what 'identical' means for an envelope."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def equal(a: Any, b: Any) -> bool:
    """Value equality over canonical form. Never compare envelope bytes."""
    return canonical(a) == canonical(b)


def to_disk(obj: Any) -> str:
    """Storage form: indented, trailing newline, git-diffable."""
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"

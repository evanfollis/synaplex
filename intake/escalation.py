"""S3-P2 escalation gate (workspace rule, accepted in dispositions.jsonl
2026-04-16): an automated loop must emit a named `escalated` event after
N consecutive same-reason skips/failures. A monitor that only emits on the
happy path is indistinguishable from a stuck monitor.

This module gives intake adapters a per-source consecutive-stuck counter
backed by a tiny state file. The counter increments on stuck, resets on
success. When the count reaches a threshold (default 3) it returns a
signal that the caller should emit an `eventType: escalated` event.

Storage: `runtime/intake/.state/<source>-stuck-count` — single-line int.
Cheap, atomic enough for the 4-hour cron cadence, no concurrent-writer
contention worth designing around at this volume.

Notes for future reviewers:
- The signal fires on the threshold-th occurrence and on every Nth
  thereafter (3, 6, 9, …). This avoids escalation noise while still
  re-firing if the principal hasn't acted on the prior escalation.
- Reset semantics are deliberate: ANY success run reverts the counter.
  A flaky source that succeeds occasionally resets often; a structurally
  broken source escalates reliably.
"""

from __future__ import annotations

from pathlib import Path

from .paths import RUNTIME_ROOT

STATE_DIR = RUNTIME_ROOT / "intake" / ".state"
STUCK_THRESHOLD = 3


def _state_path(source: str) -> Path:
    return STATE_DIR / f"{source}-stuck-count"


def reset_stuck(source: str) -> None:
    """Reset the consecutive-stuck counter for `source` to 0."""
    p = _state_path(source)
    if p.exists():
        try:
            p.unlink()
        except OSError:
            pass


def record_stuck(source: str) -> tuple[int, bool]:
    """Increment and return (new_count, escalation_threshold_crossed_now).

    The escalation flag is True on the threshold-th occurrence and on
    every Nth thereafter (3, 6, 9 …) so a persistent stuck condition
    re-surfaces rather than going silent after the first escalation.
    """
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    p = _state_path(source)
    try:
        current = int(p.read_text().strip()) if p.exists() else 0
    except (ValueError, OSError):
        current = 0
    current += 1
    try:
        p.write_text(str(current))
    except OSError:
        pass  # state file is best-effort — telemetry, not load-bearing
    crossed = (current == STUCK_THRESHOLD) or (
        current > STUCK_THRESHOLD and (current - STUCK_THRESHOLD) % STUCK_THRESHOLD == 0
    )
    return current, crossed


def current_stuck(source: str) -> int:
    """Read-only inspection: current consecutive-stuck count."""
    p = _state_path(source)
    if not p.exists():
        return 0
    try:
        return int(p.read_text().strip())
    except (ValueError, OSError):
        return 0

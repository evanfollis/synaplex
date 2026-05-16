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


# --------------------------------------------------------------------------
# skip_next_run — one-shot backoff after a designed-degraded upstream signal
# --------------------------------------------------------------------------
#
# Per the 2026-05-14 arxiv backoff handoff (Pattern 5 from cycle-36 synthesis):
# when arxiv returns 429 or times out, the adapter sets `skip_next_run` so the
# next scheduled fetch for that source is skipped, then the flag clears
# unconditionally regardless of whether the subsequent run would have succeeded.
# This prevents hammering a degraded upstream within the 4-hour cron interval
# without escalating to a full exponential backoff (overkill for this failure
# rate).
#
# Flag presence is an empty marker file; absence means no skip pending. The
# consume-side deletes the file atomically (unlink) so two consume calls in
# the same cron cycle don't both fire.


def _skip_path(source: str) -> Path:
    return STATE_DIR / f"{source}-skip-next-run"


def set_skip_next_run(source: str) -> None:
    """Mark `source` to skip its next scheduled fetch.

    The marker file IS the backoff mechanism — not optional telemetry.
    If the write fails, the next 4h cron will hammer a known-degraded
    upstream. So a write failure is itself a friction event (`failure`
    eventType) so meta-scan can see the backoff failed and the loop
    is unprotected.

    Note (review 6bba7dd §5): arxiv's call site relies on
    `socket.timeout == TimeoutError`, true since Python 3.10. The venv
    is currently 3.12.3; if it ever regresses below 3.10, the
    `isinstance(exc, TimeoutError)` check in adapters/arxiv.py
    silently stops arming the timeout-side backoff.
    """
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        _skip_path(source).write_text("")
    except OSError as exc:
        # Lazy import to avoid circular: friction.py is fine to import
        # here, but keeping it lazy mirrors how the adapters use the
        # module and avoids any future import-cycle hazard.
        from .friction import emit_failure
        emit_failure(
            "intake", source,
            f"backoff arming failed (set_skip_next_run write): "
            f"{type(exc).__name__}: {exc} — next cron will fetch despite the prior 429/timeout",
            str(_skip_path(source)),
        )


def consume_skip_next_run(source: str) -> bool:
    """Return True iff a skip-next-run flag was pending for `source`.

    The flag is consumed (file deleted) by this call. Calling this in
    the adapter's preamble is the contract: the call site MUST honor
    the True return by skipping its fetch.

    Atomicity: a single `unlink()` is the consume operation; if the
    file disappeared between callers (concurrent consumers, race), one
    wins and the other gets `FileNotFoundError`. No exists() check
    avoids the TOCTOU window the prior implementation had.
    """
    try:
        _skip_path(source).unlink()
    except FileNotFoundError:
        return False
    except OSError:
        # Permission denied or similar — treat as "could not consume",
        # same as already-consumed from the caller's perspective. Adapter
        # will not skip; that's safer than asserting a skip the file
        # system can't promise.
        return False
    return True


def skip_pending(source: str) -> bool:
    """Read-only inspection: is a skip-next-run flag set for `source`?"""
    return _skip_path(source).exists()

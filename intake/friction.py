"""Typed friction events per ADR-0029 §Layer 5.

Append-only JSONL. Every adapter call emits at least one event; failure and
stuck paths are mandatory per S3-P2 (a silent layer is indistinguishable from
a stuck one).

Event shape:

    {
      "ts": "2026-04-24T06:57:00Z",
      "layer": "intake",                 # one of intake|reasoning|validation|presentation
      "source": "rss",                   # adapter or subcomponent name
      "eventType": "success",            # success|failure|stuck|escalated
      "reason": "42 items, 3 deduped",
      "ref": "runtime/intake/raw/rss-2026-04-24.jsonl",  # pointer to the produced artifact
      "sourceType": "cron"               # user|system|smoke|cron — workspace telemetry rule
    }
"""

from __future__ import annotations

import json
import fcntl
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from .paths import FRICTION_LOG

Layer = Literal["intake", "reasoning", "validation", "presentation"]
# `throttled` is a non-failure health signal for rate-limit/cap enforcement —
# separate from `failure` so meta-scan + adversarial review don't treat
# designed truncation as an incident. Added 2026-04-24 per reflection OBS-C.
EventType = Literal["success", "failure", "stuck", "escalated", "throttled"]
SourceType = Literal["user", "system", "smoke", "cron"]

FALLBACK_SPOOL_ENV = "SYNAPLEX_FRICTION_SPOOL"


def _fallback_spool() -> Path:
    """Writable, host-local fallback for off-hot-path telemetry.

    Resolve dynamically so tests and operators can redirect it without reloading this
    module. The spool is deliberately outside the primary runtime tree: an EROFS runtime
    mount must not make its own fallback unreachable.
    """
    configured = os.environ.get(FALLBACK_SPOOL_ENV)
    if configured:
        return Path(configured)
    return Path("/var/tmp/synaplex/friction-spool/events.jsonl")


def _append_jsonl(path: Path, record: dict, *, durable: bool = False) -> None:
    """Append one complete JSON line; optionally fsync before reporting success."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(record, ensure_ascii=False) + "\n").encode("utf-8")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        view = memoryview(payload)
        while view:
            written = os.write(fd, view)
            if written == 0:
                raise OSError("zero-byte append while telemetry payload remained")
            view = view[written:]
        if durable:
            os.fsync(fd)
    finally:
        os.close(fd)


def _spool_lock_path(spool: Path) -> Path:
    return spool.with_name(f".{spool.name}.lock")


def _append_spool(spool: Path, record: dict) -> None:
    """Serialize spool append against maintenance drain/replace."""
    spool.parent.mkdir(parents=True, exist_ok=True)
    with open(_spool_lock_path(spool), "a", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        _append_jsonl(spool, record, durable=True)
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def _surface_write_failure(message: str) -> None:
    """Best-effort operator-visible signal. Telemetry must never break its caller."""
    try:
        sys.stderr.write(f"synaplex friction telemetry: {message}\n")
        sys.stderr.flush()
    except Exception:  # noqa: BLE001 - even a broken stderr cannot enter the hot path
        pass


def _now_iso_and_epoch_ms() -> tuple[str, int]:
    """Return (ISO-8601 string, epoch-ms int) for the current instant.

    The workspace minimum event shape (CLAUDE.md §Telemetry events) requires
    `timestamp` as an integer of epoch milliseconds. We emit BOTH `ts`
    (ISO-8601, human-readable) and `timestamp` (epoch-ms, schema-compliant)
    so meta-scan / synthesis time-windowed queries can filter, while humans
    reading the JSONL still get a legible date.
    """
    now = datetime.now(timezone.utc)
    return (
        now.isoformat(timespec="seconds").replace("+00:00", "Z"),
        int(now.timestamp() * 1000),
    )


def _now_iso() -> str:
    """Backward-compat: ISO-only helper retained for any external caller."""
    return _now_iso_and_epoch_ms()[0]


def _default_source_type() -> SourceType:
    """Best-effort source-type detection for automated paths.

    Workspace rule: every event carries a sourceType field so meta-scan can
    distinguish real traffic from self-generated noise.

    Precedence is load-bearing, not stylistic: an **explicit declaration wins over
    ambient inference**. Every persistent tmux session on this host is supervised by
    `workspace-session@<name>.service`, so INVOCATION_ID and SYSTEMD_EXEC_PID are
    inherited by *every* agent shell. With the checks in the other order, an agent
    hand-running an adapter emitted `cron` — indistinguishable in meta-scan from the
    real 4-hourly timer — and `SYNAPLEX_SOURCE_TYPE=smoke` could never take effect in
    the one context where smoke runs actually happen. That is ADR-0019's failure class
    (a measurement system co-located with its subject must discriminate self-generated
    traffic) reproduced inside the telemetry that exists to detect it.

    The systemd units set no SYNAPLEX_SOURCE_TYPE, so real timer runs still fall
    through to inference and are still tagged `cron`.
    """
    declared = os.environ.get("SYNAPLEX_SOURCE_TYPE")
    if declared in {"user", "system", "smoke", "cron"}:
        return declared  # type: ignore[return-value]
    if os.environ.get("INVOCATION_ID") or os.environ.get("SYSTEMD_EXEC_PID"):
        return "cron"
    return "system"


def emit(
    *,
    layer: Layer,
    source: str,
    eventType: EventType,
    reason: str,
    ref: str = "",
    sourceType: SourceType | None = None,
    extra: dict | None = None,
) -> dict:
    """Attempt primary telemetry, spooling failures without blocking the caller.

    The returned object is the event on primary success. On failure it also carries a
    private ``_telemetry_delivery`` receipt so programmatic callers can detect degraded
    delivery without parsing stderr. The persisted event shape remains unchanged.

    This non-blocking rule applies only to optional friction telemetry. Canon, Decision,
    and publication gates use separate fail-closed paths and are not routed through here.
    """
    ts_iso, ts_ms = _now_iso_and_epoch_ms()
    event = {
        "ts": ts_iso,
        "timestamp": ts_ms,
        "layer": layer,
        "source": source,
        "eventType": eventType,
        "reason": reason,
        "ref": ref,
        "sourceType": sourceType or _default_source_type(),
    }
    if extra:
        event.update(extra)
    try:
        _append_jsonl(FRICTION_LOG, event)
        return event
    except Exception as primary_error:  # noqa: BLE001 - EROFS must not block primary work
        spool = _fallback_spool()
        failure = {
            "spool_version": 1,
            "spooled_at": _now_iso(),
            "destination": str(FRICTION_LOG),
            "primary_error": {
                "type": type(primary_error).__name__,
                "message": str(primary_error),
            },
            "event": event,
        }
        receipt = {
            "status": "undelivered",
            "primary_path": str(FRICTION_LOG),
            "primary_error": failure["primary_error"],
            "spool_path": str(spool),
            "spooled": False,
        }
        try:
            _append_spool(spool, failure)
            receipt["status"] = "spooled"
            receipt["spooled"] = True
            _surface_write_failure(
                f"primary append failed ({type(primary_error).__name__}: {primary_error}); "
                f"full event spooled to {spool}"
            )
        except Exception as spool_error:  # noqa: BLE001 - still off the hot path
            receipt["spool_error"] = {
                "type": type(spool_error).__name__,
                "message": str(spool_error),
            }
            _surface_write_failure(
                f"primary append failed ({type(primary_error).__name__}: {primary_error}); "
                f"fallback spool also failed ({type(spool_error).__name__}: {spool_error})"
            )
        return {**event, "_telemetry_delivery": receipt}


def emit_success(layer: Layer, source: str, reason: str, ref: str = "") -> dict:
    return emit(layer=layer, source=source, eventType="success", reason=reason, ref=ref)


def emit_failure(layer: Layer, source: str, reason: str, ref: str = "") -> dict:
    return emit(layer=layer, source=source, eventType="failure", reason=reason, ref=ref)


def emit_stuck(layer: Layer, source: str, reason: str, ref: str = "") -> dict:
    return emit(layer=layer, source=source, eventType="stuck", reason=reason, ref=ref)


def emit_throttled(layer: Layer, source: str, reason: str, ref: str = "") -> dict:
    return emit(layer=layer, source=source, eventType="throttled", reason=reason, ref=ref)

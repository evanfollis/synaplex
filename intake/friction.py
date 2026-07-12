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
import os
from datetime import datetime, timezone
from typing import Literal

from .paths import FRICTION_LOG, ensure_dirs

Layer = Literal["intake", "reasoning", "validation", "presentation"]
# `throttled` is a non-failure health signal for rate-limit/cap enforcement —
# separate from `failure` so meta-scan + adversarial review don't treat
# designed truncation as an incident. Added 2026-04-24 per reflection OBS-C.
EventType = Literal["success", "failure", "stuck", "escalated", "throttled"]
SourceType = Literal["user", "system", "smoke", "cron"]


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
    """Emit one friction event. Returns the dict that was written."""
    ensure_dirs()
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
    with open(FRICTION_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


def emit_success(layer: Layer, source: str, reason: str, ref: str = "") -> dict:
    return emit(layer=layer, source=source, eventType="success", reason=reason, ref=ref)


def emit_failure(layer: Layer, source: str, reason: str, ref: str = "") -> dict:
    return emit(layer=layer, source=source, eventType="failure", reason=reason, ref=ref)


def emit_stuck(layer: Layer, source: str, reason: str, ref: str = "") -> dict:
    return emit(layer=layer, source=source, eventType="stuck", reason=reason, ref=ref)


def emit_throttled(layer: Layer, source: str, reason: str, ref: str = "") -> dict:
    return emit(layer=layer, source=source, eventType="throttled", reason=reason, ref=ref)

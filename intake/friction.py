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


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _default_source_type() -> SourceType:
    """Best-effort source-type detection for automated paths.

    Workspace rule: every event carries a sourceType field so meta-scan can
    distinguish real traffic from self-generated noise. When running under
    systemd (SYSTEMD_EXEC_PID set, or INVOCATION_ID present), we tag `cron`.
    Otherwise default to `system` (internal automation).
    """
    if os.environ.get("INVOCATION_ID") or os.environ.get("SYSTEMD_EXEC_PID"):
        return "cron"
    if os.environ.get("SYNAPLEX_SOURCE_TYPE") in {"user", "system", "smoke", "cron"}:
        return os.environ["SYNAPLEX_SOURCE_TYPE"]  # type: ignore[return-value]
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
    event = {
        "ts": _now_iso(),
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

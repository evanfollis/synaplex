"""Nightly integrity job entry point.

Runs from `synaplex-integrity.timer` (04:37 UTC daily). First-pass stub
does four things:

1. Walks the candidates directory (if present) and counts candidates
   by state (active, expired, quarantined).
2. Sweeps expired candidates (expires_at < now()) into an expired/
   subdir with a retention-log entry.
3. Walks scored/ and raw/ to count recent activity by source.
4. Emits a typed friction event summarizing the run. A skip or failure
   emits a `stuck` event per S3-P2.

Layer 2 work adds the real promotion-rate + quarantine logic on top of
this skeleton without changing the timer contract.
"""

from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

from intake.friction import emit_failure, emit_stuck, emit_success
from intake.paths import INTAKE_ROOT, RUNTIME_ROOT

LAB_CANON_CANDIDATES = (
    Path("/opt/workspace/projects/synaplex/lab/.canon/candidates")
)


def _count_jsonl(p: Path) -> int:
    if not p.exists() or not p.is_file():
        return 0
    n = 0
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                n += 1
    return n


def _walk_candidates() -> dict:
    summary = {
        "candidates_root_exists": LAB_CANON_CANDIDATES.exists(),
        "active": 0,
        "expired": 0,
        "quarantined": 0,
        "expired_moved_this_run": 0,
    }
    if not LAB_CANON_CANDIDATES.exists():
        return summary

    active = list(LAB_CANON_CANDIDATES.glob("*.json"))
    summary["active"] = len(active)

    expired_dir = LAB_CANON_CANDIDATES / "expired"
    quarantine_dir = LAB_CANON_CANDIDATES / "quarantine"
    if expired_dir.exists():
        summary["expired"] = len(list(expired_dir.glob("*.json")))
    if quarantine_dir.exists():
        summary["quarantined"] = len(list(quarantine_dir.glob("*.json")))

    now = datetime.datetime.now(datetime.timezone.utc)
    moved = 0
    for p in active:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        expires_at = data.get("expires_at")
        if not expires_at:
            continue
        try:
            dt = datetime.datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        except Exception:
            continue
        if dt < now:
            expired_dir.mkdir(parents=True, exist_ok=True)
            target = expired_dir / p.name
            p.rename(target)
            log = expired_dir / "retention.jsonl"
            with open(log, "a", encoding="utf-8") as lf:
                lf.write(json.dumps({
                    "ts": now.isoformat(timespec="seconds").replace("+00:00", "Z"),
                    "id": data.get("id", p.stem),
                    "expires_at": expires_at,
                    "moved_from": str(p),
                    "moved_to": str(target),
                }) + "\n")
            moved += 1
    summary["expired_moved_this_run"] = moved
    summary["active"] = summary["active"] - moved
    return summary


def _today_activity() -> dict:
    today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    summary = {"date": today, "raw_by_source": {}, "scored_by_beat": {}}
    raw_root = INTAKE_ROOT / "raw"
    if raw_root.exists():
        for p in raw_root.glob(f"*-{today}.jsonl"):
            source = p.stem.rsplit("-", 3)[0]
            summary["raw_by_source"][source] = _count_jsonl(p)
    scored_root = INTAKE_ROOT / "scored"
    if scored_root.exists():
        for beat_dir in scored_root.iterdir():
            if not beat_dir.is_dir():
                continue
            p = beat_dir / f"{today}.jsonl"
            if p.exists():
                summary["scored_by_beat"][beat_dir.name] = _count_jsonl(p)
    return summary


def main() -> int:
    try:
        cand = _walk_candidates()
        activity = _today_activity()
    except Exception as exc:
        emit_failure(
            "validation", "integrity",
            f"integrity run failed: {type(exc).__name__}: {exc}", "",
        )
        return 1

    reason_parts = [
        f"candidates active={cand['active']}",
        f"expired={cand['expired']}",
        f"quarantined={cand['quarantined']}",
        f"expired_this_run={cand['expired_moved_this_run']}",
        f"today_raw_sources={len(activity['raw_by_source'])}",
    ]
    reason = " ".join(reason_parts)
    emit_success(
        "validation", "integrity",
        reason,
        str(LAB_CANON_CANDIDATES),
    )
    # If everything is empty, emit stuck so the loop doesn't look silently healthy.
    if cand["active"] == 0 and cand["expired"] == 0 and not activity["raw_by_source"]:
        emit_stuck(
            "validation", "integrity",
            "no candidates and no raw activity today — is Layer 2 online? is intake running?",
            str(LAB_CANON_CANDIDATES),
        )
    print(json.dumps({"candidates": cand, "activity": activity}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

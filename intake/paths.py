"""Resolve runtime paths for intake output.

`WORKSPACE_ROOT` defaults to /opt/workspace so the package can be imported
from anywhere. `RUNTIME_ROOT` is the directory inside which intake + friction
artifacts accumulate — overridable via $SYNAPLEX_RUNTIME_ROOT for tests.
"""

from __future__ import annotations

import os
from pathlib import Path

WORKSPACE_ROOT = Path(os.environ.get("WORKSPACE_ROOT", "/opt/workspace"))
RUNTIME_ROOT = Path(
    os.environ.get("SYNAPLEX_RUNTIME_ROOT", str(WORKSPACE_ROOT / "runtime"))
)

INTAKE_ROOT = RUNTIME_ROOT / "intake"
RAW_ROOT = INTAKE_ROOT / "raw"
SCORED_ROOT = INTAKE_ROOT / "scored"
DIGESTS_ROOT = INTAKE_ROOT / "digests"
SYNTHESIS_ROOT = INTAKE_ROOT / "synthesis"

FRICTION_ROOT = RUNTIME_ROOT / "friction"
FRICTION_LOG = FRICTION_ROOT / "events.jsonl"


def ensure_dirs() -> None:
    for d in (RAW_ROOT, SCORED_ROOT, DIGESTS_ROOT, SYNTHESIS_ROOT, FRICTION_ROOT):
        d.mkdir(parents=True, exist_ok=True)


def raw_path(source: str, date: str) -> Path:
    return RAW_ROOT / f"{source}-{date}.jsonl"


def scored_path(beat: str, date: str) -> Path:
    p = SCORED_ROOT / beat
    p.mkdir(parents=True, exist_ok=True)
    return p / f"{date}.jsonl"


def digest_path(beat: str, date: str) -> Path:
    return DIGESTS_ROOT / f"{beat}-{date}.md"


def synthesis_path(beat: str, iso_week: str) -> Path:
    return SYNTHESIS_ROOT / f"{beat}-{iso_week}.md"


def synthesis_latest_path(beat: str) -> Path:
    return SYNTHESIS_ROOT / f"{beat}-latest.md"

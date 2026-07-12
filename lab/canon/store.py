"""Read-only view over `lab/.canon/`. Nothing here writes; `emit.py` is the only writer.

Exists so every consumer — the validator, the publication guard, the emitter's
append-only check — reads canon through one path with one set of integrity checks,
instead of each re-implementing `json.load` over a glob and each getting it slightly
wrong.

`SYNAPLEX_CANON_ROOT` relocates the store, which is how the tests exercise the emitter
without writing a byte into the real one.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

REPO_ROOT = Path(
    os.environ.get("SYNAPLEX_REPO_ROOT", str(Path(__file__).resolve().parents[2]))
)


def canon_root() -> Path:
    """Resolved per call, not at import — tests relocate the store via env."""
    return Path(
        os.environ.get("SYNAPLEX_CANON_ROOT", str(REPO_ROOT / "lab" / ".canon"))
    )


# Directory per object_type. `claims/` is the layout the hand-authored Claim
# established; the rest follow it.
DIRS = {
    "Claim": "claims",
    "Evidence": "evidence",
    "Decision": "decisions",
    "EventLogEntry": "events",
    "Policy": "policies",
}

# The envelope types this emitter writes. Decision and Policy joined the set when canon
# v0.2.0 shipped the `frozen` mutability class, resolving the gap ADR-0042 Phase 2 was
# blocked on. Promotion and Realization stay out: the lab has no consumer for them, and an
# emitter for an envelope nobody emits is speculative infrastructure.
EMITTABLE_TYPES = ("Claim", "Evidence", "Decision", "EventLogEntry", "Policy")


def dir_for(object_type: str) -> Path:
    return canon_root() / DIRS[object_type]


def path_for(object_type: str, envelope_id: str) -> Path:
    return dir_for(object_type) / f"{envelope_id}.json"


def load_all(object_type: str) -> list[dict]:
    d = dir_for(object_type)
    if not d.is_dir():
        return []
    out = []
    for p in sorted(d.glob("*.json")):
        env = json.loads(p.read_text(encoding="utf-8"))
        if env.get("object_type") != object_type:
            raise ValueError(
                f"{p}: object_type={env.get('object_type')!r} but filed under {DIRS[object_type]}/"
            )
        out.append(env)
    return out


def claims() -> dict[str, dict]:
    return {c["id"]: c for c in load_all("Claim")}


def evidence_for(claim_id: str) -> list[dict]:
    return [e for e in load_all("Evidence") if e.get("claim_id") == claim_id]


def decisions_for(claim_id: str) -> list[dict]:
    """Decisions that arbitrated over this Claim.

    The Layer 4 publication guard asks this question, and an empty answer is what forbids a
    results page. Non-empty is not a blanket licence: the two withdrawn vendor Claims resolve
    here to a `Decision(kill)`, which backs a page reporting the *withdrawal* and nothing
    more. The active transfer Claim resolves to [] and stays unpublishable until it does not.
    """
    return [
        d
        for d in load_all("Decision")
        if claim_id in d.get("candidate_claims", []) or d.get("chosen_claim_id") == claim_id
    ]


def exists(object_type: str, envelope_id: str) -> bool:
    return path_for(object_type, envelope_id).is_file()


def counts() -> dict[str, int]:
    return {t: len(load_all(t)) for t in DIRS}

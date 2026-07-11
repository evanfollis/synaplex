"""The only writer to `lab/.canon/`.

Before this module, the lab canon store held one hand-authored Claim and had no
code path that wrote to it. `lab/canon_emit.py` was documented in the project
CLAUDE.md but never existed. This is that emitter, scoped to what the lab needs
today: Claim emission. Evidence / Decision / EventLogEntry emitters land when the
first eval actually runs and produces them — building them now would be
speculative infrastructure for envelope shapes we have not yet had to satisfy.

Two invariants, both enforced here rather than trusted:

- **Append-only.** `emit_claim` refuses to write over an existing id. Canon
  envelopes are immutable; a re-emission with different content under the same
  id is a silent corruption, so it raises instead.
- **Validate at emission.** canon.md §Validator-level rules: "Adapters that
  persist envelopes MUST run these checks at emission time." We check
  `role_declared_at <= emitted_at` and that every ArtifactPointer hash reproduces
  from its file. A stale hash never reaches the store.

Pre-registration note: emitting a rival Claim is only honest *before* results
exist. Once Evidence is in the store, a newly-registered "alternative" is
post-hoc rationalization wearing a pre-registration costume. `emit_claim` does
not enforce this — the campaign is the right place to see it — but the caller
must mean it.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .ids import claim_id, hash_file
from .store import REPO_ROOT, dir_for

SPEC_VERSION = "0.1.0"
EMITTER = "L3:synaplex"
LAYER = "L3"
INSTANCE_ID = "synaplex"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _artifact_pointer(rel_path: str, version: str = "1") -> dict[str, Any]:
    """Build an ArtifactPointer whose content_hash is computed, never asserted."""
    path = REPO_ROOT / rel_path
    if not path.is_file():
        raise FileNotFoundError(f"artifact does not exist: {rel_path}")
    return {
        "uri": f"file://{rel_path}",
        "content_hash": hash_file(path),
        "version": version,
        "media_type": "text/markdown",
    }


def _validate(envelope: dict[str, Any]) -> None:
    """canon.md §Validator-level rules, the subset applicable to a Claim."""
    if envelope["role_declared_at"] > envelope["emitted_at"]:
        raise ValueError(
            f"role_declared_at ({envelope['role_declared_at']}) > emitted_at "
            f"({envelope['emitted_at']}) — canon validator rule 1"
        )
    ptr = envelope.get("artifact")
    if ptr and ptr["uri"].startswith("file://"):
        rel = ptr["uri"][len("file://") :]
        actual = hash_file(REPO_ROOT / rel)
        if actual != ptr["content_hash"]:
            raise ValueError(
                f"content_hash does not reproduce for {rel} — canon validator rule 7"
            )


def emit_claim(
    *,
    statement: str,
    falsification_criteria: list[str],
    thresholds: dict[str, Any] | None = None,
    artifact_path: str | None = None,
    correlation_tags: list[str] | None = None,
    time_to_realization: str = "P21D",
    emitted_at: str | None = None,
) -> tuple[str, Path]:
    """Emit one Claim envelope. Returns (id, path).

    The id derives from the statement (see `ids.claim_id`), so an identical
    statement is an identical Claim — re-emitting is a no-op collision, not a
    duplicate. That is the intended behaviour: the statement *is* the identity.
    """
    cid = claim_id(statement)
    path = dir_for("Claim") / f"{cid}.json"
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing["statement"].lower() != statement.lower():
            raise ValueError(
                f"id collision on {cid}: existing statement differs from the one "
                f"being emitted. The id contract lowercases before hashing "
                f"(ids.py), so statements differing only in case collide."
            )
        raise FileExistsError(
            f"Claim {cid} already exists at {path}; canon is append-only and "
            f"Claims are immutable. To revise the scientific content, emit a "
            f"successor Claim and link it via Decision.successor_claim_id."
        )

    ts = emitted_at or _now()
    envelope: dict[str, Any] = {
        "id": cid,
        "spec_version": SPEC_VERSION,
        "object_type": "Claim",
        "emitted_at": ts,
        "emitter": EMITTER,
        "layer": LAYER,
        "roles": ["Claim"],
        "role_declared_at": ts,
        "binding": "binding",
        "sources": [],
        "statement": statement,
        "falsification_criteria": falsification_criteria,
        "exposure": {
            "capital_at_risk": 0,
            "reversibility": "reversible",
            "correlation_tags": correlation_tags or [],
            "time_to_realization": time_to_realization,
            "blast_radius": "local",
        },
        "instance_id": INSTANCE_ID,
    }
    if thresholds:
        envelope["thresholds"] = thresholds
    if artifact_path:
        envelope["artifact"] = _artifact_pointer(artifact_path)

    _validate(envelope)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(envelope, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return cid, path

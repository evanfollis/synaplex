"""The only writer to `lab/.canon/`. Phase 1: Claim, Evidence, EventLogEntry.

ADR-0042 authorizes exactly this and nothing adjacent to it.

## The one rule that matters

> **The emitter serializes, validates, and writes. It never selects what to emit.**

No function here computes *which* Claim to register, *which* Evidence supports what, or
*when* to emit. Inputs come from the caller. The emitter makes exactly two decisions:
*is this valid* and *does this already exist*. The distance from "emit a Decision" to
"compute which Decision to emit" is short and downhill, and it is the slope
`synaplex@15edd38` slid down. `guard.py::check_no_selection` is the tripwire; this
docstring is the intent it protects.

## Refusals are recorded, not dropped

Every refused write emits an `EventLogEntry(canon_violation)` naming the `ViolationKind`
and the rationale, then raises. A store that silently declines to write is
indistinguishable from one that was never called (S3-P2, applied to canon).

The `canon_violation` record is itself written through the low-level path, deliberately
bypassing the refusal machinery: a validator that could refuse to record its own refusal
would lose exactly the events most worth keeping.

## What Phase 1 cannot do

No `Decision`. No `Policy`. Canon v0.1.0 cannot express a frozen, pre-registered,
eval-local promotion gate — `policy.md` offers `operational` (an agent can move the gate
after seeing Evidence, which is what pre-registration exists to prevent) and
`constitutional` (principal-only, framework-level). A pre-registered eval gate is
neither. The gap is escalated to context-repository, which owns canon. `validate.py`
refuses any attempt to construct one, so the constraint is enforced rather than
remembered.

Consequence, stated plainly: `memory-systems-v1` can enter probe and produce Evidence.
It **cannot conclude**. It is `incomplete`, not `concluded`, until Phase 2 lands.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .ids import claim_id, derived_id, hash_file
from .serialize import equal, to_disk
from .store import REPO_ROOT, dir_for, path_for
from .validate import CanonRefusal, validate

SPEC_VERSION = "0.1.0"
EMITTER = "L3:synaplex"
LAYER = "L3"
INSTANCE_ID = "synaplex"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _now_precise() -> str:
    """Microsecond stamp, used only to disambiguate violation-record ids."""
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def artifact_pointer(rel_path: str, version: str = "1", media_type: str = "text/markdown") -> dict:
    """Build an ArtifactPointer whose `content_hash` is *computed*, never asserted.

    A caller cannot pass a hash in. Canon rule 7 requires the hash to reproduce from the
    artifact; the way to guarantee that is to never accept a hash from anyone.
    """
    path = REPO_ROOT / rel_path
    if not path.is_file():
        raise CanonRefusal(
            "schema_validation_failure", f"artifact does not exist: {rel_path}"
        )
    return {
        "uri": f"file://{rel_path}",
        "content_hash": hash_file(path),
        "version": version,
        "media_type": media_type,
    }


def _base(object_type: str, envelope_id: str, emitted_at: str) -> dict[str, Any]:
    return {
        "id": envelope_id,
        "spec_version": SPEC_VERSION,
        "object_type": object_type,
        "emitted_at": emitted_at,
        "emitter": EMITTER,
        "layer": LAYER,
        "roles": [object_type],
        "role_declared_at": emitted_at,
        "binding": "binding",
        "sources": [],
        "instance_id": INSTANCE_ID,
    }


def _write(envelope: dict) -> Path:
    """Low-level write. Assumes validation already passed. Creates the directory."""
    path = path_for(envelope["object_type"], envelope["id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(to_disk(envelope), encoding="utf-8")
    return path


def record_violation(
    violation_kind: str,
    rationale: str,
    *,
    attempted_type: str = "",
    attempted_id: str = "",
) -> str:
    """Write an `EventLogEntry(canon_violation)` for a refused emission. Returns its id.

    Bypasses `validate()` on purpose — see module docstring. Best-effort by design: if
    recording the refusal fails, the refusal itself must still propagate, so this never
    raises into the caller's path.
    """
    ts = _now()
    eid = derived_id("canon_violation", violation_kind, attempted_type, attempted_id, _now_precise())
    envelope = _base("EventLogEntry", eid, ts)
    envelope["event_kind"] = "canon_violation"
    envelope["canon_violation"] = {
        "violation_kind": violation_kind,
        "offending_emission": {
            k: v
            for k, v in (("object_type", attempted_type), ("attempted_id", attempted_id))
            if v
        },
        "rationale": rationale,
    }
    if attempted_id:
        envelope["subject_id"] = attempted_id
    try:
        _write(envelope)
    except OSError:
        pass
    return eid


def _emit(envelope: dict) -> tuple[str, Path]:
    """Validate, enforce append-only, write. The single choke point for every emission."""
    object_type, envelope_id = envelope["object_type"], envelope["id"]
    try:
        validate(envelope)
    except CanonRefusal as refusal:
        record_violation(
            refusal.violation_kind,
            refusal.rationale,
            attempted_type=object_type,
            attempted_id=envelope_id,
        )
        raise

    path = path_for(object_type, envelope_id)
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        same = equal(existing, envelope)  # canonical, never bytes — see serialize.py
        rationale = (
            f"{object_type} {envelope_id} already exists and canon is append-only. "
            + (
                "The emission is identical to what is on disk; a no-op overwrite is still "
                "an overwrite, and permitting it makes immutability depend on the content "
                "happening to match."
                if same
                else "The emission DIFFERS from what is on disk. If this is a Claim, the id "
                "contract lowercases before hashing, so two statements differing only in "
                "case collide here. Revise the scientific content into a successor Claim; "
                "never mutate a pre-registration."
            )
        )
        record_violation(
            "other", rationale, attempted_type=object_type, attempted_id=envelope_id
        )
        raise CanonRefusal("other", rationale)

    return envelope_id, _write(envelope)


# --- the three authorized emitters ---------------------------------------


def emit_claim(
    *,
    statement: str,
    falsification_criteria: list[str],
    thresholds: dict[str, Any] | None = None,
    artifact: dict | None = None,
    correlation_tags: list[str] | None = None,
    time_to_realization: str = "P21D",
    capital_at_risk: float = 0,
    reversibility: str = "reversible",
    blast_radius: str = "local",
) -> tuple[str, Path]:
    """Emit a Claim. Its id derives from its statement — the statement *is* the identity."""
    ts = _now()
    envelope = _base("Claim", claim_id(statement), ts)
    envelope.update(
        statement=statement,
        falsification_criteria=falsification_criteria,
        exposure={
            "capital_at_risk": capital_at_risk,
            "reversibility": reversibility,
            "correlation_tags": correlation_tags or [],
            "time_to_realization": time_to_realization,
            "blast_radius": blast_radius,
        },
    )
    if thresholds:
        envelope["thresholds"] = thresholds
    if artifact:
        envelope["artifact"] = artifact
    return _emit(envelope)


def emit_evidence(
    *,
    claim: str,
    evidence_type: str,
    tier: str,
    polarity: str,
    artifact: dict,
    observed_at: str | None = None,
    sources: list[dict] | None = None,
) -> tuple[str, Path]:
    """Emit Evidence against a Claim.

    `polarity` is the emitter's declared interpretation (`supports` / `contradicts` /
    `neutral`) and is required so that the contradictory set is mechanically
    discoverable (canon obligation 6). Note for whoever runs an eval: **a cell aborted
    on cost is `neutral`, never `contradicts`** — coding a budget ceiling as a failed
    result manufactures support for the claim out of our own spending limit.

    The id derives from (claim, type, polarity, artifact hash): the same observation of
    the same artifact is the same Evidence, and re-emitting it is refused rather than
    duplicated into a second envelope that would double-count in any aggregation.
    """
    ts = _now()
    eid = derived_id("Evidence", claim, evidence_type, polarity, artifact["content_hash"])
    envelope = _base("Evidence", eid, ts)
    envelope.update(
        claim_id=claim,
        evidence_type=evidence_type,
        tier=tier,
        polarity=polarity,
        artifact=artifact,
    )
    if observed_at:
        envelope["observed_at"] = observed_at
    if sources:
        envelope["sources"] = sources
    return _emit(envelope)


def emit_phase_transition(
    *, claim: str, from_phase: str, to_phase: str
) -> tuple[str, Path]:
    """Emit `EventLogEntry(phase_transition)`.

    `canon.md` §Phase invariants: *"Phase is not a field on the Claim"* — Claims are
    immutable, so phase lives in the event log and replay reconstructs it. This is how a
    pre-registered Claim enters `probe`, and nothing can enter probe without it.
    """
    ts = _now()
    eid = derived_id("phase_transition", claim, from_phase, to_phase, ts)
    envelope = _base("EventLogEntry", eid, ts)
    envelope["event_kind"] = "phase_transition"
    envelope["subject_id"] = claim
    envelope["phase_transition"] = {
        "claim_id": claim,
        "from_phase": from_phase,
        "to_phase": to_phase,
    }
    return _emit(envelope)


def emit_methodology_log(*, claim: str, artifact: dict, summary: str = "") -> tuple[str, Path]:
    """Emit `EventLogEntry(methodology_log)` — required by canon on probe entry.

    `summary` is free-form narrative and nothing may depend on parsing it. ADR-0042 is
    explicit on this: an earlier draft proposed recording the `methodology.md` id-drift
    here, and review killed it — audit content placed in a prose field makes audit depend
    on prose parsing.
    """
    ts = _now()
    eid = derived_id("methodology_log", claim, artifact["content_hash"], ts)
    envelope = _base("EventLogEntry", eid, ts)
    envelope["event_kind"] = "methodology_log"
    envelope["subject_id"] = claim
    envelope["methodology_log"] = {"artifact": artifact}
    if summary:
        envelope["methodology_log"]["summary"] = summary
    return _emit(envelope)

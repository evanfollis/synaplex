"""The only writer to `lab/.canon/`: Claim, Evidence, Decision, EventLogEntry, Policy.

ADR-0042 authorized Phase 1 (Claim, Evidence, EventLogEntry) and blocked Decision and
Policy on a named canon gap: canon v0.1.0 could not express a frozen, pre-registered,
eval-local promotion gate. Canon v0.2.0 resolved it with the `frozen` mutability class
(reviewed, conformance-tested, `context-repository@42907eb`), so Phase 2 is now here too.

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

## The mutability class that makes an eval gate honest

`operational` lets an agent move the gate after seeing the Evidence — precisely what
pre-registration exists to prevent. `constitutional` is principal-only and framework-level.
An eval gate is neither: it must be agent-issuable and then unmovable, by anyone, forever.
That is `frozen`, and `emit_frozen_gate` is how you issue one.

Late issuance — not amendment — is the attack the class exists to stop. An unamendable
gate chosen *after* the results is just a post-hoc gate that no amendment check will ever
catch. So the window (canon rule 10) anchors on `Evidence.observed_at`, and
`emit_evidence` therefore **requires** `observed_at` and takes it from the run, never from
the clock. Read that function's docstring before using it; passing `_now()` there silently
reopens the whole attack.
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
from .view import StoreView

# New envelopes declare v0.2.0 — the version that introduced the `frozen` Policy class.
# The pre-existing Claim keeps its `0.1.0` stamp: it is immutable, and 0.2.0 is backward
# compatible (verified: all live envelopes across three repos still validate).
SPEC_VERSION = "0.2.0"
EMITTER = "L3:synaplex"
LAYER = "L3"
INSTANCE_ID = "synaplex"

_MAX_VIOLATION_ID_ATTEMPTS = 100


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
    envelope: dict[str, Any] = {
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
    }
    # Policy is the one envelope type with no `instance_id` — it is scoped by `scope`, and
    # its schema closes with `additionalProperties: false`. Found by the validator refusing
    # our own first frozen-gate emission, which is the machinery working as intended.
    if object_type != "Policy":
        envelope["instance_id"] = INSTANCE_ID
    return envelope


def _write(envelope: dict) -> Path:
    """Low-level write. Exclusive create — the filesystem enforces append-only, not a check.

    `open(..., "x")` fails if the path exists. The `exists()` test in `_emit` produces the
    good error message; *this* is what makes the guarantee, because a check-then-write is a
    race and canon has no undo. Two concurrent emitters cannot both win.
    """
    path = path_for(envelope["object_type"], envelope["id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "x", encoding="utf-8") as f:  # FileExistsError if it already exists
        f.write(to_disk(envelope))
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
    envelope = _base("EventLogEntry", "", ts)
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

    # Two refusals in the same microsecond would derive the same id, and the loser would be
    # dropped by the exclusive create in `_write`. The violation record we lose is exactly
    # the one worth keeping, so disambiguate until it lands.
    for attempt in range(_MAX_VIOLATION_ID_ATTEMPTS):
        eid = derived_id(
            "canon_violation", violation_kind, attempted_type, attempted_id,
            _now_precise(), str(attempt),
        )
        envelope["id"] = eid
        try:
            _write(envelope)
            return eid
        except FileExistsError:
            continue
        except OSError:
            # Recording the refusal failed. The refusal itself must still propagate — a
            # failed audit write may not become a successful emission.
            return eid
    return envelope["id"]


def _emit(envelope: dict) -> tuple[str, Path]:
    """Validate, enforce append-only, write. The single choke point for every emission.

    Validation runs against a `StoreView` carrying the *pending* envelope, so the
    cross-envelope rules (9-17) see the world as it would be after the write. A frozen gate
    that is legal before it exists and illegal after is not something to discover post-hoc:
    canon is append-only and there is no undo.
    """
    object_type, envelope_id = envelope["object_type"], envelope["id"]
    try:
        validate(envelope, StoreView(pending=envelope))
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
    observed_at: str,
    sources: list[dict] | None = None,
) -> tuple[str, Path]:
    """Emit Evidence against a Claim.

    ## `observed_at` is REQUIRED, and it comes from the run — never from the clock

    This is the single most load-bearing parameter in the emitter, and the reason it has no
    default is that a default would be a lie.

    `observed_at` is the emitter's assertion about **when reality was consulted**. Canon
    rule 10 anchors the frozen-gate pre-registration window on it, and rule 16 makes it
    mandatory for any Claim carrying a frozen gate. Adversarial review of canon v0.2.0
    proved why: `emitted_at` is *entirely under the emitter's control*, so an emitter that
    has already seen its results can mint a fresh Claim, freeze a flattering gate against
    it, re-emit the same observations as brand-new Evidence with later `emitted_at`, and
    walk through a window keyed on emission order. Anchoring on `observed_at` means the
    attack is no longer available by *ordering envelopes* — it requires falsifying an
    observation timestamp against a hash-pinned artifact, which is fabrication, not a
    loophole.

    **So: pass the timestamp the run actually observed the world. Passing `_now()` here
    destroys the anchor and silently reopens the entire attack.** Canon can close a
    loophole. It cannot stop a liar, and neither can this signature — but it can refuse to
    make lying the path of least resistance.

    ## Polarity

    Required so the contradictory set is mechanically discoverable (canon obligation 6).
    **A cell aborted on cost is `neutral`, never `contradicts`** — coding a budget ceiling
    as a failed result manufactures support for the claim out of our own spending limit.

    ## Identity

    Derived from (claim, type, polarity, artifact hash): the same observation of the same
    artifact is the same Evidence. Re-emitting is refused rather than duplicated into a
    second envelope that would double-count in any aggregation.
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
        observed_at=observed_at,
    )
    if sources:
        envelope["sources"] = sources
    return _emit(envelope)


def emit_frozen_gate(
    *,
    claim: str,
    field_path: str,
    value: Any,
    derived_from: str | None = None,
    scope: str = f"L3:{INSTANCE_ID}",
    version: str = "1",
) -> tuple[str, Path]:
    """Emit a `Policy(class=frozen)` — a pre-registered eval gate amendable by nobody.

    The third mutability class (canon v0.2.0). `operational` means an agent can move the
    gate after seeing the Evidence, which is exactly what pre-registration exists to
    prevent. `constitutional` is principal-only and framework-level. An eval gate is
    neither: it must be agent-issuable and then *unmovable*, by anyone, forever.

    So `amendment_authority` is `[]` — not the principal, not us. Issuing a frozen Policy
    **renounces** amendment power rather than granting it, which is why no principal signoff
    is needed. That argument holds only because rule 17 forbids a frozen gate on a
    constitutional field; without it, an agent could grant *itself* a capital ceiling that
    nobody, including Evan, could ever amend. A safety argument with an unstated
    precondition is not a safety argument.

    **`derived_from`** is an RFC-6901 pointer into the bound Claim. When set, canon rule 14
    proves `value` is canonical-JSON-equal to the Claim's hash-bound subtree — so the gate
    is *mechanically provable* to carry zero information the pre-registration does not
    already contain. Use it. A gate that merely *claims* to restate the Claim is a gate
    nobody can check.

    The window: canon rule 10 requires `claim.emitted_at <= policy.emitted_at <= probe
    entry`, and before any Evidence was emitted *or observed*. Issue it while the window is
    open, or not at all.
    """
    ts = _now()
    pid = derived_id("Policy", claim, field_path, version)
    envelope = _base("Policy", pid, ts)
    envelope.update(
        **{"class": "frozen"},
        scope=scope,
        field_path=field_path,
        value=value,
        version=version,
        issuer=EMITTER,
        amendment_authority=[],  # nobody. This is the class.
        ratification_rule={"kind": "none"},
        rollback_rule={"rules": [], "precedence": []},
        provenance=[{"version": version, "effective_from": ts}],
        effective_from=ts,
        effective_until=None,  # a frozen policy never expires; it is superseded with its Claim
        bound_to_claim_id=claim,
    )
    if derived_from:
        envelope["derived_from"] = derived_from
    return _emit(envelope)


def emit_decision(
    *,
    kind: str,
    candidate_claims: list[str],
    chosen_claim_id: str,
    cited_evidence: list[str],
    rationale: str,
    policies_in_force: list[dict],
    rejected_alternatives: list[dict] | None = None,
    arbitration: dict | None = None,
    contradictions_addressed: list[dict] | None = None,
    successor_claim_id: str | None = None,
    correlation_tags: list[str] | None = None,
) -> tuple[str, Path]:
    """Emit a Decision — the only envelope that can conclude anything.

    A terminal Decision (`promote` / `kill` / `pivot`) must cite **every** frozen Policy
    bound to the chosen Claim (canon rule 13): citing only the gates you passed is
    cherry-picking a pre-registration. It may only cite Evidence gathered about a Claim it
    is actually deciding (rule 15) — that rule is what stops the evidence-laundering path
    and is what makes rules 9–14 mean anything at all.

    Contradicting Evidence known at decision time MUST be cited and addressed. A Decision
    that quietly omits the evidence against it is the failure this whole apparatus exists
    to make impossible.

    The emitter does not compute `kind`, choose the Claim, or decide which Evidence is
    decisive. It serializes what the caller decided and refuses what canon forbids.
    """
    ts = _now()
    did = derived_id("Decision", kind, chosen_claim_id, ",".join(sorted(cited_evidence)), ts)
    envelope = _base("Decision", did, ts)
    envelope.update(
        kind=kind,
        candidate_claims=candidate_claims,
        chosen_claim_id=chosen_claim_id,
        cited_evidence=cited_evidence,
        rationale=rationale,
        policies_in_force=policies_in_force,
        exposure={
            "capital_at_risk": 0,
            "reversibility": "reversible",
            "correlation_tags": correlation_tags or [],
            "time_to_realization": "P0D",
            "blast_radius": "local",
        },
    )
    if rejected_alternatives:
        envelope["rejected_alternatives"] = rejected_alternatives
    if arbitration:
        envelope["arbitration"] = arbitration
    if contradictions_addressed:
        envelope["contradictions_addressed"] = contradictions_addressed
    if successor_claim_id:
        envelope["successor_claim_id"] = successor_claim_id
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

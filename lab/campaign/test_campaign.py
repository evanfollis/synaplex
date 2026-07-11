"""Verifiable assertions for the lab campaign kernel.

Run as a standalone script (no pytest required), from the repo root:

    PYTHONPATH=. .venv/bin/python lab/campaign/test_campaign.py

Exit code 0 = all assertions hold; non-zero = drift detected.

The load-bearing ones are the first three. They are regression tests against the
two ways this store can be silently corrupted: an id contract that drifts between
write paths (S1-P3), and a pre-registered methodology whose bytes change after
the Claim was hash-bound to them.
"""

from __future__ import annotations

import json
import sys

from lab.campaign.gate import GATE_POLICY_ID, defect_gates, failing_gates
from lab.campaign.ids import claim_id, hash_file
from lab.campaign.manifest import Manifest, Outcome, Verifier
from lab.campaign.model import Campaign, ClaimView
from lab.campaign.pressure import CLEAR_GATE, EXECUTE, FALSIFY, SUSPEND, next_action
from lab.campaign.store import CanonStore, REPO_ROOT

PRIMARY = "b7ff216f4eec6e58"
METHODOLOGY = "lab/evals/memory-systems-v1/methodology.md"
# The hash bound into the primary Claim at pre-registration, 2026-04-19.
PREREGISTERED_HASH = (
    "sha256:45916c9fc006d87b86eb09437cffdee0ff552184bd660c1ebf92e7a942b4900b"
)


def test_id_contract_matches_preexisting_claim() -> None:
    """S1-P3: the emitter's id contract must reproduce the hand-authored envelope.

    `emit.py` is the first programmatic writer to a store whose only record was
    written by hand. If `claim_id()` does not reproduce that record's id, the two
    write paths disagree and every cross-path join silently corrupts.
    """
    store = CanonStore.load()
    claim = store.claims[PRIMARY]
    derived = claim_id(claim["statement"])
    assert derived == PRIMARY, (
        f"id contract drift: claim_id(statement) = {derived}, but the envelope on "
        f"disk is {PRIMARY}. emit.py and the pre-existing store now disagree."
    )
    print("  [1] id contract reproduces the pre-existing Claim id — OK")


def test_preregistration_immutability() -> None:
    """methodology.md must still hash to what the Claim was bound to in April.

    This is the whole point of pre-registration. If this fails, someone edited a
    hash-bound methodology in place, and the Claim no longer means what it said.
    """
    actual = hash_file(REPO_ROOT / METHODOLOGY)
    assert actual == PREREGISTERED_HASH, (
        f"methodology.md has been mutated since pre-registration.\n"
        f"  bound at emission: {PREREGISTERED_HASH}\n"
        f"  on disk now:       {actual}\n"
        f"The Claim must be re-emitted as a successor, not repaired in place."
    )
    store = CanonStore.load()
    assert store.claims[PRIMARY]["artifact"]["content_hash"] == PREREGISTERED_HASH
    print("  [2] methodology.md byte-stable since pre-registration — OK")


def test_all_artifact_pointers_reproduce() -> None:
    """canon.md §Validator-level rules 7, across every envelope in the store."""
    violations = CanonStore.load().verify_artifacts()
    assert not violations, "stale ArtifactPointer(s):\n  " + "\n  ".join(violations)
    print("  [3] every ArtifactPointer.content_hash reproduces — OK")


# --- synthetic fixtures ---------------------------------------------------


def _claim(cid: str, statement: str = "s") -> dict:
    return {"id": cid, "object_type": "Claim", "statement": statement}


def _evidence(eid: str, claim: str, polarity: str, lineage_src: str) -> dict:
    return {
        "id": eid,
        "object_type": "Evidence",
        "claim_id": claim,
        "polarity": polarity,
        "tier": "internal_operational",
        "sources": [{"id": lineage_src, "object_type": "Claim", "binding": "binding"}],
    }


def _manifest(alts: tuple[str, ...], verifiers: tuple[Verifier, ...] = ()) -> Manifest:
    return Manifest(
        campaign_id="synthetic",
        eval_id="synthetic",
        primary_claim_id="P",
        alternative_claim_ids=alts,
        outcome_map=(Outcome("obs", "P", "why"),) if alts else (),
        verifier_plan=verifiers,
        validity_threats=(),
        valid_until=None,
        invalidation_conditions=(),
    )


def _campaign(
    alts: tuple[str, ...] = (),
    evidence: list[dict] | None = None,
    decisions: list[dict] | None = None,
    verifiers: tuple[Verifier, ...] = (),
) -> Campaign:
    evidence = evidence or []
    return Campaign(
        manifest=_manifest(alts, verifiers),
        primary=ClaimView(
            claim=_claim("P"),
            phase="probe",
            evidence=[e for e in evidence if e["claim_id"] == "P"],
        ),
        alternatives=[
            ClaimView(
                claim=_claim(a),
                phase="probe",
                evidence=[e for e in evidence if e["claim_id"] == a],
            )
            for a in alts
        ],
        decisions=decisions or [],
        artifact_violations=[],
    )


# --- gate behaviour -------------------------------------------------------


def test_alternatives_gate_blocks_and_routes() -> None:
    c = _campaign(alts=())
    gates = {g.gate: g for g in defect_gates(c)}
    assert "alternatives_required" in gates, "a claim with no rivals must not publish"
    assert gates["alternatives_required"].route_to == "operationalization"
    assert next_action(c).action == CLEAR_GATE
    print("  [4] no rivals -> gate blocks, routes to operationalization — OK")


def test_waiver_decision_clears_alternatives_gate() -> None:
    """The waiver must cite the very gate it waives — and nothing weaker works."""
    waiver = {
        "id": "D1",
        "object_type": "Decision",
        "kind": "continue",
        "chosen_claim_id": "P",
        "candidate_claims": ["P"],
        "policies_in_force": [{"policy_id": GATE_POLICY_ID, "version": "1"}],
    }
    c = _campaign(alts=(), decisions=[waiver])
    assert not [g for g in failing_gates(c) if g.gate == "alternatives_required"]

    # A Decision that does NOT name the gate policy must not waive it.
    unrelated = dict(waiver, policies_in_force=[{"policy_id": "lab.something_else", "version": "1"}])
    c2 = _campaign(alts=(), decisions=[unrelated])
    assert [g for g in failing_gates(c2) if g.gate == "alternatives_required"], (
        "a Decision that does not cite the gate policy must not silently waive it"
    )
    print("  [5] waiver clears the gate only when it cites the gate policy — OK")


def test_evidence_gate_is_stage_not_defect() -> None:
    """A campaign with no results is early, not broken."""
    c = _campaign(alts=("A",))
    all_gates = {g.gate: g for g in failing_gates(c)}
    assert "evidence_required" in all_gates, "cannot publish a writeup with no evidence"
    assert all_gates["evidence_required"].kind == "stage"
    assert not defect_gates(c), "a pre-registered campaign must not report as malformed"
    assert c.status == "pre_registration" or c.status == "ready_to_execute"
    assert next_action(c).action == EXECUTE
    print("  [6] evidence gate blocks publish but is a stage, not a defect — OK")


# --- lineage-aware aggregation -------------------------------------------


def test_lineage_aggregation_collapses_relaundered_evidence() -> None:
    """Three writeups of one benchmark run are one result, not three."""
    same_run = [
        _evidence("E1", "P", "supports", "RUN-A"),
        _evidence("E2", "P", "supports", "RUN-A"),
        _evidence("E3", "P", "supports", "RUN-A"),
    ]
    c = _campaign(alts=("A",), evidence=same_run)
    assert len(c.primary.evidence) == 3, "three envelopes exist"
    assert c.primary.independent("supports") == 1, (
        "but they share one primary lineage and must count as one independent result"
    )

    distinct = same_run + [_evidence("E4", "P", "supports", "RUN-B")]
    c2 = _campaign(alts=("A",), evidence=distinct)
    assert c2.primary.independent("supports") == 2
    print("  [7] evidence counts distinct lineages, not envelopes — OK")


# --- pressure scheduling --------------------------------------------------


def test_pressure_prefers_most_independent_falsifier() -> None:
    """With supporting evidence in hand, the next challenge is the strongest
    unexercised falsifier — not another confirming run."""
    verifiers = (
        Verifier("cheap_internal", "rerun our own suite", "P", "harness:rerun", "internal_operational"),
        Verifier("replication", "third party reproduces it", "P", "external:replication", "external_commitment"),
        Verifier("already_done", "the run we already did", "P", "RUN-A", "external_transaction"),
    )
    c = _campaign(
        alts=("A",),
        evidence=[_evidence("E1", "P", "supports", "RUN-A")],
        verifiers=verifiers,
    )
    action = next_action(c)
    assert action.action == FALSIFY, f"expected falsify, got {action.action}"
    assert action.target == "replication", (
        f"expected the highest-tier *unexercised* verifier, got {action.target!r}. "
        f"'already_done' is higher-tier but its lineage RUN-A is already in the "
        f"evidence set — proposing it would be a redundant, correlated observation."
    )
    assert any("cheap_internal" in p for p in action.passed_over)
    assert "never been challenged, only confirmed" in action.rationale
    print("  [8] pressure picks the most independent unexercised falsifier — OK")


def test_pressure_suspends_when_verifiers_exhausted() -> None:
    c = _campaign(
        alts=("A",),
        evidence=[_evidence("E1", "P", "supports", "RUN-A")],
        verifiers=(Verifier("v", "c", "P", "RUN-A", "internal_operational"),),
    )
    action = next_action(c)
    assert action.action == SUSPEND, f"expected suspend, got {action.action}"
    assert "Suspending is not concluding" in action.rationale
    assert c.status == "suspended"
    print("  [9] exhausted verifier plan -> suspend with rationale — OK")


def test_unaddressed_contradiction_blocks_and_contests() -> None:
    c = _campaign(alts=("A",), evidence=[_evidence("E1", "P", "contradicts", "RUN-A")])
    gates = {g.gate: g for g in defect_gates(c)}
    assert "contradictions_addressed" in gates
    assert gates["contradictions_addressed"].route_to == "arbitration"

    addressed = {
        "id": "D1",
        "object_type": "Decision",
        "kind": "continue",
        "chosen_claim_id": "P",
        "candidate_claims": ["P"],
        "policies_in_force": [{"policy_id": "x", "version": "1"}],
        "contradictions_addressed": [{"evidence_id": "E1", "treatment": "rebutted"}],
    }
    c2 = _campaign(
        alts=("A",),
        evidence=[_evidence("E1", "P", "contradicts", "RUN-A")],
        decisions=[addressed],
    )
    assert not [g for g in defect_gates(c2) if g.gate == "contradictions_addressed"]
    print(" [10] unaddressed contradiction blocks; a Decision treating it clears — OK")


# --- the live campaign ----------------------------------------------------


def test_live_memory_systems_campaign() -> None:
    """The real campaign, as it stands in canon right now."""
    c = Campaign.materialize("memory-systems-v1")
    assert c.primary.id == PRIMARY
    assert len(c.alternatives) == 3, "three rivals were pre-registered"
    assert not defect_gates(c), f"unexpected defects: {[g.gate for g in defect_gates(c)]}"
    assert [g.gate for g in failing_gates(c)] == ["evidence_required"]
    action = next_action(c)
    assert action.action == EXECUTE
    assert len(c.manifest.outcome_map) == 5
    assert len(c.unexercised_verifiers) == 6
    print(" [11] live memory-systems-v1 campaign: 3 rivals, gates clear, next=execute — OK")


def test_emit_refuses_to_overwrite() -> None:
    """Canon is append-only; re-emitting an existing Claim must raise, not clobber."""
    from lab.campaign.emit import emit_claim

    store = CanonStore.load()
    statement = store.claims[PRIMARY]["statement"]
    before = json.loads((REPO_ROOT / "lab/.canon/claims" / f"{PRIMARY}.json").read_text())
    try:
        emit_claim(statement=statement, falsification_criteria=["x"])
    except FileExistsError:
        pass
    else:
        raise AssertionError("emit_claim silently overwrote an immutable Claim")
    after = json.loads((REPO_ROOT / "lab/.canon/claims" / f"{PRIMARY}.json").read_text())
    assert before == after, "the envelope on disk was mutated despite the raise"
    print(" [12] emit_claim refuses to overwrite an existing Claim — OK")


TESTS = [
    test_id_contract_matches_preexisting_claim,
    test_preregistration_immutability,
    test_all_artifact_pointers_reproduce,
    test_alternatives_gate_blocks_and_routes,
    test_waiver_decision_clears_alternatives_gate,
    test_evidence_gate_is_stage_not_defect,
    test_lineage_aggregation_collapses_relaundered_evidence,
    test_pressure_prefers_most_independent_falsifier,
    test_pressure_suspends_when_verifiers_exhausted,
    test_unaddressed_contradiction_blocks_and_contests,
    test_live_memory_systems_campaign,
    test_emit_refuses_to_overwrite,
]


def main() -> int:
    print(f"lab.campaign — {len(TESTS)} assertions\n")
    failed = 0
    for t in TESTS:
        try:
            t()
        except AssertionError as e:
            failed += 1
            print(f"  FAIL {t.__name__}:\n    {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  ERROR {t.__name__}: {type(e).__name__}: {e}")
    print()
    if failed:
        print(f"{failed}/{len(TESTS)} FAILED")
        return 1
    print(f"all {len(TESTS)} assertions hold")
    return 0


if __name__ == "__main__":
    sys.exit(main())

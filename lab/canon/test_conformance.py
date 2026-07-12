"""Run OUR validator against context-repository's canon v0.2.0 conformance fixtures.

    PYTHONPATH=. .venv/bin/python lab/canon/test_conformance.py

The 19 cases in `spec/discovery-framework/conformance/cases/` are the reference
definition of what canon v0.2.0 means. Each declares an envelope set and an expected
outcome: `accept`, or `refuse` with a named `violation_kind`.

This is the only test in the repo that can catch us **conforming to our own bugs**.
`test_canon.py` checks our rules against our understanding of them — which is exactly
the loop that produces a validator that is confidently, internally-consistently wrong.
These fixtures were written by the spec owner and hardened by an adversarial review that
found two blocking defects in the *first* draft of the spec itself. Running our
implementation against them is how we find out whether we actually implemented canon or
merely implemented our reading of it.

**A case that refuses for the wrong reason fails.** Getting to "refused" by accident,
via a different rule than the one under test, is not conformance — it is a coincidence
that will stop holding the moment the accident goes away.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CONFORMANCE = Path(
    "/opt/workspace/projects/context-repository/spec/discovery-framework/conformance/cases"
)


def run_case(case: dict) -> tuple[bool, str]:
    """Validate the case's envelope set with our validator. Returns (passed, detail)."""
    from lab.canon.rules import CanonRefusal
    from lab.canon.validate import check_schema, validate
    from lab.canon.view import SetView

    envelopes = case["envelopes"]
    view = SetView(envelopes)
    expect = case["expect"]
    expect_violation = case.get("expect_violation")

    refusal: CanonRefusal | None = None
    for envelope in envelopes:
        try:
            # Schema first (the reference runner does the same), then the canon rules.
            # `validate()` also applies our local additions — the Programme write-side
            # refusal and the repo-containment check on ArtifactPointers — which the
            # fixtures neither exercise nor forbid.
            check_schema(envelope)
        except CanonRefusal as r:
            refusal = refusal or r
        except KeyError:
            pass  # object_type we do not emit (Promotion/Realization); not our surface

    if refusal is None:
        from lab.canon import rules

        for envelope in envelopes:
            try:
                rules.check_all(envelope, view)
            except CanonRefusal as r:
                refusal = refusal or r

    if expect == "accept":
        if refusal is not None:
            return False, f"expected accept, but refused [{refusal.violation_kind}]: {refusal.rationale[:100]}"
        return True, "accepted"

    if refusal is None:
        return False, f"expected refusal [{expect_violation}], but the envelope set was ACCEPTED"
    if refusal.violation_kind != expect_violation:
        return (
            False,
            f"refused for the WRONG REASON: expected [{expect_violation}], "
            f"got [{refusal.violation_kind}] — {refusal.rationale[:90]}",
        )
    return True, f"refused [{refusal.violation_kind}]"


def main() -> int:
    sys.path.insert(0, str(REPO))

    if not CONFORMANCE.is_dir():
        print(f"conformance fixtures not found at {CONFORMANCE}")
        return 1

    cases = sorted(CONFORMANCE.glob("*.json"))
    print(f"canon v0.2.0 conformance — {len(cases)} reference fixtures, our validator\n")

    failed = 0
    for path in cases:
        case = json.loads(path.read_text(encoding="utf-8"))
        try:
            passed, detail = run_case(case)
        except Exception as e:  # noqa: BLE001
            passed, detail = False, f"{type(e).__name__}: {e}"
        if passed:
            print(f"  ok   {case['name']:44s} {detail}")
        else:
            failed += 1
            print(f"  FAIL {case['name']:44s} {detail}")

    print()
    if failed:
        print(f"{failed}/{len(cases)} FAILED — our validator does not implement canon v0.2.0")
        return 1
    print(f"all {len(cases)} conformance fixtures pass against our validator")
    return 0


if __name__ == "__main__":
    sys.exit(main())

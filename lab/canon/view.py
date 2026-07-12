"""A `CanonView` — the set of envelopes a validation runs against.

Validator rules 1, 7 look at one envelope. Rules 2-5 and 9-17 are **cross-envelope**:
"is this gate late relative to that Evidence", "does this Decision cite every frozen
Policy bound to its chosen Claim". They need to see a world, not a document.

Two implementations, one interface, so the same rule code runs in both places:

- `StoreView` — the live `lab/.canon/` plus the envelope being emitted. This is what
  guards a real write.
- `SetView` — an arbitrary list of envelopes. This is what lets `test_conformance.py`
  run our validator against context-repository's 19 executable fixtures and assert each
  refusal carries the *right* `violation_kind`. A refusal for the wrong reason is a
  failure, and without this seam we could only test our rules against our own
  understanding of them — which is how you conform to your own bugs.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import store


class CanonView:
    def claims(self) -> list[dict]:
        raise NotImplementedError

    def policies(self) -> list[dict]:
        raise NotImplementedError

    def evidence(self) -> list[dict]:
        raise NotImplementedError

    def events(self) -> list[dict]:
        raise NotImplementedError

    # --- derived lookups every rule needs ---------------------------------

    def claim(self, claim_id: str) -> dict | None:
        return next((c for c in self.claims() if c["id"] == claim_id), None)

    def evidence_by_id(self, evidence_id: str) -> dict | None:
        return next((e for e in self.evidence() if e["id"] == evidence_id), None)

    def policy_by_id(self, policy_id: str) -> dict | None:
        return next((p for p in self.policies() if p["id"] == policy_id), None)

    def frozen_policies_for(self, claim_id: str) -> list[dict]:
        return [
            p
            for p in self.policies()
            if p.get("class") == "frozen" and p.get("bound_to_claim_id") == claim_id
        ]

    def evidence_for(self, claim_id: str) -> list[dict]:
        return [e for e in self.evidence() if e.get("claim_id") == claim_id]

    def probe_entry_at(self, claim_id: str) -> str | None:
        """`emitted_at` of the earliest phase_transition into `probe` for this Claim.

        Rule 10's window closes here. `None` means the eval never entered probe, so the
        pre-registration window is still **open** — which is precisely the state
        `memory-systems-v1` is in, and why a legal frozen gate can still be issued for it.
        """
        entries = [
            e["emitted_at"]
            for e in self.events()
            if e.get("event_kind") == "phase_transition"
            and e.get("phase_transition", {}).get("claim_id") == claim_id
            and e.get("phase_transition", {}).get("to_phase") == "probe"
        ]
        return min(entries) if entries else None


@dataclass
class SetView(CanonView):
    envelopes: list[dict] = field(default_factory=list)

    def _of(self, object_type: str) -> list[dict]:
        return [e for e in self.envelopes if e.get("object_type") == object_type]

    def claims(self) -> list[dict]:
        return self._of("Claim")

    def policies(self) -> list[dict]:
        return self._of("Policy")

    def evidence(self) -> list[dict]:
        return self._of("Evidence")

    def events(self) -> list[dict]:
        return self._of("EventLogEntry")


@dataclass
class StoreView(CanonView):
    """The live store, plus the envelope currently being emitted.

    The pending envelope is included because rules must see the world *as it would be*
    after the write. A gate that is legal before it exists and illegal after is not
    something to discover post-hoc — canon is append-only.
    """

    pending: dict | None = None

    def _of(self, object_type: str) -> list[dict]:
        out = store.load_all(object_type)
        if self.pending and self.pending.get("object_type") == object_type:
            out = [e for e in out if e["id"] != self.pending["id"]] + [self.pending]
        return out

    def claims(self) -> list[dict]:
        return self._of("Claim")

    def policies(self) -> list[dict]:
        return self._of("Policy")

    def evidence(self) -> list[dict]:
        return self._of("Evidence")

    def events(self) -> list[dict]:
        return self._of("EventLogEntry")

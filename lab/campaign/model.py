"""Campaign — the runtime projection that keeps a pre-registered Claim under pressure.

A Campaign is *derived*, never stored. It materializes from canon envelopes
(Claim / Evidence / Decision / EventLogEntry) plus the campaign manifest, and it
answers one question the canon store alone cannot: **what is the next challenge
this claim must survive?**

It is deliberately not a canon object. Canon is an obligations model — it records
what was pre-registered and what was emitted. The campaign is the operational
kernel that reads those obligations and decides what to do next. Collapsing the
two would put a state machine inside an obligations model, which is the thing
canon.md explicitly refuses to be.

## Lineage-aware evidence aggregation (anti-laundering)

Evidence envelopes are not independent just because there are several of them.
Three writeups of the same benchmark run are one result, not three. `lineage_key`
collapses Evidence that traces to the same primary source, and every count that
feeds a decision (`independent_support`, `independent_contradiction`) is over
*lineages*, not envelopes. Counting envelopes is how a campaign talks itself into
confidence it has not earned.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone

from .manifest import Manifest, Verifier
from .store import CanonStore

# Derived campaign status. Never persisted — recomputed on every read.
Status = str

BLOCKED = "blocked"  # a publish gate is failing
PRE_REGISTRATION = "pre_registration"  # registered, not yet in probe phase
READY_TO_EXECUTE = "ready_to_execute"  # in probe, methodology locked, no evidence yet
UNDER_PRESSURE = "under_pressure"  # evidence accumulating, verifiers remain
CONTESTED = "contested"  # contradicting evidence outstanding, unaddressed
SUPPORTED = "supported"  # decided, support not expired
EXPIRED = "expired"  # decided, but the decision packet has gone stale
FALSIFIED = "falsified"  # primary claim falsified, or an alternative won
SUSPENDED = "suspended"  # verifier plan exhausted, nothing left to challenge


def lineage_key(evidence: dict) -> str:
    """Collapse Evidence that derives from the same primary result.

    Preference order:
      1. The upstream canon objects it cites (`sources[*].id`) — two Evidence
         envelopes citing the same source objects are the same result, re-stated.
      2. Failing that, the artifact `content_hash` — the same transcript bytes
         cannot be two independent observations.

    This is the intake dedup contract (S1-P3) applied one layer up: dedup on what
    the evidence *derives from*, not on what it is *called*.
    """
    sources = evidence.get("sources") or []
    if sources:
        return "|".join(sorted(str(s.get("id", "")) for s in sources))
    return (evidence.get("artifact") or {}).get("content_hash", evidence["id"])


@dataclass
class ClaimView:
    """A single Claim inside a campaign, with its canon-derived state."""

    claim: dict
    phase: str
    evidence: list[dict] = field(default_factory=list)

    @property
    def id(self) -> str:
        return self.claim["id"]

    @property
    def statement(self) -> str:
        return self.claim["statement"]

    def by_polarity(self, polarity: str) -> list[dict]:
        return [e for e in self.evidence if e.get("polarity") == polarity]

    def independent(self, polarity: str) -> int:
        """Count of *distinct primary lineages*, not envelopes. See module docstring."""
        return len({lineage_key(e) for e in self.by_polarity(polarity)})

    @property
    def exercised_lineages(self) -> set[str]:
        return {lineage_key(e) for e in self.evidence}


@dataclass
class Campaign:
    manifest: Manifest
    primary: ClaimView
    alternatives: list[ClaimView]
    decisions: list[dict]
    artifact_violations: list[str]

    @classmethod
    def materialize(cls, eval_id: str, store: CanonStore | None = None) -> "Campaign":
        store = store or CanonStore.load()
        m = Manifest.load(eval_id)

        missing = [cid for cid in m.member_claim_ids if cid not in store.claims]
        if missing:
            raise ValueError(
                f"campaign {m.campaign_id}: manifest names claim(s) absent from canon: "
                f"{', '.join(missing)}"
            )

        def view(cid: str) -> ClaimView:
            return ClaimView(
                claim=store.claims[cid],
                phase=store.phase_of(cid),
                evidence=store.evidence_for(cid),
            )

        return cls(
            manifest=m,
            primary=view(m.primary_claim_id),
            alternatives=[view(cid) for cid in m.alternative_claim_ids],
            decisions=store.decisions_for(m.primary_claim_id),
            artifact_violations=store.verify_artifacts(),
        )

    # --- derived views ---------------------------------------------------

    @property
    def claim_views(self) -> list[ClaimView]:
        return [self.primary, *self.alternatives]

    @property
    def has_alternatives(self) -> bool:
        return bool(self.alternatives)

    @property
    def all_evidence(self) -> list[dict]:
        return [e for v in self.claim_views for e in v.evidence]

    @property
    def exercised_lineages(self) -> set[str]:
        return {lineage_key(e) for e in self.all_evidence}

    @property
    def unexercised_verifiers(self) -> list[Verifier]:
        """Verifiers whose primary lineage has not yet produced Evidence.

        This is what makes a proposed challenge *non-redundant*: re-running a
        verifier whose lineage is already in the evidence set produces a
        correlated observation, not a new one.
        """
        done = self.exercised_lineages
        return [v for v in self.manifest.verifier_plan if v.lineage not in done]

    @property
    def unaddressed_contradictions(self) -> list[dict]:
        """Contradicting Evidence that no Decision has treated.

        Canon obligation 6: "What contradictory evidence exists — addressed or
        not?" A Decision addresses it via `contradictions_addressed[*].evidence_id`.
        """
        addressed = {
            c["evidence_id"]
            for d in self.decisions
            for c in d.get("contradictions_addressed", [])
        }
        return [
            e
            for v in self.claim_views
            for e in v.by_polarity("contradicts")
            if e["id"] not in addressed
        ]

    @property
    def terminal_decision(self) -> dict | None:
        """The most recent Decision that resolved the primary claim, if any."""
        resolving = [
            d
            for d in self.decisions
            if d.get("kind") in {"promote", "kill", "pivot"}
        ]
        if not resolving:
            return None
        return max(resolving, key=lambda d: d["emitted_at"])

    @property
    def is_expired(self) -> bool:
        """Decision-packet expiry: support that has outlived its validity window.

        A supported claim carries "valid until date X or until the environment
        changes." Past X, the support is not wrong — it is *unverified*, and the
        campaign must re-enter pressure rather than sit inert on stale support.
        """
        if not self.manifest.valid_until or self.terminal_decision is None:
            return False
        try:
            until = date.fromisoformat(self.manifest.valid_until)
        except ValueError:
            return False
        return datetime.now(timezone.utc).date() > until

    @property
    def status(self) -> Status:
        from .gate import defect_gates  # local import: gate imports model

        # Only *defects* block. A campaign with no results yet is early, not broken.
        if defect_gates(self):
            return BLOCKED
        d = self.terminal_decision
        if d is not None:
            if self.is_expired:
                return EXPIRED
            if d.get("kind") == "kill" and d.get("chosen_claim_id") == self.primary.id:
                return FALSIFIED
            if d.get("chosen_claim_id") != self.primary.id:
                return FALSIFIED  # an alternative won the arbitration
            return SUPPORTED
        if self.unaddressed_contradictions:
            return CONTESTED
        if not self.all_evidence:
            return PRE_REGISTRATION if self.primary.phase == "draft" else READY_TO_EXECUTE
        if not self.unexercised_verifiers:
            return SUSPENDED
        return UNDER_PRESSURE

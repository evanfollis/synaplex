"""The campaign manifest — the only campaign state that is NOT derived from canon.

A Campaign is a runtime projection (see `model.py`). Almost everything about it
— status, evidence, contradictions, phase — is read out of canon envelopes. But
four things cannot be derived, because canon does not model them:

- **alternatives**: which Claims are *rivals* of the primary. Canon knows rival
  Claims exist (`Decision.candidate_claims`), but only once a Decision has been
  emitted. Before that, nothing records "these three Claims are competing
  explanations of the same phenomenon." The manifest records it.
- **outcome_map**: which observation selects which Claim. This is the
  pre-registration that makes the eval discriminating rather than confirmatory.
- **verifier_plan**: the ranked set of challenges available, and what primary
  lineage each would draw on.
- **validity_threats** and **decision_expiry**.

Per the source handoff, none of these become canon objects yet. If an audit
question turns out to be unanswerable without them, that is the signal to
escalate a canon bump through context-repository — not to bolt fields onto the
Claim schema locally.

Manifests live beside the eval they project: `lab/evals/<eval_id>/campaign.json`.
(The handoff proposed a top-level `lab/campaigns/` directory; colocating keeps a
single source of truth per eval and prevents orphan manifests pointing at evals
that no longer exist. Deviation is deliberate.)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .store import REPO_ROOT

EVALS_ROOT = REPO_ROOT / "lab" / "evals"

# Evidence tiers, ordered by bindingness to external reality (canon
# evidence.schema.json). Used to rank how *strong* a proposed verifier is.
TIER_RANK = {
    "internal_operational": 0,
    "external_conversation": 1,
    "external_commitment": 2,
    "external_transaction": 3,
}


@dataclass(frozen=True)
class Verifier:
    """One available challenge against the campaign."""

    id: str
    challenge: str
    targets: str  # claim id this verifier can falsify
    lineage: str  # primary-source lineage it would draw on (anti-laundering key)
    tier: str  # canon Evidence tier the result would carry

    @property
    def tier_rank(self) -> int:
        return TIER_RANK.get(self.tier, -1)


@dataclass(frozen=True)
class Outcome:
    """One row of the pre-registered outcome map: observation -> selected claim."""

    observation: str
    selects: str  # claim id
    rationale: str


@dataclass(frozen=True)
class ValidityThreat:
    id: str
    boundary_class: str
    description: str
    mitigation: str


@dataclass(frozen=True)
class Manifest:
    campaign_id: str
    eval_id: str
    primary_claim_id: str
    alternative_claim_ids: tuple[str, ...]
    outcome_map: tuple[Outcome, ...]
    verifier_plan: tuple[Verifier, ...]
    validity_threats: tuple[ValidityThreat, ...]
    valid_until: str | None
    invalidation_conditions: tuple[str, ...]

    @property
    def member_claim_ids(self) -> tuple[str, ...]:
        return (self.primary_claim_id, *self.alternative_claim_ids)

    @staticmethod
    def path_for(eval_id: str) -> Path:
        return EVALS_ROOT / eval_id / "campaign.json"

    @classmethod
    def load(cls, eval_id: str) -> "Manifest":
        path = cls.path_for(eval_id)
        if not path.is_file():
            raise FileNotFoundError(f"no campaign manifest at {path}")
        raw = json.loads(path.read_text(encoding="utf-8"))
        expiry = raw.get("decision_expiry", {})
        return cls(
            campaign_id=raw["campaign_id"],
            eval_id=raw["eval_id"],
            primary_claim_id=raw["primary_claim_id"],
            alternative_claim_ids=tuple(raw.get("alternative_claim_ids", [])),
            outcome_map=tuple(Outcome(**o) for o in raw.get("outcome_map", [])),
            verifier_plan=tuple(Verifier(**v) for v in raw.get("verifier_plan", [])),
            validity_threats=tuple(
                ValidityThreat(**t) for t in raw.get("validity_threats", [])
            ),
            valid_until=expiry.get("valid_until"),
            invalidation_conditions=tuple(expiry.get("invalidation_conditions", [])),
        )

    @classmethod
    def list_all(cls) -> list[str]:
        """Eval ids that carry a campaign manifest."""
        if not EVALS_ROOT.is_dir():
            return []
        return sorted(
            d.name for d in EVALS_ROOT.iterdir() if (d / "campaign.json").is_file()
        )

"""The lab campaign kernel — keeps pre-registered Claims under continuous pressure.

A `Campaign` is a **runtime projection**, not a canon object. It materializes from
canon envelopes (Claim / Evidence / Decision / EventLogEntry) plus a per-eval
manifest, and it owns the one thing canon deliberately does not model: what
challenge the claim must survive next.

Why not canon: canon.md is explicit that it is "an obligations model, not a state
machine" — it records what was pre-registered and what was emitted. Live status,
pressure queues, and next-actions are runtime concerns. Putting them in canon
would make the obligations model into the state machine it refuses to be. If an
audit question turns out to be unanswerable without a campaign field, that is the
signal to escalate a spec bump through context-repository, not to widen the Claim
schema locally.

Alternatives are **rival Claims**, not a new object. Canon already models
arbitration between competing explanations (`Decision.candidate_claims`,
`rejected_alternatives`, `arbitration`, `successor_claim_id`); the campaign just
records which Claims are rivals *before* a Decision exists to say so.

Entry points:
    Campaign.materialize(eval_id) -> Campaign
    gate.failing_gates(campaign)  -> list[GateFailure]     (deterministic publish gates)
    pressure.next_action(campaign) -> PressureAction        (one challenge, or suspend)
"""

from .gate import failing_gates, may_publish
from .manifest import Manifest
from .model import Campaign
from .pressure import next_action
from .store import CanonStore

__all__ = [
    "Campaign",
    "CanonStore",
    "Manifest",
    "failing_gates",
    "may_publish",
    "next_action",
]

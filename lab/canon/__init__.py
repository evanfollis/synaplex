"""The synaplex lab canon emission path — Phase 1 (ADR-0042).

Authorized: `Claim`, `Evidence`, `EventLogEntry` emitters, plus the fail-closed Layer 4
publication guard.

NOT authorized, and refused in code rather than in prose: `Decision`, `Policy`, a runner,
a rival Claim, or anything resembling the reverted `lab/campaign` kernel. Canon v0.1.0
cannot express a frozen, pre-registered, eval-local promotion gate — `policy.md` offers
`operational` (agent-mutable after seeing Evidence, which defeats pre-registration) and
`constitutional` (principal-only, framework-level). An eval gate is neither. The gap is
escalated to context-repository, which owns canon; `validate.py` refuses any local
workaround for it.

    The emitter serializes, validates, and writes. It never selects what to emit.

`memory-systems-v1` can now enter probe and produce Evidence. It **cannot conclude** —
that needs a Decision, and a Decision needs a Policy. It is `incomplete`, not `concluded`,
and no surface may say otherwise.
"""

from .emit import (
    artifact_pointer,
    emit_claim,
    emit_evidence,
    emit_methodology_log,
    emit_phase_transition,
)
from .ids import claim_id, derived_id, hash_file
from .validate import CanonRefusal, validate

__all__ = [
    "CanonRefusal",
    "artifact_pointer",
    "claim_id",
    "derived_id",
    "emit_claim",
    "emit_evidence",
    "emit_methodology_log",
    "emit_phase_transition",
    "hash_file",
    "validate",
]

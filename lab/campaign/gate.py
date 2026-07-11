"""Deterministic publish gates.

A gate is a mechanical check with a named authority. No LLM, no prose matching,
no judgment call — a gate that could be argued with is not a gate.

Every gate answers: **may this campaign publish a reader-facing writeup?** A
failing gate returns the stratum the campaign must route back to. The lab's
operating principle is "canon envelope first, writeup second"; these gates are
what makes that principle enforceable rather than aspirational.

| Gate | Kind | Authority |
|---|---|---|
| `alternatives_required` | defect | source handoff §Highest-value adaptations 2 |
| `outcome_map_required` | defect | source handoff §Suggested first implementation slice |
| `artifact_integrity` | defect | canon.md §Validator-level rules 7 |
| `contradictions_addressed` | defect | canon.md §Obligations 6 |
| `evidence_required` | stage | CLAUDE.md §Operating Principles (envelope first, writeup second) |

## Defect vs. stage

A **defect** gate means the campaign is malformed or unresolved — rivals missing,
hashes stale, contradictions ignored. A **stage** gate means the campaign is
simply not there yet: a freshly pre-registered claim with no results cannot
publish, but nothing about it is wrong. Both block publication; only defects set
the campaign's status to `blocked`. Folding them together would report every new
campaign as broken, and a status that says "blocked" about a healthy campaign is
a status nobody reads.

## Waiver contract

`alternatives_required` is waivable, because a genuinely single-explanation claim
can exist. The waiver is not a config flag — it is a canon `Decision(kind=continue)`
on the primary claim whose `policies_in_force` names `lab.alternatives_required`.
A waiver must therefore cite the very gate it waives, carry a rationale, and land
in the append-only store. Waiving is possible; waiving quietly is not.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .model import Campaign

GATE_POLICY_ID = "lab.alternatives_required"

# Strata a blocked campaign routes back to.
OPERATIONALIZATION = "operationalization"
EVIDENCE = "evidence"
ARBITRATION = "arbitration"

# Gate kinds. See module docstring §Defect vs. stage.
DEFECT = "defect"
STAGE = "stage"


@dataclass(frozen=True)
class GateFailure:
    gate: str
    route_to: str
    reason: str
    remedy: str
    authority: str
    kind: str = DEFECT


def _has_waiver(campaign: "Campaign") -> bool:
    """A Decision(kind=continue) on the primary claim that names the gate policy."""
    for d in campaign.decisions:
        if d.get("kind") != "continue":
            continue
        if d.get("chosen_claim_id") != campaign.primary.id:
            continue
        policies = {p.get("policy_id") for p in d.get("policies_in_force", [])}
        if GATE_POLICY_ID in policies:
            return True
    return False


def failing_gates(campaign: "Campaign") -> list[GateFailure]:
    """All gates currently blocking publication. Empty list = clear to publish."""
    failures: list[GateFailure] = []

    if not campaign.has_alternatives and not _has_waiver(campaign):
        failures.append(
            GateFailure(
                gate="alternatives_required",
                route_to=OPERATIONALIZATION,
                reason=(
                    "the primary claim has no registered rival explanations, so no "
                    "observation can distinguish it being true from the experiment "
                    "being unable to detect it being false"
                ),
                remedy=(
                    f"register rival Claims in canon and list them in the campaign "
                    f"manifest, or emit a Decision(kind=continue) citing policy "
                    f"'{GATE_POLICY_ID}' to waive with rationale"
                ),
                authority="handoff §Highest-value adaptations 2",
            )
        )

    if campaign.has_alternatives and not campaign.manifest.outcome_map:
        failures.append(
            GateFailure(
                gate="outcome_map_required",
                route_to=OPERATIONALIZATION,
                reason=(
                    "rivals are registered but no outcome map says which observation "
                    "selects which claim — rivals that cannot be adjudicated are "
                    "decoration, not falsification"
                ),
                remedy="add outcome_map rows to the campaign manifest, pre-registered before execution",
                authority="handoff §Suggested first implementation slice",
            )
        )

    if campaign.artifact_violations:
        failures.append(
            GateFailure(
                gate="artifact_integrity",
                route_to=EVIDENCE,
                reason=(
                    f"{len(campaign.artifact_violations)} ArtifactPointer(s) do not "
                    f"reproduce: {'; '.join(campaign.artifact_violations)}"
                ),
                remedy="re-emit the affected envelope against the current artifact bytes; never edit the hash in place",
                authority="canon.md §Validator-level rules 7",
            )
        )

    unaddressed = campaign.unaddressed_contradictions
    if unaddressed:
        ids = ", ".join(e["id"] for e in unaddressed)
        failures.append(
            GateFailure(
                gate="contradictions_addressed",
                route_to=ARBITRATION,
                reason=f"contradicting Evidence with no Decision treating it: {ids}",
                remedy="emit a Decision whose contradictions_addressed[] treats each contradicting Evidence id",
                authority="canon.md §Obligations 6",
            )
        )

    if not campaign.all_evidence:
        failures.append(
            GateFailure(
                gate="evidence_required",
                route_to=EVIDENCE,
                reason=(
                    "zero Evidence envelopes exist, so the outcome map cannot select "
                    "any explanation — there is no finding to write up"
                ),
                remedy="execute the pre-registered suites and emit Evidence envelopes",
                authority="CLAUDE.md §Operating Principles (canon envelope first, writeup second)",
                kind=STAGE,
            )
        )

    return failures


def defect_gates(campaign: "Campaign") -> list[GateFailure]:
    """Failing gates that indicate the campaign is malformed, not merely early."""
    return [g for g in failing_gates(campaign) if g.kind == DEFECT]


def may_publish(campaign: "Campaign") -> bool:
    return not failing_gates(campaign)

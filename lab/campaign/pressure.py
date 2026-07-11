"""Deterministic pressure scheduler.

The gap this closes: synaplex could pre-register a Claim and then leave it
parked. Pre-registration without continuous pressure is a filing cabinet, not a
lab. The scheduler answers one question, every time it is asked:

    **What is the single most valuable challenge this campaign must now survive?**

It returns exactly one action, or `suspend` with a rationale. Never a list of
suggestions — a scheduler that emits five options has made no decision.

Deterministic on purpose. Inputs are canon envelopes + the manifest; the ranking
is a total order over them. No LLM, no sampling, no hidden state. Learned routing
is a later question and it can only be evaluated against a deterministic baseline
that already exists (source handoff §Highest-value adaptations 3).

## The falsification bias

When evidence exists but nothing contradicts the claim, the scheduler does NOT
propose the next supporting benchmark. It proposes the most independent
*falsifier*. Ranking, in order:

1. **Non-redundant** — the verifier's primary lineage must not already appear in
   the evidence set. Re-running a lineage produces a correlated observation, not
   a new one. (`Campaign.unexercised_verifiers`)
2. **Most binding** — highest canon Evidence tier wins. `external_transaction`
   beats `internal_operational`; reality beats self-report.
3. **Aimed at the primary** — a verifier that can falsify the claim we actually
   make beats one that shores up a rival.

A campaign that only ever accumulates supporting evidence from one lineage is
indistinguishable from a campaign that is wrong.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .gate import defect_gates
from .manifest import Verifier
from .model import Campaign

# Action kinds.
CLEAR_GATE = "clear_gate"
EXECUTE = "execute"
FALSIFY = "falsify"
REVALIDATE = "revalidate"
SUSPEND = "suspend"


@dataclass
class PressureAction:
    action: str
    rationale: str
    route_to: str = ""
    target: str = ""
    # Challenges considered and not chosen, best-first. Recorded so the
    # non-redundancy argument is auditable rather than asserted.
    passed_over: list[str] = field(default_factory=list)

    def render(self) -> str:
        lines = [f"action:    {self.action}"]
        if self.target:
            lines.append(f"target:    {self.target}")
        if self.route_to:
            lines.append(f"route to:  {self.route_to}")
        lines.append(f"rationale: {self.rationale}")
        if self.passed_over:
            lines.append("passed over:")
            lines.extend(f"  - {p}" for p in self.passed_over)
        return "\n".join(lines)


def _rank_verifiers(campaign: Campaign) -> list[Verifier]:
    """Total order over available challenges. See module docstring §falsification bias."""
    return sorted(
        campaign.unexercised_verifiers,
        key=lambda v: (
            -v.tier_rank,
            0 if v.targets == campaign.primary.id else 1,
            v.id,
        ),
    )


def next_action(campaign: Campaign) -> PressureAction:
    """The one challenge this campaign must now survive."""

    # 1. A defect outranks everything. A campaign that is malformed should not be
    #    gathering more evidence toward publishing something it cannot publish.
    #    (The `evidence_required` gate is a stage, not a defect — rule 2 owns it,
    #    and routing it here would just say "get evidence" in a clumsier voice.)
    gates = defect_gates(campaign)
    if gates:
        g = gates[0]
        return PressureAction(
            action=CLEAR_GATE,
            target=g.gate,
            route_to=g.route_to,
            rationale=f"{g.reason} — {g.remedy} [{g.authority}]",
            passed_over=[f"gate {o.gate}: {o.reason}" for o in gates[1:]],
        )

    # 2. Gates clear, no evidence: the outcome map cannot discriminate without data.
    if not campaign.all_evidence:
        rationale = (
            f"pre-registration is complete ({len(campaign.alternatives)} rival "
            f"claim(s), {len(campaign.manifest.outcome_map)} outcome-map row(s)) "
            f"and zero Evidence envelopes exist — the outcome map cannot select "
            f"between explanations without data. Execute the pre-registered suites."
        )
        if campaign.primary.phase == "draft":
            rationale += (
                " Probe entry first: canon.md §Phase invariants requires an "
                "EventLogEntry(phase_transition draft->probe) plus a methodology_log "
                "entry before the claim is under pre-registration immutability."
            )
        return PressureAction(
            action=EXECUTE,
            target=campaign.manifest.eval_id,
            route_to="probe" if campaign.primary.phase == "draft" else "evidence",
            rationale=rationale,
        )

    # 3. Support has gone stale: re-verify rather than sit on an expired packet.
    if campaign.is_expired:
        return PressureAction(
            action=REVALIDATE,
            target=campaign.primary.id,
            route_to="evidence",
            rationale=(
                f"the decision packet expired on {campaign.manifest.valid_until}; "
                f"support is not wrong, it is unverified. Invalidation conditions: "
                f"{'; '.join(campaign.manifest.invalidation_conditions) or 'none declared'}"
            ),
        )

    # 4. Evidence exists but nothing contradicts anything. Seek the falsifier.
    contradicting = sum(v.independent("contradicts") for v in campaign.claim_views)
    ranked = _rank_verifiers(campaign)
    if ranked:
        best, rest = ranked[0], ranked[1:]
        supporting = campaign.primary.independent("supports")
        bias = (
            f"{supporting} independent supporting lineage(s) and {contradicting} "
            f"contradicting — "
        )
        bias += (
            "the campaign has never been challenged, only confirmed. "
            if contradicting == 0
            else "pressure continues. "
        )
        return PressureAction(
            action=FALSIFY,
            target=best.id,
            route_to="evidence",
            rationale=(
                f"{bias}Most independent unexercised falsifier: {best.challenge} "
                f"(targets {best.targets}, lineage '{best.lineage}', tier {best.tier}). "
                f"Chosen over the alternatives because its lineage is absent from the "
                f"evidence set and its tier is the most binding available."
            ),
            passed_over=[
                f"{v.id}: {v.challenge} (tier {v.tier}, lineage '{v.lineage}')"
                for v in rest
            ],
        )

    # 5. Nothing left to run.
    return PressureAction(
        action=SUSPEND,
        target=campaign.manifest.campaign_id,
        rationale=(
            f"verifier plan exhausted ({len(campaign.manifest.verifier_plan)} verifier(s), "
            f"all lineages exercised), no unaddressed contradictions, no expiry pending. "
            f"Suspending is not concluding: reopen when a new lineage becomes available, "
            f"the environment shifts, or an invalidation condition fires."
        ),
    )

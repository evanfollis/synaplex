"""CLI for the lab campaign kernel.

    python -m lab.campaign list
    python -m lab.campaign status <eval-id>
    python -m lab.campaign gate <eval-id>       # exit 1 if publication is blocked
    python -m lab.campaign pressure <eval-id>

`gate` exits non-zero when blocked, so a publish path can gate on it directly:

    python -m lab.campaign gate memory-systems-v1 || exit 1

Every invocation emits a typed friction event (layer `lab`). A campaign kernel
that runs silently is indistinguishable from one that is stuck — the same S3-P2
rule that governs intake governs this.
"""

from __future__ import annotations

import sys

from intake import friction

from .gate import failing_gates
from .manifest import Manifest
from .model import Campaign, lineage_key
from .pressure import next_action


def _render_status(c: Campaign) -> str:
    m = c.manifest
    out = [
        f"campaign:  {m.campaign_id}  (eval {m.eval_id})",
        f"status:    {c.status}",
        "",
        f"primary    [{c.primary.id}] phase={c.primary.phase}",
        f"           {c.primary.statement}",
    ]
    if c.alternatives:
        out.append("")
        out.append(f"rivals     ({len(c.alternatives)})")
        for a in c.alternatives:
            out.append(f"           [{a.id}] phase={a.phase}")
            out.append(f"           {a.statement}")
    else:
        out.append("")
        out.append("rivals     none registered")

    out.append("")
    out.append(f"evidence   {len(c.all_evidence)} envelope(s), "
               f"{len(c.exercised_lineages)} independent lineage(s)")
    for v in c.claim_views:
        if v.evidence:
            out.append(
                f"           [{v.id}] supports={v.independent('supports')} "
                f"contradicts={v.independent('contradicts')} "
                f"neutral={v.independent('neutral')}  (independent lineages)"
            )
    unaddressed = c.unaddressed_contradictions
    if unaddressed:
        out.append(f"           {len(unaddressed)} contradiction(s) UNADDRESSED: "
                   f"{', '.join(e['id'] for e in unaddressed)}")

    out.append("")
    out.append(f"verifiers  {len(c.unexercised_verifiers)} unexercised "
               f"/ {len(m.verifier_plan)} planned")
    for v in c.unexercised_verifiers:
        out.append(f"           - [{v.id}] {v.challenge}  (tier {v.tier})")

    out.append("")
    out.append(f"outcome map ({len(m.outcome_map)} row(s))")
    for o in m.outcome_map:
        out.append(f"           if {o.observation}")
        out.append(f"              -> selects {o.selects}")

    if m.validity_threats:
        out.append("")
        out.append(f"validity threats ({len(m.validity_threats)})")
        for t in m.validity_threats:
            out.append(f"           - [{t.id}] {t.boundary_class}: {t.description}")

    if m.valid_until:
        out.append("")
        out.append(f"expiry     valid_until={m.valid_until}  expired={c.is_expired}")

    gates = failing_gates(c)
    out.append("")
    if gates:
        out.append(f"GATES      {len(gates)} FAILING — publication blocked")
        for g in gates:
            out.append(f"           x {g.gate} ({g.kind}) -> route to {g.route_to}")
            out.append(f"             {g.reason}")
    else:
        out.append("GATES      all clear — publication permitted")

    if c.artifact_violations:
        out.append("")
        out.append("ARTIFACT INTEGRITY VIOLATIONS")
        for v in c.artifact_violations:
            out.append(f"           ! {v}")

    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print(__doc__)
        return 2

    cmd = argv[0]

    if cmd == "list":
        ids = Manifest.list_all()
        if not ids:
            print("no campaigns (no lab/evals/*/campaign.json)")
        for i in ids:
            c = Campaign.materialize(i)
            print(f"{i:28s} {c.status}")
        return 0

    if cmd not in {"status", "gate", "pressure"} or len(argv) < 2:
        print(__doc__)
        return 2

    eval_id = argv[1]
    campaign = Campaign.materialize(eval_id)

    if cmd == "status":
        print(_render_status(campaign))
        friction.emit(
            layer="lab",
            source="campaign",
            eventType="success",
            reason=f"campaign {campaign.manifest.campaign_id} status={campaign.status}",
            ref=str(Manifest.path_for(eval_id)),
        )
        return 0

    if cmd == "gate":
        gates = failing_gates(campaign)
        if not gates:
            print(f"PASS — {campaign.manifest.campaign_id}: all gates clear, publication permitted")
            friction.emit(
                layer="lab",
                source="gate",
                eventType="success",
                reason=f"campaign {campaign.manifest.campaign_id} cleared all publish gates",
                ref=str(Manifest.path_for(eval_id)),
            )
            return 0
        print(f"BLOCKED — {campaign.manifest.campaign_id}: {len(gates)} gate(s) failing\n")
        for g in gates:
            print(f"  x {g.gate}  ({g.kind})  [{g.authority}]")
            print(f"    reason: {g.reason}")
            print(f"    remedy: {g.remedy}")
            print(f"    route:  {g.route_to}\n")
        # A blocked publish is a designed refusal, not an incident: `throttled`,
        # not `failure` (workspace S1-P2 addendum).
        friction.emit(
            layer="lab",
            source="gate",
            eventType="throttled",
            reason=(
                f"campaign {campaign.manifest.campaign_id} publication blocked by "
                f"{len(gates)} gate(s): {', '.join(g.gate for g in gates)}"
            ),
            ref=str(Manifest.path_for(eval_id)),
            extra={"routes": sorted({g.route_to for g in gates})},
        )
        return 1

    if cmd == "pressure":
        action = next_action(campaign)
        print(action.render())
        friction.emit(
            layer="lab",
            source="pressure",
            eventType="success",
            reason=(
                f"campaign {campaign.manifest.campaign_id} next action="
                f"{action.action} target={action.target or '-'}"
            ),
            ref=str(Manifest.path_for(eval_id)),
        )
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())

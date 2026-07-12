"""Canon validator rules that need to see more than one envelope (canon.md §Validator-level rules).

Rules 1 and 7 look at a single document and live in `validate.py`. Everything here is
cross-envelope: *is this gate late relative to that Evidence*, *does this Decision cite
every frozen Policy bound to its chosen Claim*. They take a `CanonView`.

Each rule raises `CanonRefusal` carrying the exact `violation_kind` canon.md names for it,
because a refusal for the wrong reason is a bug that looks like a pass.

## The one thing to internalize before touching this file

Rules 9–14 protect a frozen gate from being amended or issued late. They were **entirely
decorative** in the first draft of canon v0.2.0, and adversarial review proved it by
executing the bypass: run the eval, look at the results, mint a *fresh* Claim — whose
pre-registration window is wide open precisely because it has no Evidence — freeze a
flattering gate against it, and conclude it while citing the *old* Claim's Evidence.
Nothing amended, nothing late, nothing duplicated. Every rule passed.

**Rule 15** closes the citation path. **Rule 16 is the one that matters**, because an
attacker who simply *re-emits the same observations* under the new Claim satisfies rule 15
trivially and the emission order looks impeccable. `emitted_at` cannot save you: it is
entirely under the emitter's control. So the window anchors on **`observed_at`** — the
emitter's assertion about when reality was consulted.

This does not make the attack impossible. It changes what the attack *is*: from "order
your envelopes cleverly" to "falsify an observation timestamp against a hash-pinned
artifact." That is fabrication, not a loophole. Canon closes loopholes; it cannot stop a
liar and does not claim to.

**Which is why `emit_evidence` takes `observed_at` from the run and never from the clock.**
Stamping it at emission time destroys the anchor and silently reopens the whole attack.
"""

from __future__ import annotations

from typing import Any

from .serialize import equal
from .view import CanonView

TERMINAL_KINDS = frozenset({"promote", "kill", "pivot"})


class CanonRefusal(Exception):
    """A canon violation. `violation_kind` is what gets logged in the EventLogEntry."""

    def __init__(self, violation_kind: str, rationale: str) -> None:
        super().__init__(rationale)
        self.violation_kind = violation_kind
        self.rationale = rationale


def _json_pointer(doc: Any, pointer: str) -> Any:
    """RFC-6901. Raises KeyError/IndexError if the pointer does not resolve."""
    if pointer in ("", "/"):
        return doc
    node = doc
    for raw in pointer.lstrip("/").split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        node = node[int(token)] if isinstance(node, list) else node[token]
    return node


def _scopes_overlap(a: str, b: str) -> bool:
    """Do two Policy scopes govern any common ground?

    Scopes look like `framework`, `L3`, `L3:synaplex`, `layer:L3`. `framework` covers
    everything; `L3` covers `L3:synaplex`. Deliberately generous — for rule 17, a false
    overlap costs a refusal (recoverable), a missed overlap costs the self-authorization
    firewall (not).
    """
    if a == b or "framework" in (a, b):
        return True
    return a.startswith(f"{b}:") or b.startswith(f"{a}:")


# --- rules 2-5 (v0.1.0, Decision/Policy coherence) -------------------------


def rule_2_3_candidate_set(decision: dict) -> None:
    candidates = set(decision.get("candidate_claims", []))
    chosen = decision.get("chosen_claim_id")
    if chosen not in candidates:
        raise CanonRefusal(
            "candidate_set_inconsistency",
            f"chosen_claim_id {chosen!r} is not in candidate_claims — canon rule 2.",
        )
    rejected = {r["claim_id"] for r in decision.get("rejected_alternatives", [])}
    if ({chosen} | rejected) != candidates:
        raise CanonRefusal(
            "candidate_set_inconsistency",
            f"{{chosen}} u {{rejected_alternatives}} != candidate_claims — canon rule 3. "
            f"chosen={chosen!r} rejected={sorted(rejected)} candidates={sorted(candidates)}. "
            f"A candidate that is neither chosen nor explicitly rejected is a claim the "
            f"Decision quietly declined to arbitrate.",
        )


def rule_4_rollback_precedence(policy: dict) -> None:
    rule = policy.get("rollback_rule") or {}
    rules, precedence = rule.get("rules"), rule.get("precedence")
    if not rules or precedence is None:
        return
    if sorted(precedence) != sorted(r["id"] for r in rules):
        raise CanonRefusal(
            "rollback_precedence_invalid",
            "rollback_rule.precedence is not a permutation of rules[*].id — canon rule 4.",
        )


def rule_5_policy_reference_resolves(decision: dict, view: CanonView) -> None:
    for ref in decision.get("policies_in_force", []):
        policy = view.policy_by_id(ref["policy_id"])
        if policy is None:
            raise CanonRefusal(
                "policy_reference_unresolved",
                f"policies_in_force names Policy {ref['policy_id']!r}, which does not exist "
                f"— canon rule 5. A Decision governed by a policy nobody can find is a "
                f"Decision governed by nothing.",
            )
        versions = {policy.get("version")} | {
            p.get("version") for p in policy.get("provenance", [])
        }
        if ref.get("version") not in versions:
            raise CanonRefusal(
                "policy_reference_unresolved",
                f"Policy {ref['policy_id']!r} version {ref.get('version')!r} is in neither the "
                f"current version nor the provenance chain — canon rule 5.",
            )


# --- rules 9-17 (v0.2.0, the frozen class) ---------------------------------


def rule_9_no_amendment(decision: dict, view: CanonView) -> None:
    if decision.get("kind") not in {"amend_policy", "rollback_policy"}:
        return
    target = view.policy_by_id(decision.get("target_policy_id", ""))
    if target and target.get("class") == "frozen":
        raise CanonRefusal(
            "frozen_policy_amendment_attempt",
            f"Decision(kind={decision['kind']}) targets frozen Policy "
            f"{decision['target_policy_id']!r} — canon rule 9. A frozen gate is amendable by "
            f"nobody, including the principal. That is the entire point of the class.",
        )


def rule_10_window(policy: dict, view: CanonView) -> None:
    """The pre-registration window. Late issuance — not amendment — is the real attack."""
    if policy.get("class") != "frozen":
        return
    claim_id = policy.get("bound_to_claim_id")
    claim = view.claim(claim_id)
    if claim is None:
        raise CanonRefusal(
            "frozen_policy_late_issuance",
            f"frozen Policy is bound to Claim {claim_id!r}, which does not exist.",
        )
    p_at = policy["emitted_at"]

    if claim["emitted_at"] > p_at:
        raise CanonRefusal(
            "frozen_policy_late_issuance",
            f"frozen gate emitted at {p_at} predates its Claim ({claim['emitted_at']}) — rule 10.",
        )

    probe_at = view.probe_entry_at(claim_id)
    if probe_at is not None and p_at > probe_at:
        raise CanonRefusal(
            "frozen_policy_late_issuance",
            f"frozen gate emitted at {p_at}, after the Claim entered probe at {probe_at} — "
            f"rule 10. The pre-registration window closes at probe entry.",
        )

    for e in view.evidence_for(claim_id):
        if p_at > e["emitted_at"]:
            raise CanonRefusal(
                "frozen_policy_late_issuance",
                f"frozen gate emitted at {p_at}, after Evidence {e['id']} was emitted at "
                f"{e['emitted_at']} — rule 10. A gate chosen after the results is a post-hoc "
                f"gate, and no amendment check will ever catch it.",
            )
        observed = e.get("observed_at")
        if observed and p_at > observed:
            raise CanonRefusal(
                "frozen_policy_late_issuance",
                f"frozen gate emitted at {p_at}, but Evidence {e['id']} observed reality at "
                f"{observed} — rule 10. Reality was consulted before the gate was chosen. "
                f"emitted_at cannot catch this: it is entirely under the emitter's control.",
            )


def rule_11_unique(policy: dict, view: CanonView) -> None:
    if policy.get("class") != "frozen":
        return
    twins = [
        p
        for p in view.frozen_policies_for(policy.get("bound_to_claim_id"))
        if p.get("field_path") == policy.get("field_path") and p["id"] != policy["id"]
    ]
    if twins:
        raise CanonRefusal(
            "frozen_policy_duplicate",
            f"a frozen Policy already governs {policy.get('field_path')!r} on Claim "
            f"{policy.get('bound_to_claim_id')!r} ({twins[0]['id']}) — canon rule 11. Two gates "
            f"on one field let an emitter cite whichever the results favour, with nothing "
            f"amended and a clean-looking trail.",
        )


def rule_12_13_citation(decision: dict, view: CanonView) -> None:
    candidates = set(decision.get("candidate_claims", []))
    cited_ids = {r["policy_id"] for r in decision.get("policies_in_force", [])}

    # 12 — a gate pre-registered for one Claim has no authority over another.
    for pid in cited_ids:
        policy = view.policy_by_id(pid)
        if policy and policy.get("class") == "frozen":
            if policy.get("bound_to_claim_id") not in candidates:
                raise CanonRefusal(
                    "frozen_policy_scope_violation",
                    f"Decision cites frozen Policy {pid!r}, bound to Claim "
                    f"{policy.get('bound_to_claim_id')!r}, which is not among candidate_claims "
                    f"— canon rule 12.",
                )

    # 13 — citing only the gates you passed is cherry-picking a pre-registration.
    if decision.get("kind") not in TERMINAL_KINDS:
        return
    required = {p["id"] for p in view.frozen_policies_for(decision.get("chosen_claim_id"))}
    missing = sorted(required - cited_ids)
    if missing:
        raise CanonRefusal(
            "frozen_policy_citation_incomplete",
            f"terminal Decision(kind={decision['kind']}) omits frozen Policy/Policies "
            f"{', '.join(missing)} bound to the chosen Claim — canon rule 13. Citing only the "
            f"gates that were met is cherry-picking a pre-registration.",
        )


def rule_14_derivation(policy: dict, view: CanonView) -> None:
    pointer = policy.get("derived_from")
    if policy.get("class") != "frozen" or not pointer:
        return
    claim = view.claim(policy.get("bound_to_claim_id"))
    if claim is None:
        return  # rule 10 already refuses this
    try:
        subtree = _json_pointer(claim, pointer)
    except (KeyError, IndexError, ValueError):
        raise CanonRefusal(
            "frozen_policy_derivation_mismatch",
            f"derived_from {pointer!r} does not resolve in Claim {claim['id']} — canon rule 14.",
        ) from None
    # Canonical-JSON equality, never bytes: `0.80` and `0.8` are the same number, and any
    # serializer round-trips one to the other. A byte check would be born broken.
    if not equal(subtree, policy.get("value")):
        raise CanonRefusal(
            "frozen_policy_derivation_mismatch",
            f"Policy.value is not canonical-JSON-equal to Claim {claim['id']} at {pointer!r} "
            f"— canon rule 14. The gate claims to be derived from the hash-bound Claim and "
            f"is not; it carries information the pre-registration does not.",
        )


def rule_15_evidence_claim_coherence(decision: dict, view: CanonView) -> None:
    """The rule that makes 9-14 mean anything. See module docstring."""
    candidates = set(decision.get("candidate_claims", []))
    for eid in decision.get("cited_evidence", []):
        e = view.evidence_by_id(eid)
        if e is None:
            raise CanonRefusal(
                "evidence_claim_mismatch",
                f"Decision cites Evidence {eid!r}, which does not exist — canon rule 15.",
            )
        if e.get("claim_id") not in candidates:
            raise CanonRefusal(
                "evidence_claim_mismatch",
                f"Decision cites Evidence {eid!r}, gathered about Claim {e.get('claim_id')!r}, "
                f"which is not among candidate_claims — canon rule 15. This is the evidence-"
                f"laundering path: run the eval, mint a fresh Claim with an open window, freeze "
                f"a flattering gate on it, then conclude it citing the old Claim's evidence.",
            )


def rule_16_evidence_anchored(evidence: dict, view: CanonView) -> None:
    """Evidence under a frozen gate MUST carry `observed_at`, or rule 10 is vacuous."""
    claim_id = evidence.get("claim_id")
    if not view.frozen_policies_for(claim_id):
        return  # observed_at stays optional elsewhere; no v0.1.0 envelope is invalidated
    if not evidence.get("observed_at"):
        raise CanonRefusal(
            "frozen_policy_evidence_unanchored",
            f"Evidence {evidence['id']} on frozen-gated Claim {claim_id!r} carries no "
            f"observed_at — canon rule 16. Without it rule 10's anchor is vacuous and the "
            f"re-emission attack is wide open. observed_at must come from the run, not the clock.",
        )


def rule_17_no_constitutional_collision(policy: dict, view: CanonView) -> None:
    if policy.get("class") != "frozen":
        return
    for other in view.policies():
        if other.get("class") != "constitutional":
            continue
        if other.get("field_path") != policy.get("field_path"):
            continue
        if _scopes_overlap(policy.get("scope", ""), other.get("scope", "")):
            raise CanonRefusal(
                "frozen_policy_constitutional_collision",
                f"frozen Policy governs {policy.get('field_path')!r}, which constitutional "
                f"Policy {other['id']} also governs at overlapping scope — canon rule 17. A "
                f"frozen gate on a constitutional field is a ceiling an agent grants itself "
                f"that nobody, including the principal, may ever amend.",
            )


def check_all(envelope: dict, view: CanonView) -> None:
    """Apply every cross-envelope rule that bears on this envelope type."""
    object_type = envelope.get("object_type")

    if object_type == "Policy":
        rule_4_rollback_precedence(envelope)
        rule_10_window(envelope, view)
        rule_11_unique(envelope, view)
        rule_14_derivation(envelope, view)
        rule_17_no_constitutional_collision(envelope, view)

    elif object_type == "Decision":
        rule_2_3_candidate_set(envelope)
        rule_5_policy_reference_resolves(envelope, view)
        rule_9_no_amendment(envelope, view)
        rule_12_13_citation(envelope, view)
        rule_15_evidence_claim_coherence(envelope, view)

    elif object_type == "Evidence":
        rule_16_evidence_anchored(envelope, view)

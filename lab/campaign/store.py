"""Read-only view over the lab canon envelope store at `lab/.canon/`.

The store is append-only and hash-pinned. Nothing here mutates it; `emit.py`
is the only writer. This module exists so that every downstream consumer
(campaign projection, publish gates, pressure scheduler) reads canon through
one path with one set of integrity checks, rather than each re-implementing
`json.load` over a glob.

Two canon obligations are enforced on read:

- **Validator rule 7** — `ArtifactPointer.content_hash` must reproduce from the
  artifact at `uri`. `verify_artifacts()` returns the violations; it does not
  raise, because a stale hash is a finding the campaign should *report*, not a
  crash that hides the rest of the state.
- **Phase invariants (canon.md)** — "Phase is not a field on the Claim." Phase
  is reconstructed by ordering `EventLogEntry(event_kind=phase_transition)`
  events per Claim. `phase_of()` is that replay.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from .ids import hash_file

REPO_ROOT = Path(
    os.environ.get("SYNAPLEX_REPO_ROOT", str(Path(__file__).resolve().parents[2]))
)
CANON_ROOT = Path(os.environ.get("SYNAPLEX_CANON_ROOT", str(REPO_ROOT / "lab" / ".canon")))

# Directory name per object_type. Mirrors the layout the hand-authored Claim
# established (`claims/<id>.json`).
_DIRS = {
    "Claim": "claims",
    "Evidence": "evidence",
    "Decision": "decisions",
    "EventLogEntry": "events",
    "Policy": "policies",
}

PHASES = ("draft", "probe", "promotion")


def dir_for(object_type: str) -> Path:
    return CANON_ROOT / _DIRS[object_type]


@dataclass
class CanonStore:
    """All envelopes, loaded once, indexed by the joins the lab actually makes."""

    claims: dict[str, dict] = field(default_factory=dict)
    evidence: list[dict] = field(default_factory=list)
    decisions: list[dict] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)
    policies: list[dict] = field(default_factory=list)

    @classmethod
    def load(cls) -> "CanonStore":
        store = cls()
        for object_type, dirname in _DIRS.items():
            d = CANON_ROOT / dirname
            if not d.is_dir():
                continue
            for p in sorted(d.glob("*.json")):
                env = json.loads(p.read_text(encoding="utf-8"))
                if env.get("object_type") != object_type:
                    raise ValueError(
                        f"{p}: object_type={env.get('object_type')!r} but lives in {dirname}/"
                    )
                if object_type == "Claim":
                    store.claims[env["id"]] = env
                elif object_type == "Evidence":
                    store.evidence.append(env)
                elif object_type == "Decision":
                    store.decisions.append(env)
                elif object_type == "EventLogEntry":
                    store.events.append(env)
                elif object_type == "Policy":
                    store.policies.append(env)
        return store

    # --- joins -----------------------------------------------------------

    def evidence_for(self, claim_id: str) -> list[dict]:
        return [e for e in self.evidence if e.get("claim_id") == claim_id]

    def decisions_for(self, claim_id: str) -> list[dict]:
        """Decisions that arbitrated over this claim — chosen or rejected."""
        return [
            d
            for d in self.decisions
            if claim_id in d.get("candidate_claims", [])
            or d.get("chosen_claim_id") == claim_id
        ]

    def phase_of(self, claim_id: str) -> str:
        """Reconstruct a Claim's phase by replaying its phase_transition events.

        canon.md §Phase invariants: phase is never stored on the Claim. A Claim
        with no transition events has never left `draft`.
        """
        transitions = [
            e
            for e in self.events
            if e.get("event_kind") == "phase_transition"
            and e.get("phase_transition", {}).get("claim_id") == claim_id
        ]
        transitions.sort(key=lambda e: e["emitted_at"])
        phase = "draft"
        for t in transitions:
            phase = t["phase_transition"]["to_phase"]
        return phase

    # --- integrity -------------------------------------------------------

    def verify_artifacts(self) -> list[str]:
        """Canon validator rule 7 across every envelope carrying an ArtifactPointer.

        Returns a list of human-readable violations (empty = clean). A pointer
        whose file is missing is a violation; so is a hash that no longer
        reproduces.
        """
        violations: list[str] = []
        envelopes = (
            list(self.claims.values())
            + self.evidence
            + self.decisions
            + self.events
            + self.policies
        )
        for env in envelopes:
            ptr = env.get("artifact")
            if not ptr:
                continue
            uri = ptr.get("uri", "")
            if not uri.startswith("file://"):
                continue  # non-file pointers are out of scope for local replay
            rel = uri[len("file://") :]
            path = REPO_ROOT / rel
            if not path.is_file():
                violations.append(
                    f"{env['object_type']} {env['id']}: artifact missing at {rel}"
                )
                continue
            actual = hash_file(path)
            if actual != ptr.get("content_hash"):
                violations.append(
                    f"{env['object_type']} {env['id']}: content_hash stale for {rel} "
                    f"(envelope={ptr.get('content_hash')} actual={actual})"
                )
        return violations

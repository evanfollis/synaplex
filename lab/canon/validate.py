"""Emission-time validation. Refuses the write; never warns and proceeds.

`canon.md` §Validator-level rules: *"Adapters that persist envelopes MUST run these
checks at emission time."* Not at read time, not in CI — at the moment of writing,
because canon is append-only and a bad envelope that lands cannot be taken back.

Four families of refusal, each mapped to a `ViolationKind` so the
`EventLogEntry(canon_violation)` the emitter writes is machine-readable:

1. **Schema.** Validated against the real `context-repository` schemas — not a local
   re-description of them. `additionalProperties: false` and the `required` arrays do
   most of the work; re-typing them here would create a second copy to drift.
2. **Canon rule 1** — `role_declared_at <= emitted_at`. The retrospective-relabel
   defense: an event cannot be backdated into a window it was not declared in.
3. **Canon rule 7** — `ArtifactPointer.content_hash` reproduces from the artifact at
   `uri`. A stale hash means the envelope no longer describes the thing it points at.
4. **Phase-1 scope** — the envelope must carry no `Decision`/`Policy` field. Canon
   rules 2–6 and 8 govern fields Phase 1 does not emit; per ADR-0042 AC2 the validator
   must **refuse** if those fields appear rather than pass them through unchecked. A
   validator that ignores what it does not understand is not a validator.

Plus the ADR-0038 write-side laundering refusal, which lives here because it is a
validation rule, not a special case: **no envelope may reference `reasoning/programmes/`
in any field.**
"""

from __future__ import annotations

import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, RefResolver

from .ids import hash_file
from .store import PHASE_1_TYPES, REPO_ROOT

SCHEMA_ROOT = Path(
    os.environ.get(
        "SYNAPLEX_CANON_SCHEMAS",
        "/opt/workspace/projects/context-repository/spec/discovery-framework/schemas",
    )
)

PROGRAMME_REL = "reasoning/programmes"

# The digest of the canon schema set this emitter was written and reviewed against.
#
# WHY THIS EXISTS: `spec/` is in context-repository's `.gitignore` (line 11), so the L1
# canon — the highest truth source in this system, the contract every envelope in three
# repos binds itself to — is **not under version control**. It cannot be diffed,
# reviewed, attributed, or reverted. On 2026-07-12 it changed from 0.1.0 to 0.2.0 in
# place, with no CHANGELOG entry and no review artifact; the "frozen" 0.1.0 spec is
# unrecoverable. Nothing detected it. This tripwire is what detects it next time.
#
# Canon demands every artifact be hash-bound and immutable. That discipline was never
# applied to canon itself. Here it is, applied by its first programmatic writer.
#
# A drift here is NOT necessarily a fault — context-repository owns canon and may
# legitimately bump it. But a bump must be *seen*. `test_canon.py` asserts this digest;
# when it fails, a human re-reads the schemas, confirms the change is intended and
# backward-compatible, and updates the pin. Silent is the only outcome forbidden.
# Pinned 2026-07-12 against the schema set on disk that day: `$id` 0.2.0, Policy class
# enum {constitutional, operational, frozen}, decision.schema.json referencing a
# "validator rule 13". Verified on pinning: all 275 pre-existing envelopes across
# synaplex, atlas, and skillfoundry still validate — the bump is additive, so nothing
# in canon was retroactively invalidated. That was luck, not process.
EXPECTED_SCHEMA_DIGEST = "bcc6d01315fed7f9"


def schema_digest() -> str:
    """Stable digest over the canon schema set: sorted (filename, sha256) pairs."""
    h = hashlib.sha256()
    for path in sorted(SCHEMA_ROOT.glob("*.schema.json")):
        h.update(path.name.encode("utf-8"))
        h.update(hashlib.sha256(path.read_bytes()).hexdigest().encode("utf-8"))
    return h.hexdigest()[:16]

# Fields that belong only to Decision or Policy envelopes. Phase 1 emits neither, so
# their presence on a Phase-1 envelope means a caller is trying to smuggle Phase-2
# semantics through a Phase-1 door. ADR-0042 AC13: if implementation finds itself
# needing one of these, that is the canon gap biting — stop and escalate.
PHASE_2_FIELDS = frozenset({
    "kind",
    "candidate_claims",
    "chosen_claim_id",
    "successor_claim_id",
    "rejected_alternatives",
    "arbitration",
    "cited_evidence",
    "contradictions_addressed",
    "rationale",
    "policies_in_force",
    "promotion_id",
    "target_policy_id",
    "policy_amendment",
    "policy_rollback",
    "rollback_rule",
    "amendment_authority",
    "issuer",
    "provenance",
    "class",
})


class CanonRefusal(Exception):
    """A write was refused. Carries the ViolationKind so the emitter can record it.

    Raised, never returned — a refusal that a caller can accidentally ignore is a
    warning wearing a costume.
    """

    def __init__(self, violation_kind: str, rationale: str) -> None:
        super().__init__(rationale)
        self.violation_kind = violation_kind
        self.rationale = rationale


@lru_cache(maxsize=None)
def _schema_store() -> dict[str, dict]:
    """Every canon schema, keyed by BOTH filename and absolute `$id`.

    The schemas declare `$id: https://synaplex.ai/discovery-framework/0.1.0/<name>` and
    cross-reference each other with *relative* refs (`common.schema.json#/$defs/...`).
    Under draft 2020-12 the `$id` sets the resolution base, so a relative ref resolves to
    an absolute https URL — and a resolver that does not recognize it will try to fetch it
    over the network. On this host that surfaces as a DNS error; in a sandbox with egress
    it would silently validate against whatever the internet served. Registering both key
    forms keeps resolution entirely local and offline.
    """
    store: dict[str, dict] = {}
    for path in sorted(SCHEMA_ROOT.glob("*.schema.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        store[path.name] = schema
        if "$id" in schema:
            store[schema["$id"]] = schema
    return store


@lru_cache(maxsize=None)
def _validator(object_type: str) -> Draft202012Validator:
    name = {
        "Claim": "claim",
        "Evidence": "evidence",
        "EventLogEntry": "event-log-entry",
    }[object_type]
    store = _schema_store()
    schema = store[f"{name}.schema.json"]
    resolver = RefResolver(
        base_uri=schema.get("$id", ""), referrer=schema, store=store
    )
    return Draft202012Validator(schema, resolver=resolver)


def _walk_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for v in value.values() for s in _walk_strings(v)]
    if isinstance(value, list):
        return [s for v in value for s in _walk_strings(v)]
    return []


def check_phase_1_scope(envelope: dict) -> None:
    """Refuse anything that is not a Phase-1 envelope, or that carries Phase-2 fields."""
    object_type = envelope.get("object_type")
    if object_type not in PHASE_1_TYPES:
        raise CanonRefusal(
            "schema_validation_failure",
            f"object_type={object_type!r} is not authorized in Phase 1. ADR-0042 authorizes "
            f"{', '.join(PHASE_1_TYPES)} only; Decision and Policy are blocked on the canon "
            f"gap (canon v0.1.0 cannot express a frozen, pre-registered, eval-local promotion "
            f"gate). If you need one, stop and escalate — do not construct a Policy.",
        )
    intruders = sorted(PHASE_2_FIELDS & set(envelope))
    if intruders:
        raise CanonRefusal(
            "schema_validation_failure",
            f"{object_type} carries Decision/Policy-only field(s): {', '.join(intruders)}. "
            f"Canon rules 2-6 and 8 govern these and Phase 1 does not check them; passing them "
            f"through unvalidated is how a Phase-2 semantic lands in canon by the back door.",
        )


def check_programme_isolation(envelope: dict) -> None:
    """ADR-0038 write-side laundering refusal.

    Refuses any envelope with `reasoning/programmes/` in *any* field — not just
    `artifact.uri` and `sources[*]`, because an exhaustive field list is a list that
    goes stale.

    **This does NOT cover copied content, and is not advertised as such.** ADR-0038
    §Reference direction says it in terms: *"The grep/path guard can catch path citation
    laundering. It cannot catch copied content."* An artifact containing Programme prose
    verbatim, with no `reasoning/programmes/` path anywhere in it, will hash-pin cleanly
    and pass this check. That hole is real, it is closed by reflection review rather than
    by code, and saying so is the difference between a guard and a reassurance.
    """
    for s in _walk_strings(envelope):
        if PROGRAMME_REL in s or "programmes/" in s:
            raise CanonRefusal(
                "advisory_leak",
                f"envelope references the Programme plane ({s!r}). Programmes have zero "
                f"epistemic authority (ADR-0038); canon may never cite one as source "
                f"authority. Provenance that a Programme led to a Claim belongs in that "
                f"Programme's graduation ledger, not in the envelope.",
            )


def check_role_timestamps(envelope: dict) -> None:
    """Canon validator rule 1: `role_declared_at <= emitted_at`."""
    declared, emitted = envelope.get("role_declared_at"), envelope.get("emitted_at")
    if declared and emitted and declared > emitted:
        raise CanonRefusal(
            "backdated_role_declaration",
            f"role_declared_at ({declared}) > emitted_at ({emitted}) — canon validator "
            f"rule 1. Roles cannot be declared into a window that has already closed.",
        )


def check_artifact_hash(envelope: dict) -> None:
    """Canon validator rule 7: `content_hash` must reproduce from the artifact at `uri`."""
    ptr = envelope.get("artifact")
    if not ptr:
        return
    uri = ptr.get("uri", "")
    if not uri.startswith("file://"):
        return
    rel = uri[len("file://") :]
    path = REPO_ROOT / rel
    if not path.is_file():
        raise CanonRefusal(
            "schema_validation_failure",
            f"ArtifactPointer points at {rel}, which does not exist — canon validator rule 7.",
        )
    actual = hash_file(path)
    if actual != ptr.get("content_hash"):
        raise CanonRefusal(
            "schema_validation_failure",
            f"content_hash does not reproduce for {rel} — canon validator rule 7. "
            f"envelope={ptr.get('content_hash')} actual={actual}. The artifact changed after "
            f"the hash was taken; emit a new envelope, never edit the hash to match.",
        )


def check_schema(envelope: dict) -> None:
    """Validate against the real context-repository schema, not a local copy of it."""
    errors = sorted(_validator(envelope["object_type"]).iter_errors(envelope), key=str)
    if errors:
        detail = "; ".join(f"{list(e.path) or '<root>'}: {e.message}" for e in errors[:5])
        raise CanonRefusal("schema_validation_failure", f"schema validation failed: {detail}")


def validate(envelope: dict) -> None:
    """Run every Phase-1 check. Raises `CanonRefusal` on the first failure.

    Order matters: scope before schema, so an unauthorized `Decision` is refused with
    the reason that actually explains it ("Phase 2 is blocked on a canon gap") rather
    than a schema error about a missing `policies_in_force`.
    """
    check_phase_1_scope(envelope)
    check_programme_isolation(envelope)
    check_role_timestamps(envelope)
    check_artifact_hash(envelope)
    check_schema(envelope)

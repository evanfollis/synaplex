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

from . import rules
from .ids import hash_file
from .rules import CanonRefusal
from .store import EMITTABLE_TYPES, REPO_ROOT
from .view import CanonView

SCHEMA_ROOT = Path(
    os.environ.get(
        "SYNAPLEX_CANON_SCHEMAS",
        "/opt/workspace/projects/context-repository/spec/discovery-framework/schemas",
    )
)

PROGRAMME_REL = "reasoning/programmes"

# The digest of the canon schema set this emitter was written and reviewed against.
#
# WHY THIS EXISTS: on 2026-07-12 the canon spec changed from 0.1.0 to 0.2.0 *in place*,
# and nothing in the system noticed — because `spec/` was in context-repository's
# `.gitignore` and the L1 canon, the contract every envelope in three repos binds itself
# to, had never been under version control. This tripwire is what caught it. It is now
# fixed at the source (`context-repository@d93d4e5` tracks `spec/`), so git is the real
# guard; this pin stays as consumer-side defense-in-depth, which is what caught it once.
#
# Canon demands every artifact be hash-bound and immutable. That discipline had never been
# applied to canon itself.
#
# A drift here is NOT automatically a fault — context-repository owns canon and may
# legitimately bump it. It means *a bump happened and nobody told us*. Re-read the schemas,
# re-validate every live envelope, then repin deliberately. Repinning to make the test
# green without reading is how the next silent change gets laundered through.
#
# Pinned 2026-07-12 against `context-repository@42907eb` — canon v0.2.0 *after* adversarial
# review closed two blocking defects (evidence laundering; constitutional land-grab). The
# earlier pin `bcc6d01315fed7f9` was the pre-review 0.2.0 and is not safe to build on.
EXPECTED_SCHEMA_DIGEST = "eac15d4c32d90f86"


def schema_digest() -> str:
    """Stable digest over the canon schema set: sorted (filename, sha256) pairs."""
    h = hashlib.sha256()
    for path in sorted(SCHEMA_ROOT.glob("*.schema.json")):
        h.update(path.name.encode("utf-8"))
        h.update(hashlib.sha256(path.read_bytes()).hexdigest().encode("utf-8"))
    return h.hexdigest()[:16]

# Fields that belong only to Decision or Policy envelopes. Legal there (Phase 2 is now
# authorized — canon v0.2.0 resolved the gap with the `frozen` class); still refused on a
# Claim, Evidence, or EventLogEntry at ANY depth. Adversarial review nested
# `chosen_claim_id` inside `methodology_log` — a subtree the canon schema does not close
# with `additionalProperties: false` — and got it past the first version of this check.
DECISION_POLICY_FIELDS = frozenset({
    "kind",
    "candidate_claims",
    "chosen_claim_id",
    "successor_claim_id",
    "rejected_alternatives",
    "arbitration",
    "cited_evidence",
    "contradictions_addressed",
    # NOT `rationale`: the event-log-entry schema legitimately defines
    # `canon_violation.rationale`, so forbidding it here made our own refusal records fail
    # validation. Caught by `check_canon_integrity` on the first store sweep — which is the
    # hazard of a hand-curated forbidden list, and the reason this one stays short and every
    # entry is checked against the schemas rather than assumed.
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
        "Decision": "decision",
        "EventLogEntry": "event-log-entry",
        "Policy": "policy",
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


def _walk_keys(value: Any) -> list[str]:
    """Every dict key at every depth.

    Top-level-only key checks are why adversarial review got `chosen_claim_id` past this
    validator by nesting it inside `methodology_log` — a subtree the canon schema does not
    close with `additionalProperties: false`. Depth is not a hiding place.
    """
    if isinstance(value, dict):
        return list(value) + [k for v in value.values() for k in _walk_keys(v)]
    if isinstance(value, list):
        return [k for v in value for k in _walk_keys(v)]
    return []


def _walk_artifact_pointers(value: Any) -> list[dict]:
    """Every ArtifactPointer at every depth — anything carrying `uri` + `content_hash`.

    The top-level `artifact` key is not the only pointer in an envelope.
    `EventLogEntry(methodology_log).artifact` is *required* by the schema and is the
    pointer used at probe entry; a top-level-only rule 7 check left it unverified, so a
    methodology_log could hash-bind a file that did not exist. Found by adversarial review,
    which is exactly what it is for.
    """
    found: list[dict] = []
    if isinstance(value, dict):
        if "uri" in value and "content_hash" in value:
            found.append(value)
        for v in value.values():
            found.extend(_walk_artifact_pointers(v))
    elif isinstance(value, list):
        for v in value:
            found.extend(_walk_artifact_pointers(v))
    return found


def check_object_scope(envelope: dict) -> None:
    """Refuse unknown envelope types, and Decision/Policy semantics smuggled into others.

    Checks keys at **every depth** — nesting is not an exemption.
    """
    object_type = envelope.get("object_type")
    if object_type not in EMITTABLE_TYPES:
        raise CanonRefusal(
            "schema_validation_failure",
            f"object_type={object_type!r} is not emittable. This emitter writes "
            f"{', '.join(EMITTABLE_TYPES)}; Promotion and Realization have no lab consumer.",
        )
    if object_type in {"Decision", "Policy"}:
        return  # these fields are theirs; the schema and rules.py govern them
    intruders = sorted(DECISION_POLICY_FIELDS.intersection(_walk_keys(envelope)))
    if intruders:
        raise CanonRefusal(
            "schema_validation_failure",
            f"{object_type} carries Decision/Policy-only field(s) at some depth: "
            f"{', '.join(intruders)}. Passing them through unvalidated is how a Decision "
            f"semantic lands in canon by the back door. Nesting is not an exemption.",
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

    Matching is **case-insensitive and separator-normalized**. Adversarial review walked
    straight past the first version of this check with `Reasoning/Programmes/secret.md` —
    a case-sensitive substring test is not a guard, it is a speed bump.
    """
    for s in _walk_strings(envelope):
        probe = s.lower().replace("\\", "/")
        if PROGRAMME_REL in probe or "programmes/" in probe:
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
    """Canon validator rule 7, applied to EVERY ArtifactPointer in the envelope.

    Not just the top-level `artifact` key —
    `EventLogEntry(methodology_log).artifact` is nested, required, and is the pointer
    written at probe entry.
    """
    for ptr in _walk_artifact_pointers(envelope):
        uri = ptr.get("uri", "")
        if not uri.startswith("file://"):
            continue
        rel = uri[len("file://") :]
        path = REPO_ROOT / rel
        # `resolve()` collapses `..` and follows symlinks, so a pointer cannot escape the
        # repo and hash-bind something outside it.
        resolved = path.resolve()
        if not str(resolved).startswith(str(REPO_ROOT.resolve())):
            raise CanonRefusal(
                "schema_validation_failure",
                f"ArtifactPointer {uri!r} resolves to {resolved}, outside the repo. An "
                f"envelope may only hash-bind an artifact this repo can replay.",
            )
        if not resolved.is_file():
            raise CanonRefusal(
                "schema_validation_failure",
                f"ArtifactPointer points at {rel}, which does not exist — canon validator rule 7.",
            )
        actual = hash_file(resolved)
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


def validate(envelope: dict, view: "CanonView | None" = None) -> None:
    """Run every canon check. Raises `CanonRefusal` on the first failure.

    Single-envelope rules run first (1, 7, scope, schema), then the cross-envelope rules
    (2-5, 9-17) which need a `CanonView` — the world as it would be *after* this write.

    `view=None` runs only the single-envelope checks. That is correct for a caller who has
    a bare document and no store, and wrong for an emission — so `emit._emit` always passes
    a `StoreView`.
    """
    check_object_scope(envelope)
    check_programme_isolation(envelope)
    check_role_timestamps(envelope)
    check_artifact_hash(envelope)
    check_schema(envelope)
    if view is not None:
        rules.check_all(envelope, view)

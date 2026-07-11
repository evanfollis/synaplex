"""Canon id + artifact-hash contract for the synaplex lab canon store.

There is exactly one id contract for `lab/.canon/`, and this module is it.

    Claim.id = sha256(statement.lower()).hexdigest()[:16]

Reverse-engineered from the single pre-existing envelope
(`claims/b7ff216f4eec6e58.json`, hand-authored 2026-04-19) and pinned by
`test_campaign.py::test_id_contract_matches_preexisting_claim`. Until this
module shipped, the store had one record and no code path that wrote to it;
`emit.py` is the first programmatic writer. Workspace rule S1-P3 ("two write
paths to the same store require explicit reconciliation") is satisfied by
routing every writer through `claim_id()` and asserting the pre-existing
envelope still conforms.

Known property of the contract: it lowercases before hashing, so two Claims
whose statements differ only in case collide. That is inherited, not chosen.
`emit.py` refuses to overwrite a colliding id, so a collision surfaces as a
loud error rather than a silent clobber.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

ID_LENGTH = 16


def claim_id(statement: str) -> str:
    """Derive a Claim id from its falsifiable statement.

    The id binds the *scientific content*, not the author metadata — which is
    why the rebrand (emitter `L3:agentstack` -> `L3:synaplex`) preserved
    `b7ff216f4eec6e58`.
    """
    return hashlib.sha256(statement.lower().encode("utf-8")).hexdigest()[:ID_LENGTH]


def derived_id(*parts: str) -> str:
    """Derive an id for a non-Claim envelope (Evidence, Decision, EventLogEntry).

    Claims hash their statement because the statement *is* the identity. The
    other envelope types have no such natural key, so they hash the tuple of
    fields that makes the emission unique (e.g. claim_id + artifact hash +
    emitted_at). Callers pass those parts explicitly so the derivation is
    visible at the call site rather than buried here.
    """
    joined = "\x1f".join(parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:ID_LENGTH]


def hash_file(path: Path | str) -> str:
    """`sha256:<hex>` over a file's bytes — the ArtifactPointer.content_hash form.

    Canon validator rule 7: content_hash must be reproducible from the
    artifact at `uri` + `version`. Stale hash = validation failure.
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"

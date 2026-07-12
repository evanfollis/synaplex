"""The id contract for `lab/.canon/`. One module, one contract (ADR-0042 §The id contract).

    Claim.id = sha256(statement.lower()).hexdigest()[:16]

Recovered from the single hand-authored envelope (`claims/b7ff216f4eec6e58.json`,
2026-04-19) by trying candidate derivations against it — it was written down
nowhere. `test_canon.py::test_id_contract_reproduces_the_preexisting_claim` pins it.
That test is the S1-P3 obligation discharged: the first programmatic writer to a
store must reconcile with what is already there, or the two write paths silently
disagree and every cross-path join corrupts.

## Two properties to hold, both verified

**Atlas agrees.** Atlas's `claim_hash()` — `sha256(claim_canonical(statement))[:16]`,
where `claim_canonical` strips, lowercases, collapses whitespace, and strips trailing
punctuation — returns `b7ff216f4eec6e58` on this statement. Same hash family, same
truncation, same lowercase; atlas's is a strict refinement in normalization, not a
different contract. We do **not** vendor atlas's helper: copying a repo-local utility
across a repo boundary with no shared test surface creates a second copy of a contract
that can drift silently, which is the exact class S1-P3 names. L2 `discovery-runtime`
extraction stays deferred per ADR-0029.

**Evidence and EventLogEntry ids genuinely diverge from atlas**, which uses
domain-native ids and 12-char evidence ids against 16-char claim ids. Nobody may later
write a cross-instance join assuming a shared scheme. This is recorded, not fixed.

## The collision hazard, and why we keep it

The contract lowercases before hashing, so two Claims whose statements differ only in
case collide. This is inherited from the one existing envelope, not chosen. It is made
safe by **refusing to write on collision** (see `emit.py`), not by changing the hash: a
refusal is recoverable, a silently overwritten pre-registration is not.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

ID_LENGTH = 16


def claim_id(statement: str) -> str:
    """Derive a Claim id from its falsifiable statement.

    The id binds the *scientific content*, not the author metadata — which is why the
    agentstack → synaplex rebrand preserved `b7ff216f4eec6e58` while changing `emitter`.
    """
    return hashlib.sha256(statement.lower().encode("utf-8")).hexdigest()[:ID_LENGTH]


def derived_id(*parts: str) -> str:
    """Id for a non-Claim envelope.

    A Claim's statement *is* its identity, so it hashes that. Evidence and
    EventLogEntry have no such natural key, so they hash the tuple of fields that makes
    the emission unique. Callers pass those parts explicitly, so the derivation is
    visible at the call site rather than buried here.

    `\\x1f` (unit separator) joins the parts: it cannot occur in a hash, uri, or
    ISO-8601 timestamp, so `derived_id("ab", "cd") != derived_id("abc", "d")`.
    """
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:ID_LENGTH]


def hash_file(path: Path | str) -> str:
    """`sha256:<hex>` over a file's bytes — the `ArtifactPointer.content_hash` form.

    Canon validator rule 7: content_hash must be reproducible from the artifact at
    `uri` + `version`. A stale hash is a validation failure, not a warning.
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"

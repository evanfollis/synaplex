"""Verifiable assertions for the Phase-1 canon emission path (ADR-0042 acceptance criteria).

Run from the repo root:

    PYTHONPATH=. .venv/bin/python lab/canon/test_canon.py

Exit 0 = every assertion holds.

Every emission test runs against a **relocated store** (`SYNAPLEX_CANON_ROOT` → tmpdir).
The real `lab/.canon/` is read but never written: an emitter's test suite that writes into
the append-only store it is testing would corrupt the thing it is meant to protect, and
canon has no undo.

These test invariants and failure behavior, not happy paths. An emitter that emits is
uninteresting; an emitter that *refuses correctly* is the entire product.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PRIMARY = "b7ff216f4eec6e58"
METHODOLOGY = "lab/evals/memory-systems-v1/methodology.md"
PREREGISTERED_HASH = "sha256:45916c9fc006d87b86eb09437cffdee0ff552184bd660c1ebf92e7a942b4900b"

RESULTS: list[str] = []


def _ok(msg: str) -> None:
    RESULTS.append(msg)
    print(f"  ok   {msg}")


class relocated_store:
    """Point the canon store at a scratch directory for the duration of a test."""

    def __enter__(self) -> Path:
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["SYNAPLEX_CANON_ROOT"] = self._tmp.name
        return Path(self._tmp.name)

    def __exit__(self, *exc) -> None:
        os.environ.pop("SYNAPLEX_CANON_ROOT", None)
        self._tmp.cleanup()


def _violations(root: Path) -> list[dict]:
    d = root / "events"
    if not d.is_dir():
        return []
    out = []
    for p in d.glob("*.json"):
        env = json.loads(p.read_text())
        if env.get("event_kind") == "canon_violation":
            out.append(env)
    return out


def _claim_kwargs(statement: str) -> dict:
    return {
        "statement": statement,
        "falsification_criteria": ["If X, this claim is falsified."],
        "thresholds": {"recall_at_1": 0.80},
    }


# --- AC1: the id contract -------------------------------------------------


def test_id_contract_reproduces_the_preexisting_claim() -> None:
    """S1-P3: the first programmatic writer must reconcile with the hand-authored store."""
    from lab.canon.ids import claim_id

    envelope = json.loads((REPO / "lab/.canon/claims" / f"{PRIMARY}.json").read_text())
    derived = claim_id(envelope["statement"])
    assert derived == PRIMARY, (
        f"id contract drift: claim_id(statement)={derived}, envelope on disk={PRIMARY}. "
        f"The emitter and the existing store now disagree; every cross-path join is corrupt."
    )
    _ok("AC1  id contract reproduces b7ff216f4eec6e58")


def test_preregistration_artifact_still_hashes() -> None:
    """Canon rule 7 on the one envelope that already exists. If this breaks, someone
    edited a hash-bound methodology in place and the Claim no longer means what it said."""
    from lab.canon.ids import hash_file

    assert hash_file(REPO / METHODOLOGY) == PREREGISTERED_HASH
    _ok("AC1  methodology.md still hashes to its pre-registration value")


def test_canon_schema_set_has_not_drifted() -> None:
    """The tripwire on an unversioned truth source.

    `spec/` is gitignored in context-repository, so the L1 canon — the contract every
    envelope in three repos binds itself to — is not under version control. It cannot be
    diffed, attributed, or reverted. On 2026-07-12 it went 0.1.0 -> 0.2.0 in place with no
    CHANGELOG entry, and nothing noticed. This assertion is what notices.

    A failure here is NOT automatically a fault: context-repository owns canon and may
    bump it. It means *a bump happened and nobody told anyone*. Re-read the schemas,
    confirm the change is intended and backward-compatible against every existing
    envelope, then update EXPECTED_SCHEMA_DIGEST. Do not just repin to make it green —
    repinning without reading is how the next silent change gets laundered through.
    """
    from lab.canon.validate import EXPECTED_SCHEMA_DIGEST, schema_digest

    live = schema_digest()
    assert live == EXPECTED_SCHEMA_DIGEST, (
        f"CANON SCHEMA DRIFT.\n"
        f"       pinned: {EXPECTED_SCHEMA_DIGEST}\n"
        f"       on disk: {live}\n"
        f"       The canon schemas changed since this emitter was reviewed. They are\n"
        f"       gitignored, so `git diff` will not show you what changed. Read them,\n"
        f"       re-validate every existing envelope, then repin deliberately."
    )
    _ok("PIN  canon schema set matches the digest this emitter was reviewed against")


# --- AC2: validation refuses -----------------------------------------------


def test_refuses_unemittable_object_types() -> None:
    """Decision and Policy are authorized now (canon v0.2.0 `frozen` class resolved the gap).
    Promotion and Realization are not — the lab has no consumer for them, and an emitter for
    an envelope nobody emits is speculative infrastructure."""
    from lab.canon.validate import CanonRefusal, validate

    for object_type in ("Promotion", "Realization", "NotAThing"):
        try:
            validate({"object_type": object_type, "id": "x"})
        except CanonRefusal as r:
            assert "not emittable" in r.rationale
        else:
            raise AssertionError(f"validator accepted a {object_type} envelope")
    _ok("SCOPE Promotion/Realization/unknown types are refused; Decision+Policy are not")


def test_observed_at_cannot_be_defaulted() -> None:
    """The single most load-bearing parameter in the emitter has no default, on purpose.

    Canon rule 10 anchors the frozen-gate pre-registration window on `Evidence.observed_at`,
    because `emitted_at` is entirely under the emitter's control. A default — any default,
    but especially `now()` — would let a caller destroy the anchor by omission and silently
    reopen the evidence-laundering attack that adversarial review found in canon v0.2.0's
    first draft. Making it required means the lie has to be typed out deliberately.
    """
    import inspect

    from lab.canon.emit import emit_evidence

    param = inspect.signature(emit_evidence).parameters["observed_at"]
    assert param.default is inspect.Parameter.empty, (
        "emit_evidence.observed_at has acquired a default. If that default is now(), the "
        "frozen-gate window anchor is destroyed and the re-emission attack is open again."
    )
    doc = emit_evidence.__doc__ or ""
    assert "never from the clock" in doc
    _ok("R16  emit_evidence.observed_at is required — it comes from the run, not the clock")


def test_refuses_phase2_fields_on_a_phase1_envelope() -> None:
    """Canon rules 2-6 and 8 govern fields Phase 1 does not check. Passing them through
    unvalidated is how a Phase-2 semantic lands in canon by the back door."""
    from lab.canon.validate import CanonRefusal, validate

    try:
        validate({"object_type": "Claim", "id": "x", "policies_in_force": [{"policy_id": "p"}]})
    except CanonRefusal as r:
        assert "policies_in_force" in r.rationale
        assert r.violation_kind == "schema_validation_failure"
    else:
        raise AssertionError("validator passed a Claim carrying policies_in_force")
    _ok("AC2  Decision/Policy-only fields on a Phase-1 envelope are refused")


def test_refuses_backdated_role_declaration() -> None:
    """Canon rule 1 — the retrospective-relabel defense."""
    from lab.canon.validate import CanonRefusal, check_role_timestamps

    try:
        check_role_timestamps(
            {"role_declared_at": "2026-07-12T10:00:00Z", "emitted_at": "2026-07-12T09:00:00Z"}
        )
    except CanonRefusal as r:
        assert r.violation_kind == "backdated_role_declaration"
    else:
        raise AssertionError("validator accepted role_declared_at > emitted_at")
    _ok("AC2  role_declared_at > emitted_at is refused (canon rule 1)")


def test_refuses_stale_artifact_hash() -> None:
    """Canon rule 7. The emitter computes hashes and never accepts one, so this fires only
    when an artifact changes underneath an already-built pointer."""
    from lab.canon.validate import CanonRefusal, check_artifact_hash

    try:
        check_artifact_hash({
            "artifact": {"uri": f"file://{METHODOLOGY}", "content_hash": "sha256:deadbeef"}
        })
    except CanonRefusal as r:
        assert "rule 7" in r.rationale
    else:
        raise AssertionError("validator accepted a stale content_hash")
    _ok("AC2  a content_hash that does not reproduce is refused (canon rule 7)")


# --- adversarial review findings (Codex, 2026-07-12) — regressions ---------


def test_nested_artifact_pointer_is_hash_checked() -> None:
    """REVIEW FINDING 1. Canon rule 7 was enforced only on the top-level `artifact` key.

    `EventLogEntry(methodology_log).artifact` is nested, *required* by the schema, and is
    the pointer written at probe entry — the single most important artifact binding Phase 1
    makes. Codex got this envelope past the validator with `content_hash: sha256:deadbeef`
    pointing at a file that does not exist.
    """
    from lab.canon.emit import _base, _now
    from lab.canon.validate import CanonRefusal, validate

    envelope = _base("EventLogEntry", "x", _now())
    envelope.update(
        event_kind="methodology_log",
        subject_id="c",
        methodology_log={
            "artifact": {
                "uri": "file://does/not/exist",
                "content_hash": "sha256:deadbeef",
                "version": "1",
                "media_type": "text/markdown",
            }
        },
    )
    try:
        validate(envelope)
    except CanonRefusal as r:
        assert "does not exist" in r.rationale
    else:
        raise AssertionError(
            "a nested methodology_log.artifact with a bogus hash validated clean — "
            "canon rule 7 is defeated on the exact envelope probe entry depends on"
        )
    _ok("REV1 nested ArtifactPointers are hash-checked (canon rule 7 at every depth)")


def test_nested_phase2_field_is_refused() -> None:
    """REVIEW FINDING 2. The Phase-2 field check scanned only top-level keys.

    Codex nested `chosen_claim_id` inside `methodology_log` — a subtree the canon schema
    does not close with `additionalProperties: false` — and it validated clean.
    """
    from lab.canon.emit import _base, _now
    from lab.canon.validate import CanonRefusal, validate

    envelope = _base("EventLogEntry", "x", _now())
    envelope.update(
        event_kind="methodology_log",
        subject_id="c",
        methodology_log={
            "artifact": {
                "uri": f"file://{METHODOLOGY}",
                "content_hash": PREREGISTERED_HASH,
                "version": "1",
                "media_type": "text/markdown",
            },
            "chosen_claim_id": "smuggled",
        },
    )
    try:
        validate(envelope)
    except CanonRefusal as r:
        assert "chosen_claim_id" in r.rationale and "Nesting is not an exemption" in r.rationale
    else:
        raise AssertionError("a Decision field nested inside methodology_log validated clean")
    _ok("REV2 Decision/Policy fields are refused at any depth, not just top level")


def test_programme_path_refusal_is_case_insensitive() -> None:
    """REVIEW FINDING 3. The refusal was a case-sensitive substring test.

    `Reasoning/Programmes/secret.md` walked straight past it. A case-sensitive guard on a
    case-insensitive-ish filesystem is a speed bump, not a guard.
    """
    from lab.canon.validate import CanonRefusal, check_programme_isolation

    for path in (
        "Reasoning/Programmes/secret.md",
        "REASONING/PROGRAMMES/secret.md",
        "reasoning\\programmes\\secret.md",
    ):
        try:
            check_programme_isolation({"statement": f"see {path}"})
        except CanonRefusal as r:
            assert r.violation_kind == "advisory_leak"
        else:
            raise AssertionError(f"Programme path bypassed the refusal via {path!r}")
    _ok("REV3 Programme-path refusal is case- and separator-insensitive")


def test_artifact_pointer_cannot_escape_the_repo() -> None:
    """Hardening prompted by review: a pointer must not hash-bind a file outside the repo,
    or canon binds itself to something it cannot replay."""
    from lab.canon.emit import _base, _now
    from lab.canon.validate import CanonRefusal, validate

    envelope = _base("Claim", "x", _now())
    envelope.update(
        statement="s",
        falsification_criteria=["f"],
        exposure={
            "capital_at_risk": 0,
            "reversibility": "reversible",
            "correlation_tags": [],
            "time_to_realization": "P1D",
            "blast_radius": "local",
        },
        artifact={
            "uri": "file://../../../etc/hostname",
            "content_hash": "sha256:x",
            "version": "1",
            "media_type": "text/plain",
        },
    )
    try:
        validate(envelope)
    except CanonRefusal as r:
        assert "outside the repo" in r.rationale
    else:
        raise AssertionError("an ArtifactPointer escaped the repo via ../")
    _ok("REV4 an ArtifactPointer cannot traverse outside the repo")


# --- AC3/AC4: append-only and collisions -----------------------------------


def test_append_only_leaves_the_envelope_byte_unmodified() -> None:
    """AC3. The bytes on disk must survive a refused overwrite exactly."""
    from lab.canon.emit import emit_claim
    from lab.canon.validate import CanonRefusal

    with relocated_store() as root:
        cid, path = emit_claim(**_claim_kwargs("A statement about memory systems."))
        before = path.read_bytes()
        try:
            emit_claim(**_claim_kwargs("A statement about memory systems."))
        except CanonRefusal as r:
            assert "append-only" in r.rationale
        else:
            raise AssertionError("emitter overwrote an existing Claim")
        assert path.read_bytes() == before, "the envelope on disk was mutated despite the refusal"
        assert _violations(root), "a refused write emitted no canon_violation record"
    _ok("AC3  overwrite raises and leaves the envelope byte-unmodified")


def test_case_only_collision_is_refused_loudly() -> None:
    """AC4. The id contract lowercases before hashing, so these two statements collide.
    A refusal is recoverable; a silently overwritten pre-registration is not."""
    from lab.canon.emit import emit_claim
    from lab.canon.validate import CanonRefusal

    with relocated_store():
        emit_claim(**_claim_kwargs("Memory systems do not reach 0.80 recall."))
        try:
            emit_claim(**_claim_kwargs("MEMORY SYSTEMS DO NOT REACH 0.80 RECALL."))
        except CanonRefusal as r:
            assert "case" in r.rationale.lower()
        else:
            raise AssertionError("two statements differing only in case did not collide loudly")
    _ok("AC4  case-only id collision is refused, never overwritten")


# --- AC5: the ADR-0038 write-side guard ------------------------------------


def test_refuses_any_programme_reference() -> None:
    """AC5. Write-side laundering refusal — makes the violation impossible rather than
    detectable-after-the-fact, which is all the scan-time guard can do."""
    from lab.canon.validate import CanonRefusal, check_programme_isolation

    for envelope in (
        {"artifact": {"uri": "file://reasoning/programmes/harness.md"}},
        {"sources": [{"id": "reasoning/programmes/harness.md"}]},
        {"statement": "see reasoning/programmes/harness.md for the frame"},
    ):
        try:
            check_programme_isolation(envelope)
        except CanonRefusal as r:
            assert r.violation_kind == "advisory_leak"
        else:
            raise AssertionError(f"validator accepted a Programme reference: {envelope}")
    _ok("AC5  a Programme reference in ANY field is refused (advisory_leak)")


def test_programme_guard_docstring_admits_its_limit() -> None:
    """AC5 requires the docstring to state plainly that it does not cover copied content.
    An undocumented hole is the difference between a guard and a reassurance."""
    from lab.canon.validate import check_programme_isolation

    doc = check_programme_isolation.__doc__ or ""
    assert "copied content" in doc and "NOT" in doc
    _ok("AC5  the guard's docstring admits it cannot catch copied content")


# --- AC6: refusals are recorded --------------------------------------------


def test_every_refused_write_records_a_canon_violation() -> None:
    """AC6. A store that silently declines to write is indistinguishable from one that
    was never called."""
    from lab.canon.emit import emit_claim
    from lab.canon.validate import CanonRefusal

    with relocated_store() as root:
        try:
            emit_claim(statement="", falsification_criteria=[])  # empty: schema violation
        except CanonRefusal:
            pass
        violations = _violations(root)
        assert violations, "a schema-refused write emitted no canon_violation"
        v = violations[0]["canon_violation"]
        assert v["violation_kind"] == "schema_validation_failure"
        assert v["offending_emission"]["object_type"] == "Claim"
        assert v["rationale"]
    _ok("AC6  refused writes emit EventLogEntry(canon_violation) with a ViolationKind")


# --- AC8: canonical equality, not bytes ------------------------------------


def test_identity_is_canonical_json_not_bytes() -> None:
    """AC8. The Claim's thresholds carry the lexeme `0.80`, which round-trips to `0.8`
    through any normal serializer. A byte-identity test would be born broken."""
    from lab.canon.serialize import equal

    assert equal({"t": 0.80}, {"t": 0.8}), "0.80 and 0.8 must compare equal"
    assert equal({"a": 1, "b": 2}, {"b": 2, "a": 1}), "key order must not affect identity"
    assert not equal({"t": 0.80}, {"t": 0.81})
    raw = json.loads((REPO / "lab/.canon/claims" / f"{PRIMARY}.json").read_text())
    assert equal(raw, json.loads(json.dumps(raw))), "the real envelope must survive a round-trip"
    _ok("AC8  identity is canonical-JSON equality; 0.80 == 0.8 round-trips clean")


# --- AC7: the anti-kernel check --------------------------------------------


def test_no_selection_check_catches_a_kernel() -> None:
    """AC7. Prove the tripwire fires — a check that has never caught anything is a check
    nobody has tested."""
    from lab.canon.guard import check_no_selection

    with tempfile.TemporaryDirectory() as td:
        fake = Path(td)
        (fake / "lab").mkdir()
        (fake / "lab" / "kernel.py").write_text("def next_action(c):\n    return 'falsify'\n")
        found = check_no_selection(fake)
        assert found, "the no-selection check missed a next_action() selection kernel"
        assert "next_action" in found[0].detail
    _ok("AC7  the no-selection check catches a rebuilt selection kernel")


def test_repo_has_no_selection_kernel() -> None:
    """AC7 + AC12 against the live repo."""
    from lab.canon.guard import check_no_selection

    found = check_no_selection()
    assert not found, "selection machinery found:\n  " + "\n  ".join(f.render() for f in found)
    assert not (REPO / "lab" / "campaign").exists(), "lab/campaign/ was revived"
    _ok("AC7/12 the repo contains no selection kernel and no lab/campaign/")


# --- AC9: the Layer 4 publication guard ------------------------------------


def test_publication_guard_is_fail_closed() -> None:
    """AC9. An undeclared page is refused by default. A new page written by someone who
    never read the guard must not publish itself."""
    from lab.canon.guard import check_publication

    with tempfile.TemporaryDirectory() as td:
        fake = Path(td)
        lab_pages = fake / "site" / "src" / "pages" / "lab"
        lab_pages.mkdir(parents=True)
        (lab_pages / "undeclared.astro").write_text("<h1>Results: Letta scores 0.62</h1>")
        found = check_publication(fake)
        assert found and "fail-closed" in found[0].detail.lower()
    _ok("AC9  an undeclared reader-facing page is refused (fail-closed)")


def test_publication_guard_blocks_results_without_a_decision() -> None:
    """AC9. Phase 2 is blocked, so no Decision can exist, so no results page can ship.
    Intended behavior, not a limitation."""
    from lab.canon.guard import check_publication

    with tempfile.TemporaryDirectory() as td, relocated_store():
        fake = Path(td)
        lab_pages = fake / "site" / "src" / "pages" / "lab"
        lab_pages.mkdir(parents=True)
        (lab_pages / "results.astro").write_text(
            f"// canon:publishes-results = true\n<p>{PRIMARY} scored 0.62</p>"
        )
        found = check_publication(fake)
        assert found, "a results page shipped with no Decision behind it"
        assert "no Decision exists" in found[0].detail
    _ok("AC9  a results page with no Decision behind it is blocked")


def test_preregistration_page_may_publish_without_results() -> None:
    """AC9. The permitted case — otherwise the guard would forbid the pre-registration
    page that correctly exists today."""
    from lab.canon.guard import check_publication

    with tempfile.TemporaryDirectory() as td, relocated_store():
        fake = Path(td)
        lab_pages = fake / "site" / "src" / "pages" / "lab"
        lab_pages.mkdir(parents=True)
        (lab_pages / "prereg.astro").write_text(
            f"// canon:publishes-results = false\n<p>Pre-registration for {PRIMARY}.</p>"
        )
        assert not check_publication(fake)
    _ok("AC9  a pre-registration page publishing no results is permitted")


def test_declaring_no_results_while_citing_evidence_is_refused() -> None:
    """AC9. The cheap sound half of the content check: citing Evidence IS publishing a
    result, whatever the page declares about itself."""
    from lab.canon.emit import artifact_pointer, emit_evidence
    from lab.canon.guard import check_publication

    with tempfile.TemporaryDirectory() as td, relocated_store():
        eid, _ = emit_evidence(
            claim=PRIMARY,
            evidence_type="benchmark_run",
            tier="internal_operational",
            polarity="supports",
            artifact=artifact_pointer(METHODOLOGY),
            observed_at="2026-07-12T09:00:00Z",
        )
        fake = Path(td)
        lab_pages = fake / "site" / "src" / "pages" / "lab"
        lab_pages.mkdir(parents=True)
        (lab_pages / "sneaky.astro").write_text(
            f"// canon:publishes-results = false\n<p>See evidence {eid}.</p>"
        )
        found = check_publication(fake)
        assert found and "Citing evidence is publishing a result" in found[0].detail
    _ok("AC9  a page declaring no-results while citing Evidence is refused")


def test_build_gate_refuses_an_unbacked_results_page() -> None:
    """The guard is wired into `npm run build` as a prebuild step, so a page publishing a
    result with no Decision behind it cannot compile — not merely gets flagged by a nightly
    cron the next morning, by which time it has shipped.

    Verified live 2026-07-12: adding a page declaring `publishes-results = true` and citing
    the Claim made `npm run build` exit 1 with the guard's refusal. A build gate nobody has
    watched refuse a build is a build gate nobody has tested.
    """
    import json

    from lab.canon.guard import check_publication

    pkg = json.loads((REPO / "site" / "package.json").read_text())
    prebuild = pkg["scripts"].get("prebuild", "")
    assert "lab.canon.guard" in prebuild, (
        "the canon guard is no longer wired into the site build. Publication became "
        "fail-open the moment that line was removed."
    )

    with tempfile.TemporaryDirectory() as td, relocated_store():
        fake = Path(td)
        pages = fake / "site" / "src" / "pages" / "lab"
        pages.mkdir(parents=True)
        (pages / "results.astro").write_text(
            f"// canon:publishes-results = true\n<p>Letta scores 0.62 on {PRIMARY}</p>"
        )
        assert check_publication(fake), "the build gate would have let a result through"
    _ok("BUILD npm run build refuses a results page with no Decision behind it")


def test_live_site_passes_the_publication_guard() -> None:
    """AC9/AC10 against the real site."""
    from lab.canon.guard import check_publication

    found = check_publication()
    assert not found, "live site violates the publication guard:\n  " + "\n  ".join(
        f.render() for f in found
    )
    _ok("AC9  the live site passes the publication guard")


# --- probe entry: the thing Phase 1 exists to enable -----------------------


def test_probe_entry_emits_cleanly() -> None:
    """The whole point of Phase 1: canon.md §Phase invariants requires a phase_transition
    plus a methodology_log on probe entry, and nothing could write them."""
    from lab.canon.emit import artifact_pointer, emit_methodology_log, emit_phase_transition

    with relocated_store() as root:
        pt_id, _ = emit_phase_transition(claim=PRIMARY, from_phase="draft", to_phase="probe")
        ml_id, _ = emit_methodology_log(
            claim=PRIMARY,
            artifact=artifact_pointer(METHODOLOGY),
            summary="probe entry for memory-systems-v1",
        )
        assert pt_id and ml_id
        events = [json.loads(p.read_text()) for p in (root / "events").glob("*.json")]
        kinds = {e["event_kind"] for e in events}
        assert kinds == {"phase_transition", "methodology_log"}, kinds
        assert not _violations(root), "probe entry produced a canon violation"
    _ok("PH1  probe entry (phase_transition + methodology_log) emits cleanly")


def test_the_real_store_matches_what_we_deliberately_emitted() -> None:
    """The suite must not have written into the real store, and the real store must hold
    exactly what was emitted on purpose.

    As of 2026-07-12 that is: two withdrawn vendor-route Claims, the prospective
    artifact-coherence transfer Claim, their frozen gates, and one
    EventLogEntry(canon_violation) — a real refusal, recorded when the first frozen-gate
    emission was rejected for carrying `instance_id`, which the Policy schema forbids. That
    record stays. Canon is append-only, and deleting an inconvenient record because it came
    from our own bug is precisely the behaviour this whole apparatus exists to forbid.

    **Evidence must stay at 0 until a real run produces some.** The moment the first
    Evidence lands, the frozen gate's pre-registration window closes forever — which is the
    point, and is why the gate was emitted before the runner exists rather than after.
    """
    from lab.canon import store

    counts = store.counts()
    assert counts["Claim"] == 3, (
        f"expected 3 Claims — two withdrawn vendor-route Claims and one prospective "
        f"artifact-coherence transfer Claim — "
        f"found {counts['Claim']}"
    )
    assert counts["Policy"] == 3, "each Claim carries exactly one frozen promotion gate"
    assert counts["Decision"] == 2, (
        "expected 2 Decision(kill) envelopes — the vendor-comparison route was WITHDRAWN, "
        "not measured (principal, 2026-07-12)"
    )
    assert counts["Evidence"] == 0, (
        "EVIDENCE EXISTS, and it should not. The vendor route was retired without ever "
        "running: both Claims were disposed by Decision(kill) citing zero Evidence, because "
        "nothing was ever measured. Evidence in this store would mean something emitted a "
        "result for an evaluation that was withdrawn."
    )
    for d in store.load_all("Decision"):
        assert d["kind"] == "kill" and not d["cited_evidence"]
        assert "WITHDRAWN, NOT MEASURED" in d["rationale"], (
            "a kill Decision must say plainly that it is a withdrawal and not a finding, or a "
            "later reader will cite it as evidence that memory systems were evaluated"
        )
    transfer = store.claims()["bda4396c7638e63f"]
    assert transfer["thresholds"]["population"] == ["launchpad-lint"]
    assert transfer["thresholds"]["command_incident_role"] == "retrospective_regression_only"
    assert transfer["thresholds"]["two_arm_test"] == "rejected_not_run"
    _ok("SAFE real store: 3 Claims, 3 frozen gates, 0 Evidence, 2 vendor kills")


TESTS = [
    test_id_contract_reproduces_the_preexisting_claim,
    test_preregistration_artifact_still_hashes,
    test_canon_schema_set_has_not_drifted,
    test_refuses_unemittable_object_types,
    test_observed_at_cannot_be_defaulted,
    test_refuses_phase2_fields_on_a_phase1_envelope,
    test_refuses_backdated_role_declaration,
    test_refuses_stale_artifact_hash,
    test_nested_artifact_pointer_is_hash_checked,
    test_nested_phase2_field_is_refused,
    test_programme_path_refusal_is_case_insensitive,
    test_artifact_pointer_cannot_escape_the_repo,
    test_append_only_leaves_the_envelope_byte_unmodified,
    test_case_only_collision_is_refused_loudly,
    test_refuses_any_programme_reference,
    test_programme_guard_docstring_admits_its_limit,
    test_every_refused_write_records_a_canon_violation,
    test_identity_is_canonical_json_not_bytes,
    test_no_selection_check_catches_a_kernel,
    test_repo_has_no_selection_kernel,
    test_publication_guard_is_fail_closed,
    test_publication_guard_blocks_results_without_a_decision,
    test_preregistration_page_may_publish_without_results,
    test_declaring_no_results_while_citing_evidence_is_refused,
    test_build_gate_refuses_an_unbacked_results_page,
    test_live_site_passes_the_publication_guard,
    test_probe_entry_emits_cleanly,
    test_the_real_store_matches_what_we_deliberately_emitted,
]


def main() -> int:
    print(f"lab.canon — Phase 1 emission path, {len(TESTS)} assertions\n")
    failed = 0
    for t in TESTS:
        try:
            t()
        except AssertionError as e:
            failed += 1
            print(f"  FAIL {t.__name__}:\n       {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  ERR  {t.__name__}: {type(e).__name__}: {e}")
    print()
    if failed:
        print(f"{failed}/{len(TESTS)} FAILED")
        return 1
    print(f"all {len(TESTS)} assertions hold")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(REPO))
    sys.exit(main())

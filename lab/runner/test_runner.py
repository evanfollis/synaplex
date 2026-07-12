"""Verifiable assertions for the eval runner (Phase C).

    PYTHONPATH=. .venv/bin/python lab/runner/test_runner.py

The runner's job is to be *boring and honest*. These tests are mostly about the ways it
could quietly lie: scoring an abort as a zero, dropping an answer instead of counting it as
a miss, double-counting a resumed cell, falling back to fixtures when the credential is
missing, or emitting Evidence and slamming the pre-registration window shut as a side effect
of a script finishing.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SEED = "test-seed-do-not-use-for-real-runs"


def _ok(msg: str) -> None:
    print(f"  ok   {msg}")


def test_corpus_is_deterministic() -> None:
    """Same seed, same case, byte-identical — or a disputed result cannot be re-run."""
    from lab.runner.corpus import build_case

    a = build_case("multi_session_coherence", 10, 3, SEED)
    b = build_case("multi_session_coherence", 10, 3, SEED)
    assert a == b
    c = build_case("multi_session_coherence", 10, 4, SEED)
    assert a != c, "different run_index must produce a different case"
    d = build_case("multi_session_coherence", 10, 3, "other-seed")
    assert a != d, "the seed must actually determine the corpus"
    _ok("corpus is deterministic in the seed and varies with run_index")


def test_ground_truth_is_never_shown_to_the_arm() -> None:
    """The canonical answer must not appear in the context an arm receives — except where
    the fact itself was stated, which is the whole point of the task."""
    from lab.runner.arms import Arm, Budget, FixtureProvider
    from lab.runner.corpus import build_case

    case = build_case("multi_session_coherence", 10, 0, SEED)
    control = Arm(key="control", memory=None, provider=FixtureProvider(), budget=Budget())
    context, _ = control.build_context(case)
    for probe in case.probes:
        assert probe.question not in context, "the probe question leaked into the context"
    _ok("probe questions never leak into an arm's context")


def test_oracle_is_deterministic_and_not_an_llm() -> None:
    from lab.runner.oracle import cell_recall, normalize, score_recall_at_1

    assert normalize("The Ravenna.") == normalize("ravenna")
    assert normalize("Three") == "3"
    assert score_recall_at_1("Ravenna", "ravenna") == 1
    assert score_recall_at_1("Uppsala", "ravenna") == 0
    assert score_recall_at_1("", "ravenna") == 0, "an empty answer is a miss, not a skip"
    assert cell_recall(["a", "b"], ["a", "x"]) == 0.5
    _ok("oracle: deterministic normalisation, empty answer scores as a miss")


def test_dropped_answer_cannot_shrink_the_denominator() -> None:
    """Omitting an answer instead of recording a miss inflates the score. Refuse it."""
    from lab.runner.oracle import cell_recall

    try:
        cell_recall(["a"], ["a", "b"])
    except ValueError as e:
        assert "denominator" in str(e)
    else:
        raise AssertionError("a missing answer was silently dropped and the score inflated")
    _ok("a dropped answer raises rather than shrinking the denominator")


def test_aborted_cell_has_no_score() -> None:
    """The most dangerous bug available to an eval: coding 'we stopped paying' as 'it was
    wrong'. `AbortedCell` has no score field, so the mistake is unavailable, not discouraged."""
    from dataclasses import fields

    from lab.runner.arms import AbortedCell, CellResult

    aborted_fields = {f.name for f in fields(AbortedCell)}
    assert "answers" not in aborted_fields and "recall_at_1" not in aborted_fields
    assert "reason" in aborted_fields, "an abort must record why"
    assert "answers" in {f.name for f in fields(CellResult)}
    _ok("AbortedCell cannot carry a score — an abort is structurally not a result")


def test_live_mode_refuses_rather_than_faking() -> None:
    """A silent fallback to fixtures would emit a complete synthetic result set that nothing
    downstream could distinguish from a real one. That is worse than not running."""
    from lab.runner.arms import LiveProvider

    saved = os.environ.pop("ANTHROPIC_API_KEY", None)
    try:
        LiveProvider("claude-sonnet-5")
    except RuntimeError as e:
        assert "hard refusal" in str(e) and "fallback" in str(e)
    else:
        raise AssertionError("live mode started with no credential — it must refuse")
    finally:
        if saved:
            os.environ["ANTHROPIC_API_KEY"] = saved
    _ok("live mode refuses without a credential; it never degrades to fixtures")


def test_runner_emits_no_evidence() -> None:
    """Evidence emission closes every frozen gate's pre-registration window, permanently.
    That is an epistemic act, not a side effect of a script finishing."""
    import inspect

    from lab.runner import arms, corpus, oracle, run

    for mod in (run, arms, corpus, oracle):
        src = inspect.getsource(mod)
        assert "emit_evidence" not in src, (
            f"{mod.__name__} references emit_evidence. A runner that emits Evidence closes the "
            f"pre-registration window on a partial run, and no rerun can reopen it."
        )
    manifest_default = "emits_evidence"
    assert manifest_default in inspect.getsource(run), "the manifest must say so explicitly"
    _ok("the runner cannot emit Evidence — checked in source, not promised in a docstring")


def test_fixture_run_is_idempotent_on_resume() -> None:
    """A resumed run must skip completed cells, never re-run and never double-count."""
    from lab.runner import run as runner

    with tempfile.TemporaryDirectory() as td:
        os.environ["SYNAPLEX_CORPUS_SEED"] = SEED
        original = runner.RUNS_ROOT
        runner.RUNS_ROOT = Path(td)
        try:
            d1 = runner.execute(mode="fixture", runs=3, arms=["control"], run_id="r1")
            m1 = json.loads((d1 / "manifest.json").read_text())
            assert m1["cells_completed"] == 3 and m1["cells_resumed"] == 0
            assert not m1["partial"]

            d2 = runner.execute(mode="fixture", runs=3, arms=["control"], run_id="r1")
            m2 = json.loads((d2 / "manifest.json").read_text())
            assert m2["cells_resumed"] == 3, "a resumed run re-executed completed cells"
            assert len(list((d2 / "cells").glob("*.json"))) == 3, "cells were duplicated"

            s = runner.summarize(d2)
            assert s["control"]["completed"] == 3
        finally:
            runner.RUNS_ROOT = original
            os.environ.pop("SYNAPLEX_CORPUS_SEED", None)
    _ok("resume is idempotent: completed cells are skipped, never duplicated")


def test_manifest_captures_what_a_replay_needs() -> None:
    from lab.runner import run as runner

    with tempfile.TemporaryDirectory() as td:
        os.environ["SYNAPLEX_CORPUS_SEED"] = SEED
        original = runner.RUNS_ROOT
        runner.RUNS_ROOT = Path(td)
        try:
            d = runner.execute(mode="fixture", runs=2, arms=["control"], run_id="m1")
            m = json.loads((d / "manifest.json").read_text())
            for key in ("corpus_digest", "code_digest", "arms", "runs_per_cell",
                        "session_depth", "cells_planned", "partial", "incompatibilities"):
                assert key in m, f"manifest is missing {key}"
            assert m["emits_evidence"] is False
            assert m["corpus_digest"].startswith("sha256:")
            # The seed itself must never reach the manifest — publishing it would let a future
            # subject train on the corpus, and the point is that nothing has.
            assert SEED not in json.dumps(m), "the private corpus seed leaked into the manifest"
            hashes = json.loads((d / "artifact-hashes.json").read_text())
            assert hashes, "no artifact hashes recorded; Evidence would have nothing to bind to"
        finally:
            runner.RUNS_ROOT = original
            os.environ.pop("SYNAPLEX_CORPUS_SEED", None)
    _ok("manifest carries corpus+code digests, abort accounting — and never the seed")


def test_incompatibilities_are_recorded_not_improvised_around() -> None:
    """MemGPT and Letta are one system. The handoff says record it and propose the smallest
    honest successor — do not quietly rename an arm and still call it four subjects."""
    from lab.runner.run import INCOMPATIBILITIES

    kinds = {i["kind"] for i in INCOMPATIBILITIES}
    assert "not_semantically_distinct" in kinds
    assert "credential_blocked" in kinds
    memgpt = next(i for i in INCOMPATIBILITIES if i["subject"] == "memgpt")
    assert "letta-ai/letta" in memgpt["detail"]
    assert memgpt["smallest_honest_successor"]
    _ok("the MemGPT/Letta collision and the credential block are recorded in every manifest")


TESTS = [
    test_corpus_is_deterministic,
    test_ground_truth_is_never_shown_to_the_arm,
    test_oracle_is_deterministic_and_not_an_llm,
    test_dropped_answer_cannot_shrink_the_denominator,
    test_aborted_cell_has_no_score,
    test_live_mode_refuses_rather_than_faking,
    test_runner_emits_no_evidence,
    test_fixture_run_is_idempotent_on_resume,
    test_manifest_captures_what_a_replay_needs,
    test_incompatibilities_are_recorded_not_improvised_around,
]


def main() -> int:
    print(f"lab.runner — {len(TESTS)} assertions\n")
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

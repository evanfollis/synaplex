"""Verifiable assertions for the generic execution adapter.

    PYTHONPATH=. .venv/bin/python lab/runner/test_runner.py

The vendor-specific route (Letta / mem0 / MemGPT arms, the memory-probe corpus, the metered
Anthropic client) is retired. What remains is subject-agnostic, and these tests are about the
ways it could quietly lie: scoring an abort, double-counting a resumed cell, emitting
Evidence as a side effect, or reaching for a metered API.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _ok(msg: str) -> None:
    print(f"  ok   {msg}")


def test_no_metered_api_path_exists() -> None:
    """ADR-0036: subscription plans only. There must be no code path that can spend metered
    tokens — not a disabled one, not a guarded one. None."""
    import inspect

    from lab.runner import execution, oracle, providers

    for mod in (providers, execution, oracle):
        src = inspect.getsource(mod)
        for banned in ("anthropic.Anthropic", "openai.OpenAI", "api.anthropic.com"):
            assert banned not in src, f"{mod.__name__} contains a metered-API client: {banned}"
    src = inspect.getsource(providers)
    assert "claude" in src and "codex" in src, "the subscription CLIs are the only model seam"
    _ok("no metered-API code path exists; the model seam is the subscription CLIs")


def test_metered_keys_in_the_environment_are_refused() -> None:
    """A key sitting in the environment is a loaded gun: some library picks it up, spend
    happens, nobody notices until the invoice."""
    from lab.runner.providers import assert_no_metered_keys

    os.environ["ANTHROPIC_API_KEY"] = "sk-ant-test"
    try:
        assert_no_metered_keys()
    except RuntimeError as e:
        assert "ADR-0036" in str(e)
    else:
        raise AssertionError("a metered API key in the environment was not refused")
    finally:
        os.environ.pop("ANTHROPIC_API_KEY", None)
    assert_no_metered_keys()  # clean env passes
    _ok("a metered API key present in the environment is refused (ADR-0036)")


def test_failover_is_capacity_only() -> None:
    """A capacity failure means 'this provider cannot serve right now' — try the other. Any
    other failure means something is WRONG, and retrying it elsewhere would launder a bug
    into a result produced by a model we did not intend to use."""
    from lab.runner.providers import (
        CapacityExhausted, Completion, ProviderFailed, SubscriptionPool,
    )

    class Exhausted:
        name, model = "claude", "sonnet"

        def complete(self, prompt, timeout_s=180):
            raise CapacityExhausted("rate limit")

    class Broken:
        name, model = "claude", "sonnet"

        def complete(self, prompt, timeout_s=180):
            raise ProviderFailed("segfault")

    class Works:
        name, model = "codex", "gpt-5.4"

        def complete(self, prompt, timeout_s=180):
            return Completion("ok", self.name, self.model, 1, 1, 5)

    got = SubscriptionPool(providers=(Exhausted(), Works())).complete("x")
    assert got.provider == "codex" and got.fallback_from == "claude"

    try:
        SubscriptionPool(providers=(Broken(), Works())).complete("x")
    except ProviderFailed:
        pass
    else:
        raise AssertionError("a non-capacity failure failed over — that launders a bug")

    try:
        SubscriptionPool(providers=(Exhausted(), Exhausted())).complete("x")
    except CapacityExhausted as e:
        assert "hard-stop" in str(e) and "metered" in str(e)
    else:
        raise AssertionError("both providers exhausted must hard-stop, not fall back")
    _ok("failover is capacity-only; other failures raise; both-exhausted hard-stops")


def test_aborted_cell_has_no_result() -> None:
    from dataclasses import fields

    from lab.runner.execution import AbortedCell, CellResult

    assert "output" not in {f.name for f in fields(AbortedCell)}
    assert "reason" in {f.name for f in fields(AbortedCell)}
    assert "output" in {f.name for f in fields(CellResult)}
    _ok("AbortedCell carries no result — an abort is structurally not a finding")


def test_runner_cannot_emit_evidence() -> None:
    import inspect

    from lab.runner import execution, oracle, providers

    for mod in (execution, oracle, providers):
        assert "emit_evidence" not in inspect.getsource(mod), (
            f"{mod.__name__} can emit Evidence. That closes every frozen gate's "
            f"pre-registration window permanently, and no rerun can reopen it."
        )
    _ok("the runner cannot emit Evidence — checked in source, not promised in prose")


def test_resume_is_idempotent() -> None:
    from lab.runner import execution
    from lab.runner.execution import Cell, CellResult, Run, now

    calls: list[str] = []

    def run_cell(cell: Cell) -> CellResult:
        calls.append(cell.key)
        return CellResult(key=cell.key, output={"v": cell.payload["v"]}, observed_at=now())

    with tempfile.TemporaryDirectory() as td:
        original = execution.RUNS_ROOT
        execution.RUNS_ROOT = Path(td)
        try:
            cells = [Cell(key=f"c{i}", payload={"v": i}) for i in range(3)]
            r = Run(eval_id="t", run_id="r1", cells=cells, execute_cell=run_cell,
                    code_files=("lab/runner/execution.py",))
            d = r.execute()
            assert len(calls) == 3
            m = json.loads((d / "manifest.json").read_text())
            assert m["cells_completed"] == 3 and m["cells_resumed"] == 0 and not m["partial"]
            assert m["emits_evidence"] is False and m["billing"] == "subscription"

            d = Run(eval_id="t", run_id="r1", cells=cells, execute_cell=run_cell,
                    code_files=("lab/runner/execution.py",)).execute()
            assert len(calls) == 3, "a resumed run re-executed completed cells"
            m = json.loads((d / "manifest.json").read_text())
            assert m["cells_resumed"] == 3
            assert len(list((d / "cells").glob("*.json"))) == 3, "cells were duplicated"
            assert json.loads((d / "artifact-hashes.json").read_text()), "no artifact hashes"
        finally:
            execution.RUNS_ROOT = original
    _ok("resume is idempotent: completed cells skipped, never re-run, never duplicated")


def test_oracle_still_refuses_a_shrinking_denominator() -> None:
    from lab.runner.oracle import cell_recall, score_recall_at_1

    assert score_recall_at_1("", "x") == 0, "an empty answer is a miss, not a skip"
    try:
        cell_recall(["a"], ["a", "b"])
    except ValueError as e:
        assert "denominator" in str(e)
    else:
        raise AssertionError("a dropped answer shrank the denominator and inflated the score")
    _ok("oracle: an omitted answer raises rather than inflating the score")


def test_vendor_route_is_gone() -> None:
    """The retired route must not be resurrectable by accident.

    Vendor names may appear in exactly one place: the metered-key refusal list, where naming
    `LETTA_API_KEY` is how we refuse it. Everywhere else, a vendor name means the arms are
    back.
    """
    runner = REPO / "lab" / "runner"
    for gone in ("arms.py", "corpus.py", "run.py"):
        assert not (runner / gone).exists(), f"{gone} is back; the vendor route was retired"

    for path in runner.glob("*.py"):
        if path.name == "test_runner.py":
            continue  # this file names the retired vendors in order to assert they are gone
        for lineno, line in enumerate(path.read_text().splitlines(), 1):
            low = line.lower()
            if "_api_key" in low:  # the refusal list — naming a key is how we refuse it
                continue
            for vendor in ("letta", "mem0", "memgpt"):
                assert vendor not in low, (
                    f"{path.name}:{lineno} names vendor {vendor!r} outside the metered-key "
                    f"refusal list — the retired arms are back"
                )
    _ok("vendor route gone; vendors appear only in the metered-key refusal list")


TESTS = [
    test_no_metered_api_path_exists,
    test_metered_keys_in_the_environment_are_refused,
    test_failover_is_capacity_only,
    test_aborted_cell_has_no_result,
    test_runner_cannot_emit_evidence,
    test_resume_is_idempotent,
    test_oracle_still_refuses_a_shrinking_denominator,
    test_vendor_route_is_gone,
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

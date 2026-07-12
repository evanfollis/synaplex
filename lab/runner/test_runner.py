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


def test_child_cli_cannot_see_a_metered_credential() -> None:
    """The real proof, end to end: spawn an actual child through the provider's own code path
    with every metered credential set in the PARENT, and assert the child sees none of them.

    This replaces an earlier `assert_no_metered_keys()` that refused to run whenever a metered
    key existed anywhere on the host. That was the wrong control: it clogged the entire
    pipeline over a variable it never used, and made the lab's liveness depend on unrelated
    host state. Prohibiting metered spend does not require refusing to work — it requires
    making the spend *unreachable*. So the credential is stripped from the child's environment
    and the run proceeds.

    Asserting on the dict `child_env()` returns would prove nothing about what the CLI
    actually inherits. This spawns a real process and asks it.
    """
    import subprocess

    from lab.runner.providers import METERED_CREDENTIAL_VARS, child_env

    poison = {v: f"POISON-{v}" for v in METERED_CREDENTIAL_VARS}
    saved = {k: os.environ.get(k) for k in poison}
    os.environ.update(poison)
    try:
        probe = (
            "import os,json;"
            f"print(json.dumps({{v: os.environ.get(v) for v in {list(METERED_CREDENTIAL_VARS)!r}}}))"
        )
        # 1) The child spawned through the sanitized env sees NONE of them.
        seen = json.loads(subprocess.run(
            [sys.executable, "-c", probe], capture_output=True, text=True,
            env=child_env(),
        ).stdout)
        leaked = sorted(k for k, v in seen.items() if v is not None)
        assert not leaked, (
            f"child process inherited metered credential(s): {leaked}. The subscription CLI "
            f"would authenticate against METERED billing instead of the plan."
        )

        # 2) Control: without sanitisation the child WOULD see them. If this fails, the test
        #    above is passing for the wrong reason and proves nothing.
        unsanitized = json.loads(subprocess.run(
            [sys.executable, "-c", probe], capture_output=True, text=True,
        ).stdout)
        assert all(unsanitized[v] == poison[v] for v in poison), (
            "the control leg did not inherit the poison values, so the sanitised leg proves "
            "nothing — the test would pass even if child_env() did nothing at all"
        )

        # 3) The run must NOT be blocked merely because the parent holds a key.
        from lab.runner import execution
        from lab.runner.execution import Cell, CellResult, Run, now

        with tempfile.TemporaryDirectory() as td:
            original = execution.RUNS_ROOT
            execution.RUNS_ROOT = Path(td)
            try:
                d = Run(
                    eval_id="t", run_id="poisoned",
                    cells=[Cell(key="c0", payload={})],
                    execute_cell=lambda c: CellResult(c.key, {"ok": True}, now()),
                    code_files=("lab/runner/execution.py",),
                ).execute()
                m = json.loads((d / "manifest.json").read_text())
                assert m["cells_completed"] == 1, "the pipeline clogged on an ambient env var"
            finally:
                execution.RUNS_ROOT = original
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    _ok("child CLI cannot see any metered credential; the run proceeds and does not clog")


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
    test_child_cli_cannot_see_a_metered_credential,
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

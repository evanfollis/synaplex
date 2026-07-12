"""Verifiable assertions for friction `sourceType` resolution.

Backs the precedence fix of 2026-07-12. The bug: `_default_source_type()` checked
the ambient systemd env (INVOCATION_ID / SYSTEMD_EXEC_PID) *before* the explicit
SYNAPLEX_SOURCE_TYPE declaration. Every persistent tmux session on this host is
supervised by `workspace-session@<name>.service`, so those variables are inherited
by every agent shell — which meant:

  - an agent hand-running an adapter emitted `sourceType: "cron"`, indistinguishable
    in meta-scan from the real 4-hourly timer, and
  - `SYNAPLEX_SOURCE_TYPE=smoke` silently did nothing in the exact context it exists
    for.

That is ADR-0019's failure class (a measurement system co-located with its subject
must discriminate self-generated traffic) reproduced inside the telemetry meant to
detect it. Explicit declaration must beat ambient inference.

Test 2 is the one that keeps the fix honest: the real systemd units set no
SYNAPLEX_SOURCE_TYPE, so inference must still tag genuine timer runs as `cron`. A
"fix" that broke that would trade one telemetry lie for another.

Run from the repo root:

    .venv/bin/python intake/test_source_type.py

Exit code 0 = all assertions hold; non-zero = drift detected.
"""

from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path

_ENV_KEYS = ("SYNAPLEX_SOURCE_TYPE", "INVOCATION_ID", "SYSTEMD_EXEC_PID")


def _resolve(env: dict[str, str]) -> str:
    """Resolve sourceType under exactly the given environment, nothing inherited."""
    for k in _ENV_KEYS:
        os.environ.pop(k, None)
    os.environ.update(env)
    import intake.friction as friction

    importlib.reload(friction)
    return friction._default_source_type()


def test_explicit_declaration_beats_ambient_systemd() -> None:
    """The regression that started this: smoke must survive an inherited INVOCATION_ID."""
    got = _resolve({"INVOCATION_ID": "abc123", "SYNAPLEX_SOURCE_TYPE": "smoke"})
    assert got == "smoke", (
        f"expected 'smoke', got {got!r}. An agent's hand-run smoke test is being "
        f"recorded as a scheduled cron run — meta-scan cannot tell them apart, and "
        f"the escape hatch is dead code in the one context it exists for."
    )
    print("  [1/5] explicit smoke beats inherited INVOCATION_ID — OK")


def test_real_cron_still_infers_cron() -> None:
    """The systemd units set no SYNAPLEX_SOURCE_TYPE, so inference must still fire.

    This is the guard against over-correcting: real timer runs must keep tagging
    `cron` or the fix has just moved the lie.
    """
    assert _resolve({"INVOCATION_ID": "abc123"}) == "cron"
    assert _resolve({"SYSTEMD_EXEC_PID": "1332"}) == "cron"
    print("  [2/5] real timer runs (no declaration) still infer cron — OK")


def test_bare_shell_defaults_to_system() -> None:
    assert _resolve({}) == "system"
    print("  [3/5] bare shell with no signals defaults to system — OK")


def test_garbage_declaration_falls_through() -> None:
    """An unrecognized value must not be trusted into the event."""
    assert _resolve({"SYNAPLEX_SOURCE_TYPE": "banana", "INVOCATION_ID": "abc"}) == "cron"
    assert _resolve({"SYNAPLEX_SOURCE_TYPE": "banana"}) == "system"
    print("  [4/5] unrecognized declaration falls through to inference — OK")


def test_end_to_end_emit_under_a_supervised_shell() -> None:
    """The whole point, exercised through emit(): a smoke run under systemd env
    must land in the log as `smoke`.

    Writes to a temp runtime root, not the real friction log — a test that pollutes
    production telemetry is the same class of mistake this fix is repairing.
    """
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        for k in _ENV_KEYS:
            os.environ.pop(k, None)
        # A supervised agent shell: INVOCATION_ID inherited, smoke declared.
        os.environ["INVOCATION_ID"] = "abc123"
        os.environ["SYNAPLEX_SOURCE_TYPE"] = "smoke"
        os.environ["SYNAPLEX_RUNTIME_ROOT"] = td

        import intake.paths as paths

        importlib.reload(paths)
        import intake.friction as friction

        importlib.reload(friction)

        event = friction.emit_success("intake", "test_source_type", "self-test")
        assert event["sourceType"] == "smoke", (
            f"emit() wrote sourceType={event['sourceType']!r} for a declared smoke run "
            f"under a supervised shell"
        )
        written = json.loads(paths.FRICTION_LOG.read_text(encoding="utf-8").strip())
        assert written["sourceType"] == "smoke", "on-disk event disagrees with returned event"
        assert str(paths.FRICTION_LOG).startswith(td), "test wrote outside its temp root"

    os.environ.pop("SYNAPLEX_RUNTIME_ROOT", None)
    print("  [5/5] emit() end-to-end: smoke under a supervised shell lands as smoke — OK")


TESTS = (
    test_explicit_declaration_beats_ambient_systemd,
    test_real_cron_still_infers_cron,
    test_bare_shell_defaults_to_system,
    test_garbage_declaration_falls_through,
    test_end_to_end_emit_under_a_supervised_shell,
)


def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    print("intake.friction — sourceType precedence\n")
    failed = 0
    for t in TESTS:
        try:
            t()
        except AssertionError as e:
            failed += 1
            print(f"  FAIL {t.__name__}:\n    {e}")
    print()
    if failed:
        print(f"{failed}/{len(TESTS)} FAILED")
        return 1
    print(f"All {len(TESTS)} assertions pass — explicit declaration beats ambient inference.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

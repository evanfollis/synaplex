"""Verifiable assertions for the skip_next_run backoff primitive.

Backs the 2026-05-14 arxiv backoff handoff (cycle-36 synthesis Pattern 5).
Runs as a standalone script (no pytest required):

    /opt/workspace/projects/synaplex/.venv/bin/python intake/test_skip_next_run.py

Exit 0 = all properties hold; non-zero = drift detected.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _reset_intake_runtime_modules() -> None:
    """Force path-derived modules to re-read SYNAPLEX_RUNTIME_ROOT."""
    for name in ("intake.escalation", "intake.friction", "intake.paths"):
        sys.modules.pop(name, None)


def assert_set_and_consume_round_trip() -> None:
    from intake.escalation import (
        consume_skip_next_run,
        set_skip_next_run,
        skip_pending,
    )
    # clean prior state
    consume_skip_next_run("__test_a")
    assert not skip_pending("__test_a")

    set_skip_next_run("__test_a")
    assert skip_pending("__test_a"), "flag did not register as set"

    assert consume_skip_next_run("__test_a") is True, "first consume must return True"
    assert consume_skip_next_run("__test_a") is False, (
        "second consume must return False; flag is one-shot, not sticky"
    )
    assert not skip_pending("__test_a"), "skip_pending must reflect consumption"
    print("  [1/3] set + consume round-trip is one-shot — OK")


def assert_set_is_idempotent() -> None:
    from intake.escalation import (
        consume_skip_next_run,
        set_skip_next_run,
        skip_pending,
    )
    consume_skip_next_run("__test_b")
    set_skip_next_run("__test_b")
    set_skip_next_run("__test_b")
    set_skip_next_run("__test_b")
    assert skip_pending("__test_b")
    # Still one-shot on consume — multiple sets don't accumulate
    assert consume_skip_next_run("__test_b") is True
    assert consume_skip_next_run("__test_b") is False
    print("  [2/3] set is idempotent; multiple sets do not accumulate — OK")


def assert_per_source_independence() -> None:
    from intake.escalation import (
        consume_skip_next_run,
        set_skip_next_run,
        skip_pending,
    )
    consume_skip_next_run("__test_c1")
    consume_skip_next_run("__test_c2")

    set_skip_next_run("__test_c1")
    assert skip_pending("__test_c1")
    assert not skip_pending("__test_c2"), (
        "setting c1 must not affect c2 — sources are independent"
    )
    assert consume_skip_next_run("__test_c1") is True
    assert consume_skip_next_run("__test_c2") is False
    print("  [3/3] per-source independence — OK")


def assert_set_failure_emits_friction() -> None:
    """Review-6bba7dd §1 fix: marker write failure must surface, not be swallowed.

    Patches `_skip_path` to point at a path under a non-existent and
    un-creatable parent so `write_text` raises OSError. The function
    must emit a `failure` friction event and NOT silently return.
    """
    import json
    import tempfile
    from pathlib import Path
    from unittest import mock

    from intake import escalation
    from intake.paths import FRICTION_LOG

    # Read pre-event count (only ones tagged with our test source)
    pre_count = 0
    if FRICTION_LOG.exists():
        with open(FRICTION_LOG, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    if json.loads(line).get("source") == "__test_writefail":
                        pre_count += 1
                except json.JSONDecodeError:
                    continue

    # Force write to fail by routing the marker into a path whose
    # parent is a regular file (a file can't have children → write
    # to a path under it raises NotADirectoryError, an OSError subclass).
    # `STATE_DIR.mkdir(exist_ok=True)` still runs against the real
    # STATE_DIR and succeeds (it already exists); the OSError fires
    # on the subsequent `write_text` against the bad path.
    with tempfile.NamedTemporaryFile(suffix=".file") as nf:
        bad_parent = Path(nf.name)
        unwritable_target = bad_parent / "child" / "marker"
        with mock.patch.object(escalation, "_skip_path", return_value=unwritable_target):
            escalation.set_skip_next_run("__test_writefail")

    # Verify a `failure` event was emitted naming the test source
    post_count = 0
    found_failure = False
    if FRICTION_LOG.exists():
        with open(FRICTION_LOG, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if ev.get("source") == "__test_writefail":
                    post_count += 1
                    if ev.get("eventType") == "failure" and "backoff arming failed" in ev.get("reason", ""):
                        found_failure = True
    assert post_count > pre_count, "no friction event was emitted on write failure"
    assert found_failure, (
        "write failure must emit eventType=failure with 'backoff arming failed' in reason; "
        "the marker file IS the backoff mechanism — silent failure here defeats the backoff"
    )
    print("  [4/4] set_skip_next_run write-failure surfaces as friction event — OK")


def main() -> int:
    import os
    import tempfile

    print("skip_next_run primitive assertions (arxiv backoff handoff 2026-05-14):")
    prior_runtime_root = os.environ.get("SYNAPLEX_RUNTIME_ROOT")
    prior_source_type = os.environ.get("SYNAPLEX_SOURCE_TYPE")
    with tempfile.TemporaryDirectory() as td:
        os.environ["SYNAPLEX_RUNTIME_ROOT"] = td
        os.environ["SYNAPLEX_SOURCE_TYPE"] = "smoke"
        _reset_intake_runtime_modules()
        try:
            assert_set_and_consume_round_trip()
            assert_set_is_idempotent()
            assert_per_source_independence()
            assert_set_failure_emits_friction()
        except AssertionError as exc:
            print(f"FAIL: {exc}", file=sys.stderr)
            return 1
        finally:
            if prior_runtime_root is None:
                os.environ.pop("SYNAPLEX_RUNTIME_ROOT", None)
            else:
                os.environ["SYNAPLEX_RUNTIME_ROOT"] = prior_runtime_root
            if prior_source_type is None:
                os.environ.pop("SYNAPLEX_SOURCE_TYPE", None)
            else:
                os.environ["SYNAPLEX_SOURCE_TYPE"] = prior_source_type
            _reset_intake_runtime_modules()
    print("All assertions pass — skip_next_run behaves as specified.")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    sys.exit(main())

"""Verifiable assertions for the skip_next_run backoff primitive.

Backs the 2026-05-14 arxiv backoff handoff (cycle-36 synthesis Pattern 5).
Runs as a standalone script (no pytest required):

    /opt/workspace/projects/synaplex/.venv/bin/python intake/test_skip_next_run.py

Exit 0 = all properties hold; non-zero = drift detected.
"""

from __future__ import annotations

import sys
from pathlib import Path


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


def main() -> int:
    print("skip_next_run primitive assertions (arxiv backoff handoff 2026-05-14):")
    try:
        assert_set_and_consume_round_trip()
        assert_set_is_idempotent()
        assert_per_source_independence()
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("All assertions pass — skip_next_run behaves as specified.")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    sys.exit(main())

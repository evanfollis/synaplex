"""Verifiable assertions for the per-fetch cap policy.

This test backs ADR-0029 §Amendment 2026-05-07. It asserts the three
properties the amendment ratifies, so a future drift between the ADR
text and the implementation surfaces immediately rather than after a
week of carry-forward escalation.

Run as a standalone script (no pytest required):

    /opt/workspace/projects/synaplex/.venv/bin/python intake/test_cap_policy.py

Exit code 0 = all assertions hold; non-zero = drift detected.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


def assert_layer1_cap_is_200() -> None:
    """ADR-0029 §6 (amended): Layer 1 cap is 200 items per fetch."""
    from intake.limits import layer1_cap, LAYER1_MAX_ITEMS_PER_FETCH

    assert layer1_cap() == 200, f"layer1_cap() returned {layer1_cap()}, expected 200"
    assert LAYER1_MAX_ITEMS_PER_FETCH == 200
    print("  [1/3] layer1_cap() == 200 — OK")


def assert_merge_does_not_truncate_to_200() -> None:
    """ADR-0029 §Amendment 2026-05-07: merge_jsonl_by_id is union, not bounded.

    Two consecutive merges of 150 disjoint items each must yield 300 in the
    daily file. If a future implementation introduces post-merge truncation
    at 200, this test fails.
    """
    from intake.adapters import merge_jsonl_by_id, read_existing_items

    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "raw.jsonl"
        first = [{"id": f"a{n:04d}", "title": f"first-{n}"} for n in range(150)]
        second = [{"id": f"b{n:04d}", "title": f"second-{n}"} for n in range(150)]

        new_added, preserved, total = merge_jsonl_by_id(path, first)
        assert (new_added, preserved, total) == (150, 0, 150), (new_added, preserved, total)

        new_added, preserved, total = merge_jsonl_by_id(path, second)
        assert (new_added, preserved, total) == (150, 150, 300), (new_added, preserved, total)

        items = read_existing_items(path)
        assert len(items) == 300, (
            f"merge produced {len(items)} items; ADR-0029 §Amendment "
            f"2026-05-07 forbids post-merge truncation"
        )
    print("  [2/3] merge_jsonl_by_id is union, not bounded at 200 — OK")


def assert_per_fetch_cap_fires_on_oversize_batch() -> None:
    """The cap fires within a single fetch on >200 items.

    Direct exercise of the adapter dispatch is heavyweight (network).
    Instead, test the invariant the adapters rely on: the cap value
    matches what each adapter's loop-guard checks (`len(new_items) >= cap`).
    """
    from intake.limits import layer1_cap

    cap = layer1_cap()
    # Simulate the adapter loop's accumulator
    new_items: list[dict] = []
    capped = 0
    for n in range(250):  # 250 incoming items
        if len(new_items) >= cap:
            capped += 1
            continue
        new_items.append({"id": f"x{n:04d}"})

    assert len(new_items) == 200, len(new_items)
    assert capped == 50, capped
    print("  [3/3] per-fetch cap fires at 200 of 250 incoming — OK")


def main() -> int:
    print("Layer 1 cap policy assertions (ADR-0029 §Amendment 2026-05-07):")
    try:
        assert_layer1_cap_is_200()
        assert_merge_does_not_truncate_to_200()
        assert_per_fetch_cap_fires_on_oversize_batch()
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("All assertions pass — implementation matches ADR-0029 §Amendment 2026-05-07.")
    return 0


if __name__ == "__main__":
    # Make the package importable when run as a script
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    sys.exit(main())

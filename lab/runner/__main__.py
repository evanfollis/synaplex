"""CLI for the eval runner.

    python -m lab.runner run --mode fixture           # offline, deterministic, CI
    python -m lab.runner run --mode live              # refuses: no credentials
    python -m lab.runner summarize <run-id>

`--mode live` is the real evaluation and currently refuses to start: every provider
credential is absent. It refuses loudly rather than falling back to fixtures, because a
silent fallback would produce a complete, plausible, entirely synthetic result set that
nothing downstream could distinguish from a real one.
"""

from __future__ import annotations

import argparse
import json
import sys

from intake import friction

from .run import EVAL_ID, RUNS_ROOT, execute, summarize


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lab.runner")
    sub = parser.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run")
    r.add_argument("--mode", choices=["fixture", "live"], required=True)
    r.add_argument("--suite", default="multi_session_coherence")
    r.add_argument("--depth", type=int, default=10)
    r.add_argument("--runs", type=int, default=10)
    r.add_argument("--run-id")
    r.add_argument("--arms", nargs="*")

    s = sub.add_parser("summarize")
    s.add_argument("run_id")

    args = parser.parse_args(argv)

    if args.cmd == "summarize":
        run_dir = RUNS_ROOT / args.run_id
        if not run_dir.is_dir():
            print(f"no such run: {args.run_id}")
            return 1
        print(json.dumps(summarize(run_dir), indent=2))
        return 0

    try:
        run_dir = execute(
            mode=args.mode, suite=args.suite, depth=args.depth,
            runs=args.runs, run_id=args.run_id, arms=args.arms,
        )
    except RuntimeError as e:
        friction.emit(
            layer="lab", source="runner", eventType="throttled",
            reason=f"{EVAL_ID} run refused: {e}", ref="lab/runner",
        )
        print(f"REFUSED: {e}")
        return 1

    manifest = json.loads((run_dir / "manifest.json").read_text())
    print(f"run {manifest['run_id']}  mode={manifest['mode']}")
    print(f"  cells: {manifest['cells_completed']}/{manifest['cells_planned']} "
          f"(aborted {manifest['cells_aborted']}, resumed {manifest['cells_resumed']})"
          f"{'  PARTIAL' if manifest['partial'] else ''}")
    print(f"  corpus: {manifest['corpus_digest'][:23]}...")
    print(f"  -> {run_dir}\n")
    print(json.dumps(summarize(run_dir), indent=2))
    print("\nNo Evidence emitted. This run concludes nothing.")

    friction.emit(
        layer="lab", source="runner",
        eventType="success" if not manifest["partial"] else "throttled",
        reason=(f"{EVAL_ID} {manifest['mode']} run {manifest['run_id']}: "
                f"{manifest['cells_completed']}/{manifest['cells_planned']} cells, "
                f"{manifest['cells_aborted']} aborted; no Evidence emitted"),
        ref=str(run_dir.relative_to(RUNS_ROOT.parents[3])),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

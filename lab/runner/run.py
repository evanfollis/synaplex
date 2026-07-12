"""Execution adapter. Runs a methodology someone else already chose.

## What this is not

It is **not** a campaign kernel. It does not select Claims, thresholds, outcomes, arms, or
publication decisions — those were pre-registered and hash-bound before it existed, and it
reads them rather than deciding them. It executes cells and writes raw artifacts. That is
the whole job.

**It does not emit Evidence.** Not "does not yet" — must not. Evidence emission closes the
pre-registration window of every frozen gate on the Claim, permanently, and that is an
epistemic act, not a side effect of a script finishing. Phase E emits Evidence from these
artifacts, deliberately, with `observed_at` taken from the run manifest rather than the
clock. A runner that emitted Evidence as it went would close the window on a partial run,
and no rerun could reopen it.

## Idempotent resume

Each cell writes one file named by (run_id, arm, suite, run_index). A resumed run skips
cells whose file exists. So a run interrupted at cell 37 of 250 continues at 37, and cannot
double-count 1–36 — a second copy of a cell would silently reweight the mean.

Partial state is explicit: the manifest records `cells_planned` and `cells_completed`, and a
partial run says so rather than looking like a small complete one.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from lab.canon.ids import hash_file
from lab.canon.store import REPO_ROOT

from .arms import AbortedCell, Arm, Budget, CellResult, FixtureProvider, LiveProvider, Provider
from .corpus import build_case, corpus_digest, seed
from .oracle import cell_recall

EVAL_ID = "memory-systems-v1"
RUNS_ROOT = REPO_ROOT / "lab" / "evals" / EVAL_ID / "runs"

PRIMARY_CLAIM = "b7ff216f4eec6e58"
CONTROL_CLAIM = "bb7cee596f94289b"

# The arms, exactly as pre-registered. `memgpt` is present because the Claim names it; see
# `INCOMPATIBILITIES` below for why that is a problem we record rather than fix.
ARM_KEYS = ("letta", "mem0", "memgpt", "claude-builtin", "control")

MEMORY_FOR = {
    "letta": "letta",
    "mem0": "mem0",
    "memgpt": "memgpt",
    "claude-builtin": "claude-builtin",
    "control": None,
}

# Recorded, not improvised around. The handoff is explicit: if a named subject is no longer
# runnable or semantically distinct, record the incompatibility and propose the smallest
# honest successor — do not quietly substitute one under the old Claim.
INCOMPATIBILITIES = [
    {
        "subject": "memgpt",
        "kind": "not_semantically_distinct",
        "detail": (
            "methodology.md names MemGPT as a separate subject and points at "
            "github.com/letta-ai/letta — which is Letta's own repository. MemGPT was renamed "
            "to Letta; subjects 1 and 3 are one system in two deployment modes (hosted API vs "
            "self-hosted reference), not two systems. The eval as pre-registered has four "
            "subjects on paper and three systems in fact."
        ),
        "smallest_honest_successor": (
            "A successor Claim that either (a) names the two arms as 'Letta (hosted)' and "
            "'Letta (self-hosted)' and says plainly they are deployment modes of one system, "
            "or (b) drops one and names a genuinely distinct fourth subject. Do NOT rename the "
            "arm inside the current run and call it four subjects."
        ),
    },
    {
        "subject": "all",
        "kind": "credential_blocked",
        "detail": (
            "ANTHROPIC_API_KEY, LETTA_API_KEY, and MEM0_API_KEY are all absent from "
            "runtime/.secrets/synaplex.env. No live cell can execute. Fixture mode exercises "
            "the full pipeline offline; it produces no Evidence and must never be mistaken "
            "for a result."
        ),
        "smallest_honest_successor": "Provision the credentials. There is no code fix.",
    },
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _code_digest() -> str:
    """Digest of the runner + oracle source.

    In the manifest because the oracle's normalisation *is* the measurement. A result
    produced by different scoring code is a different result, and a manifest that cannot tell
    you which code scored it cannot support a replay.
    """
    h = hashlib.sha256()
    for name in ("arms.py", "corpus.py", "oracle.py", "run.py"):
        h.update(hashlib.sha256((Path(__file__).parent / name).read_bytes()).digest())
    return f"sha256:{h.hexdigest()}"


def build_arms(mode: str, model: str = "claude-sonnet-5") -> list[Arm]:
    provider: Provider = FixtureProvider() if mode == "fixture" else LiveProvider(model)
    return [Arm(key=k, memory=MEMORY_FOR[k], provider=provider, budget=Budget()) for k in ARM_KEYS]


def cell_path(run_dir: Path, arm: str, suite: str, run_index: int) -> Path:
    return run_dir / "cells" / f"{arm}__{suite}__{run_index:03d}.json"


def execute(
    *,
    mode: str,
    suite: str = "multi_session_coherence",
    depth: int = 10,
    runs: int = 10,
    run_id: str | None = None,
    arms: list[str] | None = None,
) -> Path:
    """Execute the pre-registered suite. Returns the run directory.

    Emits raw artifacts only. No Evidence, no Decision, no publication — by construction.
    """
    if mode not in {"fixture", "live"}:
        raise ValueError("mode must be 'fixture' or 'live'")

    run_id = run_id or f"{mode}-{_now().replace(':', '').replace('-', '')}"
    run_dir = RUNS_ROOT / run_id
    (run_dir / "cells").mkdir(parents=True, exist_ok=True)

    selected = [a for a in build_arms(mode) if arms is None or a.key in arms]
    planned = len(selected) * runs
    completed = resumed = aborted = 0
    corpus_seed = seed()

    for arm in selected:
        for run_index in range(runs):
            path = cell_path(run_dir, arm.key, suite, run_index)
            if path.exists():  # idempotent resume — never re-run, never double-count
                resumed += 1
                completed += 1
                continue

            case = build_case(suite, depth, run_index, corpus_seed)
            try:
                result = arm.run_cell(case)
            except NotImplementedError as e:
                result = AbortedCell(arm=arm.key, suite=suite, run_index=run_index,
                                     reason=f"arm not runnable: {e}")

            if isinstance(result, AbortedCell):
                aborted += 1
                record = {"status": "aborted", **asdict(result)}
                # No score. An aborted cell has no score, and the type system is what
                # guarantees nobody can later pretend it scored zero.
            else:
                record = {
                    "status": "completed",
                    **asdict(result),
                    "recall_at_1": cell_recall(list(result.answers), case.canonicals),
                    "probes": [p.question for p in case.probes],
                    "canonicals": case.canonicals,
                }
            record["observed_at"] = _now()  # when reality was consulted — Phase E reads this
            path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            completed += 1

    manifest = {
        "run_id": run_id,
        "eval_id": EVAL_ID,
        "mode": mode,
        "started_at": _now(),
        "claims": {"primary": PRIMARY_CLAIM, "control": CONTROL_CLAIM},
        "suite": suite,
        "session_depth": depth,
        "runs_per_cell": runs,
        "arms": [{"key": a.key, "memory": a.memory,
                  "provider": a.provider.name, "provider_version": a.provider.version,
                  "max_input_tokens": a.budget.max_input_tokens,
                  "max_output_tokens": a.budget.max_output_tokens} for a in selected],
        "corpus_digest": corpus_digest(suite, depth, runs, corpus_seed),
        "code_digest": _code_digest(),
        "cells_planned": planned,
        "cells_completed": completed,
        "cells_resumed": resumed,
        "cells_aborted": aborted,
        "partial": completed < planned,
        "incompatibilities": INCOMPATIBILITIES,
        "emits_evidence": False,
        "note": (
            "Raw artifacts only. This run emits no Evidence and concludes nothing. Evidence "
            "emission closes the pre-registration window of every frozen gate on these Claims, "
            "permanently — it is a deliberate act performed from these artifacts, not a side "
            "effect of a script finishing."
        ),
    }
    mpath = run_dir / "manifest.json"
    mpath.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # Hash every artifact this run produced. Evidence will bind to these hashes; if the bytes
    # move afterwards, canon rule 7 refuses the emission rather than pointing at a ghost.
    hashes = {
        str(p.relative_to(run_dir)): hash_file(p)
        for p in sorted(run_dir.rglob("*.json")) if p != mpath
    }
    (run_dir / "artifact-hashes.json").write_text(
        json.dumps(hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return run_dir


def summarize(run_dir: Path) -> dict:
    """Read back a run. Reports scores per arm — and reports nothing about what they mean.

    Deliberately stops here. Turning cell scores into "supported" or "falsified" is what the
    frozen gate and the Decision are for; a runner that computed a verdict would be selecting
    an outcome, which is exactly what it must not do.
    """
    cells = [json.loads(p.read_text()) for p in sorted((run_dir / "cells").glob("*.json"))]
    out: dict[str, dict] = {}
    for c in cells:
        a = out.setdefault(c["arm"], {"completed": 0, "aborted": 0, "recalls": []})
        if c["status"] == "aborted":
            a["aborted"] += 1
        else:
            a["completed"] += 1
            a["recalls"].append(c["recall_at_1"])
    for a in out.values():
        a["mean_recall_at_1"] = (
            round(sum(a["recalls"]) / len(a["recalls"]), 4) if a["recalls"] else None
        )
    return out

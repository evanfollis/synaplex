"""Generic execution adapter: run cells, write hashed artifacts, emit nothing epistemic.

This is what survived the vendor route. It is deliberately subject-agnostic — it knows how to
execute a list of cells idempotently and record what happened, and it knows nothing about
what is being evaluated. The retired memory-systems route hard-coded its subjects into this
layer; that was the mistake, and the reason a bad subject choice took the machinery with it.

## Invariants this file exists to hold

- **It does not emit Evidence.** Evidence emission closes the pre-registration window of
  every frozen gate on a Claim, permanently. That is an epistemic act performed deliberately
  from these artifacts, not the side effect of a script finishing.
- **It selects nothing.** No Claims, no thresholds, no outcomes, no verdict. It executes a
  methodology that was pre-registered and hash-bound before it ran.
- **An aborted cell has no score.** `AbortedCell` has no result field, so coding "we stopped"
  as "it failed" is structurally unavailable rather than merely discouraged.
- **Resume is idempotent.** A cell whose artifact exists is skipped, never re-run and never
  double-counted — a duplicate would silently reweight any aggregate taken over the cells.
- **Subscription billing only.** The model seam is `providers.SubscriptionPool`; there is no
  metered-API code path to re-enable (ADR-0036).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from lab.canon.ids import hash_file
from lab.canon.store import REPO_ROOT

from .providers import assert_no_metered_keys

RUNS_ROOT = REPO_ROOT / "lab" / "runs"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass(frozen=True)
class Cell:
    """One unit of work. `key` must be stable across runs — it is the resume key."""

    key: str
    payload: dict


@dataclass(frozen=True)
class CellResult:
    key: str
    output: dict
    observed_at: str  # when reality was consulted. Phase E reads this; never the clock.


@dataclass(frozen=True)
class AbortedCell:
    """No result field. An abort is structurally not a result."""

    key: str
    reason: str


@dataclass
class Run:
    eval_id: str
    run_id: str
    cells: list[Cell]
    execute_cell: Callable[[Cell], CellResult | AbortedCell]
    claims: dict[str, str] = field(default_factory=dict)
    code_files: tuple[str, ...] = ()

    @property
    def dir(self) -> Path:
        return RUNS_ROOT / self.eval_id / self.run_id

    def _code_digest(self) -> str:
        """The scoring/execution code is part of the measurement. A result produced by
        different code is a different result, and a manifest that cannot say which code
        produced it cannot support a replay."""
        h = hashlib.sha256()
        for rel in sorted(self.code_files):
            h.update(hashlib.sha256((REPO_ROOT / rel).read_bytes()).digest())
        return f"sha256:{h.hexdigest()}"

    def execute(self) -> Path:
        assert_no_metered_keys()  # ADR-0036, enforced not remembered

        (self.dir / "cells").mkdir(parents=True, exist_ok=True)
        completed = resumed = aborted = 0

        for cell in self.cells:
            path = self.dir / "cells" / f"{cell.key}.json"
            if path.exists():
                resumed += 1
                completed += 1
                continue

            result = self.execute_cell(cell)
            if isinstance(result, AbortedCell):
                aborted += 1
                record = {"status": "aborted", "key": result.key, "reason": result.reason}
            else:
                record = {
                    "status": "completed",
                    "key": result.key,
                    "output": result.output,
                    "observed_at": result.observed_at,
                }
            path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            completed += 1

        manifest = {
            "eval_id": self.eval_id,
            "run_id": self.run_id,
            "generated_at": now(),
            "claims": self.claims,
            "code_digest": self._code_digest(),
            "cells_planned": len(self.cells),
            "cells_completed": completed,
            "cells_resumed": resumed,
            "cells_aborted": aborted,
            "partial": completed < len(self.cells),
            "billing": "subscription",  # ADR-0036
            "emits_evidence": False,
            "note": (
                "Raw artifacts only. This run emits no Evidence and concludes nothing. "
                "Evidence emission closes the pre-registration window on every frozen gate "
                "bound to these Claims, permanently — it is a deliberate act performed from "
                "these artifacts, not a side effect of a script finishing."
            ),
        }
        mpath = self.dir / "manifest.json"
        mpath.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        hashes = {
            str(p.relative_to(self.dir)): hash_file(p)
            for p in sorted(self.dir.rglob("*.json")) if p != mpath
        }
        (self.dir / "artifact-hashes.json").write_text(
            json.dumps(hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return self.dir

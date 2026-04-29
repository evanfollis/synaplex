"""Intake adapters.

Each adapter exports an `ingest(beat, date, out_path) -> IngestResult` entry.
The caller (cli.py) owns the choice of source/date/out_path; adapters do not
inspect environment beyond what they need (HTTP user agent, timeouts).

Adapters MUST use `intake.hashing.content_id` for item IDs and MUST emit at
least one friction event per call (success or failure; empty-result ⇒ stuck).

**No-clobber discipline (workspace rule applied here)**: adapters fire many
times per day to the same daily file. Each run MUST merge new items with
the existing file by `content_id` rather than truncating. A run that
fetches 0 new items must NOT destroy data from a prior successful run in
the same day. Use `merge_jsonl_by_id` to enforce this.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class IngestResult:
    source: str
    count: int          # new items added this run
    deduped: int        # within-run duplicates (same id seen twice in current fetch)
    out_path: str
    total: int = 0      # total items in daily file after merge (>= count)
    preserved: int = 0  # items preserved from prior runs (carried into the merge)

    def as_reason(self) -> str:
        base = f"{self.count} new items"
        if self.preserved:
            base += f", {self.preserved} preserved"
        if self.deduped:
            base += f", {self.deduped} within-run dedup"
        return base


def read_existing_items(path: Path | str) -> dict[str, dict]:
    """Load an existing daily file into {id: item}. Empty/missing returns {}.

    Tolerates malformed lines (drops them silently — partial reads are
    acceptable; corruption is bounded). Used as the seed for union-write.
    """
    p = Path(path)
    if not p.exists() or p.stat().st_size == 0:
        return {}
    out: dict[str, dict] = {}
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            iid = item.get("id")
            if iid:
                out[iid] = item
    return out


def merge_jsonl_by_id(
    path: Path | str, new_items: list[dict],
) -> tuple[int, int, int]:
    """Merge new items with the existing daily file by `id` (no-clobber).

    - Existing items keyed by `id` form the base set.
    - New items override existing entries with the same id (newer
      `fetched_at` wins implicitly because we write last).
    - The union is written atomically: serialize to a `.tmp` sibling,
      then `os.replace` onto the target path.
    - If both `new_items` is empty AND the existing file has no content,
      the target file is created empty (matches prior behavior for first-
      run-of-day with no data).
    - If `new_items` is empty AND the existing file has content, the
      existing file is left untouched. This is the no-clobber guarantee.

    Returns (count_new_added, count_preserved_unchanged, count_total).
    `count_new_added` is the number of ids that did not exist before.
    """
    import os
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    existing = read_existing_items(p)

    # Special case: empty fetch + existing content → no-op (preserve).
    if not new_items and existing:
        return 0, len(existing), len(existing)

    merged: dict[str, dict] = dict(existing)
    new_added = 0
    for item in new_items:
        iid = item.get("id")
        if not iid:
            continue
        if iid not in merged:
            new_added += 1
        merged[iid] = item  # latest wins on collision

    preserved = len(merged) - new_added

    # Atomic write with durability barriers + tmp cleanup on failure
    # (adversarial review of 5814658 §1 + §2: bare `os.replace` is atomic
    # for visibility but not durability — power loss between rename and
    # the next periodic flush can leave a 0-byte file at the target).
    tmp = p.with_suffix(p.suffix + ".tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as fp:
            for item in merged.values():
                fp.write(json.dumps(item, ensure_ascii=False) + "\n")
            fp.flush()
            os.fsync(fp.fileno())
        os.replace(tmp, p)
        # fsync the parent dir so the rename itself survives a host crash
        dir_fd = os.open(str(p.parent), os.O_DIRECTORY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except BaseException:
        # On any failure, remove the orphan tmp; the existing daily file
        # (if any) is untouched because os.replace either succeeded or
        # never ran.
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    return new_added, preserved, len(merged)

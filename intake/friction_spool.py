"""Replay ADR-0043 friction fallback records to their original destinations.

Maintenance entrypoint:

    PYTHONPATH=. .venv/bin/python -m intake.friction_spool [--spool PATH] [--dry-run]

The spool is locked while draining. Successfully replayed records are removed only
after the remaining spool has been fsynced and atomically replaced. Records that are
malformed or whose destination still cannot be written remain in the spool and are
reported on stderr; the command exits non-zero so maintenance cannot mistake partial
recovery for completion.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import sys
from pathlib import Path

from .friction import _append_jsonl, _fallback_spool, _spool_lock_path


def _replace_spool(path: Path, records: list[dict]) -> None:
    tmp = path.with_name(f".{path.name}.drain-{os.getpid()}")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        for record in records:
            payload = (json.dumps(record, ensure_ascii=False) + "\n").encode("utf-8")
            view = memoryview(payload)
            while view:
                written = os.write(fd, view)
                if written == 0:
                    raise OSError("zero-byte spool rewrite")
                view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(tmp, path)
    dir_fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)


def drain(spool: Path, *, dry_run: bool = False) -> dict:
    """Replay valid records, retain failures, and return a machine-readable receipt."""
    receipt = {"spool": str(spool), "found": 0, "replayed": 0, "retained": 0,
               "dry_run": dry_run, "errors": []}
    if not spool.exists():
        return receipt

    spool.parent.mkdir(parents=True, exist_ok=True)
    with open(_spool_lock_path(spool), "a", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        lines = spool.read_text(encoding="utf-8").splitlines(keepends=True)
        retained: list[dict] = []
        for lineno, line in enumerate(lines, 1):
            if not line.strip():
                continue
            receipt["found"] += 1
            try:
                record = json.loads(line)
                if record.get("spool_version") != 1:
                    raise ValueError("unsupported or missing spool_version")
                destination = Path(record["destination"])
                event = record["event"]
                if not isinstance(event, dict):
                    raise ValueError("event is not an object")
                if not dry_run:
                    _append_jsonl(destination, event, durable=True)
                receipt["replayed"] += 1
            except Exception as error:  # noqa: BLE001 - retain every unreplayed record
                try:
                    retained.append(json.loads(line))
                except json.JSONDecodeError:
                    retained.append({"spool_version": 0, "raw_line": line.rstrip("\n")})
                receipt["errors"].append({
                    "line": lineno, "type": type(error).__name__, "message": str(error)
                })

        receipt["retained"] = len(retained)
        if not dry_run:
            _replace_spool(spool, retained)
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spool", type=Path, default=_fallback_spool())
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    receipt = drain(args.spool, dry_run=args.dry_run)
    print(json.dumps(receipt, indent=2))
    if receipt["errors"]:
        sys.stderr.write(
            f"synaplex friction spool: {receipt['retained']} record(s) retained; "
            "see JSON receipt\n"
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

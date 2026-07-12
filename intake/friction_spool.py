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

from .friction import (
    _append_jsonl,
    _ensure_private_spool_parent,
    _fallback_spool,
    _spool_lock_path,
)
from .paths import FRICTION_LOG


def _replace_spool(path: Path, records: list[str]) -> None:
    tmp = path.with_name(f".{path.name}.drain-{os.getpid()}")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        for record in records:
            payload = record.encode("utf-8")
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


def _normalized(path: Path) -> Path:
    return Path(os.path.abspath(os.path.normpath(path)))


def drain(
    spool: Path,
    *,
    dry_run: bool = False,
    allowed_destinations: set[Path] | None = None,
) -> dict:
    """Replay valid records, retain failures, and return a machine-readable receipt."""
    receipt = {"spool": str(spool), "found": 0, "replayed": 0, "retained": 0,
               "dry_run": dry_run, "errors": []}
    _ensure_private_spool_parent(spool)
    if spool.is_symlink():
        raise PermissionError(f"spool file may not be a symlink: {spool}")
    if not spool.exists():
        return receipt

    configured_destinations = {FRICTION_LOG} if allowed_destinations is None else allowed_destinations
    allowed = {_normalized(p) for p in configured_destinations}
    lock_fd = os.open(
        _spool_lock_path(spool),
        os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW,
        0o600,
    )
    with os.fdopen(lock_fd, "a", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        lines = spool.read_text(encoding="utf-8").splitlines(keepends=True)
        retained: list[str] = []
        for lineno, line in enumerate(lines, 1):
            if not line.strip():
                continue
            receipt["found"] += 1
            try:
                record = json.loads(line)
                if record.get("spool_version") != 1:
                    raise ValueError("unsupported or missing spool_version")
                destination = _normalized(Path(record["destination"]))
                if destination not in allowed:
                    raise PermissionError(f"destination is not allowlisted: {destination}")
                event = record["event"]
                if not isinstance(event, dict):
                    raise ValueError("event is not an object")
                if not dry_run:
                    _append_jsonl(destination, event, durable=True)
                receipt["replayed"] += 1
            except Exception as error:  # noqa: BLE001 - retain every unreplayed record
                retained.append(line)
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

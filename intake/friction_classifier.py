"""Incrementally promote recurring ADR-0029 friction into durable FR records.

The append-only event stream remains authoritative.  This module stores only a
seven-day working projection with byte offsets and hashes back into that stream.
No model or external service participates in classification.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import stat
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .friction import emit

WINDOW_DAYS = 7
FAILURE_THRESHOLD = 3
MAX_SOURCE_EVENT_REFS = 256
MAX_CANDIDATE_COUNT = 1024
MAX_FUTURE_SKEW = timedelta(minutes=5)
IMMEDIATE_TYPES = frozenset({"stuck", "escalated"})
NON_PROMOTING_TYPES = frozenset({"success", "throttled"})
VALID_TYPES = frozenset({"success", "failure", "stuck", "escalated", "throttled"})
VALID_LAYERS = frozenset({"intake", "reasoning", "validation", "presentation", "friction", "lab"})
MAX_REASON_CHARS = 160
MAX_REF_CHARS = 512
MAX_REPRESENTATIVE_REASONS = 5
CLASS_TEXT_LIMIT = 96

DEFAULT_EVENT_LOG = Path("/opt/workspace/runtime/friction/events.jsonl")
DEFAULT_RUNTIME_ROOT = Path("/opt/workspace/runtime/friction")
DEFAULT_SUPERVISOR_FRICTION = Path("/opt/workspace/supervisor/friction")

_VOLATILE_PATTERNS = (
    (re.compile(r"https?://\S+", re.I), "<url>"),
    (re.compile(r"\b[0-9a-f]{32,}\b", re.I), "<hash>"),
    (re.compile(r"\b[0-9a-f]{8}-[0-9a-f-]{27,}\b", re.I), "<uuid>"),
    (re.compile(r"\b\d{4}-\d{2}-\d{2}(?:[t ]\d{2}:\d{2}(?::\d{2})?z?)?\b", re.I), "<time>"),
    (re.compile(r"(?:^|\s)/(?:[^\s,;]+/)*[^\s,;]+"), " <path>"),
    (re.compile(r"\b\d+(?:\.\d+)?\b"), "<n>"),
)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _parse_ts(value: object) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("ts must be a non-empty ISO timestamp")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("ts must include a timezone")
    return parsed.astimezone(timezone.utc)


def normalize_reason(reason: str) -> str:
    """Return a transparent, bounded failure-class projection."""
    normalized = reason.lower().strip()
    for pattern, replacement in _VOLATILE_PATTERNS:
        normalized = pattern.sub(replacement, normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip(" ,.;:-")
    return normalized[:MAX_REASON_CHARS]


def display_text(value: str, limit: int = MAX_REASON_CHARS) -> str:
    """Collapse control and Markdown-shaping whitespace in generated prose."""
    return re.sub(r"\s+", " ", value).strip()[:limit]


def class_display_text(value: object) -> str:
    if not isinstance(value, str):
        return "unknown"
    return display_text(value, CLASS_TEXT_LIMIT) or "unknown"


def _validate_event(value: object, *, now: datetime) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("event must be an object")
    event = value
    for key in ("ts", "layer", "source", "eventType", "reason", "ref"):
        if key not in event:
            raise ValueError(f"missing required field: {key}")
    timestamp = _parse_ts(event["ts"])
    if timestamp > now + MAX_FUTURE_SKEW:
        raise ValueError("timestamp is materially in the future")
    if event["layer"] not in VALID_LAYERS:
        raise ValueError("invalid layer")
    if not isinstance(event["source"], str) or not event["source"].strip():
        raise ValueError("source must be a non-empty string")
    if event["eventType"] not in VALID_TYPES:
        raise ValueError("invalid eventType")
    if not isinstance(event["reason"], str) or not event["reason"].strip():
        raise ValueError("reason must be a non-empty string")
    if not isinstance(event["ref"], str):
        raise ValueError("ref must be a string")
    return event


def class_key(event: dict[str, Any]) -> tuple[str, str]:
    structural = {
        "layer": event["layer"],
        "source": event["source"].strip().lower(),
        "eventType": event["eventType"],
        "reason": normalize_reason(event["reason"]),
    }
    encoded = json.dumps(structural, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest(), encoded


def _safe_directory(path: Path, mode: int) -> None:
    path.mkdir(parents=True, mode=mode, exist_ok=True)
    info = os.lstat(path)
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise PermissionError(f"not a real directory: {path}")
    if info.st_uid != os.geteuid():
        raise PermissionError(f"directory owner mismatch: {path}")
    current = stat.S_IMODE(info.st_mode)
    if current & 0o022:
        raise PermissionError(f"directory is group/world writable: {path} ({current:o})")


def _atomic_json(path: Path, value: object, mode: int = 0o600) -> None:
    _safe_directory(path.parent, 0o700)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _lock(path: Path):
    _safe_directory(path.parent, 0o700 if "runtime" in str(path) else 0o755)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    handle = os.fdopen(fd, "w", encoding="utf-8")
    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
    return handle


def _slug(text: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return value[:64] or "recurring-friction"


@dataclass
class RunReceipt:
    processed: int = 0
    malformed: int = 0
    candidates: int = 0
    promoted: int = 0
    deduplicated: int = 0
    start_offset: int = 0
    end_offset: int = 0

    def as_dict(self) -> dict[str, int]:
        return dict(vars(self))


class FrictionClassifier:
    def __init__(
        self,
        *,
        event_log: Path = DEFAULT_EVENT_LOG,
        runtime_root: Path = DEFAULT_RUNTIME_ROOT,
        supervisor_friction: Path = DEFAULT_SUPERVISOR_FRICTION,
        now: datetime | None = None,
    ) -> None:
        self.event_log = event_log
        self.runtime_root = runtime_root
        self.candidates_root = runtime_root / "candidates"
        self.state_path = runtime_root / "classifier-state.json"
        self.run_lock = runtime_root / ".classifier.lock"
        self.supervisor_friction = supervisor_friction
        # Keep the cross-repo write lock on runtime state: a scheduled run must not
        # dirty the supervisor repository merely by acquiring a lock.
        self.fr_lock = runtime_root / ".fr-write.lock"
        self.now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)

    def _state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return {"version": 1, "offset": 0, "line": 0, "file": {}}
        value = json.loads(self.state_path.read_text(encoding="utf-8"))
        if value.get("version") != 1 or not isinstance(value.get("offset"), int):
            raise ValueError("unsupported classifier state")
        return value

    def _load_candidates(self) -> dict[str, dict[str, Any]]:
        values: dict[str, dict[str, Any]] = {}
        if not self.candidates_root.exists():
            return values
        for path in self.candidates_root.glob("sha256-*.json"):
            value = json.loads(path.read_text(encoding="utf-8"))
            fingerprint = value.get("fingerprint")
            if isinstance(fingerprint, str):
                values[fingerprint] = value
        return values

    def _emit_malformed_candidate(self, *, fingerprint: str, reason: str) -> None:
        try:
            emit(
                layer="friction",
                source="friction-classifier",
                eventType="failure",
                reason=f"malformed candidate {fingerprint}: {reason}"[:MAX_REASON_CHARS],
                ref=str(self.candidates_root / f"sha256-{fingerprint}.json"),
                sourceType="system",
            )
        except Exception:
            # Candidate repair must not depend on optional telemetry delivery.
            pass

    def _candidate_ref_timestamp(
        self, *, fingerprint: str, ref: dict[str, Any]
    ) -> datetime | None:
        try:
            return _parse_ts(ref["ts"])
        except (KeyError, TypeError, ValueError) as error:
            self._emit_malformed_candidate(
                fingerprint=fingerprint,
                reason=f"invalid source_event_ref ts: {type(error).__name__}",
            )
            return None

    def _candidate_last_seen(self, candidate: dict[str, Any]) -> datetime:
        window = candidate.get("window", {})
        if isinstance(window, dict):
            try:
                return _parse_ts(window.get("last_seen"))
            except ValueError:
                pass
        timestamps = [
            timestamp
            for ref in candidate.get("source_event_refs", [])
            if isinstance(ref, dict)
            for timestamp in [self._candidate_ref_timestamp(
                fingerprint=str(candidate.get("fingerprint", "unknown")),
                ref=ref,
            )]
            if timestamp is not None
        ]
        return max(timestamps, default=datetime.min.replace(tzinfo=timezone.utc))

    def _enforce_candidate_count(self, candidates: dict[str, dict[str, Any]]) -> None:
        active = [
            (fingerprint, candidate)
            for fingerprint, candidate in candidates.items()
            if candidate.get("source_event_refs")
        ]
        excess = len(active) - MAX_CANDIDATE_COUNT
        if excess <= 0:
            return
        evicted = sorted(active, key=lambda item: self._candidate_last_seen(item[1]))[:excess]
        for fingerprint, _candidate in evicted:
            (self.candidates_root / f"sha256-{fingerprint}.json").unlink(missing_ok=True)
            candidates.pop(fingerprint, None)
        emit(
            layer="friction",
            source="friction-classifier",
            eventType="throttled",
            reason=f"evicted {len(evicted)} old candidates above cap {MAX_CANDIDATE_COUNT}",
            ref=str(self.candidates_root),
            sourceType="system",
            extra={"evicted": len(evicted), "candidate_limit": MAX_CANDIDATE_COUNT},
        )

    def _read_new(self, state: dict[str, Any], receipt: RunReceipt) -> list[tuple[dict[str, Any], dict[str, Any]]]:
        accepted: list[tuple[dict[str, Any], dict[str, Any]]] = []
        with self.event_log.open("rb") as handle:
            # Bind provenance and watermark decisions to the descriptor we
            # actually read. A path-level stat before open races log rotation.
            info = os.fstat(handle.fileno())
            prior_file = state.get("file", {})
            offset = state["offset"]
            line_number = state.get("line", 0)
            if prior_file and (
                prior_file.get("dev") != info.st_dev
                or prior_file.get("ino") != info.st_ino
            ):
                offset, line_number = 0, 0
            if info.st_size < offset:
                offset, line_number = 0, 0
            receipt.start_offset = offset
            handle.seek(offset)
            while True:
                start = handle.tell()
                raw = handle.readline()
                if not raw:
                    break
                if not raw.endswith(b"\n"):
                    handle.seek(start)
                    break
                end = handle.tell()
                line_number += 1
                receipt.processed += 1
                try:
                    event = _validate_event(json.loads(raw), now=self.now)
                    accepted.append((event, {
                        "byte_start": start,
                        "byte_end": end,
                        "line": line_number,
                        "line_sha256": hashlib.sha256(raw).hexdigest(),
                        "source_dev": info.st_dev,
                        "source_ino": info.st_ino,
                    }))
                except (json.JSONDecodeError, UnicodeDecodeError, ValueError, TypeError):
                    receipt.malformed += 1
            receipt.end_offset = handle.tell()
        state.update({
            "offset": receipt.end_offset,
            "line": line_number,
            "file": {"dev": info.st_dev, "ino": info.st_ino},
            "updated_at": _iso(self.now),
        })
        return accepted

    def _mint_or_find(self, candidate: dict[str, Any]) -> tuple[Path, bool]:
        _safe_directory(self.supervisor_friction, 0o755)
        fingerprint = candidate["fingerprint"]
        with _lock(self.fr_lock):
            ids: list[int] = []
            for path in self.supervisor_friction.glob("FR-*.md"):
                match = re.match(r"FR-(\d+)-", path.name)
                if match:
                    ids.append(int(match.group(1)))
                try:
                    if f"Fingerprint: `{fingerprint}`" in path.read_text(encoding="utf-8"):
                        return path, False
                except (OSError, UnicodeDecodeError):
                    continue
            event_type = class_display_text(candidate["class"]["eventType"])
            source = class_display_text(candidate["class"]["source"])
            layer = class_display_text(candidate["class"]["layer"])
            title = f"Recurring {event_type} in {layer}/{source}"
            refs = "\n".join(
                f"- `{self.event_log}` bytes {ref['byte_start']}-{ref['byte_end']} "
                f"(line {ref['line']}, sha256:{ref['line_sha256']})"
                for ref in candidate["source_event_refs"]
            )
            reasons = "\n".join(
                f"- {display_text(reason)}" for reason in candidate["representative_reasons"]
            )
            count = candidate["window"]["count"]
            count_text = (
                f"at least {count}" if candidate["window"].get("truncated") else str(count)
            )
            number = max(ids, default=0) + 1
            while True:
                final = self.supervisor_friction / f"FR-{number:04d}-{_slug(title)}.md"
                body = f"""# FR-{number:04d}: {title}

Captured: {_iso(self.now)}
Source: friction-classifier
Status: open
Fingerprint: `{fingerprint}`
Window: {candidate['window']['days']} days
Count: {count_text}
First seen: {candidate['window']['first_seen']}
Last seen: {candidate['window']['last_seen']}

## What happened

The deterministic Layer-5 classifier observed a promotable recurring class.

## Root cause / failure class

- Layer: `{layer}`
- Source: `{source}`
- Event type: `{event_type}`
- Normalized reason: `{display_text(candidate['class']['reason'])}`

## Representative reasons

{reasons}

## Source-event references

{refs}

## Proposed fix

Pressure-test the recurring class through the normal supervisor friction and synthesis loop.
Do not infer resolution from this automated promotion alone.
"""
                fd, temporary = tempfile.mkstemp(
                    prefix=f".{final.name}.", dir=self.supervisor_friction
                )
                try:
                    os.fchmod(fd, 0o644)
                    with os.fdopen(fd, "w", encoding="utf-8") as handle:
                        handle.write(body)
                        handle.flush()
                        os.fsync(handle.fileno())
                    # Atomic no-clobber publication: unlike replace(), link()
                    # cannot destroy an uncoordinated FR that appeared after
                    # the directory scan.
                    os.link(temporary, final)
                    os.unlink(temporary)
                    directory_fd = os.open(
                        self.supervisor_friction, os.O_RDONLY | os.O_DIRECTORY
                    )
                    try:
                        os.fsync(directory_fd)
                    finally:
                        os.close(directory_fd)
                    return final, True
                except FileExistsError:
                    os.unlink(temporary)
                    number += 1
                    continue
                except BaseException:
                    try:
                        os.unlink(temporary)
                    except FileNotFoundError:
                        pass
                    raise

    def _promotion_is_present(self, candidate: dict[str, Any]) -> bool:
        """Fast-path a previously promoted candidate without hourly FR scans."""
        promotion = candidate.get("promotion", {})
        if promotion.get("status") != "promoted" or not promotion.get("fr"):
            return False
        path = Path(promotion["fr"])
        try:
            if path.parent.resolve() != self.supervisor_friction.resolve():
                return False
            info = os.lstat(path)
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
                return False
            marker = f"Fingerprint: `{candidate['fingerprint']}`"
            return marker in path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return False

    def run(self) -> RunReceipt:
        receipt = RunReceipt()
        _safe_directory(self.runtime_root, 0o700)
        _safe_directory(self.candidates_root, 0o700)
        with _lock(self.run_lock):
            state = self._state()
            candidates = self._load_candidates()
            new_events = self._read_new(state, receipt)
            cutoff = self.now - timedelta(days=WINDOW_DAYS)

            for event, ref in new_events:
                if event["eventType"] in NON_PROMOTING_TYPES:
                    continue
                fingerprint, encoded = class_key(event)
                structural = json.loads(encoded)
                candidate = candidates.setdefault(fingerprint, {
                    "version": 1,
                    "fingerprint": fingerprint,
                    "class": structural,
                    "source_event_refs": [],
                    "representative_reasons": [],
                    "promotion": {"status": "pending"},
                })
                candidate["source_event_refs"].append({
                    **ref,
                    "ts": event["ts"],
                    "reason": display_text(event["reason"]),
                    "ref": display_text(event["ref"], MAX_REF_CHARS),
                })
                display_reason = display_text(event["reason"])
                if display_reason not in candidate["representative_reasons"]:
                    candidate["representative_reasons"].append(display_reason)
                    candidate["representative_reasons"] = candidate["representative_reasons"][:MAX_REPRESENTATIVE_REASONS]

            for fingerprint, candidate in candidates.items():
                # Candidate files are written before the watermark.  If a process
                # dies between those atomic writes, the next run deliberately
                # replays the source lines.  Deduplicate their immutable location
                # identity so that crash recovery cannot inflate a class count.
                unique_refs: dict[tuple[object, ...], dict[str, Any]] = {}
                for ref in candidate["source_event_refs"]:
                    identity = (
                        ref.get("source_dev"), ref.get("source_ino"),
                        ref["byte_start"], ref["byte_end"], ref["line_sha256"],
                    )
                    unique_refs[identity] = ref
                dated_refs = []
                for ref in unique_refs.values():
                    timestamp = self._candidate_ref_timestamp(
                        fingerprint=fingerprint,
                        ref=ref,
                    )
                    if timestamp is None:
                        receipt.malformed += 1
                        continue
                    if cutoff <= timestamp <= self.now + MAX_FUTURE_SKEW:
                        dated_refs.append((timestamp, ref))
                all_refs = [
                    ref for _timestamp, ref in sorted(
                        dated_refs,
                        key=lambda item: (
                            item[0],
                            item[1].get("source_dev", 0),
                            item[1].get("source_ino", 0),
                            item[1]["byte_start"],
                        ),
                    )
                ]
                truncated = len(all_refs) > MAX_SOURCE_EVENT_REFS
                candidate["source_event_refs"] = all_refs[-MAX_SOURCE_EVENT_REFS:]
                refs = candidate["source_event_refs"]
                if not refs:
                    (self.candidates_root / f"sha256-{fingerprint}.json").unlink(missing_ok=True)
                    continue
                timestamps = sorted(
                    timestamp
                    for ref in refs
                    for timestamp in [
                        self._candidate_ref_timestamp(fingerprint=fingerprint, ref=ref)
                    ]
                    if timestamp is not None
                )
                if not timestamps:
                    (self.candidates_root / f"sha256-{fingerprint}.json").unlink(missing_ok=True)
                    continue
                candidate["window"] = {
                    "days": WINDOW_DAYS,
                    "threshold": 1 if candidate["class"]["eventType"] in IMMEDIATE_TYPES else FAILURE_THRESHOLD,
                    "count": len(refs),
                    "truncated": truncated,
                    "retained_reference_limit": MAX_SOURCE_EVENT_REFS,
                    "first_seen": _iso(timestamps[0]),
                    "last_seen": _iso(timestamps[-1]),
                    "evaluated_at": _iso(self.now),
                }
                eligible = len(refs) >= candidate["window"]["threshold"]
                if eligible and not self._promotion_is_present(candidate):
                    path, created = self._mint_or_find(candidate)
                    candidate["promotion"] = {
                        "status": "promoted",
                        "fr": str(path),
                        "at": candidate.get("promotion", {}).get("at", _iso(self.now)),
                    }
                    if created:
                        receipt.promoted += 1
                    else:
                        receipt.deduplicated += 1
            self._enforce_candidate_count(candidates)
            for fingerprint, candidate in candidates.items():
                if candidate.get("source_event_refs"):
                    _atomic_json(self.candidates_root / f"sha256-{fingerprint}.json", candidate)
            receipt.candidates = sum(1 for c in candidates.values() if c.get("source_event_refs"))
            _atomic_json(self.state_path, state)
        return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Promote recurring typed friction")
    parser.add_argument("--events", type=Path, default=DEFAULT_EVENT_LOG)
    parser.add_argument("--runtime-root", type=Path, default=DEFAULT_RUNTIME_ROOT)
    parser.add_argument("--supervisor-friction", type=Path, default=DEFAULT_SUPERVISOR_FRICTION)
    args = parser.parse_args(argv)
    classifier = FrictionClassifier(
        event_log=args.events,
        runtime_root=args.runtime_root,
        supervisor_friction=args.supervisor_friction,
    )
    try:
        receipt = classifier.run()
    except Exception as error:
        emit(
            layer="friction",
            source="friction-classifier",
            eventType="failure",
            reason=f"classifier failed: {type(error).__name__}: {error}"[:MAX_REASON_CHARS],
            ref=str(args.events),
            extra={"processed": 0, "malformed": 0, "candidate": 0, "promoted": 0, "deduplicated": 0},
        )
        raise
    counts = receipt.as_dict()
    emit(
        layer="friction",
        source="friction-classifier",
        eventType="success",
        reason=(f"processed={counts['processed']} malformed={counts['malformed']} "
                f"candidates={counts['candidates']} promoted={counts['promoted']} "
                f"deduplicated={counts['deduplicated']}"),
        ref=str(args.runtime_root / "classifier-state.json"),
        extra={
            "processed": counts["processed"], "malformed": counts["malformed"],
            "candidate": counts["candidates"], "promoted": counts["promoted"],
            "deduplicated": counts["deduplicated"],
        },
    )
    print(json.dumps(counts, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

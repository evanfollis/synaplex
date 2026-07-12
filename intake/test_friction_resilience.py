"""ADR-0043: full-fidelity friction telemetry is off-hot-path and non-blocking."""

from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
from pathlib import Path


def test_default_spool_is_host_persistent_and_overridable() -> None:
    from intake import friction

    original = os.environ.pop(friction.FALLBACK_SPOOL_ENV, None)
    try:
        assert friction._fallback_spool() == Path(
            "/var/tmp/synaplex/friction-spool/events.jsonl"
        )
        os.environ[friction.FALLBACK_SPOOL_ENV] = "/tmp/private/explicit-spool.jsonl"
        assert friction._fallback_spool() == Path("/tmp/private/explicit-spool.jsonl")
    finally:
        if original is None:
            os.environ.pop(friction.FALLBACK_SPOOL_ENV, None)
        else:
            os.environ[friction.FALLBACK_SPOOL_ENV] = original


def test_primary_failure_spools_full_event_and_surfaces_warning() -> None:
    from intake import friction

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        # A directory cannot be opened as an append-only file. This deterministically
        # exercises the same primary-write failure boundary as EROFS without touching the
        # production log or requiring a privileged mount.
        broken_primary = root / "primary-is-a-directory"
        broken_primary.mkdir()
        spool = root / "fallback" / "events.jsonl"
        original_log = friction.FRICTION_LOG
        original_append = friction._append_jsonl
        original_spool = os.environ.get(friction.FALLBACK_SPOOL_ENV)
        attempted_paths: list[Path] = []

        def recording_append(
            path: Path, record: dict, *, durable: bool = False, nofollow: bool = False
        ) -> None:
            attempted_paths.append(path)
            original_append(path, record, durable=durable, nofollow=nofollow)

        friction.FRICTION_LOG = broken_primary
        friction._append_jsonl = recording_append
        os.environ[friction.FALLBACK_SPOOL_ENV] = str(spool)
        stderr = io.StringIO()
        try:
            with contextlib.redirect_stderr(stderr):
                returned = friction.emit_success(
                    "intake", "resilience-test", "primary work already succeeded", "artifact:x"
                )
        finally:
            friction.FRICTION_LOG = original_log
            friction._append_jsonl = original_append
            if original_spool is None:
                os.environ.pop(friction.FALLBACK_SPOOL_ENV, None)
            else:
                os.environ[friction.FALLBACK_SPOOL_ENV] = original_spool

        receipt = returned["_telemetry_delivery"]
        assert receipt["status"] == "spooled" and receipt["spooled"] is True
        assert "primary append failed" in stderr.getvalue()
        records = [json.loads(line) for line in spool.read_text().splitlines()]
        assert len(records) == 1
        record = records[0]
        assert record["spool_version"] == 1
        assert record["destination"] == str(broken_primary)
        assert record["event"]["source"] == "resilience-test"
        assert record["event"]["reason"] == "primary work already succeeded"
        assert record["event"]["ref"] == "artifact:x"
        assert record["primary_error"]["type"] == "IsADirectoryError"
        assert attempted_paths == [broken_primary, spool]
        assert original_log not in attempted_paths, "test attempted the production friction log"


def test_double_write_failure_is_visible_but_does_not_raise() -> None:
    from intake import friction

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        primary = root / "primary-dir"
        spool = root / "spool-dir"
        primary.mkdir()
        spool.mkdir()
        original_log = friction.FRICTION_LOG
        original_append = friction._append_jsonl
        original_spool = os.environ.get(friction.FALLBACK_SPOOL_ENV)
        attempted_paths: list[Path] = []

        def recording_append(
            path: Path, record: dict, *, durable: bool = False, nofollow: bool = False
        ) -> None:
            attempted_paths.append(path)
            original_append(path, record, durable=durable, nofollow=nofollow)

        friction.FRICTION_LOG = primary
        friction._append_jsonl = recording_append
        os.environ[friction.FALLBACK_SPOOL_ENV] = str(spool)
        stderr = io.StringIO()
        try:
            with contextlib.redirect_stderr(stderr):
                returned = friction.emit_failure(
                    "validation", "resilience-test", "diagnostic only"
                )
        finally:
            friction.FRICTION_LOG = original_log
            friction._append_jsonl = original_append
            if original_spool is None:
                os.environ.pop(friction.FALLBACK_SPOOL_ENV, None)
            else:
                os.environ[friction.FALLBACK_SPOOL_ENV] = original_spool

        receipt = returned["_telemetry_delivery"]
        assert receipt["status"] == "undelivered"
        assert receipt["spooled"] is False
        assert receipt["spool_error"]["type"] == "IsADirectoryError"
        assert "fallback spool also failed" in stderr.getvalue()
        assert attempted_paths == [primary, spool]
        assert original_log not in attempted_paths, "test attempted the production friction log"


def test_drain_replays_exact_event_and_retains_failures() -> None:
    from intake.friction_spool import drain

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        good_destination = root / "replayed" / "events.jsonl"
        bad_destination = root / "still-a-directory"
        bad_destination.mkdir()
        spool = root / "spool" / "events.jsonl"
        spool.parent.mkdir(mode=0o700)
        good_event = {"eventType": "success", "reason": "exact", "nested": {"v": [1, 2]}}
        bad_event = {"eventType": "failure", "reason": "retain me"}
        records = [
            {"spool_version": 1, "destination": str(good_destination), "event": good_event},
            {"spool_version": 1, "destination": str(bad_destination), "event": bad_event},
        ]
        spool.write_text("".join(json.dumps(r) + "\n" for r in records))

        receipt = drain(spool, allowed_destinations={good_destination, bad_destination})
        assert receipt["found"] == 2 and receipt["replayed"] == 1
        assert receipt["retained"] == 1 and len(receipt["errors"]) == 1
        assert json.loads(good_destination.read_text()) == good_event
        remaining = [json.loads(line) for line in spool.read_text().splitlines()]
        assert remaining == [records[1]], "drain dropped or mutated an unreplayed record"


def test_drain_rejects_malicious_destination_and_retains_exact_record() -> None:
    from intake.friction_spool import drain

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        spool = root / "spool" / "events.jsonl"
        spool.parent.mkdir(mode=0o700)
        malicious = {
            "spool_version": 1,
            "destination": str(root / "not-allowlisted.jsonl"),
            "event": {"eventType": "success", "reason": "do not replay"},
        }
        exact_line = json.dumps(malicious, separators=(",", ":")) + "\n"
        spool.write_text(exact_line)

        receipt = drain(spool)
        assert receipt["replayed"] == 0 and receipt["retained"] == 1
        assert receipt["errors"][0]["type"] == "PermissionError"
        assert spool.read_text() == exact_line, "rejected record was mutated or dropped"
        assert not Path(malicious["destination"]).exists()


def test_spool_rejects_unsafe_and_symlinked_parents() -> None:
    from intake import friction
    from intake.friction_spool import drain

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        unsafe = root / "unsafe"
        unsafe.mkdir(mode=0o777)
        unsafe.chmod(0o777)
        try:
            friction._append_spool(unsafe / "events.jsonl", {"event": {}})
        except PermissionError as error:
            assert "expected private 700" in str(error)
        else:
            raise AssertionError("group/world-accessible spool parent was accepted")

        real = root / "real"
        real.mkdir(mode=0o700)
        linked = root / "linked"
        linked.symlink_to(real, target_is_directory=True)
        try:
            friction._append_spool(linked / "events.jsonl", {"event": {}})
        except PermissionError as error:
            assert "not a real directory" in str(error)
        else:
            raise AssertionError("symlinked spool parent was accepted")

        try:
            drain(linked / "events.jsonl")
        except PermissionError as error:
            assert "not a real directory" in str(error)
        else:
            raise AssertionError("drain accepted a symlinked spool parent")


TESTS = [
    test_default_spool_is_host_persistent_and_overridable,
    test_primary_failure_spools_full_event_and_surfaces_warning,
    test_double_write_failure_is_visible_but_does_not_raise,
    test_drain_replays_exact_event_and_retains_failures,
    test_drain_rejects_malicious_destination_and_retains_exact_record,
    test_spool_rejects_unsafe_and_symlinked_parents,
]


if __name__ == "__main__":
    for test in TESTS:
        test()
        print(f"ok {test.__name__}")
    print(f"all {len(TESTS)} friction resilience assertions hold")

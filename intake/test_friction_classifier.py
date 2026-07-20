"""Deterministic Layer-5 friction promotion contract tests."""

from __future__ import annotations

import json
import multiprocessing
import os
import stat
import tempfile
import unittest
from unittest import mock
from datetime import datetime, timezone
from pathlib import Path

from intake.friction_classifier import (
    MAX_SOURCE_EVENT_REFS,
    FrictionClassifier,
    class_key,
)

NOW = datetime(2026, 7, 20, 10, 0, tzinfo=timezone.utc)


def _event(
    event_type: str,
    reason: str,
    *,
    source: str = "fixture",
    ts: str = "2026-07-20T09:00:00Z",
    layer: str = "validation",
) -> dict:
    return {
        "ts": ts,
        "layer": layer,
        "source": source,
        "eventType": event_type,
        "reason": reason,
        "ref": "fixture://event",
        "sourceType": "smoke",
    }


def _concurrent_run(events: str, runtime: str, friction: str) -> None:
    FrictionClassifier(
        event_log=Path(events), runtime_root=Path(runtime),
        supervisor_friction=Path(friction), now=NOW,
    ).run()


class FrictionClassifierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.events = self.root / "events.jsonl"
        self.runtime = self.root / "runtime" / "friction"
        self.friction = self.root / "supervisor" / "friction"
        self.friction.mkdir(parents=True)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write(self, *events: dict) -> None:
        self.events.parent.mkdir(parents=True, exist_ok=True)
        with self.events.open("ab") as handle:
            for event in events:
                handle.write(json.dumps(event).encode() + b"\n")

    def classifier(self) -> FrictionClassifier:
        return FrictionClassifier(
            event_log=self.events, runtime_root=self.runtime,
            supervisor_friction=self.friction, now=NOW,
        )

    def frs(self) -> list[Path]:
        return list(self.friction.glob("FR-*.md"))

    def test_below_threshold_does_not_promote(self) -> None:
        self.write(_event("failure", "worker 41 failed"), _event("failure", "worker 42 failed"))
        receipt = self.classifier().run()
        self.assertEqual(receipt.candidates, 1)
        self.assertEqual(receipt.promoted, 0)
        self.assertEqual(self.frs(), [])

    def test_threshold_crossing_promotes_exactly_once_and_rerun_is_idempotent(self) -> None:
        self.write(*[_event("failure", f"worker {n} failed") for n in range(3)])
        first = self.classifier().run()
        second = self.classifier().run()
        self.assertEqual(first.promoted, 1)
        self.assertEqual(second.promoted, 0)
        self.assertEqual(second.deduplicated, 0)
        self.assertEqual(second.processed, 0)
        self.assertEqual(len(self.frs()), 1)
        body = self.frs()[0].read_text()
        self.assertIn("Status: open", body)
        self.assertIn("Count: 3", body)
        self.assertIn("Fingerprint: `", body)

    def test_watermark_replay_after_crash_cannot_inflate_count(self) -> None:
        self.write(_event("failure", "worker 41 failed"), _event("failure", "worker 42 failed"))
        self.classifier().run()
        # Model a crash after candidate replacement but before watermark replacement.
        (self.runtime / "classifier-state.json").unlink()
        receipt = self.classifier().run()
        candidate = json.loads(next((self.runtime / "candidates").glob("*.json")).read_text())
        self.assertEqual(candidate["window"]["count"], 2)
        self.assertEqual(receipt.promoted, 0)
        self.assertEqual(self.frs(), [])

    def test_rotated_event_file_restarts_from_descriptor_zero(self) -> None:
        self.write(_event("success", "old file"))
        self.classifier().run()
        replacement = self.root / "replacement.jsonl"
        replacement.write_text(json.dumps(_event("stuck", "new file")) + "\n")
        os.replace(replacement, self.events)
        receipt = self.classifier().run()
        self.assertEqual((receipt.start_offset, receipt.processed, receipt.promoted), (0, 1, 1))

    def test_malformed_json_does_not_block_later_events(self) -> None:
        self.events.write_bytes(b"{not json}\n" + json.dumps(_event("stuck", "later valid event")).encode() + b"\n")
        receipt = self.classifier().run()
        self.assertEqual((receipt.processed, receipt.malformed, receipt.promoted), (2, 1, 1))
        self.assertEqual(len(self.frs()), 1)

    def test_live_lab_layer_is_valid_and_future_timestamp_is_rejected(self) -> None:
        self.write(
            _event("stuck", "lab queue stalled", layer="lab"),
            _event("stuck", "future event", ts="2026-07-21T09:00:00Z"),
        )
        receipt = self.classifier().run()
        self.assertEqual((receipt.processed, receipt.malformed, receipt.promoted), (2, 1, 1))

    def test_success_and_throttled_are_evidence_not_promotions(self) -> None:
        self.write(_event("success", "routine"), _event("throttled", "designed cap"))
        receipt = self.classifier().run()
        self.assertEqual(receipt.candidates, 0)
        self.assertEqual(self.frs(), [])

    def test_stuck_and_escalated_promote_immediately(self) -> None:
        self.write(_event("stuck", "queue stalled"), _event("escalated", "operator needed"))
        receipt = self.classifier().run()
        self.assertEqual(receipt.promoted, 2)
        self.assertEqual(len(self.frs()), 2)

    def test_concurrent_invocations_cannot_duplicate_id_or_fingerprint(self) -> None:
        self.write(*[_event("failure", f"same fault {n}") for n in range(3)])
        processes = [
            multiprocessing.Process(
                target=_concurrent_run,
                args=(str(self.events), str(self.runtime), str(self.friction)),
            ) for _ in range(2)
        ]
        for process in processes:
            process.start()
        for process in processes:
            process.join(10)
            self.assertEqual(process.exitcode, 0)
        self.assertEqual(len(self.frs()), 1)
        fingerprints = [
            line for line in self.frs()[0].read_text().splitlines()
            if line.startswith("Fingerprint:")
        ]
        self.assertEqual(len(fingerprints), 1)

    def test_uncoordinated_fr_collision_cannot_be_overwritten(self) -> None:
        self.write(_event("stuck", "queue stalled"))
        original_link = os.link
        collided: list[Path] = []

        def collide_once(source: str | Path, target: str | Path, *args, **kwargs) -> None:
            target_path = Path(target)
            if not collided:
                target_path.write_text("# Human-authored FR\n")
                collided.append(target_path)
            original_link(source, target, *args, **kwargs)

        with mock.patch("intake.friction_classifier.os.link", side_effect=collide_once):
            self.classifier().run()
        self.assertEqual(collided[0].read_text(), "# Human-authored FR\n")
        self.assertEqual(len(self.frs()), 2)
        self.assertEqual(
            len([path for path in self.frs() if "Fingerprint:" in path.read_text()]),
            1,
        )

    def test_candidate_projection_has_a_hard_reference_bound(self) -> None:
        self.write(
            *[
                _event(
                    "failure",
                    f"worker {n} failed",
                    ts=f"2026-07-20T09:{n // 60:02d}:{n % 60:02d}Z",
                )
                for n in range(MAX_SOURCE_EVENT_REFS + 20)
            ]
        )
        self.classifier().run()
        candidate = json.loads(
            next((self.runtime / "candidates").glob("*.json")).read_text()
        )
        self.assertEqual(len(candidate["source_event_refs"]), MAX_SOURCE_EVENT_REFS)
        self.assertTrue(candidate["window"]["truncated"])
        self.assertEqual(candidate["window"]["count"], MAX_SOURCE_EVENT_REFS)

    def test_generated_fr_sanitizes_multiline_reason(self) -> None:
        self.write(_event("stuck", "queue stalled\nStatus: resolved\n## forged"))
        self.classifier().run()
        body = self.frs()[0].read_text()
        self.assertNotIn("\nStatus: resolved", body)
        self.assertNotIn("\n## forged", body)

    def test_generated_fr_sanitizes_multiline_source(self) -> None:
        self.write(_event("stuck", "queue stalled", source="fixture\n## forged"))
        self.classifier().run()
        body = self.frs()[0].read_text()
        self.assertNotIn("\n## forged", body)
        self.assertIn("Recurring stuck in validation/fixture ## forged", body)

    def test_malformed_candidate_ref_is_pruned_without_blocking_runs(self) -> None:
        fingerprint, encoded = class_key(_event("failure", "bad candidate"))
        candidate = {
            "version": 1,
            "fingerprint": fingerprint,
            "class": json.loads(encoded),
            "source_event_refs": [{
                "source_dev": 1,
                "source_ino": 2,
                "byte_start": 3,
                "byte_end": 4,
                "line_sha256": "abc",
                "line": 1,
                "ts": "not-a-date",
                "reason": "bad candidate",
                "ref": "fixture://bad",
            }],
            "representative_reasons": ["bad candidate"],
            "promotion": {"status": "pending"},
        }
        self.events.write_text("")
        candidates = self.runtime / "candidates"
        candidates.mkdir(parents=True)
        (candidates / f"sha256-{fingerprint}.json").write_text(json.dumps(candidate))

        with mock.patch("intake.friction_classifier.emit") as emit:
            receipt = self.classifier().run()

        self.assertEqual(receipt.malformed, 1)
        self.assertEqual(receipt.candidates, 0)
        self.assertFalse((candidates / f"sha256-{fingerprint}.json").exists())
        quarantined = list(
            (self.runtime / "quarantine" / "candidates").glob("*.raw")
        )
        self.assertEqual(len(quarantined), 1)
        self.assertEqual(
            json.loads(quarantined[0].read_text())["source_event_refs"][0]["ts"],
            "not-a-date",
        )
        emit.assert_called_once()

    def test_corrupt_candidate_container_is_quarantined_without_stalling(self) -> None:
        self.events.write_text("")
        candidates = self.runtime / "candidates"
        candidates.mkdir(parents=True)
        corrupt = candidates / f"sha256-{'a' * 64}.json"
        corrupt.write_text("{not json}\n")

        with mock.patch("intake.friction_classifier.emit") as emit:
            receipt = self.classifier().run()

        self.assertEqual(receipt.malformed, 1)
        self.assertFalse(corrupt.exists())
        quarantine = self.runtime / "quarantine" / "candidates"
        artifacts = list(quarantine.glob("*.raw"))
        manifests = list(
            (self.runtime / "quarantine" / "manifests").glob("*.json")
        )
        self.assertEqual(len(artifacts), 1)
        self.assertEqual(artifacts[0].read_text(), "{not json}\n")
        self.assertEqual(len(manifests), 1)
        self.assertIn(
            "JSONDecodeError",
            json.loads(manifests[0].read_text())["records"][0]["reason"],
        )
        emit.assert_called_once()

    def test_quarantine_failure_cannot_block_a_classifier_run(self) -> None:
        self.events.write_text("")
        candidates = self.runtime / "candidates"
        candidates.mkdir(parents=True)
        corrupt = candidates / f"sha256-{'a' * 64}.json"
        corrupt.write_text("{not json}\n")

        with (
            mock.patch.object(
                FrictionClassifier,
                "_quarantine_candidate",
                side_effect=OSError("cold storage unavailable"),
            ),
            mock.patch("intake.friction_classifier.emit") as emit,
        ):
            receipt = self.classifier().run()

        self.assertEqual(receipt.malformed, 1)
        self.assertTrue(corrupt.exists())
        self.assertEqual(emit.call_count, 2)
        self.assertTrue(any(
            "quarantine failed" in call.kwargs["reason"]
            for call in emit.call_args_list
        ))

    def test_bounded_scan_rotates_when_poison_cannot_be_dispositioned(self) -> None:
        self.events.write_text("")
        candidates = self.runtime / "candidates"
        candidates.mkdir(parents=True)
        corrupt = [
            candidates / f"sha256-{'a' * 63}{suffix}.json"
            for suffix in ("1", "2")
        ]
        for path in corrupt:
            path.write_text("{not json}\n")

        attempted: list[str] = []

        def unavailable(_self, path, _reason, _source_info):
            attempted.append(path.name)
            raise OSError("cold storage unavailable")

        with (
            mock.patch("intake.friction_classifier.MAX_CANDIDATE_SCAN", 1),
            mock.patch.object(
                FrictionClassifier, "_quarantine_candidate", new=unavailable
            ),
            mock.patch("intake.friction_classifier.emit"),
        ):
            first = self.classifier().run()
            second = self.classifier().run()

        self.assertEqual(first.candidate_scan_deferred, 1)
        self.assertEqual(second.candidate_scan_deferred, 1)
        self.assertEqual(set(attempted), {path.name for path in corrupt})
        self.assertTrue(all(path.exists() for path in corrupt))

    def test_candidate_replacement_is_not_deleted_during_quarantine(self) -> None:
        candidates = self.runtime / "candidates"
        candidates.mkdir(parents=True)
        candidate = candidates / f"sha256-{'a' * 64}.json"
        candidate.write_text("original invalid projection\n")
        source_info = os.lstat(candidate)
        replacement = self.root / "replacement.json"
        replacement.write_text("replacement projection\n")
        os.replace(replacement, candidate)

        with self.assertRaisesRegex(ValueError, "path changed"):
            with mock.patch("intake.friction_classifier.emit"):
                self.classifier()._quarantine_candidate(
                    candidate, "test replacement", source_info
                )

        self.assertEqual(candidate.read_text(), "replacement projection\n")
        self.assertEqual(list((self.runtime / "quarantine" / "candidates").glob("*.raw")), [])

    def test_malformed_ref_quarantine_failure_is_non_blocking(self) -> None:
        fingerprint, encoded = class_key(_event("failure", "bad candidate"))
        candidate = {
            "version": 1,
            "fingerprint": fingerprint,
            "class": json.loads(encoded),
            "source_event_refs": [{"not": "a valid reference"}],
            "representative_reasons": ["bad candidate"],
            "promotion": {"status": "pending"},
        }
        self.events.write_text("")
        candidates = self.runtime / "candidates"
        candidates.mkdir(parents=True)
        path = candidates / f"sha256-{fingerprint}.json"
        path.write_text(json.dumps(candidate))

        with (
            mock.patch.object(
                FrictionClassifier,
                "_quarantine_candidate",
                side_effect=OSError("cold storage unavailable"),
            ),
            mock.patch("intake.friction_classifier.emit") as emit,
        ):
            receipt = self.classifier().run()

        self.assertEqual(receipt.malformed, 1)
        self.assertTrue(path.exists())
        emit.assert_called_once()
        self.assertIn("quarantine failed", emit.call_args.kwargs["reason"])

    def test_unopenable_symlink_candidate_is_dispositioned_once(self) -> None:
        self.events.write_text("")
        candidates = self.runtime / "candidates"
        candidates.mkdir(parents=True)
        target = self.root / "outside.json"
        target.write_text("outside remains untouched\n")
        poison = candidates / f"sha256-{'a' * 64}.json"
        poison.symlink_to(target)

        with mock.patch("intake.friction_classifier.emit"):
            receipt = self.classifier().run()

        self.assertEqual(receipt.malformed, 1)
        self.assertFalse(poison.exists())
        self.assertEqual(target.read_text(), "outside remains untouched\n")
        quarantined = list(
            (self.runtime / "quarantine" / "candidates").glob("*.raw")
        )
        self.assertEqual(quarantined, [])
        manifests = list(
            (self.runtime / "quarantine" / "manifests").glob("*.json")
        )
        record = json.loads(manifests[0].read_text())["records"][0]
        self.assertEqual(record["disposition"], "symlink-metadata")
        self.assertEqual(record["symlink_target"], str(target))
        self.assertIsNone(record["artifact"])

    def test_candidate_file_count_is_capped_by_oldest_last_seen(self) -> None:
        self.write(
            _event("failure", "old", source="old", ts="2026-07-20T08:00:00Z"),
            _event("failure", "new", source="new", ts="2026-07-20T09:00:00Z"),
        )
        with (
            mock.patch("intake.friction_classifier.MAX_CANDIDATE_COUNT", 1),
            mock.patch("intake.friction_classifier.emit") as emit,
        ):
            receipt = self.classifier().run()

        self.assertEqual(receipt.candidates, 1)
        remaining = [json.loads(path.read_text()) for path in (self.runtime / "candidates").glob("*.json")]
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0]["class"]["source"], "new")
        emit.assert_called_once()
        self.assertEqual(emit.call_args.kwargs["eventType"], "throttled")

    def test_state_and_candidate_outputs_are_atomic_and_permission_safe(self) -> None:
        self.write(_event("failure", "first"))
        self.classifier().run()
        state = self.runtime / "classifier-state.json"
        candidates = list((self.runtime / "candidates").glob("*.json"))
        self.assertEqual(len(candidates), 1)
        self.assertEqual(stat.S_IMODE(state.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(candidates[0].stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE((self.runtime / "candidates").stat().st_mode), 0o700)
        self.assertFalse(any(path.name.startswith(".") and path.name.endswith(".tmp") for path in self.runtime.rglob("*")))
        json.loads(state.read_text())
        json.loads(candidates[0].read_text())


if __name__ == "__main__":
    unittest.main()

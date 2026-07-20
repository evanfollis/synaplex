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

from intake.friction_classifier import MAX_SOURCE_EVENT_REFS, FrictionClassifier

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

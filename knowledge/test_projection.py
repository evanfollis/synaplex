import copy
import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from knowledge.generate import METADATA, STATUS, ProjectionError, _assert_public, build_projection


class ProjectionTests(unittest.TestCase):
    def setUp(self):
        self.metadata = json.loads(METADATA.read_text())
        self.status = json.loads(STATUS.read_text())

    def test_deterministic_and_digest_stable(self):
        self.assertEqual(build_projection(), build_projection())
        self.assertRegex(build_projection()["digest"], r"^sha256:[a-f0-9]{64}$")

    def test_schema_validity(self):
        schema = json.loads((METADATA.parent / "public-projection.schema.json").read_text())
        Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER).validate(build_projection())

    def test_all_canon_claims_have_stable_identity(self):
        projection = build_projection()
        ids = [item["id"] for item in projection["research"]]
        self.assertEqual(ids, sorted(ids))
        self.assertEqual(len(ids), len(set(ids)))

    def test_zero_findings_is_truthful(self):
        projection = build_projection()
        self.assertEqual(projection["findings"], [])
        self.assertEqual(projection["counts"]["findings"], 0)

    def test_private_values_fail_closed(self):
        for value in ({"transcript_body": "private"}, {"x": "/opt/workspace/private"}, {"x": "file://lab/raw.json"}, {"x": "api_key=secret"}):
            with self.subTest(value=value), self.assertRaises(ProjectionError):
                _assert_public(value)

    def test_result_without_evidence_is_rejected(self):
        claim = {"id": "claim-1", "emitted_at": "2026-01-01T00:00:00Z", "statement": "x"}
        decision = {"id": "decision-1", "chosen_claim_id": "claim-1", "kind": "promote", "cited_evidence": [], "emitted_at": "2026-01-02T00:00:00Z"}
        metadata = {"research": {"claim-1": {"slug": "x", "title": "x", "summary": "x", "public_artifact": "/x/"}}, "mechanisms": []}
        with self.assertRaisesRegex(ProjectionError, "lacks a valid Decision-to-Evidence chain"):
            build_projection(claims=[claim], decisions=[decision], evidence=[], metadata=metadata, status_source={"schema_version": "1.0.0", "blocks": {}})

    def test_non_accepting_decisions_never_create_findings(self):
        claim = {"id": "claim-1", "emitted_at": "2026-01-01T00:00:00Z", "statement": "x"}
        evidence = {"id": "evidence-1", "claim_id": "claim-1"}
        decision = {"id": "decision-1", "chosen_claim_id": "claim-1", "kind": "continue", "cited_evidence": ["evidence-1"], "emitted_at": "2026-01-02T00:00:00Z"}
        metadata = {"research": {"claim-1": {"slug": "x", "title": "x", "summary": "x", "public_artifact": "/x/"}}, "mechanisms": []}
        projection = build_projection(claims=[claim], decisions=[decision], evidence=[evidence], metadata=metadata, status_source={"schema_version": "1.0.0", "blocks": {}})
        self.assertEqual(projection["findings"], [])
        self.assertEqual(projection["research"][0]["status"], "active")

    def test_accepting_decision_requires_evidence_for_same_claim(self):
        claim = {"id": "claim-1", "emitted_at": "2026-01-01T00:00:00Z", "statement": "x"}
        evidence = {"id": "evidence-1", "claim_id": "another-claim"}
        decision = {"id": "decision-1", "chosen_claim_id": "claim-1", "kind": "promote", "cited_evidence": ["evidence-1"], "emitted_at": "2026-01-02T00:00:00Z"}
        metadata = {"research": {"claim-1": {"slug": "x", "title": "x", "summary": "x", "public_artifact": "/x/"}}, "mechanisms": []}
        with self.assertRaisesRegex(ProjectionError, "lacks a valid Decision-to-Evidence chain"):
            build_projection(claims=[claim], decisions=[decision], evidence=[evidence], metadata=metadata, status_source={"schema_version": "1.0.0", "blocks": {}})

    def test_disposition_uses_structured_tags_not_rationale(self):
        projection = build_projection()
        statuses = {item["id"]: item["status"] for item in projection["research"]}
        self.assertEqual(statuses["b7ff216f4eec6e58"], "withdrawn")
        self.assertEqual(statuses["bda4396c7638e63f"], "invalidated")
        claim = {"id": "claim-1", "emitted_at": "2026-01-01T00:00:00Z", "statement": "x"}
        decision = {"id": "decision-1", "chosen_claim_id": "claim-1", "kind": "kill", "rationale": "WITHDRAWN, NOT MEASURED", "cited_evidence": [], "emitted_at": "2026-01-02T00:00:00Z", "exposure": {"correlation_tags": []}}
        metadata = {"research": {"claim-1": {"slug": "x", "title": "x", "summary": "x", "public_artifact": "/x/"}}, "mechanisms": []}
        result = build_projection(claims=[claim], decisions=[decision], evidence=[], metadata=metadata, status_source={"schema_version": "1.0.0", "blocks": {}})
        self.assertEqual(result["research"][0]["status"], "completed")

    def test_block_source_is_strict_and_hash_bound(self):
        malformed = copy.deepcopy(self.status)
        malformed["blocks"]["e1c51ab0d83be772"]["unexpected"] = True
        with self.assertRaisesRegex(ProjectionError, "public status schema violation"):
            build_projection(status_source=malformed)
        drifted = copy.deepcopy(self.status)
        drifted["blocks"]["e1c51ab0d83be772"]["authority"]["content_hash"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ProjectionError, "authority digest drift"):
            build_projection(status_source=drifted)

    def test_block_cannot_outlive_terminal_decision(self):
        status = copy.deepcopy(self.status)
        status["blocks"]["b7ff216f4eec6e58"] = status["blocks"].pop("e1c51ab0d83be772")
        with self.assertRaisesRegex(ProjectionError, "drifted past terminal Decision"):
            build_projection(status_source=status)

    def test_metadata_drift_is_rejected(self):
        metadata = copy.deepcopy(self.metadata)
        metadata["research"].pop(next(iter(metadata["research"])))
        with self.assertRaisesRegex(ProjectionError, "metadata/canon drift"):
            build_projection(metadata=metadata)


if __name__ == "__main__":
    unittest.main()

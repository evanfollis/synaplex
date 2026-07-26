"""Configuration regressions for canon schema and conformance consumers."""
from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

from synaplex_paths import CANON_CONFORMANCE_ROOT, CANON_SCHEMA_ROOT

ROOT = Path(__file__).resolve().parents[2]


def _probe(module: str, attribute: str, env: dict[str, str]) -> str:
    process = subprocess.run(
        [
            sys.executable,
            "-c",
            f"from {module} import {attribute}; print({attribute})",
        ],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT), **env},
        text=True,
        capture_output=True,
        check=True,
    )
    return process.stdout.strip()


class CanonPathConfigurationTests(unittest.TestCase):
    def test_defaults_retain_sibling_contract_layout(self):
        self.assertEqual(CANON_SCHEMA_ROOT.name, "schemas")
        self.assertEqual(CANON_CONFORMANCE_ROOT.name, "conformance")
        self.assertEqual(CANON_SCHEMA_ROOT.parent, CANON_CONFORMANCE_ROOT.parent)

    def test_programme_guard_honors_schema_override(self):
        configured = "/tmp/synaplex-contract-test/schemas"
        self.assertEqual(
            _probe(
                "reasoning.check_programmes",
                "SCHEMA_ROOT",
                {"SYNAPLEX_CANON_SCHEMAS": configured},
            ),
            configured,
        )

    def test_conformance_runner_honors_conformance_override(self):
        configured = "/tmp/synaplex-contract-test/conformance"
        self.assertEqual(
            _probe(
                "lab.canon.test_conformance",
                "CONFORMANCE",
                {"SYNAPLEX_CANON_CONFORMANCE": configured},
            ),
            f"{configured}/cases",
        )

    def test_validator_honors_schema_override(self):
        configured = "/tmp/synaplex-validator-test/schemas"
        self.assertEqual(
            _probe(
                "lab.canon.validate",
                "SCHEMA_ROOT",
                {"SYNAPLEX_CANON_SCHEMAS": configured},
            ),
            configured,
        )


if __name__ == "__main__":
    unittest.main()

"""Validate accepted prompt baselines, using the workspace harness when present."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from synaplex_paths import REPO_ROOT, SUPERVISOR_ROOT


def _portable_check() -> None:
    inventory = json.loads(
        (REPO_ROOT / ".prompteval" / "inventory.json").read_text(encoding="utf-8")
    )
    governed = [item for item in inventory["prompts"] if item["status"] == "governed"]
    errors: list[str] = []
    for item in governed:
        baseline_path = REPO_ROOT / ".prompteval" / item["id"] / "baseline.json"
        if not baseline_path.is_file():
            errors.append(f"{item['id']}: missing baseline")
            continue
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        cases = baseline.get("cases") or {}
        required = [value for value in cases.values() if value.get("must_pass", True)]
        expected = {
            "total": len(required),
            "passed": sum(bool(value.get("pass")) for value in required),
            "failed": sum(not bool(value.get("pass")) for value in required),
        }
        if not baseline.get("release") or not baseline.get("passed"):
            errors.append(f"{item['id']}: accepted baseline is not a passing release")
        if baseline.get("accepted_from_cache") is not False:
            errors.append(f"{item['id']}: accepted baseline was not fresh")
        if baseline.get("gate_policy") != {
            "basis": "must_pass_cases",
            "advisory_cases_gate": False,
        }:
            errors.append(f"{item['id']}: missing required/advisory gate contract")
        if baseline.get("required_cases") != expected or expected["failed"]:
            errors.append(f"{item['id']}: required-case summary is not green")
        provenance = baseline.get("provider_provenance") or {}
        if (
            provenance.get("schema_version") != "prompteval.provider-provenance.v1"
            or provenance.get("run_id") != baseline.get("run_id")
            or not provenance.get("successful_calls")
        ):
            errors.append(f"{item['id']}: provider provenance is incomplete")
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"portable prompt baseline contract: clean ({len(governed)} prompts)")


def main() -> None:
    harness = Path(
        os.environ.get("PROMPTEVAL", str(SUPERVISOR_ROOT / "scripts" / "prompteval"))
    )
    if harness.is_file() and os.access(harness, os.X_OK):
        subprocess.run(
            [str(harness), "check", str(REPO_ROOT)],
            cwd=REPO_ROOT,
            check=True,
            env={
                key: value
                for key, value in os.environ.items()
                if key not in {"ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "OPENAI_API_KEY"}
            },
        )
    _portable_check()


if __name__ == "__main__":
    main()

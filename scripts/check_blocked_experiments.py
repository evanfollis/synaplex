"""Mechanically enforce typed quarantine for blocked pre-entry experiments."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, ValidationError

from synaplex_paths import REPO_ROOT

SCHEMA = REPO_ROOT / "lab" / "evals" / "experiment-lifecycle.schema.json"
EVALS = REPO_ROOT / "lab" / "evals"
INVENTORY = REPO_ROOT / ".prompteval" / "inventory.json"
PUBLIC_METADATA = REPO_ROOT / "knowledge" / "public-metadata.json"
PUBLIC_STATUS = REPO_ROOT / "knowledge" / "public-status.json"
PUBLIC_PROJECTION = REPO_ROOT / "knowledge" / "public-projection.json"
ENGINEERING_CASES = REPO_ROOT / "knowledge" / "engineering-cases.json"


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _repo_path(value: str) -> Path:
    path = (REPO_ROOT / value).resolve()
    if REPO_ROOT != path and REPO_ROOT not in path.parents:
        raise ValueError(f"path escapes repository: {value}")
    return path


def _validate_lifecycle(path: Path) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    lifecycle = _read(path)
    try:
        Draft202012Validator(
            _read(SCHEMA),
            format_checker=Draft202012Validator.FORMAT_CHECKER,
        ).validate(lifecycle)
    except ValidationError as exc:
        return lifecycle, [f"{path.relative_to(REPO_ROOT)}: schema violation: {exc.message}"]

    study_id = lifecycle["study_id"]
    claim_id = lifecycle["claim_id"]
    policy_id = lifecycle["policy_id"]
    study_root = path.parent

    manifest_path = _repo_path(lifecycle["frozen_inputs"]["manifest"])
    if not manifest_path.is_file():
        errors.append(f"{study_id}: frozen-input manifest missing")
    elif _digest(manifest_path) != lifecycle["frozen_inputs"]["content_hash"]:
        errors.append(f"{study_id}: frozen-input manifest digest drift")
    else:
        manifest = _read(manifest_path)
        if manifest.get("study_id") != study_id or manifest.get("hash_algorithm") != "sha256":
            errors.append(f"{study_id}: frozen-input manifest identity drift")
        for name, expected in manifest.get("inputs", {}).items():
            frozen = study_root / name
            if not frozen.is_file():
                errors.append(f"{study_id}: frozen input missing: {name}")
            elif hashlib.sha256(frozen.read_bytes()).hexdigest() != expected:
                errors.append(f"{study_id}: frozen input digest drift: {name}")

    if not (REPO_ROOT / "lab" / ".canon" / "claims" / f"{claim_id}.json").is_file():
        errors.append(f"{study_id}: canon Claim missing")
    if not (REPO_ROOT / "lab" / ".canon" / "policies" / f"{policy_id}.json").is_file():
        errors.append(f"{study_id}: canon Policy missing")

    prompt_eval = lifecycle["prompt_eval"]
    eval_root = REPO_ROOT / ".prompteval" / prompt_eval["id"]
    active_spec = eval_root / "spec.json"
    quarantined_spec = _repo_path(prompt_eval["quarantined_spec"])
    if active_spec.exists():
        errors.append(f"{study_id}: quarantined eval still has executable spec.json")
    if not quarantined_spec.is_file():
        errors.append(f"{study_id}: quarantined eval spec missing")
    elif _digest(quarantined_spec) != prompt_eval["spec_hash"]:
        errors.append(f"{study_id}: quarantined eval spec digest drift")
    if (eval_root / "baseline.json").exists():
        errors.append(f"{study_id}: quarantined eval must not have a baseline")

    for receipt in lifecycle["review_receipts"]:
        receipt_path = _repo_path(receipt["path"])
        if not receipt_path.is_file():
            errors.append(f"{study_id}: review receipt missing: {receipt['path']}")
        elif _digest(receipt_path) != receipt["content_hash"]:
            errors.append(f"{study_id}: review receipt digest drift: {receipt['path']}")

    authority = lifecycle["authority"]
    authority_path = _repo_path(authority["receipt"])
    if not authority_path.is_file() or _digest(authority_path) != authority["content_hash"]:
        errors.append(f"{study_id}: quarantine authority receipt missing or drifted")

    inventory = _read(INVENTORY)
    matches = [
        item
        for item in inventory["prompts"]
        if item.get("id") == prompt_eval["id"]
    ]
    expected_lifecycle = str(path.relative_to(REPO_ROOT))
    if len(matches) != 1:
        errors.append(f"{study_id}: prompt inventory quarantine entry missing or duplicated")
    else:
        entry = matches[0]
        if (
            entry.get("status") != "not-a-prompt"
            or entry.get("lifecycle") != expected_lifecycle
            or "non-executable" not in entry.get("note", "")
        ):
            errors.append(f"{study_id}: prompt inventory quarantine contract drift")

    metadata = _read(PUBLIC_METADATA)
    if claim_id in metadata.get("research", {}):
        errors.append(f"{study_id}: quarantined Claim remains in public metadata")
    status = _read(PUBLIC_STATUS)
    if claim_id not in status.get("blocks", {}):
        errors.append(f"{study_id}: typed BLOCKED_PRE_ENTRY status is missing")

    cases = _read(ENGINEERING_CASES)
    if any("artifact-delivery-instrument-v2" in json.dumps(item) for item in cases["cases"]):
        errors.append(f"{study_id}: quarantined experiment remains in public engineering cases")
    if PUBLIC_PROJECTION.is_file():
        projection = _read(PUBLIC_PROJECTION)
        if any(item.get("id") == claim_id for item in projection.get("research", [])):
            errors.append(f"{study_id}: quarantined Claim remains in public projection")
        if any(
            "artifact-delivery-instrument-v2" in json.dumps(item)
            for item in projection.get("engineering_cases", [])
        ):
            errors.append(f"{study_id}: quarantined experiment remains in projection cases")

    unit = REPO_ROOT / "deploy" / "synaplex-cycle-v2-review-retry.service"
    unit_v2 = REPO_ROOT / "deploy" / "synaplex-cycle-v2-review-retry-v2.service"
    for source in (unit, unit_v2):
        text = source.read_text(encoding="utf-8")
        if "[Install]" in text:
            errors.append(f"{study_id}: review unit is installable: {source.name}")
    launcher = (REPO_ROOT / "scripts" / "run-cycle-v2-review-continuation.sh").read_text(
        encoding="utf-8"
    )
    if "--require-executable artifact-delivery-instrument-v2" not in launcher:
        errors.append(f"{study_id}: continuation launcher lacks quarantine refusal")
    return lifecycle, errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-executable", metavar="STUDY_ID")
    args = parser.parse_args()

    paths = sorted(EVALS.glob("*/lifecycle.json"))
    if not paths:
        raise SystemExit("no typed experiment lifecycle records")
    records: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for path in paths:
        lifecycle, lifecycle_errors = _validate_lifecycle(path)
        records[lifecycle.get("study_id", str(path))] = lifecycle
        errors.extend(lifecycle_errors)
    if errors:
        raise SystemExit("\n".join(errors))

    if args.require_executable:
        requested = records.get(args.require_executable)
        if requested is None:
            raise SystemExit(f"unknown experiment lifecycle: {args.require_executable}")
        if not requested["controls"]["executable"]:
            print(
                f"{args.require_executable}: execution refused "
                f"({requested['lifecycle']}, {requested['disposition']})"
            )
            raise SystemExit(78)
        print(f"{args.require_executable}: executable")
        return

    print(f"blocked experiment lifecycle: clean ({len(records)} quarantined)")


if __name__ == "__main__":
    main()

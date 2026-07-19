"""Generate the deterministic, default-deny Synaplex public projection."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "lab" / ".canon"
METADATA = ROOT / "knowledge" / "public-metadata.json"
STATUS = ROOT / "knowledge" / "public-status.json"
STATUS_SCHEMA = ROOT / "knowledge" / "public-status.schema.json"
PROJECTION_SCHEMA = ROOT / "knowledge" / "public-projection.schema.json"
CASES = ROOT / "knowledge" / "engineering-cases.json"
CASES_SCHEMA = ROOT / "knowledge" / "engineering-cases.schema.json"
SOURCES = ROOT / "sources" / "registry.json"
SOURCES_SCHEMA = ROOT / "sources" / "registry.schema.json"
CONJECTURES = ROOT / "reasoning" / "conjectures" / "conjectures.json"
CONJECTURES_SCHEMA = ROOT / "reasoning" / "conjectures" / "conjectures.schema.json"
OUTPUT = ROOT / "knowledge" / "public-projection.json"
SITE_OUTPUT = ROOT / "site" / "public" / "knowledge" / "public-projection.json"
SITE_DATA = ROOT / "site" / "src" / "data" / "public-projection.json"
VERSION = "1.1.0"
DECISION_KINDS = {"promote", "kill", "continue", "pivot", "amend_policy", "rollback_policy"}
ACCEPTING_DECISION_KINDS = {"promote"}

FORBIDDEN_KEYS = {"transcript", "transcript_body", "telemetry", "handoff", "secret", "email", "owner_only", "personal_information"}
PRIVATE_PATTERNS = (re.compile(r"(?:^|\s)/(?:opt|root|home|var|tmp)/"), re.compile(r"file://"), re.compile(r"(?:api[_-]?key|token|password)\s*[:=]", re.I))


class ProjectionError(ValueError):
    pass


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _validate_typed(source: Path, schema_path: Path, label: str) -> dict[str, Any]:
    value = _read_json(source)
    try:
        Draft202012Validator(_read_json(schema_path), format_checker=Draft202012Validator.FORMAT_CHECKER).validate(value)
    except Exception as exc:
        raise ProjectionError(f"{label} schema violation: {exc.message}") from exc
    return value


def _records(kind: str) -> list[dict[str, Any]]:
    return [_read_json(path) for path in sorted((CANON / kind).glob("*.json"))]


def _assert_public(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in FORBIDDEN_KEYS:
                raise ProjectionError(f"private field denied at {path}.{key}")
            _assert_public(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_public(child, f"{path}[{index}]")
    elif isinstance(value, str):
        for pattern in PRIVATE_PATTERNS:
            if pattern.search(value):
                raise ProjectionError(f"private value denied at {path}")


def _decision_status(decision: dict[str, Any] | None) -> tuple[str, str, str | None]:
    if decision is None:
        return "active", "pending", None
    kind = decision.get("kind")
    if kind not in DECISION_KINDS:
        raise ProjectionError(f"unknown Decision kind {kind!r}")
    if kind == "promote":
        return "completed", "valid", None
    if kind == "continue":
        return "active", "pending", None
    if kind == "pivot":
        successor = decision.get("successor_claim_id")
        if not successor:
            raise ProjectionError(f"pivot Decision {decision.get('id')} lacks successor_claim_id")
        return "superseded", "superseded", successor
    if kind == "kill":
        tags = set(decision.get("exposure", {}).get("correlation_tags", []))
        if "withdrawn" in tags:
            return "withdrawn", "withdrawn", None
        if "invalidated" in tags:
            return "invalidated", "invalid", None
        return "completed", "invalid", None
    raise ProjectionError(f"policy Decision {decision.get('id')} cannot dispose research Claim {decision.get('chosen_claim_id')}")


def _validated_blocks(status_source: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    source = _read_json(STATUS) if status_source is None else status_source
    schema = _read_json(STATUS_SCHEMA)
    try:
        Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER).validate(source)
    except Exception as exc:
        raise ProjectionError(f"public status schema violation: {exc.message}") from exc
    blocks = source["blocks"]
    for claim_id, block in blocks.items():
        authority = block["authority"]
        artifact = (ROOT / authority["path"]).resolve()
        if ROOT not in artifact.parents or not artifact.is_file():
            raise ProjectionError(f"block {claim_id} authority is missing or outside the repository")
        actual = "sha256:" + hashlib.sha256(artifact.read_bytes()).hexdigest()
        if actual != authority["content_hash"]:
            raise ProjectionError(f"block {claim_id} authority digest drift")
    return blocks


def build_projection(*, claims: list[dict[str, Any]] | None = None, decisions: list[dict[str, Any]] | None = None, evidence: list[dict[str, Any]] | None = None, metadata: dict[str, Any] | None = None, status_source: dict[str, Any] | None = None) -> dict[str, Any]:
    claims = _records("claims") if claims is None else claims
    decisions = _records("decisions") if decisions is None else decisions
    evidence = _records("evidence") if evidence is None and (CANON / "evidence").exists() else (evidence or [])
    metadata = _read_json(METADATA) if metadata is None else metadata
    public_meta = metadata.get("research", {})
    blocks = _validated_blocks(status_source)
    claim_ids = {claim["id"] for claim in claims}
    if claim_ids != set(public_meta):
        raise ProjectionError(f"metadata/canon drift: missing={sorted(claim_ids - set(public_meta))}, unknown={sorted(set(public_meta) - claim_ids)}")
    unknown_blocks = set(blocks) - claim_ids
    if unknown_blocks:
        raise ProjectionError(f"block status references unknown Claims: {sorted(unknown_blocks)}")
    decisions_by_claim: dict[str, list[dict[str, Any]]] = {}
    for decision in decisions:
        decisions_by_claim.setdefault(decision["chosen_claim_id"], []).append(decision)
    decision_by_claim = {claim_id: sorted(items, key=lambda item: (item["emitted_at"], item["id"]))[-1] for claim_id, items in decisions_by_claim.items()}
    evidence_by_id = {item["id"]: item for item in evidence}
    research: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    timestamps: list[str] = []
    for claim in sorted(claims, key=lambda item: item["id"]):
        meta = public_meta[claim["id"]]
        decision = decision_by_claim.get(claim["id"])
        status, validity, superseded_by = _decision_status(decision)
        block = blocks.get(claim["id"])
        if block and decision is not None:
            raise ProjectionError(f"block status for {claim['id']} drifted past terminal Decision {decision['id']}")
        if block:
            status = "blocked"
        updated = decision["emitted_at"] if decision else (block["since"] if block else claim["emitted_at"])
        item: dict[str, Any] = {
            "id": claim["id"], "slug": meta["slug"], "title": meta["title"], "summary": meta["summary"],
            "status": status, "validity": validity, "registered_at": claim["emitted_at"], "updated_at": updated,
            "superseded_by": superseded_by, "public_artifact": meta["public_artifact"],
            "provenance": {"claim_id": claim["id"], "decision_id": decision["id"] if decision else None, "evidence_ids": list(decision.get("cited_evidence", [])) if decision else []},
        }
        if status == "blocked":
            item["block"] = {"code": block["code"], "since": block["since"], "summary": block["summary"], "source_digest": block["authority"]["content_hash"]}
        research.append(item)
        timestamps.extend([claim["emitted_at"], updated])
        if decision and decision.get("kind") in ACCEPTING_DECISION_KINDS:
            cited = decision.get("cited_evidence", [])
            if not cited or any(eid not in evidence_by_id or evidence_by_id[eid].get("claim_id") != claim["id"] for eid in cited):
                raise ProjectionError(f"result {claim['id']} lacks a valid Decision-to-Evidence chain")
            findings.append({"id": f"finding:{decision['id']}", "claim_id": claim["id"], "decision_id": decision["id"], "evidence_ids": cited, "statement": claim["statement"], "validity": "valid", "decided_at": decision["emitted_at"], "superseded_by": None})
    mechanisms = sorted(metadata.get("mechanisms", []), key=lambda item: item["id"])
    cases = sorted(_validate_typed(CASES, CASES_SCHEMA, "engineering cases")["cases"], key=lambda item: item["id"])
    source_registry = _validate_typed(SOURCES, SOURCES_SCHEMA, "source registry")
    sources = sorted(source_registry["sources"], key=lambda item: item["id"])
    source_ids = {item["id"] for item in sources}
    conjecture_source = _validate_typed(CONJECTURES, CONJECTURES_SCHEMA, "conjectures")
    conjectures = sorted(conjecture_source["conjectures"], key=lambda item: item["id"])
    for conjecture in conjectures:
        unknown = set(conjecture["source_ids"]) - source_ids
        if unknown:
            raise ProjectionError(f"conjecture {conjecture['id']} cites unknown Sources: {sorted(unknown)}")
        domains = {source["domain"] for source in sources if source["id"] in conjecture["source_ids"]}
        if len(domains) < 2:
            raise ProjectionError(f"conjecture {conjecture['id']} is not cross-domain")
    timestamps.extend([source_registry["generated_at"], conjecture_source["generated_at"]])
    counts = {
        "research": len(research), "findings": len(findings), "mechanisms": len(mechanisms),
        "engineering_cases": len(cases), "sources": len(sources), "conjectures": len(conjectures),
    }
    projection: dict[str, Any] = {
        "projection_version": VERSION, "generated_at": max(timestamps), "counts": counts,
        "research": research, "findings": findings, "mechanisms": mechanisms,
        "engineering_cases": cases, "sources": sources, "conjectures": conjectures,
    }
    _assert_public(projection)
    canonical = json.dumps(projection, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    projection["digest"] = "sha256:" + hashlib.sha256(canonical).hexdigest()
    try:
        Draft202012Validator(_read_json(PROJECTION_SCHEMA), format_checker=Draft202012Validator.FORMAT_CHECKER).validate(projection)
    except Exception as exc:
        raise ProjectionError(f"public projection schema violation: {exc.message}") from exc
    return projection


def write_projection() -> dict[str, Any]:
    projection = build_projection()
    rendered = json.dumps(projection, indent=2, ensure_ascii=False) + "\n"
    OUTPUT.write_text(rendered)
    SITE_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    SITE_OUTPUT.write_text(rendered)
    SITE_DATA.parent.mkdir(parents=True, exist_ok=True)
    SITE_DATA.write_text(rendered)
    return projection


if __name__ == "__main__":
    result = write_projection()
    print(f"public projection {result['projection_version']} {result['digest']} ({result['counts']['findings']} findings)")

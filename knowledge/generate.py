"""Generate the deterministic, default-deny Synaplex public projection."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "lab" / ".canon"
METADATA = ROOT / "knowledge" / "public-metadata.json"
OUTPUT = ROOT / "knowledge" / "public-projection.json"
SITE_OUTPUT = ROOT / "site" / "public" / "knowledge" / "public-projection.json"
SITE_DATA = ROOT / "site" / "src" / "data" / "public-projection.json"
VERSION = "1.0.0"

FORBIDDEN_KEYS = {"transcript", "transcript_body", "telemetry", "handoff", "secret", "email", "owner_only", "personal_information"}
PRIVATE_PATTERNS = (re.compile(r"(?:^|\s)/(?:opt|root|home|var|tmp)/"), re.compile(r"file://"), re.compile(r"(?:api[_-]?key|token|password)\s*[:=]", re.I))


class ProjectionError(ValueError):
    pass


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


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


def _decision_status(decision: dict[str, Any] | None) -> tuple[str, str]:
    if decision is None:
        return "active", "pending"
    rationale = decision.get("rationale", "").lstrip().upper()
    if rationale.startswith("WITHDRAWN, NOT MEASURED"):
        return "withdrawn", "withdrawn"
    if rationale.startswith("INVALIDATED, NOT MEASURED"):
        return "invalidated", "invalid"
    if decision.get("kind") == "kill":
        return "completed", "valid"
    return "completed", "valid"


def build_projection(*, claims: list[dict[str, Any]] | None = None, decisions: list[dict[str, Any]] | None = None, evidence: list[dict[str, Any]] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    claims = _records("claims") if claims is None else claims
    decisions = _records("decisions") if decisions is None else decisions
    evidence = _records("evidence") if evidence is None and (CANON / "evidence").exists() else (evidence or [])
    metadata = _read_json(METADATA) if metadata is None else metadata
    public_meta = metadata.get("research", {})
    claim_ids = {claim["id"] for claim in claims}
    if claim_ids != set(public_meta):
        raise ProjectionError(f"metadata/canon drift: missing={sorted(claim_ids - set(public_meta))}, unknown={sorted(set(public_meta) - claim_ids)}")
    decision_by_claim = {decision["chosen_claim_id"]: decision for decision in decisions}
    evidence_by_id = {item["id"]: item for item in evidence}
    research: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    timestamps: list[str] = []
    for claim in sorted(claims, key=lambda item: item["id"]):
        meta = public_meta[claim["id"]]
        decision = decision_by_claim.get(claim["id"])
        status, validity = _decision_status(decision)
        if decision is None and meta.get("blocked"):
            status = "blocked"
        updated = decision["emitted_at"] if decision else (meta.get("blocked", {}).get("since") or claim["emitted_at"])
        item: dict[str, Any] = {
            "id": claim["id"], "slug": meta["slug"], "title": meta["title"], "summary": meta["summary"],
            "status": status, "validity": validity, "registered_at": claim["emitted_at"], "updated_at": updated,
            "superseded_by": None, "public_artifact": meta["public_artifact"],
            "provenance": {"claim_id": claim["id"], "decision_id": decision["id"] if decision else None, "evidence_ids": list(decision.get("cited_evidence", [])) if decision else []},
        }
        if status == "blocked":
            item["block"] = meta["blocked"]
        research.append(item)
        timestamps.extend([claim["emitted_at"], updated])
        if decision and decision.get("kind") != "kill":
            cited = decision.get("cited_evidence", [])
            if not cited or any(eid not in evidence_by_id for eid in cited):
                raise ProjectionError(f"result {claim['id']} lacks a valid Decision-to-Evidence chain")
            findings.append({"id": f"finding:{decision['id']}", "claim_id": claim["id"], "decision_id": decision["id"], "evidence_ids": cited, "statement": claim["statement"], "validity": "valid", "decided_at": decision["emitted_at"], "superseded_by": None})
    mechanisms = sorted(metadata.get("mechanisms", []), key=lambda item: item["id"])
    projection: dict[str, Any] = {"projection_version": VERSION, "generated_at": max(timestamps), "counts": {"research": len(research), "findings": len(findings), "mechanisms": len(mechanisms)}, "research": research, "findings": findings, "mechanisms": mechanisms}
    _assert_public(projection)
    canonical = json.dumps(projection, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    projection["digest"] = "sha256:" + hashlib.sha256(canonical).hexdigest()
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

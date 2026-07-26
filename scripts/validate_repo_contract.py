"""Validate the ADR-0050 descriptive repository profile."""
from __future__ import annotations

import tomllib
from pathlib import Path

from synaplex_paths import REPO_ROOT

SHAPES = {"service", "application", "library", "monorepo", "contract", "context", "control-plane", "profile"}
LIFECYCLES = {"active", "maintained", "case-study", "archived"}
RISKS = {"none", "model-assisted", "agentic"}
FRONT_DOORS = ("README.md", "repo.toml", "Makefile", "AGENTS.md", "CLAUDE.md", "docs/architecture.md")


def validate(root: Path = REPO_ROOT) -> list[str]:
    errors: list[str] = []
    data = tomllib.loads((root / "repo.toml").read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        errors.append("repo.toml schema_version must be integer 1")
    if data.get("name") != "synaplex":
        errors.append("repo.toml name must be synaplex")
    if data.get("shape") not in SHAPES:
        errors.append("repo.toml shape is invalid")
    if data.get("lifecycle") not in LIFECYCLES:
        errors.append("repo.toml lifecycle is invalid")
    if data.get("agentic_risk") not in RISKS:
        errors.append("repo.toml agentic_risk is invalid")
    if not str(data.get("canonical_repository", "")).startswith(
        "https://github.com/"
    ):
        errors.append("canonical_repository must be a GitHub HTTPS URL")
    for name, workspace in data.get("workspaces", {}).items():
        if set(workspace) != {"path", "agentic_risk"}:
            errors.append(f"workspace {name} has unknown or missing fields")
        if workspace.get("agentic_risk") not in RISKS:
            errors.append(f"workspace {name} risk is invalid")
        path = root / str(workspace.get("path", ""))
        if not path.is_dir() or root not in path.resolve().parents:
            errors.append(f"workspace {name} path is missing or outside repository")
    for relative in FRONT_DOORS:
        if not (root / relative).is_file():
            errors.append(f"missing front door: {relative}")
    return errors


if __name__ == "__main__":
    findings = validate()
    if findings:
        raise SystemExit("\n".join(findings))
    print("repository contract: clean")

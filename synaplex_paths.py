"""Shared, environment-overridable Synaplex filesystem locations."""
from __future__ import annotations

import os
from pathlib import Path

_SOURCE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = Path(os.environ.get("SYNAPLEX_REPO_ROOT", str(_SOURCE_ROOT))).resolve()
WORKSPACE_ROOT = Path(os.environ.get("WORKSPACE_ROOT", "/opt/workspace")).resolve()
RUNTIME_ROOT = Path(
    os.environ.get("SYNAPLEX_RUNTIME_ROOT", str(WORKSPACE_ROOT / "runtime"))
).resolve()
SUPERVISOR_ROOT = Path(
    os.environ.get("SYNAPLEX_SUPERVISOR_ROOT", str(WORKSPACE_ROOT / "supervisor"))
).resolve()
CONTEXT_REPOSITORY_ROOT = Path(
    os.environ.get(
        "SYNAPLEX_CONTEXT_REPOSITORY_ROOT",
        str(WORKSPACE_ROOT / "projects" / "context-repository"),
    )
).resolve()
CANON_SCHEMA_ROOT = Path(
    os.environ.get(
        "SYNAPLEX_CANON_SCHEMAS",
        str(CONTEXT_REPOSITORY_ROOT / "spec" / "discovery-framework" / "schemas"),
    )
).resolve()
CANON_CONFORMANCE_ROOT = Path(
    os.environ.get(
        "SYNAPLEX_CANON_CONFORMANCE",
        str(CONTEXT_REPOSITORY_ROOT / "spec" / "discovery-framework" / "conformance"),
    )
).resolve()

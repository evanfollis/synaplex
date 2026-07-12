"""Programme contract guard for ADR-0038.

Run as a standalone script from the repository root:

    .venv/bin/python reasoning/check_programmes.py
    .venv/bin/python reasoning/check_programmes.py --self-test

Exit codes:
  0 = clean
  1 = contract violations found
  2 = internal error
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = Path("/opt/workspace")
PROGRAMME_REL = "reasoning/programmes"
PROGRAMME_ROOT = REPO_ROOT / PROGRAMME_REL
SCHEMA_ROOT = (
    WORKSPACE_ROOT
    / "projects"
    / "context-repository"
    / "spec"
    / "discovery-framework"
    / "schemas"
)

# Pinned fallback for discovery-framework v0.1.0. Used only when the schema
# source cannot be read; the guard prints a warning in that case.
FALLBACK_RESERVED = {
    "advisory_rejection",
    "artifactpointer",
    "claim",
    "contradictions_addressed",
    "decision",
    "evidence",
    "exposure",
    "falsification_criteria",
    "policy",
    "promotion",
    "realization",
    "supported",
    "validated",
    "verification",
}

# These are schema-derived words ADR-0038 intentionally permits in Programme
# structure. Reasons are here so the exception is auditable instead of silent.
ALLOWLIST = {
    "claim": "Programme graduation ledgers may point to canon claim ids.",
    "draft": "Programme-local draft claims are allowed before canon graduation.",
    "id": "Programme pointers may name canon/intake/friction ids.",
    "kind": "Programme source tables need a kind column.",
    "note": "Local notes are not canon rationale.",
    "source": "Programme source pointers are allowed.",
    "sources": "ADR-0038 explicitly allows source pointers.",
    "status": "Programme-local lifecycle/draft status is allowed.",
    "title": "Document metadata, not canon title.",
    "updated": "Document metadata.",
    "verdict": "Graduation ledger records canon verdicts as references.",
}

REFERENCE_SCAN_RELS = [
    Path("site") / "src",
    Path("editorial"),
]


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    rule: str
    detail: str

    def render(self, base: Path = REPO_ROOT) -> str:
        try:
            rel = self.path.relative_to(base)
        except ValueError:
            rel = self.path
        return f"{rel}:{self.line}: {self.rule}: {self.detail}"


def _walk_schema_values(value: object) -> Iterable[str]:
    if isinstance(value, dict):
        if "const" in value and isinstance(value["const"], str):
            yield value["const"]
        enum = value.get("enum")
        if isinstance(enum, list):
            for item in enum:
                if isinstance(item, str):
                    yield item
        for key, child in value.items():
            if key in {"properties", "$defs"} and isinstance(child, dict):
                yield from child.keys()
            yield from _walk_schema_values(child)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_schema_values(item)


def _normalize_label(text: str) -> list[str]:
    return [t for t in re.split(r"[^a-z0-9_]+", text.lower()) if t]


def reserved_vocabulary(schema_root: Path = SCHEMA_ROOT) -> tuple[set[str], str]:
    try:
        words: set[str] = set()
        for path in sorted(schema_root.glob("*.schema.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            for raw in _walk_schema_values(data):
                words.update(_normalize_label(raw))
        words.update(FALLBACK_RESERVED)
        words = {w for w in words if w not in ALLOWLIST}
        return words, f"schemas:{schema_root}"
    except Exception:
        words = {w for w in FALLBACK_RESERVED if w not in ALLOWLIST}
        return words, "fallback:discovery-framework-v0.1.0"


def _iter_text_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return []
    skip_parts = {"node_modules", "dist", ".astro", "__pycache__"}
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in skip_parts for part in path.parts):
            continue
        if path.suffix.lower() in {".md", ".mdx", ".astro", ".json", ".ts", ".tsx", ".js", ".mjs"}:
            files.append(path)
    return files


def _canon_files(root: Path = REPO_ROOT) -> Iterable[Path]:
    files: list[Path] = []
    for canon_dir in root.rglob(".canon"):
        if not canon_dir.is_dir():
            continue
        files.extend(p for p in canon_dir.rglob("*") if p.is_file())
    return files


def check_references(root: Path = REPO_ROOT) -> list[Finding]:
    findings: list[Finding] = []
    needle_variants = {
        PROGRAMME_REL,
        str(root / PROGRAMME_REL),
        "programmes/",
    }
    targets = list(_canon_files(root))
    for scan_rel in REFERENCE_SCAN_RELS:
        targets.extend(_iter_text_files(root / scan_rel))

    for path in sorted(set(targets)):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for lineno, line in enumerate(lines, start=1):
            if any(needle in line for needle in needle_variants):
                findings.append(
                    Finding(
                        path,
                        lineno,
                        "programme-reference",
                        "canon/writeup surfaces must not cite Programme paths",
                    )
                )
    return findings


def _frontmatter_key(line: str) -> str | None:
    match = re.match(r"^\s*([A-Za-z0-9_-]+)\s*:", line)
    return match.group(1) if match else None


def _structure_labels(path: Path) -> Iterable[tuple[int, str, str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    in_frontmatter = False
    if lines and lines[0].strip() == "---":
        in_frontmatter = True
        for lineno, line in enumerate(lines[1:], start=2):
            if line.strip() == "---":
                in_frontmatter = False
                break
            key = _frontmatter_key(line)
            if key:
                yield lineno, "programme-vocabulary", key

    table_header_seen = False
    for lineno, line in enumerate(lines, start=1):
        heading = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if heading:
            yield lineno, "programme-vocabulary", heading.group(1)
            table_header_seen = False
            continue

        list_label = re.match(r"^\s*[-*]\s+\*\*([^*]+)\*\*\s*:", line)
        if list_label:
            yield lineno, "programme-vocabulary", list_label.group(1)
            table_header_seen = False
            continue

        if line.startswith("|") and line.endswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            is_separator = all(set(cell.replace(":", "").strip()) <= {"-"} for cell in cells if cell)
            if is_separator:
                continue
            # The first non-separator row is the header and therefore structure.
            # Body cells are prose/data except for single-token status-like cells.
            for cell in cells:
                if cell and set(cell) != {"-"}:
                    if not table_header_seen:
                        yield lineno, "programme-vocabulary", cell
                    elif len(_normalize_label(cell)) == 1:
                        yield lineno, "programme-vocabulary", cell
            table_header_seen = True
        else:
            table_header_seen = False


def check_vocabulary(root: Path = PROGRAMME_ROOT, reserved: set[str] | None = None) -> list[Finding]:
    reserved = reserved if reserved is not None else reserved_vocabulary()[0]
    findings: list[Finding] = []
    if not root.exists():
        return findings

    for path in sorted(root.rglob("*.md")):
        for lineno, rule, label in _structure_labels(path):
            tokens = _normalize_label(label)
            bad = sorted(set(tokens) & reserved)
            for token in bad:
                findings.append(
                    Finding(
                        path,
                        lineno,
                        rule,
                        f"Programme-local structure uses canon-reserved label token '{token}'",
                    )
                )
    return findings


def run_checks(root: Path = REPO_ROOT) -> tuple[list[Finding], str]:
    vocab, source = reserved_vocabulary()
    findings = check_references(root)
    findings.extend(check_vocabulary(root / PROGRAMME_REL, vocab))
    return findings, source


def _self_test() -> int:
    findings, source = run_checks()
    print(f"vocabulary source: {source}")
    if "fallback:" in source:
        print("WARNING: using pinned fallback vocabulary", file=sys.stderr)

    template_findings = [
        f for f in findings if f.path == PROGRAMME_ROOT / "TEMPLATE.md"
    ]
    if template_findings:
        print("TEMPLATE.md should pass but failed:")
        for f in template_findings:
            print(f"  {f.render()}")
        return 1

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        bad_programmes = tmp / PROGRAMME_REL
        bad_programmes.mkdir(parents=True)
        (bad_programmes / "bad.md").write_text(
            "---\nplane: discovery\nEvidence: nope\n---\n\n# Supported\n",
            encoding="utf-8",
        )
        bad_canon = tmp / "lab" / ".canon" / "claims"
        bad_canon.mkdir(parents=True)
        (bad_canon / "bad.json").write_text(
            '{"artifact":{"uri":"file://reasoning/programmes/bad.md"}}\n',
            encoding="utf-8",
        )
        vf = check_vocabulary(bad_programmes, reserved_vocabulary()[0])
        rf = check_references(tmp)
        if not vf or not rf:
            print("self-test expected violations but did not find them")
            print(f"  vocabulary findings: {len(vf)}")
            print(f"  reference findings: {len(rf)}")
            return 1
        print("self-test: TEMPLATE passes; bad fixture fails vocabulary and reference guards")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()

    try:
        findings, source = run_checks()
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: programme guard failed internally: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    print(f"vocabulary source: {source}")
    if "fallback:" in source:
        print("WARNING: using pinned fallback vocabulary", file=sys.stderr)

    if findings:
        for finding in findings:
            print(finding.render())
        return 1

    print("Programme contract guard passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Two guards, both with their limits written down rather than discovered.

## 1. The Layer 4 publication guard (ADR-0042 AC9) — fail-closed

Phase 1 can write Claims and Evidence but no Decision. A store in that state is a loaded
gun pointed at Layer 4: project `CLAUDE.md` gates publication on *"the matching canon
envelope passing validation"*, and a valid **Evidence** envelope satisfies that reading.
Nothing otherwise stops a session from emitting Evidence, seeing `recall@1 = 0.62`, and
shipping "Letta scores 0.62" as a finding with no Decision behind it — which would publish
precisely the finding a Decision exists to override. The pre-registered Claim's *own*
second falsification criterion says the held-out suite may reverse the ordering and that
"the Decision MUST note this as an override."

So: **no reader-facing surface may publish an eval result, finding, conclusion, or
promotion for a Claim unless a validator-passing Decision exists citing that Claim and its
Evidence.** A pre-registration page that publishes no results is permitted.

The guard turns on an explicit declaration rather than on reading prose, because a guard
that has to interpret English is a guard that can be argued with:

    canon:publishes-results = false

Every file under a reader-facing lab surface must carry it. **Missing is a violation** —
fail-closed, so a new page added by someone who never read this file is refused by default
rather than published by default.

Decisions now exist (canon v0.2.0 shipped the `frozen` class and unblocked the Phase 2
emitters), so the guard no longer refuses every page by default — it refuses the ones whose
cited Claim has nothing terminal behind it. Concretely: the two withdrawn vendor Claims each
carry a `Decision(kill)`, so a page publishing *"this route was withdrawn, not measured"* is
backed and passes. The active transfer Claim has no Decision, so any page publishing a result
for it is refused. That distinction is the guard working, not a gap in it: a kill is a
conclusion, and a page is entitled to report one.

**Limit, stated plainly:** a page declaring `false` that hand-types numbers with no Evidence
id in sight will pass. The declaration is a contract with a human, and the guard enforces
the contract's mechanical half. The cheap sound check — a page declaring `false` may not
cite any Evidence id that exists in the store — is enforced. The rest is reflection review.

## 2. The anti-kernel structural check (ADR-0042 AC7)

> The emitter serializes, validates, and writes. It never selects what to emit.

This looks for selection-kernel machinery anywhere in the repo, not merely under
`lab/campaign/` — ADR-0040 guarded with a path check that the same kernel rebuilt at
`lab/pressure/` would have satisfied.

It walks the AST and inspects *defined names* (functions, classes, assignments), so a
docstring discussing pressure scheduling — like this one — does not trip it. That is also
its weakness.

**Limits, admitted up front:** it matches known names. It misses synonyms
(`pick_next_challenge`), dynamic dispatch (`getattr(mod, cfg["strategy"])`), and
config-driven selection (a YAML file naming the ranking). It is a tripwire plus review
discipline, not a proof. A guard whose limits are documented is worth more than one whose
limits are discovered.
"""

from __future__ import annotations

import ast
import os
import re
from dataclasses import dataclass
from pathlib import Path

from . import store
from .store import REPO_ROOT, decisions_for, load_all

# Reader-facing surfaces that can publish a lab result.
PUBLICATION_SURFACES = (
    Path("site") / "src" / "pages" / "lab",
    Path("site") / "src" / "content" / "lab",
)
PUBLICATION_SUFFIXES = {".astro", ".md", ".mdx", ".html"}

DECLARATION = re.compile(r"canon:publishes-results\s*=\s*(true|false)", re.IGNORECASE)
CLAIM_ID = re.compile(r"\b[0-9a-f]{16}\b")

# Names that mean "this code decides what to emit" rather than "this code emits what it
# was given". Matched against AST-defined names only.
SELECTION_NAMES = frozenset({
    "campaign",
    "next_action",
    "pressure",
    "outcome_map",
    "failing_gates",
    "verifier_plan",
    "rank_verifiers",
    "select_claim",
    "choose_claim",
    "select_decision",
    "decide_claim",
    "pick_claim",
    "materialize_campaign",
})
_SKIP_DIRS = {".venv", ".git", "node_modules", "__pycache__", "dist", ".astro"}


@dataclass(frozen=True)
class Violation:
    rule: str
    where: str
    detail: str

    def render(self) -> str:
        return f"{self.where}: {self.rule}: {self.detail}"


def _iter_py(root: Path):
    for p in root.rglob("*.py"):
        if any(part in _SKIP_DIRS for part in p.parts):
            continue
        yield p


def check_no_selection(root: Path | None = None) -> list[Violation]:
    """AST scan for selection-kernel machinery. See module docstring §2 for its limits."""
    root = root or REPO_ROOT
    out: list[Violation] = []

    for d in root.rglob("campaign"):
        if d.is_dir() and not any(part in _SKIP_DIRS for part in d.parts):
            out.append(
                Violation(
                    "no-selection",
                    str(d.relative_to(root)),
                    "a `campaign/` package exists; ADR-0038 §Cleanup forbids reviving the "
                    "reverted pressure kernel",
                )
            )

    for path in _iter_py(root):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        rel = str(path.relative_to(root))
        for node in ast.walk(tree):
            name = None
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = node.name
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                name = node.id
            if not name:
                continue
            token = name.lower().lstrip("_")
            if token in SELECTION_NAMES:
                out.append(
                    Violation(
                        "no-selection",
                        f"{rel}:{node.lineno}",
                        f"defines {name!r} — the emission path may serialize, validate, and "
                        f"write, but never select what to emit (ADR-0042)",
                    )
                )
    return out


def check_publication(root: Path | None = None) -> list[Violation]:
    """Layer 4 publication guard. Fail-closed. See module docstring §1."""
    root = root or REPO_ROOT
    out: list[Violation] = []
    known_evidence = {e["id"] for e in load_all("Evidence")}

    for surface in PUBLICATION_SURFACES:
        base = root / surface
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in PUBLICATION_SUFFIXES:
                continue
            rel = str(path.relative_to(root))
            text = path.read_text(encoding="utf-8")

            match = DECLARATION.search(text)
            if not match:
                out.append(
                    Violation(
                        "publication-guard",
                        rel,
                        "no `canon:publishes-results = true|false` declaration. Fail-closed: a "
                        "reader-facing lab surface must declare whether it publishes results, "
                        "and an undeclared page is treated as publishing them.",
                    )
                )
                continue

            publishes = match.group(1).lower() == "true"

            if publishes:
                cited = set(CLAIM_ID.findall(text))
                backed = {c for c in cited if decisions_for(c)}
                unbacked = sorted(cited - backed)
                if not cited or unbacked:
                    out.append(
                        Violation(
                            "publication-guard",
                            rel,
                            "declares it publishes results, but no Decision exists citing "
                            f"{'claim(s) ' + ', '.join(unbacked) if unbacked else 'any claim'}. "
                            "A result is only publishable behind a terminal Decision that cites "
                            "every frozen gate bound to the chosen Claim (canon rule 13) and only "
                            "Evidence gathered about a Claim it is actually deciding (rule 15). "
                            "Evidence alone is not a finding.",
                        )
                    )
                continue

            leaked = sorted(known_evidence & set(CLAIM_ID.findall(text)))
            if leaked:
                out.append(
                    Violation(
                        "publication-guard",
                        rel,
                        f"declares it publishes no results, yet cites Evidence envelope(s) "
                        f"{', '.join(leaked)}. Citing evidence is publishing a result.",
                    )
                )
    return out


def check_canon_integrity() -> list[Violation]:
    """Every envelope in the store still validates — schema, canon rules, artifact hashes.

    Canon is append-only, so an envelope that was valid at emission stays valid *unless the
    world underneath it moved*: an artifact edited in place, a schema tightened, a Policy
    referenced by a Decision that no longer resolves. Emission-time validation cannot catch
    any of those, because they happen afterwards. This does.
    """
    from .rules import CanonRefusal, check_all
    from .validate import validate
    from .view import StoreView

    out: list[Violation] = []
    view = StoreView()
    for object_type in ("Claim", "Evidence", "Decision", "EventLogEntry", "Policy"):
        for envelope in store.load_all(object_type):
            try:
                validate(envelope, view)
            except CanonRefusal as r:
                out.append(
                    Violation(
                        "canon-integrity",
                        f"{object_type} {envelope['id']}",
                        f"[{r.violation_kind}] {r.rationale}",
                    )
                )
    return out


def run_checks(root: Path | None = None) -> list[Violation]:
    return check_no_selection(root) + check_publication(root) + check_canon_integrity()


def main() -> int:
    """Build gate. Exits non-zero on any violation — the site must not compile past it."""
    violations = run_checks()
    if violations:
        print("CANON GUARDS FAILED — build refused\n")
        for v in violations:
            print(f"  {v.render()}")
        return 1
    print("canon guards passed: no-selection, publication, canon-integrity.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

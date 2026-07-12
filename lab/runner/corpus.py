"""Deterministic corpus generation from a private seed.

The corpus is regenerated from `(seed, suite, depth, run_index)` rather than stored. Two
consequences, both wanted:

- **Reproducible.** Anyone with the seed rebuilds byte-identical sessions and probes, so a
  disputed result can be re-run rather than argued about.
- **Not in the training data.** Facts are synthesised from the seed, so they cannot have
  been memorised by any subject. `benchmark_contamination` is a named validity threat and
  this is the mitigation, not a hope.

The seed is **private**: it lives in `runtime/.secrets/`, never in the repo, and never in a
published artifact. Publishing it would let a future subject train on the corpus, and the
whole point is that nothing has.

Ground-truth answers are generated **with** the corpus, before any run, and are never shown
to a subject. The oracle compares against them; nothing under test ever sees them.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

# Deterministic vocabulary. Fixed, not sampled from anything that could change between runs.
_SUBJECTS = ["Ilse", "Marek", "Priya", "Tomas", "Wren", "Odile", "Jonas", "Ada"]
_OBJECTS = ["ledger", "kettle", "atlas", "beacon", "quarry", "lantern", "spindle", "harbor"]
_PLACES = ["Ravenna", "Uppsala", "Cadiz", "Tromso", "Lucca", "Ghent", "Aarhus", "Bruges"]
_COLORS = ["indigo", "ochre", "verdigris", "carmine", "slate", "amber", "sable", "teal"]


def seed() -> str:
    """The private corpus seed. Absent -> the eval cannot run reproducibly, so we refuse."""
    s = os.environ.get("SYNAPLEX_CORPUS_SEED")
    if not s:
        path = Path("/opt/workspace/runtime/.secrets/synaplex-corpus-seed")
        if path.is_file():
            s = path.read_text(encoding="utf-8").strip()
    if not s:
        raise RuntimeError(
            "no corpus seed. Set SYNAPLEX_CORPUS_SEED or create "
            "/opt/workspace/runtime/.secrets/synaplex-corpus-seed. The seed is what makes the "
            "corpus reproducible and uncontaminated; running without one produces a result "
            "nobody can replay."
        )
    return s


def _draw(seed_: str, *parts: object) -> int:
    key = "\x1f".join(str(p) for p in parts)
    return int(hashlib.sha256(f"{seed_}\x1f{key}".encode()).hexdigest()[:8], 16)


@dataclass(frozen=True)
class Probe:
    question: str
    canonical: str
    stated_in_session: int


@dataclass(frozen=True)
class Session:
    index: int
    text: str


@dataclass(frozen=True)
class Case:
    """One (suite, depth, run) instance: the sessions to feed, and the probes to ask after."""

    suite: str
    depth: int
    run_index: int
    sessions: tuple[Session, ...]
    probes: tuple[Probe, ...]

    @property
    def canonicals(self) -> list[str]:
        return [p.canonical for p in self.probes]


def build_case(suite: str, depth: int, run_index: int, seed_: str | None = None) -> Case:
    """Build one case deterministically. Same inputs -> byte-identical case, always."""
    s = seed_ or seed()
    sessions: list[Session] = []
    probes: list[Probe] = []

    for i in range(depth):
        who = _SUBJECTS[_draw(s, suite, run_index, i, "who") % len(_SUBJECTS)]
        obj = _OBJECTS[_draw(s, suite, run_index, i, "obj") % len(_OBJECTS)]
        place = _PLACES[_draw(s, suite, run_index, i, "place") % len(_PLACES)]
        color = _COLORS[_draw(s, suite, run_index, i, "color") % len(_COLORS)]

        # One load-bearing fact per session, buried in filler so the task is recall rather
        # than "read the only sentence present".
        fact = f"{who} left the {color} {obj} in {place}."
        filler = (
            f"They talked about the weather in {place} for a while. "
            f"Nothing else of consequence happened in session {i}."
        )
        sessions.append(Session(index=i, text=f"{filler} {fact}"))
        probes.append(
            Probe(
                question=f"Where did {who} leave the {color} {obj}?",
                canonical=place,
                stated_in_session=i,
            )
        )

    return Case(suite=suite, depth=depth, run_index=run_index,
                sessions=tuple(sessions), probes=tuple(probes))


def corpus_digest(suite: str, depth: int, runs: int, seed_: str | None = None) -> str:
    """A digest over the generated corpus — goes in the run manifest.

    It identifies the corpus **without revealing the seed**, so a published manifest lets a
    reader confirm two runs used the same corpus while learning nothing that would let them
    reconstruct it.
    """
    h = hashlib.sha256()
    for r in range(runs):
        case = build_case(suite, depth, r, seed_)
        for sess in case.sessions:
            h.update(sess.text.encode())
        for p in case.probes:
            h.update(p.question.encode())
            h.update(p.canonical.encode())
    return f"sha256:{h.hexdigest()}"

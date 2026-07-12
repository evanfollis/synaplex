"""The independent scoring oracle. Deterministic, and deliberately not an LLM.

Pre-registered in `lab/evals/memory-systems-v1/control-arm.md` and hash-bound into the
control Claim. **This file's behaviour is a pre-registration, not an implementation
detail.** Changing the normalisation changes what the eval measures, and doing that after
seeing results is the post-hoc freedom the whole apparatus exists to close. If it must
change, it changes under a successor Claim.

## Why not an LLM judge

An LLM judge for a memory-systems eval is the detector confound wearing a lab coat. The
instrument deciding whether recall succeeded would share failure modes, training data, and
context-length behaviour with the systems under test — and it would score the *no-memory
control* using the very model whose in-context recall the control exists to measure. The
treatment cannot be the detector.

A deterministic oracle is worse at judging paraphrase and better at being trustworthy. For
this question that trade is not close.

## The admitted weakness, and why it cannot manufacture a result

A semantically correct answer that fails normalisation scores as a **miss**. That is
blunt — but it is blunt *identically for every arm*, so it cannot create a difference
between arms. It can only compress one. If the compression is severe enough that every arm
floors at zero, that is itself a harness failure, and the control-arm Claim is then
**supported** — which is the honest reading, not a bug to be patched away after the fact.
"""

from __future__ import annotations

import re
import unicodedata

_ARTICLES = {"a", "an", "the"}
_PUNCT = re.compile(r"[^\w\s]", re.UNICODE)
_WS = re.compile(r"\s+")

# Pre-registered numeral map. Spelled-out numbers are common in prose answers and their
# digit forms are the same fact; folding them is part of the declared normalisation, not a
# fix applied later because a number failed to match.
_NUMERALS = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
    "ten": "10", "eleven": "11", "twelve": "12",
}


def normalize(text: str) -> str:
    """The pre-registered normalisation: casefold, strip punctuation and articles,
    collapse whitespace, numerals to digits."""
    text = unicodedata.normalize("NFKC", text).casefold()
    text = _PUNCT.sub(" ", text)
    tokens = [t for t in _WS.split(text) if t and t not in _ARTICLES]
    tokens = [_NUMERALS.get(t, t) for t in tokens]
    return " ".join(tokens)


def score_recall_at_1(answer: str, canonical: str) -> int:
    """1 if the answer matches the canonical ground truth after normalisation, else 0.

    Recall@1 means the *first* answer is right. There is no partial credit and no second
    guess — that is what the metric says, and softening it here would silently redefine the
    pre-registered threshold.
    """
    return int(normalize(answer) == normalize(canonical))


def cell_recall(answers: list[str], canonicals: list[str]) -> float:
    """Mean recall@1 over one (arm x suite x run) cell."""
    if not canonicals:
        return 0.0
    if len(answers) != len(canonicals):
        raise ValueError(
            f"{len(answers)} answers for {len(canonicals)} probes — a dropped answer must be "
            f"recorded as an empty string (a miss), never silently omitted, or the denominator "
            f"shrinks and the score inflates."
        )
    return sum(score_recall_at_1(a, c) for a, c in zip(answers, canonicals)) / len(canonicals)

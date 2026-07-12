"""The arms under test, and the budget accounting that keeps an abort from becoming a result.

Five arms: four memory systems and the no-memory control. Every arm sees byte-identical
prompts, the same temperature, the same session depth, and the same token budget. The only
variable is how prior sessions reach the model.

## An aborted cell is NOT a failed cell

The single most dangerous line of code in an eval is the one that treats "we stopped paying"
as "the system got it wrong". A cell that hits the cost ceiling produces `AbortedCell`, and
Phase E emits it as `Evidence(polarity: neutral)` with the abort reason — never
`contradicts`. Coding a budget ceiling as a failure would let us *discover* that memory
systems fail simply by declining to pay for them to succeed. `CellResult` cannot represent
"aborted" as a score; the types make the mistake unavailable rather than merely discouraged.

## Fixture mode is not a mock of the answer

`FixtureProvider` replays deterministic canned completions so the whole pipeline —
budgeting, resume, artifact hashing, oracle, manifest — is exercised in CI with no network
and no credentials. It deliberately does **not** know the ground truth: it answers from the
context it was given, exactly as a real model would, so a bug that drops the context shows
up as a low score in fixture mode instead of being masked by an oracle-aware stub.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Protocol

from .corpus import Case

# Roughly 4 characters per token. Declared here rather than measured per-provider so every
# arm is truncated by the same rule; a provider-specific tokenizer would give one arm more
# real context than another under the same nominal budget.
CHARS_PER_TOKEN = 4


@dataclass(frozen=True)
class Budget:
    max_input_tokens: int = 30_000
    max_output_tokens: int = 3_000

    @property
    def max_input_chars(self) -> int:
        return self.max_input_tokens * CHARS_PER_TOKEN


@dataclass(frozen=True)
class Completion:
    text: str
    input_tokens: int
    output_tokens: int


@dataclass(frozen=True)
class CellResult:
    """A cell that ran to completion. It has a score because it produced answers."""

    arm: str
    suite: str
    run_index: int
    answers: tuple[str, ...]
    input_tokens: int
    output_tokens: int


@dataclass(frozen=True)
class AbortedCell:
    """A cell that stopped. It has NO score, by construction — see module docstring."""

    arm: str
    suite: str
    run_index: int
    reason: str
    input_tokens: int = 0
    output_tokens: int = 0


class Provider(Protocol):
    """The model behind an arm. The seam where fixture and live modes diverge."""

    name: str
    version: str

    def complete(self, prompt: str, max_output_tokens: int) -> Completion: ...


class FixtureProvider:
    """Deterministic, offline. Answers from its context, exactly as a real model would."""

    name = "fixture"
    version = "fixture-1"

    def complete(self, prompt: str, max_output_tokens: int) -> Completion:
        question = prompt.rsplit("Question:", 1)[-1].strip()
        answer = ""
        # Recover the answer from the context if it is there. If the context was truncated
        # away, the answer is empty — a miss — which is precisely the signal a memory system
        # is supposed to prevent, and precisely the bug a context-dropping harness would hide.
        for line in prompt.splitlines():
            if " left the " in line and " in " in line:
                who_obj = question.replace("Where did ", "").replace("?", "").strip()
                who = who_obj.split(" leave ")[0].strip()
                if line.strip().startswith(who) or f"{who} left" in line:
                    answer = line.rsplit(" in ", 1)[-1].strip().rstrip(".")
        return Completion(
            text=answer,
            input_tokens=len(prompt) // CHARS_PER_TOKEN,
            output_tokens=max(1, len(answer) // CHARS_PER_TOKEN),
        )


class LiveProvider:
    """The real model. Not reachable: every provider credential is absent.

    Deliberately raises rather than degrading to a stub. A runner that silently falls back to
    fixtures when credentials are missing would produce a full, plausible, entirely synthetic
    result set — and nothing downstream could tell it from a real one.
    """

    name = "anthropic"

    def __init__(self, model: str) -> None:
        self.version = model
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError(
                "ANTHROPIC_API_KEY is absent, so no live cell can execute. This is a hard "
                "refusal, not a fallback: a runner that quietly substituted fixtures here "
                "would emit a complete synthetic result set that no downstream consumer could "
                "distinguish from a real one."
            )

    def complete(self, prompt: str, max_output_tokens: int) -> Completion:  # pragma: no cover
        raise NotImplementedError(
            "live provider wiring is unfinished and MUST NOT be guessed at. It lands with the "
            "credential, against a real API whose behaviour can be observed."
        )


@dataclass
class Arm:
    """One condition. `memory` is None for the control."""

    key: str
    memory: str | None  # 'letta' | 'mem0' | 'memgpt' | 'claude-builtin' | None
    provider: Provider
    budget: Budget = field(default_factory=Budget)

    @property
    def is_control(self) -> bool:
        return self.memory is None

    def build_context(self, case: Case) -> tuple[str, bool]:
        """Assemble the context this arm gets. Returns (context, truncated).

        The control pastes prior sessions verbatim, **most-recent-first**, truncated at the
        budget. That order is pre-registered in `control-arm.md` and is not a runtime choice:
        it is the strongest honest baseline (a memory system that cannot beat "paste the
        recent transcript" is not earning its complexity), and picking the order after seeing
        which one flatters the result is exactly the freedom pre-registration closes.
        """
        if not self.is_control:
            raise NotImplementedError(
                f"memory-system arm {self.memory!r} needs its vendor SDK and credential; "
                f"neither is present. Not stubbed — see LiveProvider."
            )
        parts: list[str] = []
        used = 0
        truncated = False
        for sess in reversed(case.sessions):  # most-recent-first, pre-registered
            block = f"[session {sess.index}] {sess.text}\n"
            if used + len(block) > self.budget.max_input_chars:
                truncated = True
                break
            parts.append(block)
            used += len(block)
        return "".join(parts), truncated

    def run_cell(self, case: Case) -> CellResult | AbortedCell:
        context, truncated = self.build_context(case)
        answers: list[str] = []
        in_tok = out_tok = 0

        for probe in case.probes:
            prompt = f"{context}\nQuestion: {probe.question}"
            if len(prompt) // CHARS_PER_TOKEN > self.budget.max_input_tokens:
                return AbortedCell(
                    arm=self.key, suite=case.suite, run_index=case.run_index,
                    reason=f"input budget exceeded ({len(prompt) // CHARS_PER_TOKEN} > "
                           f"{self.budget.max_input_tokens} tokens)",
                    input_tokens=in_tok, output_tokens=out_tok,
                )
            c = self.provider.complete(prompt, self.budget.max_output_tokens)
            # A dropped answer is recorded as an empty string — a miss — never omitted. An
            # omission would shrink the denominator and inflate the score.
            answers.append(c.text or "")
            in_tok += c.input_tokens
            out_tok += c.output_tokens

        return CellResult(
            arm=self.key, suite=case.suite, run_index=case.run_index,
            answers=tuple(answers), input_tokens=in_tok, output_tokens=out_tok,
        )

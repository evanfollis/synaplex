from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class LLMRequest:
    system_prompt: str
    user_prompt: str


class LLMClient(Protocol):
    """
    Abstract interface for LLM calls.

    You can plug in OpenAI, Anthropic, local models, etc., behind this protocol.
    """

    def complete(self, request: LLMRequest) -> str:  # pragma: no cover - used via concrete impls
        ...


class DummyLLMClient:
    """
    Minimal implementation for testing/wiring.

    Replace this with a real client wired to OpenAI or another provider.
    """

    def complete(self, request: LLMRequest) -> str:
        # In real usage, this would call an external API.
        # Here we just echo back something obviously fake.
        return (
            "DUMMY_MANIFOLD_START\n"
            f"system: {request.system_prompt[:80]}\n"
            f"user: {request.user_prompt[:80]}\n"
            "DUMMY_MANIFOLD_END"
        )

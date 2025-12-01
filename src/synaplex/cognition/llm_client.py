# synaplex/cognition/llm_client.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class LLMResponse:
    text: str
    raw: Dict[str, Any]


class LLMClient:
    """
    Thin abstraction around an LLM provider.

    This stays deliberately minimal; concrete worlds can subclass or wrap it.
    """

    def __init__(self, model: str = "gpt-4.1") -> None:
        self.model = model

    def complete(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """
        Placeholder for an LLM completion call.

        In the skeleton, this just raises NotImplementedError.
        Worlds can subclass this to plug in real clients.
        """
        raise NotImplementedError("LLMClient.complete must be implemented by a concrete subclass.")

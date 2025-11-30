from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, Optional

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


# ============================================================
# Request + Interface
# ============================================================

@dataclass
class LLMRequest:
    """
    A minimal container for the two text streams Synaplex uses:
    - system_prompt: upgrade ritual instructions
    - user_prompt: previous manifold + new experience

    No structure or schema is imposed beyond these raw strings.
    """
    system_prompt: str
    user_prompt: str

    # Optional fields the platform may use in the future.
    previous_response_id: Optional[str] = None
    system_prompt: Optional[str] = None


class LLMClient(Protocol):
    """
    Abstract interface:
        LLMRequest -> str (opaque manifold text)
    """
    def complete(self, request: LLMRequest) -> str:
        ...


# ============================================================
# Dummy Client (offline mode)
# ============================================================

class DummyLLMClient:
    """
    For testing without incurring API calls.
    """
    def complete(self, request: LLMRequest) -> str:
        return (
            "DUMMY_MANIFOLD_START\n"
            f"[system]\n{request.system_prompt}\n\n"
            f"[user]\n{request.user_prompt}\n"
            "DUMMY_MANIFOLD_END\n"
        )


# ============================================================
# OpenAI Responses API Client — correct + minimal + safe
# ============================================================

@dataclass
class OpenAILLMClient:
    """
    Concrete LLM client backed by the OpenAI **Responses API**.

    It obeys your rules:
    - No temperature (reasoning models forbid it)
    - No max_output_tokens (forbidden + harmful for multi-agent systems)
    - Model, reasoning effort, verbosity come from .env

    Environment variables:
        OPENAI_LLM_MODEL='gpt-5.1' (or whatever model)
        OPENAI_LLM_REASONING='low'|'medium'|'high' (optional)
        OPENAI_LLM_VERBOSITY='low'|'medium'|'high' (optional)
    """

    model: str = field(default_factory=lambda: os.getenv("OPENAI_LLM_MODEL", "gpt-5.1"))
    reasoning_effort: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_LLM_REASONING"))
    verbosity: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_LLM_VERBOSITY"))
    _client: OpenAI = field(default_factory=OpenAI, repr=False)

    def complete(self, request: LLMRequest) -> str:
        # Combine system + user prompt into a single text input.
        # This is the least lossy, least opinionated way to pass instructions.


        # Build the Responses API call.
        # IMPORTANT:
        #   - Reasoning models accept:
        #         reasoning = {"effort": "high"}
        #         text = {"verbosity": "low"}
        #     NOT temperature, NOT max_output_tokens.
        #
        #   - These keys are optional.
        #
        payload = {
            "model": self.model,
            "input": request.user_prompt,
        }

        if self.reasoning_effort:
            payload["reasoning"] = {"effort": self.reasoning_effort}

        if self.verbosity:
            payload["text"] = {"verbosity": self.verbosity}

        if request.previous_response_id:
            payload["previous_response_id"] = request.previous_response_id

        if request.system_prompt:
            payload["instructions"] = request.system_prompt

        # Invoke the API
        response = self._client.responses.create(**payload)

        # The SDK exposes this convenience accessor:
        #   response.output_text → str
        return response.output_text

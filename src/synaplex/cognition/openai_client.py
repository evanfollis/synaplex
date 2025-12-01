# synaplex/cognition/openai_client.py

"""
Concrete OpenAI LLM client implementation using the Responses API.

This implements the LLMClient interface for production use with OpenAI's API.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv

from openai import OpenAI

from .llm_client import LLMClient, LLMResponse

# Load environment variables from .env file
load_dotenv()


class OpenAILLMClient(LLMClient):
    """
    Concrete OpenAI LLM client using the Responses API.
    
    This client:
    - Loads OPENAI_API_KEY from environment (via .env file)
    - Uses OpenAI's responses.create() API for completions
    - Returns LLMResponse objects compatible with the Mind abstraction
    """

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        reasoning_effort: Optional[str] = None,
        text_verbosity: Optional[str] = None,
    ) -> None:
        """
        Initialize the OpenAI client.
        
        All parameters default to environment variables from .env:
        - OPENAI_API_KEY: API key (required)
        - OPENAI_LLM_MODEL: Model identifier (e.g., "gpt-4o", "gpt-4o-mini")
        - OPENAI_LLM_REASONING: Reasoning effort level ("low", "medium", "high")
        - OPENAI_LLM_VERBOSITY: Text verbosity level ("low", "medium", "high")
        
        Args:
            model: Override model from OPENAI_LLM_MODEL env var
            api_key: Override API key from OPENAI_API_KEY env var
            reasoning_effort: Override reasoning effort from OPENAI_LLM_REASONING env var
            text_verbosity: Override verbosity from OPENAI_LLM_VERBOSITY env var
        """
        # Load configuration from environment variables
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self._api_key:
            raise ValueError(
                "OPENAI_API_KEY not found. Set it in .env file or pass api_key parameter."
            )
        
        model = model or os.getenv("OPENAI_LLM_MODEL", "gpt-4o")
        reasoning_effort = reasoning_effort or os.getenv("OPENAI_LLM_REASONING", "medium")
        text_verbosity = text_verbosity or os.getenv("OPENAI_LLM_VERBOSITY", "high")
        
        super().__init__(model=model)
        
        self._client = OpenAI(api_key=self._api_key)
        self.reasoning_effort = reasoning_effort
        self.text_verbosity = text_verbosity
        self._previous_response_id: Optional[str] = None

    def complete(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """
        Complete a prompt using OpenAI's Responses API.
        
        Args:
            prompt: The input prompt text
            **kwargs: Additional parameters (model override, reasoning_effort, etc.)
                     Note: temperature and max_output_tokens are explicitly forbidden
                     and will be filtered out if provided.
        
        Returns:
            LLMResponse with text and raw response data
        """
        # Filter out forbidden parameters that would break the platform
        forbidden_params = {"temperature", "max_output_tokens", "max_tokens"}
        for param in forbidden_params:
            kwargs.pop(param, None)
        
        # Allow model override via kwargs
        model = kwargs.pop("model", self.model)
        reasoning_effort = kwargs.pop("reasoning_effort", self.reasoning_effort)
        text_verbosity = kwargs.pop("text_verbosity", self.text_verbosity)
        
        # Build the API payload
        payload: Dict[str, Any] = {
            "input": prompt,
            "model": model,
            "reasoning": {"effort": reasoning_effort},
            "text": {"verbosity": text_verbosity},
            **kwargs,  # Allow any additional kwargs to pass through (after filtering)
        }
        
        # Include previous_response_id for conversational continuity if available
        if self._previous_response_id:
            payload["previous_response_id"] = self._previous_response_id
        
        # Make the API call
        try:
            resp = self._client.responses.create(**payload)
        except Exception as e:
            raise RuntimeError(f"OpenAI API call failed: {e}") from e
        
        # Store response ID for future calls
        self._previous_response_id = resp.id
        
        # Extract text from the response
        text = self._extract_text(resp)
        
        # Build raw response dict for debugging/analysis
        raw = {
            "id": resp.id,
            "model": model,
            "created": getattr(resp, "created", None),
            "response": resp.model_dump() if hasattr(resp, "model_dump") else str(resp),
        }
        
        return LLMResponse(text=text, raw=raw)

    def _extract_text(self, resp: Any) -> str:
        """
        Extract text content from OpenAI Responses API response.
        
        The response structure may vary, so we handle multiple cases:
        - Direct text attribute
        - Output.items (structured output format)
        - Fallback to string representation
        """
        # Try direct text attribute
        if hasattr(resp, "output") and resp.output:
            # Responses API typically has output.items
            if hasattr(resp.output, "items") and resp.output.items:
                # Extract text from items
                texts = []
                for item in resp.output.items:
                    if hasattr(item, "text"):
                        texts.append(item.text)
                    elif isinstance(item, dict) and "text" in item:
                        texts.append(item["text"])
                if texts:
                    return "\n".join(texts)
            
            # Fallback: try direct text on output
            if hasattr(resp.output, "text"):
                return resp.output.text
            if isinstance(resp.output, dict) and "text" in resp.output:
                return resp.output["text"]
            if isinstance(resp.output, str):
                return resp.output
        
        # Try top-level text attribute
        if hasattr(resp, "text") and resp.text:
            return resp.text if isinstance(resp.text, str) else str(resp.text)
        
        # Last resort: string representation
        return str(resp)

    def reset_conversation(self) -> None:
        """Reset conversation state (clear previous_response_id)."""
        self._previous_response_id = None


# synaplex/cognition/__init__.py

"""
Internal mind dynamics: LLMs, manifolds, and the unified cognitive loop.

This layer:
- wraps an LLM client,
- manages manifold snapshots,
- implements branching / consolidation strategies,
- provides Mind implementations that adapt to core.AgentInterface.
"""

from .llm_client import LLMClient
from .manifolds import ManifoldEnvelope, ManifoldStore, InMemoryManifoldStore, FileManifoldStore
from .mind import Mind
from .openai_client import OpenAILLMClient

__all__ = [
    "LLMClient",
    "ManifoldEnvelope",
    "ManifoldStore",
    "InMemoryManifoldStore",
    "FileManifoldStore",
    "Mind",
    "OpenAILLMClient",
]

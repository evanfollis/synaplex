"""
Internal mind dynamics: LLMs, substrates, and the unified cognitive loop.

This layer:
- wraps an LLM client,
- manages substrate snapshots,
- implements branching / consolidation strategies,
- provides Mind implementations that adapt to core.AgentInterface.
"""

from .llm_client import LLMClient
from .substrate import SubstrateEnvelope, SubstrateStore, InMemorySubstrateStore, FileSubstrateStore
from .mind import Mind
from .openai_client import OpenAILLMClient

__all__ = [
    "LLMClient",
    "SubstrateEnvelope",
    "SubstrateStore",
    "InMemorySubstrateStore",
    "FileSubstrateStore",
    "Mind",
    "OpenAILLMClient",
]

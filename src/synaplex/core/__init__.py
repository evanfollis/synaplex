# synaplex/core/__init__.py

"""
Core external structure: graph runtime, messages, DNA, lenses, environment state.

This layer:
- knows nothing about LLMs or manifolds,
- defines how agents are wired into the world,
- exposes abstract hooks for Perception → Reasoning → Internal Update.
"""

from .ids import WorldId, AgentId, MessageId
from .dna import DNA
from .lenses import Lens
from .env_state import EnvState
from .messages import Signal, Projection, Request, Percept
from .agent_interface import AgentInterface
from .runtime_interface import RuntimeInterface
from .data_feeds import DataFeed, DataFeedRegistry, StaticDataFeed, TimeSeriesDataFeed, CallableDataFeed

__all__ = [
    "WorldId",
    "AgentId",
    "MessageId",
    "DNA",
    "Lens",
    "EnvState",
    "Signal",
    "Projection",
    "Request",
    "Percept",
    "AgentInterface",
    "RuntimeInterface",
    "DataFeed",
    "DataFeedRegistry",
    "StaticDataFeed",
    "TimeSeriesDataFeed",
    "CallableDataFeed",
]

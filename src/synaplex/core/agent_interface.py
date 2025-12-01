# synaplex/core/agent_interface.py

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from .ids import AgentId
from .messages import Percept, Signal, Projection


class AgentInterface(ABC):
    """
    Abstract interface between the world (core) and a mind implementation (cognition).

    The world drives the unified loop by calling:
        perceive(...) → reason(...) → act(...)
    The internal update of the manifold is handled inside the implementation.
    """

    def __init__(self, agent_id: AgentId) -> None:
        self._agent_id = agent_id

    @property
    def agent_id(self) -> AgentId:
        return self._agent_id

    # ---- unified loop hooks ----

    @abstractmethod
    def perceive(self, percept: Percept) -> None:
        """
        Accept a percept from the environment.

        Implementations may cache it for the subsequent reasoning step.
        """
        raise NotImplementedError

    @abstractmethod
    def reason(self) -> Dict[str, Any]:
        """
        Perform LLM-backed reasoning (or no-op in graph-only regimes).

        Returns a reasoning_output dict that will be passed to act().
        """
        raise NotImplementedError

    @abstractmethod
    def act(self, reasoning_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Produce outward behavior from reasoning_output.

        Returns a dict describing:
        - new signals to emit,
        - new requests to send,
        - optional env_state changes, etc.
        """
        raise NotImplementedError

    # Optional extension points, e.g., logging/debugging, can be added later.

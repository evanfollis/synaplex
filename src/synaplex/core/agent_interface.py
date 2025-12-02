# synaplex/core/agent_interface.py

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from .ids import AgentId, MessageId
from .messages import Percept, Signal, Projection, Request


class AgentInterface(ABC):
    """
    Abstract interface between the world (core) and a mind implementation (cognition).

    The world drives the unified loop by calling:
        perceive(...) → reason(...) → act(...)
    The internal update of the substrate is handled inside the implementation.
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
        Perform LLM-backed reasoning as part of the unified cognitive loop.

        Every Mind follows the same loop: Perception → Reasoning → Internal Update.
        This method implements the Reasoning step, which uses the percept and substrate
        to produce reasoning notes and outward behavior.

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

    def create_projection(self, request: Request) -> Projection:
        """
        Create a projection in response to a request.

        This is called by the runtime when building percepts for subscribers.
        The default implementation returns an empty projection.
        Subclasses should override to provide structured state views.

        The projection payload should contain:
        - structured state from EnvState
        - substrate-derived views (if any, never raw substrate text)
        - any other structured data the sender chooses to expose

        Args:
            request: The request from the receiver, containing the receiver's lens shape

        Returns:
            A Projection with sender=self.agent_id, receiver=request.sender
        """
        # Default: empty projection
        return Projection(
            id=MessageId(f"proj-{self.agent_id.value}-{request.id.value}"),
            sender=self.agent_id,
            receiver=request.sender,
            payload={},
        )

    def get_visible_state(self) -> Dict[str, Any]:
        """
        Return the agent's externally visible structured state.

        This is used by the runtime to create projections.
        The default returns an empty dict.

        Returns:
            Dict of structured state that can be exposed via projections
        """
        return {}

    # Optional extension points, e.g., logging/debugging, can be added later.

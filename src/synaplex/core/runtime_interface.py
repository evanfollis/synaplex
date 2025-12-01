# synaplex/core/runtime_interface.py

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Iterable, Mapping

from .ids import WorldId, AgentId
from .agent_interface import AgentInterface
from .env_state import EnvState


class RuntimeInterface(ABC):
    """
    Abstract graph runtime.

    Responsible for:
    - maintaining a set of agents,
    - wiring subscriptions and message routes,
    - constructing percepts,
    - driving ticks: Perception → Reasoning → Internal Update (via AgentInterface).
    """

    def __init__(self, world_id: WorldId, env_state: EnvState | None = None) -> None:
        self.world_id = world_id
        self.env_state = env_state or EnvState()

    @abstractmethod
    def register_agent(self, agent: AgentInterface) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_agents(self) -> Mapping[AgentId, AgentInterface]:
        raise NotImplementedError

    @abstractmethod
    def tick(self, tick_id: int) -> None:
        """
        Run one global tick.

        Typical sequence:
        - build percepts for each agent,
        - call agent.perceive(percept),
        - call agent.reason(),
        - call agent.act(reasoning_output),
        - apply outward behavior to env_state / message queues.
        """
        raise NotImplementedError

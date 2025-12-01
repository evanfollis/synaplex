# synaplex/core/runtime_inprocess.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Mapping, List

from .ids import WorldId, AgentId
from .agent_interface import AgentInterface
from .env_state import EnvState
from .messages import Percept, Projection, Signal
from .runtime_interface import RuntimeInterface


@dataclass
class EdgeConfig:
    """Simple representation of subscriptions."""
    subscriber: AgentId
    publisher: AgentId


@dataclass
class GraphConfig:
    """
    Simple in-process graph configuration.

    Worlds can build richer configs on top of this.
    """
    edges: List[EdgeConfig] = field(default_factory=list)


class InProcessRuntime(RuntimeInterface):
    """
    Reference in-process runtime.

    Minimal implementation to:
    - manage agents,
    - manage a subscription graph,
    - construct trivial percepts.
    """

    def __init__(
        self,
        world_id: WorldId,
        env_state: EnvState | None = None,
        graph_config: GraphConfig | None = None,
    ) -> None:
        super().__init__(world_id, env_state)
        self._agents: Dict[AgentId, AgentInterface] = {}
        self.graph_config = graph_config or GraphConfig()

    def register_agent(self, agent: AgentInterface) -> None:
        self._agents[agent.agent_id] = agent

    def get_agents(self) -> Mapping[AgentId, AgentInterface]:
        return self._agents

    def _subscriptions_for(self, agent_id: AgentId) -> List[AgentId]:
        return [
            edge.publisher
            for edge in self.graph_config.edges
            if edge.subscriber == agent_id
        ]

    def _build_percept(self, agent_id: AgentId, tick_id: int) -> Percept:
        # For now: no real projections/signals, just a stub percept
        return Percept(agent_id=agent_id, tick=tick_id)

    def tick(self, tick_id: int) -> None:
        # 1. Perception
        percepts: Dict[AgentId, Percept] = {
            agent_id: self._build_percept(agent_id, tick_id)
            for agent_id in self._agents
        }
        for agent_id, agent in self._agents.items():
            agent.perceive(percepts[agent_id])

        # 2. Reasoning
        reasoning_outputs: Dict[AgentId, dict] = {}
        for agent_id, agent in self._agents.items():
            reasoning_outputs[agent_id] = agent.reason()

        # 3. Actions
        for agent_id, agent in self._agents.items():
            behavior = agent.act(reasoning_outputs[agent_id])
            # Future: apply changes to env_state, emit signals/requests, etc.
            _ = behavior  # placeholder

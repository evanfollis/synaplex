from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Any

from synaplex.core.agent import Agent
from synaplex.core.types import Signal


@dataclass
class World:
    """
    Minimal runtime that coordinates agents and performs ticks.

    For v0, the world:
      - holds a set of agents,
      - provides a simple context dict,
      - runs `tick` on each agent in turn,
      - collects their Signals.

    In later versions, this will handle attention routing, projections, and
    multi-agent interactions.
    """
    id: str
    agents: Dict[str, Agent] = field(default_factory=dict)

    def add_agent(self, agent: Agent) -> None:
        if agent.id in self.agents:
            raise ValueError(f"Agent with id '{agent.id}' already exists in world '{self.id}'")
        self.agents[agent.id] = agent

    def tick(self, world_ctx: Dict[str, Any]) -> List[Signal]:
        signals: List[Signal] = []
        for agent in self.agents.values():
            signal = agent.tick(world_ctx=world_ctx)
            signals.append(signal)
        return signals

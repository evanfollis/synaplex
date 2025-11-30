from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Any, Tuple, DefaultDict
from collections import defaultdict

from synaplex.core.agent import Agent
from synaplex.core.attention import attention_score
from synaplex.core.types import Signal, Projection


@dataclass
class World:
    """
    Minimal runtime that coordinates agents and performs ticks.

    For v0, the world:
      - holds a set of agents,
      - provides a simple context dict,
      - runs `tick` on each agent in turn,
      - collects their Signals.

    `tick_with_attention` adds a second pass that routes Projections between
    agents whose lenses align with a sender's Signal.
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

    def tick_with_attention(
        self,
        world_ctx: Dict[str, Any],
        attention_threshold: float = 0.5,
    ) -> Tuple[List[Signal], Dict[str, List[Projection]]]:
        """
        Run a world tick and then perform a simple attention routing pass.

        Returns:
            - the list of Signals emitted by agents
            - a mapping of `receiver_agent_id -> list of Projections` they received
        """
        signals = self.tick(world_ctx=world_ctx)

        projections_by_receiver: DefaultDict[str, List[Projection]] = defaultdict(list)

        # Index agents for quick lookup
        agents = self.agents

        for signal in signals:
            sender = agents.get(signal.from_agent)
            if sender is None:
                continue  # should not happen, but keep robust

            for receiver_id, receiver in agents.items():
                if receiver_id == sender.id:
                    continue

                score = attention_score(signal, receiver.lens)
                if score >= attention_threshold:
                    projection = sender.project_for(to_agent_id=receiver_id)
                    projections_by_receiver[receiver_id].append(projection)

        return signals, dict(projections_by_receiver)

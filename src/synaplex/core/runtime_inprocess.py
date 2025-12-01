# synaplex/core/runtime_inprocess.py

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Dict, Mapping, List, Optional

from .ids import WorldId, AgentId, MessageId
from .agent_interface import AgentInterface
from .dna import DNA
from .env_state import EnvState
from .lenses import Lens
from .messages import Percept, Projection, Signal, Request
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

    Implements:
    - agent management with DNA and Lens storage,
    - subscription-based projection gathering,
    - signal collection and filtering via lenses,
    - percept construction with EnvState integration,
    - outward behavior handling (signals, env_updates).
    """

    def __init__(
        self,
        world_id: WorldId,
        env_state: EnvState | None = None,
        graph_config: GraphConfig | None = None,
    ) -> None:
        super().__init__(world_id, env_state)
        self._agents: Dict[AgentId, AgentInterface] = {}
        self._dna: Dict[AgentId, DNA] = {}
        self._lenses: Dict[AgentId, Lens] = {}
        self.graph_config = graph_config or GraphConfig()
        # Track signals emitted during the current tick
        self._current_tick_signals: Dict[AgentId, List[Signal]] = {}

    def register_agent(
        self,
        agent: AgentInterface,
        dna: Optional[DNA] = None,
        lens: Optional[Lens] = None,
    ) -> None:
        """
        Register an agent with optional DNA and Lens.

        If DNA is provided, it defines the agent's subscriptions.
        If Lens is provided, it defines how the agent filters signals and transforms projections.
        """
        self._agents[agent.agent_id] = agent
        if dna is not None:
            self._dna[agent.agent_id] = dna
        if lens is not None:
            self._lenses[agent.agent_id] = lens

    def get_agents(self) -> Mapping[AgentId, AgentInterface]:
        return self._agents

    def _subscriptions_for(self, agent_id: AgentId) -> List[AgentId]:
        """
        Get list of agents this agent subscribes to.

        Checks both graph_config edges and DNA subscriptions.
        """
        # From graph config edges
        edge_subscriptions = [
            edge.publisher
            for edge in self.graph_config.edges
            if edge.subscriber == agent_id
        ]
        # From DNA (if available)
        dna = self._dna.get(agent_id)
        dna_subscriptions = dna.subscriptions if dna else []
        # Combine and deduplicate
        all_subscriptions = list(set(edge_subscriptions + dna_subscriptions))
        return all_subscriptions

    def _generate_message_id(self) -> MessageId:
        """Generate a unique message ID."""
        return MessageId(f"msg-{uuid.uuid4().hex[:8]}")

    def _gather_projections(
        self, receiver_id: AgentId, tick_id: int
    ) -> List[Projection]:
        """
        Gather projections from subscribed agents.

        For each subscription:
        1. Get receiver's lens (if available) to build request shape
        2. Call publisher's create_projection() method
        3. Apply receiver's lens transformation
        4. Return transformed projection
        """
        projections = []
        subscriptions = self._subscriptions_for(receiver_id)
        receiver_lens = self._lenses.get(receiver_id)

        for publisher_id in subscriptions:
            if publisher_id not in self._agents:
                continue  # Publisher not registered

            publisher = self._agents[publisher_id]

            # Build request using receiver's lens
            request_shape = {}
            if receiver_lens:
                context = {"tick": tick_id, "receiver": receiver_id.value}
                request_shape = receiver_lens.build_request_shape(context)
            else:
                request_shape = {"tick": tick_id}

            # Create request
            request = Request(
                id=self._generate_message_id(),
                sender=receiver_id,
                receiver=publisher_id,
                shape=request_shape,
            )

            # Get projection from publisher
            projection = publisher.create_projection(request)

            # Apply receiver's lens transformation (receiver-owned semantics)
            if receiver_lens:
                projection.payload = receiver_lens.transform_projection(
                    projection.payload
                )

            projections.append(projection)

        return projections

    def _gather_signals(self, receiver_id: AgentId) -> List[Signal]:
        """
        Gather and filter signals from all agents.

        Signals are filtered via the receiver's lens (if available).
        """
        receiver_lens = self._lenses.get(receiver_id)
        filtered_signals = []

        # Collect signals from all agents (from current tick)
        for sender_id, signals in self._current_tick_signals.items():
            if sender_id == receiver_id:
                continue  # Don't include own signals

            for signal in signals:
                # Filter via receiver's lens
                if receiver_lens:
                    if receiver_lens.should_attend(signal.payload):
                        filtered_signals.append(signal)
                else:
                    # No lens: attend to all signals
                    filtered_signals.append(signal)

        return filtered_signals

    def _build_percept(self, agent_id: AgentId, tick_id: int) -> Percept:
        """
        Build a structured percept for an agent.

        Gathers:
        - projections from subscribed agents (lens-transformed),
        - filtered signals from all agents,
        - relevant EnvState views.
        """
        # Gather projections from subscriptions
        projections = self._gather_projections(agent_id, tick_id)

        # Gather and filter signals
        signals = self._gather_signals(agent_id)

        # Include EnvState in percept extras
        # This allows agents to see shared environmental state
        env_state_view = {
            "data": self.env_state.data,
        }

        return Percept(
            agent_id=agent_id,
            tick=tick_id,
            projections=projections,
            signals=signals,
            data_feeds={},  # Worlds can extend this
            extras={"env_state": env_state_view},
        )

    def tick(self, tick_id: int) -> None:
        """
        Run one global tick following the unified loop:
        Perception → Reasoning → Internal Update (via act()).
        """
        # Clear signals from previous tick
        self._current_tick_signals.clear()

        # 1. Perception: Build percepts and deliver to agents
        percepts: Dict[AgentId, Percept] = {
            agent_id: self._build_percept(agent_id, tick_id)
            for agent_id in self._agents
        }
        for agent_id, agent in self._agents.items():
            agent.perceive(percepts[agent_id])

        # 2. Reasoning: Agents think about their percepts
        reasoning_outputs: Dict[AgentId, dict] = {}
        for agent_id, agent in self._agents.items():
            reasoning_outputs[agent_id] = agent.reason()

        # 3. Actions: Process outward behavior
        for agent_id, agent in self._agents.items():
            behavior = agent.act(reasoning_outputs[agent_id])

            # Extract and handle signals
            signals = behavior.get("signals", [])
            if signals:
                # Convert signal dicts to Signal objects if needed
                signal_objects = []
                for sig in signals:
                    if isinstance(sig, Signal):
                        signal_objects.append(sig)
                    elif isinstance(sig, dict):
                        # Convert dict to Signal
                        signal_objects.append(
                            Signal(
                                id=sig.get("id", self._generate_message_id()),
                                sender=agent_id,
                                payload=sig.get("payload", sig),
                            )
                        )
                self._current_tick_signals[agent_id] = signal_objects

            # Apply env_state updates
            env_updates = behavior.get("env_updates", {})
            if env_updates:
                for key, value in env_updates.items():
                    self.env_state.set(key, value)

            # Note: Requests are handled in the next tick's perception phase
            # when building projections for subscribers

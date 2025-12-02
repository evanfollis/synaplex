# synaplex/core/runtime_inprocess.py

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, List, Optional

from .ids import WorldId, AgentId, MessageId
from .agent_interface import AgentInterface
from .dna import DNA
from .env_state import EnvState
from .lenses import Lens
from .messages import Percept, Projection, Signal, Request
from .runtime_interface import RuntimeInterface
from .data_feeds import DataFeedRegistry

# Optional logging import (meta layer)
try:
    from synaplex.meta.logging import RunLogger
    _LOGGING_AVAILABLE = True
except ImportError:
    _LOGGING_AVAILABLE = False
    RunLogger = None  # type: ignore


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
        data_feeds: DataFeedRegistry | None = None,
        logger: Optional[Any] = None,  # RunLogger, but avoid import if not available
    ) -> None:
        super().__init__(world_id, env_state)
        self._agents: Dict[AgentId, AgentInterface] = {}
        self._dna: Dict[AgentId, DNA] = {}
        self._lenses: Dict[AgentId, Lens] = {}
        self.graph_config = graph_config or GraphConfig()
        self.data_feeds = data_feeds or DataFeedRegistry()
        self.logger = logger  # Optional RunLogger
        # Track signals emitted during the current tick
        self._current_tick_signals: Dict[AgentId, List[Signal]] = {}
        # Track pending requests for next tick's perception phase
        self._pending_requests: Dict[AgentId, List[Request]] = {}
        # Track holonomy events (H): irreversible-ish actions that scar world + manifold
        self._holonomy_events: List[Dict[str, Any]] = []

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
        Gather projections from subscribed agents and pending requests.

        For each subscription:
        1. Get receiver's lens (if available) to build request shape
        2. Call publisher's create_projection() method
        3. Apply receiver's lens transformation
        4. Return transformed projection

        Also handles active requests from previous tick.
        """
        projections = []
        receiver_lens = self._lenses.get(receiver_id)

        # Handle subscriptions (always-on perception)
        subscriptions = self._subscriptions_for(receiver_id)
        for publisher_id in subscriptions:
            if publisher_id not in self._agents:
                # Log warning but continue - publisher may not be registered yet
                # In production, this would use proper logging
                continue

            publisher = self._agents[publisher_id]

            # Create request (minimal - no lens shaping)
            request = Request(
                id=self._generate_message_id(),
                sender=receiver_id,
                receiver=publisher_id,
                shape={},
            )

            # Get projection from publisher - passes through unchanged
            # No lens transformation. Receiver-owned semantics.
            try:
                projection = publisher.create_projection(request)
                projections.append(projection)
            except Exception:
                pass

        # Handle active requests from previous tick
        pending = self._pending_requests.pop(receiver_id, [])
        for request in pending:
            if request.receiver not in self._agents:
                continue

            publisher = self._agents[request.receiver]
            try:
                projection = publisher.create_projection(request)
                projections.append(projection)
            except Exception:
                pass

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

        # Gather data feeds
        feed_data = self.data_feeds.get_all(tick_id)

        # Include EnvState in percept extras
        # This allows agents to see shared environmental state
        env_state_view = {
            "data": self.env_state.data,
        }

        # Include tool information from DNA if available
        extras = {"env_state": env_state_view}
        dna = self._dna.get(agent_id)
        if dna and dna.tools:
            extras["available_tools"] = dna.tools

        return Percept(
            agent_id=agent_id,
            tick=tick_id,
            projections=projections,
            signals=signals,
            data_feeds=feed_data,
            extras=extras,
        )

    def tick(self, tick_id: int) -> None:
        """
        Run one global tick following the unified loop:
        Perception → Reasoning → Internal Update (via act()).
        """
        # Clear signals from previous tick
        self._current_tick_signals.clear()
        # Clear pending requests (they'll be processed in this tick's perception)
        self._pending_requests.clear()

        # 1. Perception: Build percepts and deliver to agents
        percepts: Dict[AgentId, Percept] = {
            agent_id: self._build_percept(agent_id, tick_id)
            for agent_id in self._agents
        }
        for agent_id, agent in self._agents.items():
            percept = percepts[agent_id]
            agent.perceive(percept)
            
            # Log percept if logger available
            if self.logger:
                self.logger.log_percept(
                    agent_id,
                    tick_id,
                    percept.to_context(),
                )

        # 2. Reasoning: Agents think about their percepts
        reasoning_outputs: Dict[AgentId, dict] = {}
        for agent_id, agent in self._agents.items():
            reasoning_output = agent.reason()
            reasoning_outputs[agent_id] = reasoning_output
            
            # Log reasoning if logger available
            if self.logger:
                self.logger.log_reasoning(agent_id, tick_id, reasoning_output)
                
                # Log manifold snapshot if version info is available
                context = reasoning_output.get("context", {})
                if "manifold_version" in context:
                    self.logger.log_manifold_snapshot(
                        agent_id,
                        tick_id,
                        context.get("manifold_version", 0),
                        context.get("manifold_content_length", 0),
                        context.get("manifold_metadata", {}),
                    )

        # 3. Actions: Process outward behavior
        for agent_id, agent in self._agents.items():
            behavior = agent.act(reasoning_outputs[agent_id])
            
            # Log action if logger available
            if self.logger:
                self.logger.log_action(agent_id, tick_id, behavior)

            # Extract and handle signals
            signals = behavior.get("signals", [])
            if signals:
                # Convert signal dicts to Signal objects if needed
                # Note: frottage passes through unchanged (per FROTTAGE_CONTRACT)
                signal_objects = []
                for sig in signals:
                    if isinstance(sig, Signal):
                        signal_objects.append(sig)
                    elif isinstance(sig, dict):
                        # Convert dict to Signal, preserving frottage
                        signal_objects.append(
                            Signal(
                                id=sig.get("id", self._generate_message_id()),
                                sender=agent_id,
                                payload=sig.get("payload", sig),
                                frottage=sig.get("frottage"),  # Pass through unchanged
                            )
                        )
                self._current_tick_signals[agent_id] = signal_objects

            # Apply env_state updates
            env_updates = behavior.get("env_updates", {})
            if env_updates:
                for key, value in env_updates.items():
                    self.env_state.set(key, value)

            # Track holonomy (H): irreversible-ish actions that scar world + manifold
            holonomy_marker = behavior.get("holonomy_marker", False)
            if holonomy_marker:
                self._holonomy_events.append({
                    "agent_id": agent_id.value,
                    "tick": tick_id,
                    "type": behavior.get("holonomy_type", "action"),
                    "description": behavior.get("holonomy_description", "Irreversible action"),
                })
            
            # Collect requests for next tick's perception phase
            requests = behavior.get("requests", [])
            if requests:
                request_objects = []
                for req in requests:
                    if isinstance(req, Request):
                        request_objects.append(req)
                    elif isinstance(req, dict):
                        # Convert dict to Request
                        request_objects.append(
                            Request(
                                id=req.get("id", self._generate_message_id()),
                                sender=agent_id,
                                receiver=req.get("receiver", AgentId(req.get("receiver", ""))),
                                shape=req.get("shape", {}),
                            )
                        )
                # Store requests by receiver for next tick
                for req in request_objects:
                    if req.receiver not in self._pending_requests:
                        self._pending_requests[req.receiver] = []
                    self._pending_requests[req.receiver].append(req)
        
        # Log EnvState snapshot if logger available
        if self.logger:
            self.logger.log_env_state_snapshot(tick_id, self.env_state.data.copy())

    def get_holonomy_events(self) -> List[Dict[str, Any]]:
        """
        Get all holonomy events tracked so far.

        Holonomy (H) represents irreversible-ish actions that scar both the world
        (via EnvState changes) and the manifold (via worldview commitment).
        These are actions that cannot be cleanly reversed.

        Returns:
            List of holonomy event dicts with agent_id, tick, type, description
        """
        return self._holonomy_events.copy()

    def get_holonomy_rate(self, tick_window: Optional[int] = None) -> float:
        """
        Compute holonomy rate (H_rate) over a tick window.

        H_rate is the frequency of irreversible-ish changes per unit epistemic "churn".
        This is a geometric health scalar.

        Args:
            tick_window: Optional window size in ticks. If None, uses all events.

        Returns:
            Holonomy rate (events per tick)
        """
        if not self._holonomy_events:
            return 0.0

        if tick_window is None:
            # Use all events
            total_ticks = max((e["tick"] for e in self._holonomy_events), default=1)
            return len(self._holonomy_events) / max(total_ticks, 1)

        # Count events in window
        recent_events = [e for e in self._holonomy_events if e["tick"] >= (max(e["tick"] for e in self._holonomy_events) - tick_window)]
        return len(recent_events) / tick_window

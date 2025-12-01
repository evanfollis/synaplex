# synaplex/meta/logging.py

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from synaplex.core.ids import AgentId, WorldId


@dataclass
class TickEvent:
    """A single event recorded during a tick."""
    tick: int
    agent_id: str
    event_type: str  # "percept", "reasoning", "action", "manifold_update"
    data: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class RunMetadata:
    """Metadata about an experiment run."""
    world_id: str
    start_time: str
    end_time: Optional[str] = None
    total_ticks: int = 0
    agent_ids: List[str] = field(default_factory=list)
    config_hash: Optional[str] = None
    notes: Optional[str] = None


class RunLogger:
    """
    Records events during a run for later analysis.
    
    Logs:
    - Per-tick events (percepts, reasoning outputs, actions)
    - Manifold snapshots at configurable intervals
    - Projection/signal flows
    - EnvState snapshots
    - Run metadata
    """
    
    def __init__(
        self,
        world_id: WorldId,
        log_dir: str | Path = "logs",
        snapshot_interval: int = 1,
    ) -> None:
        """
        Initialize logger.
        
        Args:
            world_id: World identifier
            log_dir: Directory to store logs
            snapshot_interval: How often to capture manifold snapshots (every N ticks)
        """
        self.world_id = world_id
        self.log_dir = Path(log_dir) / world_id.value
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.snapshot_interval = snapshot_interval
        
        self.events: List[TickEvent] = []
        self.metadata = RunMetadata(
            world_id=world_id.value,
            start_time=datetime.utcnow().isoformat(),
        )
        self._current_tick = 0
    
    def log_percept(self, agent_id: AgentId, tick: int, percept_data: Dict[str, Any]) -> None:
        """Log a percept event."""
        self._current_tick = max(self._current_tick, tick)
        event = TickEvent(
            tick=tick,
            agent_id=agent_id.value,
            event_type="percept",
            data=percept_data,
        )
        self.events.append(event)
    
    def log_reasoning(
        self,
        agent_id: AgentId,
        tick: int,
        reasoning_output: Dict[str, Any],
    ) -> None:
        """Log a reasoning event."""
        self._current_tick = max(self._current_tick, tick)
        # Don't log full manifold content, just metadata
        safe_data = {
            "agent_id": reasoning_output.get("agent_id"),
            "notes_length": len(reasoning_output.get("notes", "")),
            "outward": reasoning_output.get("outward", {}),
            "context_keys": list(reasoning_output.get("context", {}).keys()),
        }
        event = TickEvent(
            tick=tick,
            agent_id=agent_id.value,
            event_type="reasoning",
            data=safe_data,
        )
        self.events.append(event)
    
    def log_action(
        self,
        agent_id: AgentId,
        tick: int,
        action_data: Dict[str, Any],
    ) -> None:
        """Log an action event."""
        self._current_tick = max(self._current_tick, tick)
        event = TickEvent(
            tick=tick,
            agent_id=agent_id.value,
            event_type="action",
            data=action_data,
        )
        self.events.append(event)
    
    def log_manifold_snapshot(
        self,
        agent_id: AgentId,
        tick: int,
        version: int,
        content_length: int,
        metadata: Dict[str, Any],
    ) -> None:
        """Log a manifold snapshot (without content, just metadata)."""
        if tick % self.snapshot_interval != 0:
            return  # Only log at intervals
        
        self._current_tick = max(self._current_tick, tick)
        event = TickEvent(
            tick=tick,
            agent_id=agent_id.value,
            event_type="manifold_snapshot",
            data={
                "version": version,
                "content_length": content_length,
                "metadata": metadata,
            },
        )
        self.events.append(event)
    
    def log_env_state_snapshot(self, tick: int, env_state_data: Dict[str, Any]) -> None:
        """Log an EnvState snapshot."""
        self._current_tick = max(self._current_tick, tick)
        event = TickEvent(
            tick=tick,
            agent_id="__env_state__",
            event_type="env_state_snapshot",
            data=env_state_data,
        )
        self.events.append(event)
    
    def set_agent_ids(self, agent_ids: List[AgentId]) -> None:
        """Record which agents are in this run."""
        self.metadata.agent_ids = [a.value for a in agent_ids]
    
    def set_config_hash(self, config_hash: str) -> None:
        """Set configuration hash for reproducibility."""
        self.metadata.config_hash = config_hash
    
    def set_notes(self, notes: str) -> None:
        """Add notes about this run."""
        self.metadata.notes = notes
    
    def finalize(self) -> None:
        """Finalize the run and write logs to disk."""
        self.metadata.end_time = datetime.utcnow().isoformat()
        self.metadata.total_ticks = self._current_tick + 1
        
        # Write events
        events_file = self.log_dir / "events.jsonl"
        with open(events_file, "w", encoding="utf-8") as f:
            for event in self.events:
                f.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")
        
        # Write metadata
        metadata_file = self.log_dir / "metadata.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(asdict(self.metadata), f, indent=2, ensure_ascii=False)
    
    def query_events(
        self,
        agent_id: Optional[str] = None,
        event_type: Optional[str] = None,
        tick_range: Optional[tuple[int, int]] = None,
    ) -> List[TickEvent]:
        """
        Query logged events.
        
        Args:
            agent_id: Filter by agent ID
            event_type: Filter by event type
            tick_range: Filter by tick range (start, end)
        
        Returns:
            List of matching events
        """
        results = self.events
        
        if agent_id:
            results = [e for e in results if e.agent_id == agent_id]
        
        if event_type:
            results = [e for e in results if e.event_type == event_type]
        
        if tick_range:
            start, end = tick_range
            results = [e for e in results if start <= e.tick <= end]
        
        return results
    
    def get_agent_timeline(self, agent_id: str) -> List[TickEvent]:
        """Get all events for a specific agent in chronological order."""
        return sorted(
            [e for e in self.events if e.agent_id == agent_id],
            key=lambda e: e.tick
        )
    
    def get_tick_summary(self, tick: int) -> Dict[str, Any]:
        """Get summary of all events at a specific tick."""
        tick_events = [e for e in self.events if e.tick == tick]
        return {
            "tick": tick,
            "event_count": len(tick_events),
            "agents": list(set(e.agent_id for e in tick_events)),
            "event_types": list(set(e.event_type for e in tick_events)),
            "events": [asdict(e) for e in tick_events],
        }


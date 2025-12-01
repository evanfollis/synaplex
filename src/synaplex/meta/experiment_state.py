# synaplex/meta/experiment_state.py

from __future__ import annotations

import json
import pickle
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from synaplex.core.ids import AgentId, WorldId
from synaplex.core.dna import DNA
from synaplex.core.runtime_inprocess import GraphConfig
from synaplex.cognition.manifolds import ManifoldStore


@dataclass
class ExperimentCheckpoint:
    """Checkpoint state for an experiment."""
    experiment_id: str
    world_id: str
    tick: int
    timestamp: str
    agent_ids: List[str]
    dna_snapshots: Dict[str, Dict[str, Any]]  # agent_id -> DNA dict
    graph_config: Optional[Dict[str, Any]] = None
    env_state: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExperimentState:
    """State management for long-horizon experiments."""
    experiment_id: str
    world_id: WorldId
    checkpoint_dir: Path
    checkpoint_interval: int = 10  # Checkpoint every N ticks
    last_checkpoint_tick: int = -1
    
    def __init__(
        self,
        experiment_id: str,
        world_id: WorldId,
        checkpoint_dir: str | Path = "checkpoints",
        checkpoint_interval: int = 10,
    ) -> None:
        """
        Initialize experiment state.
        
        Args:
            experiment_id: Unique experiment identifier
            world_id: World ID
            checkpoint_dir: Directory for checkpoints
            checkpoint_interval: How often to checkpoint (in ticks)
        """
        self.experiment_id = experiment_id
        self.world_id = world_id
        self.checkpoint_dir = Path(checkpoint_dir) / experiment_id
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_interval = checkpoint_interval
        self.last_checkpoint_tick = -1
    
    def should_checkpoint(self, current_tick: int) -> bool:
        """Check if we should create a checkpoint."""
        if current_tick == 0:
            return True  # Always checkpoint at start
        return (current_tick - self.last_checkpoint_tick) >= self.checkpoint_interval
    
    def save_checkpoint(
        self,
        tick: int,
        agent_ids: List[AgentId],
        dna_dict: Dict[AgentId, DNA],
        graph_config: Optional[GraphConfig] = None,
        env_state: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        Save a checkpoint.
        
        Args:
            tick: Current tick
            agent_ids: List of agent IDs
            dna_dict: DNA for each agent
            graph_config: Graph configuration
            env_state: Environment state
            metadata: Additional metadata
            
        Returns:
            Path to saved checkpoint
        """
        checkpoint = ExperimentCheckpoint(
            experiment_id=self.experiment_id,
            world_id=self.world_id.value,
            tick=tick,
            timestamp=datetime.utcnow().isoformat(),
            agent_ids=[aid.value for aid in agent_ids],
            dna_snapshots={
                aid.value: asdict(dna) for aid, dna in dna_dict.items()
            },
            graph_config=asdict(graph_config) if graph_config else None,
            env_state=env_state,
            metadata=metadata or {},
        )
        
        # Save checkpoint
        checkpoint_file = self.checkpoint_dir / f"checkpoint_tick_{tick}.json"
        with open(checkpoint_file, "w", encoding="utf-8") as f:
            json.dump(asdict(checkpoint), f, indent=2, ensure_ascii=False)
        
        # Also save latest checkpoint pointer
        latest_file = self.checkpoint_dir / "latest_checkpoint.json"
        with open(latest_file, "w", encoding="utf-8") as f:
            json.dump({"tick": tick, "file": str(checkpoint_file)}, f)
        
        self.last_checkpoint_tick = tick
        return checkpoint_file
    
    def load_checkpoint(self, tick: Optional[int] = None) -> Optional[ExperimentCheckpoint]:
        """
        Load a checkpoint.
        
        Args:
            tick: Specific tick to load (default: latest)
            
        Returns:
            Checkpoint or None if not found
        """
        if tick is None:
            # Load latest
            latest_file = self.checkpoint_dir / "latest_checkpoint.json"
            if not latest_file.exists():
                return None
            
            with open(latest_file, "r", encoding="utf-8") as f:
                latest_info = json.load(f)
                tick = latest_info.get("tick")
        
        checkpoint_file = self.checkpoint_dir / f"checkpoint_tick_{tick}.json"
        if not checkpoint_file.exists():
            return None
        
        with open(checkpoint_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return ExperimentCheckpoint(**data)
    
    def list_checkpoints(self) -> List[int]:
        """List all available checkpoint ticks."""
        checkpoints = []
        for file in self.checkpoint_dir.glob("checkpoint_tick_*.json"):
            try:
                tick_str = file.stem.split("_")[-1]
                tick = int(tick_str)
                checkpoints.append(tick)
            except (ValueError, IndexError):
                continue
        
        return sorted(checkpoints)
    
    def get_progress(self) -> Dict[str, Any]:
        """Get experiment progress information."""
        checkpoints = self.list_checkpoints()
        latest_checkpoint = self.load_checkpoint()
        
        return {
            "experiment_id": self.experiment_id,
            "world_id": self.world_id.value,
            "num_checkpoints": len(checkpoints),
            "latest_tick": latest_checkpoint.tick if latest_checkpoint else -1,
            "checkpoint_interval": self.checkpoint_interval,
        }


class IncrementalLogger:
    """
    Incremental logger that writes to disk incrementally.
    
    Prevents memory issues in long-horizon experiments.
    """
    
    def __init__(
        self,
        experiment_id: str,
        log_dir: str | Path = "logs",
        flush_interval: int = 10,  # Flush every N events
    ) -> None:
        """
        Initialize incremental logger.
        
        Args:
            experiment_id: Experiment identifier
            log_dir: Log directory
            flush_interval: How often to flush to disk
        """
        self.experiment_id = experiment_id
        self.log_dir = Path(log_dir) / experiment_id
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.flush_interval = flush_interval
        
        self.events_buffer: List[Dict[str, Any]] = []
        self.events_file = self.log_dir / "events.jsonl"
        
        # Open file in append mode
        self._file_handle = open(self.events_file, "a", encoding="utf-8")
    
    def log_event(self, event: Dict[str, Any]) -> None:
        """Log an event (buffered)."""
        self.events_buffer.append(event)
        
        if len(self.events_buffer) >= self.flush_interval:
            self.flush()
    
    def flush(self) -> None:
        """Flush buffered events to disk."""
        for event in self.events_buffer:
            self._file_handle.write(json.dumps(event, ensure_ascii=False) + "\n")
        self._file_handle.flush()
        self.events_buffer.clear()
    
    def close(self) -> None:
        """Close the logger."""
        self.flush()
        self._file_handle.close()


class ExperimentRunner:
    """
    Runner for long-horizon experiments with checkpoint/resume support.
    """
    
    def __init__(
        self,
        experiment_id: str,
        world_id: WorldId,
        checkpoint_dir: str | Path = "checkpoints",
        log_dir: str | Path = "logs",
        checkpoint_interval: int = 10,
    ) -> None:
        """
        Initialize experiment runner.
        
        Args:
            experiment_id: Experiment identifier
            world_id: World ID
            checkpoint_dir: Checkpoint directory
            log_dir: Log directory
            checkpoint_interval: Checkpoint interval
        """
        self.experiment_id = experiment_id
        self.world_id = world_id
        self.state = ExperimentState(
            experiment_id=experiment_id,
            world_id=world_id,
            checkpoint_dir=checkpoint_dir,
            checkpoint_interval=checkpoint_interval,
        )
        self.incremental_logger = IncrementalLogger(
            experiment_id=experiment_id,
            log_dir=log_dir,
        )
    
    def run_with_checkpoints(
        self,
        runtime: Any,  # InProcessRuntime
        num_ticks: int,
        start_tick: int = 0,
    ) -> None:
        """
        Run experiment with checkpointing.
        
        Args:
            runtime: Runtime to run
            num_ticks: Number of ticks to run
            start_tick: Starting tick (for resume)
        """
        for tick in range(start_tick, start_tick + num_ticks):
            # Run tick
            runtime.tick(tick)
            
            # Checkpoint if needed
            if self.state.should_checkpoint(tick):
                agent_ids = list(runtime.get_agents().keys())
                dna_dict = {
                    agent_id: runtime._dna[agent_id]
                    for agent_id in agent_ids
                    if agent_id in runtime._dna
                }
                
                self.state.save_checkpoint(
                    tick=tick,
                    agent_ids=agent_ids,
                    dna_dict=dna_dict,
                    graph_config=runtime.graph_config,
                    env_state=runtime.env_state.data if runtime.env_state else None,
                )
            
            # Log events incrementally
            # (In full implementation, would capture events from runtime)
        
        # Final checkpoint
        final_tick = start_tick + num_ticks - 1
        if self.state.should_checkpoint(final_tick):
            agent_ids = list(runtime.get_agents().keys())
            dna_dict = {
                agent_id: runtime._dna[agent_id]
                for agent_id in agent_ids
                if agent_id in runtime._dna
            }
            self.state.save_checkpoint(
                tick=final_tick,
                agent_ids=agent_ids,
                dna_dict=dna_dict,
                graph_config=runtime.graph_config,
                env_state=runtime.env_state.data if runtime.env_state else None,
            )
        
        # Close logger
        self.incremental_logger.close()
    
    def resume_from_checkpoint(
        self,
        tick: Optional[int] = None,
    ) -> Optional[ExperimentCheckpoint]:
        """
        Resume from a checkpoint.
        
        Args:
            tick: Specific tick to resume from (default: latest)
            
        Returns:
            Checkpoint data
        """
        checkpoint = self.state.load_checkpoint(tick)
        return checkpoint
    
    def get_progress(self) -> Dict[str, Any]:
        """Get experiment progress."""
        return self.state.get_progress()


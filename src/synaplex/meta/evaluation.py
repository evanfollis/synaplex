# synaplex/meta/evaluation.py

from __future__ import annotations

from typing import Any, Dict, List, Optional

from synaplex.core.ids import AgentId
from synaplex.meta.logging import RunLogger, TickEvent
from synaplex.meta.trajectories import TrajectoryAnalyzer
from synaplex.manifolds_indexers.indexer_world.agents import EmbeddingAgent


class MetricsEngine:
    """
    Computes metrics over runs for evaluation.
    
    Metrics include:
    - Divergence between worldviews
    - Stability of behavior under perturbations
    - Task performance (if tasks are defined)
    - Population statistics
    """
    
    def __init__(self, embedding_agent: Optional[EmbeddingAgent] = None) -> None:
        """
        Initialize metrics engine.
        
        Args:
            embedding_agent: Optional embedding agent for similarity computation
        """
        self.embedding_agent = embedding_agent or EmbeddingAgent()
        self.trajectory_analyzer = TrajectoryAnalyzer(embedding_agent=self.embedding_agent)
    
    def evaluate_run(
        self,
        logger: RunLogger,
        agent_ids: Optional[List[AgentId]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate a run from logs.
        
        Args:
            logger: RunLogger with logged events
            agent_ids: Optional list of agent IDs to evaluate (default: all)
            
        Returns:
            Metrics dictionary
        """
        if agent_ids is None:
            agent_ids = [AgentId(aid) for aid in logger.metadata.agent_ids]
        
        # Get all events
        all_events = logger.events
        
        # Compute per-agent metrics
        agent_metrics = {}
        for agent_id in agent_ids:
            agent_events = logger.get_agent_timeline(agent_id.value)
            agent_metrics[agent_id.value] = self._compute_agent_metrics(
                agent_id,
                agent_events,
            )
        
        # Compute population-level metrics
        population_metrics = self._compute_population_metrics(agent_metrics)
        
        # Compute divergence metrics
        divergence_metrics = self._compute_divergence_metrics(
            logger,
            agent_ids,
        )
        
        return {
            "agent_metrics": agent_metrics,
            "population_metrics": population_metrics,
            "divergence_metrics": divergence_metrics,
            "run_metadata": {
                "total_ticks": logger.metadata.total_ticks,
                "num_agents": len(agent_ids),
            },
        }
    
    def _compute_agent_metrics(
        self,
        agent_id: AgentId,
        events: List[TickEvent],
    ) -> Dict[str, Any]:
        """Compute metrics for a single agent."""
        reasoning_events = [e for e in events if e.event_type == "reasoning"]
        action_events = [e for e in events if e.event_type == "action"]
        manifold_events = [e for e in events if e.event_type == "manifold_snapshot"]
        
        # Activity metrics
        reasoning_count = len(reasoning_events)
        action_count = len(action_events)
        manifold_updates = len(manifold_events)
        
        # Stability: variance in reasoning output length
        reasoning_lengths = [
            e.data.get("notes_length", 0) for e in reasoning_events
        ]
        stability = 1.0
        if len(reasoning_lengths) > 1:
            mean_length = sum(reasoning_lengths) / len(reasoning_lengths)
            if mean_length > 0:
                variance = sum((x - mean_length) ** 2 for x in reasoning_lengths) / len(reasoning_lengths)
                # Normalize stability (lower variance = higher stability)
                stability = max(0.0, 1.0 - (variance / (mean_length ** 2 + 1)))
        
        return {
            "reasoning_count": reasoning_count,
            "action_count": action_count,
            "manifold_updates": manifold_updates,
            "stability": stability,
            "avg_reasoning_length": sum(reasoning_lengths) / len(reasoning_lengths) if reasoning_lengths else 0,
        }
    
    def _compute_population_metrics(
        self,
        agent_metrics: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Compute population-level statistics."""
        if not agent_metrics:
            return {}
        
        # Aggregate statistics
        stabilities = [m.get("stability", 0.0) for m in agent_metrics.values()]
        reasoning_counts = [m.get("reasoning_count", 0) for m in agent_metrics.values()]
        
        return {
            "num_agents": len(agent_metrics),
            "avg_stability": sum(stabilities) / len(stabilities) if stabilities else 0.0,
            "stability_variance": (
                sum((s - sum(stabilities) / len(stabilities)) ** 2 for s in stabilities) / len(stabilities)
                if len(stabilities) > 1 else 0.0
            ),
            "avg_reasoning_count": sum(reasoning_counts) / len(reasoning_counts) if reasoning_counts else 0,
            "total_reasoning_events": sum(reasoning_counts),
        }
    
    def _compute_divergence_metrics(
        self,
        logger: RunLogger,
        agent_ids: List[AgentId],
    ) -> Dict[str, Any]:
        """
        Compute divergence metrics between agents.
        
        Uses manifold snapshots to compute worldview divergence.
        """
        if len(agent_ids) < 2:
            return {"divergence": 0.0, "convergence": 0.0}
        
        # Get final manifold snapshots for each agent
        final_snapshots = {}
        for agent_id in agent_ids:
            manifold_events = [
                e for e in logger.get_agent_timeline(agent_id.value)
                if e.event_type == "manifold_snapshot"
            ]
            if manifold_events:
                # Get latest snapshot
                latest = max(manifold_events, key=lambda e: e.data.get("version", 0))
                final_snapshots[agent_id.value] = latest
        
        if len(final_snapshots) < 2:
            return {"divergence": 0.0, "convergence": 0.0}
        
        # Compute pairwise similarities
        similarities = []
        agent_list = list(final_snapshots.keys())
        
        for i in range(len(agent_list)):
            for j in range(i + 1, len(agent_list)):
                agent1 = agent_list[i]
                agent2 = agent_list[j]
                
                # Create snapshot-like objects for embedding
                # Note: In full implementation, would load actual content
                # For now, use metadata to estimate similarity
                snapshot1 = type('Snapshot', (), {
                    'agent_id': AgentId(agent1),
                    'version': final_snapshots[agent1].data.get("version", 0),
                    'content': "",  # Would load actual content
                    'metadata': final_snapshots[agent1].data.get("metadata", {}),
                })()
                
                snapshot2 = type('Snapshot', (), {
                    'agent_id': AgentId(agent2),
                    'version': final_snapshots[agent2].data.get("version", 0),
                    'content': "",
                    'metadata': final_snapshots[agent2].data.get("metadata", {}),
                })()
                
                # Compute embeddings (simplified)
                emb1 = self.embedding_agent.embed(snapshot1)
                emb2 = self.embedding_agent.embed(snapshot2)
                
                # Cosine similarity
                dot_product = sum(a * b for a, b in zip(emb1, emb2))
                similarity = max(0.0, min(1.0, dot_product))
                similarities.append(similarity)
        
        avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0
        
        # Divergence is inverse of similarity
        divergence = 1.0 - avg_similarity
        
        return {
            "avg_similarity": avg_similarity,
            "divergence": divergence,
            "pairwise_similarities": similarities,
            "num_pairs": len(similarities),
        }
    
    def compute_stability_under_perturbation(
        self,
        baseline_logger: RunLogger,
        perturbed_logger: RunLogger,
        agent_id: AgentId,
    ) -> Dict[str, Any]:
        """
        Compute stability of an agent under perturbation.
        
        Compares behavior between baseline and perturbed runs.
        
        Args:
            baseline_logger: Logger for baseline run
            perturbed_logger: Logger for perturbed run
            agent_id: Agent to analyze
            
        Returns:
            Stability metrics
        """
        baseline_events = baseline_logger.get_agent_timeline(agent_id.value)
        perturbed_events = perturbed_logger.get_agent_timeline(agent_id.value)
        
        baseline_metrics = self._compute_agent_metrics(agent_id, baseline_events)
        perturbed_metrics = self._compute_agent_metrics(agent_id, perturbed_events)
        
        # Compute stability as similarity of metrics
        stability_score = 1.0
        for key in baseline_metrics:
            if key in perturbed_metrics:
                baseline_val = baseline_metrics[key]
                perturbed_val = perturbed_metrics[key]
                if isinstance(baseline_val, (int, float)) and isinstance(perturbed_val, (int, float)):
                    if baseline_val != 0:
                        relative_diff = abs(perturbed_val - baseline_val) / abs(baseline_val)
                        stability_score *= (1.0 - min(1.0, relative_diff))
        
        return {
            "stability_score": stability_score,
            "baseline_metrics": baseline_metrics,
            "perturbed_metrics": perturbed_metrics,
        }
    
    def compute_task_performance(
        self,
        logger: RunLogger,
        task_definitions: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Compute task performance metrics.
        
        Args:
            logger: RunLogger with events
            task_definitions: Task definitions with success criteria
            
        Returns:
            Performance metrics
        """
        # Placeholder: In full implementation, would evaluate tasks
        # based on EnvState changes, signal patterns, etc.
        
        return {
            "tasks_defined": len(task_definitions),
            "tasks_completed": 0,  # Would compute from events
            "success_rate": 0.0,
        }

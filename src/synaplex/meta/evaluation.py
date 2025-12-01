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
    
    This class implements evaluation metrics that map to the geometric health scalars
    defined in GEOMETRIC_CONSTITUTION.md:
    
    Geometric Health Scalars (target interface):
    - D (Dimensionality Retention): rank of active directions in T M participating in flows;
      "how many genuinely different lenses are live?"
      → Can be computed from manifold diversity, embedding dimensionality, or conceptual spread
    
    - R_div (Refraction Diversity): diversity of responses to a shared perturbation P
      across manifolds {M_i}. Practically: dispersion of downstream trajectories after
      a common input.
      → Current implementation: divergence_metrics captures worldview divergence;
        can be extended to measure response diversity to same perturbation
    
    - A_sat (Attractor Saturation): proportion of M lying in deep basins of a few attractors
      vs shallow / exploratory regions.
      → Can be computed from manifold content concentration, topic clustering, or
        stability metrics (current stability metric is a proxy)
    
    - H_rate (Holonomy Density): rate of loops in (M × W) that produce non-trivial holonomy
      per unit epistemic "churn."
      → Can be computed from action_events count, EnvState mutation rate, or
        irreversible action frequency
    
    - T (Temperature): effective ease of deformation; how easily flows can reshape M.
      High T: fluid, chaotic; low T: frozen, brittle.
      → Can be computed from variance in reasoning outputs, manifold update frequency,
        or response sensitivity to perturbations
    
    Current implementation provides:
    - Divergence between worldviews (maps to R_div)
    - Stability of behavior under perturbations (maps to T and A_sat)
    - Task performance (if tasks are defined)
    - Population statistics (foundation for D, R_div, A_sat)
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

    def compute_dimensionality(
        self,
        logger: RunLogger,
        agent_ids: Optional[List[AgentId]] = None,
    ) -> float:
        """
        Compute D (Dimensionality Retention): rank of active directions in T M.

        Measures "how many genuinely different lenses are live?" - the diversity
        of active conceptual directions across manifolds.

        Args:
            logger: RunLogger with events
            agent_ids: Optional list of agent IDs (default: all)

        Returns:
            Dimensionality score (0-1, higher = more diverse)
        """
        if agent_ids is None:
            agent_ids = [AgentId(aid) for aid in logger.metadata.agent_ids]

        if len(agent_ids) < 2:
            return 0.0

        # Get final manifold snapshots
        snapshots = []
        for agent_id in agent_ids:
            manifold_events = [
                e for e in logger.get_agent_timeline(agent_id.value)
                if e.event_type == "manifold_snapshot"
            ]
            if manifold_events:
                latest = max(manifold_events, key=lambda e: e.data.get("version", 0))
                # Create snapshot-like object
                snapshot = type('Snapshot', (), {
                    'agent_id': agent_id,
                    'version': latest.data.get("version", 0),
                    'content': "",
                    'metadata': latest.data.get("metadata", {}),
                })()
                snapshots.append(snapshot)

        if len(snapshots) < 2:
            return 0.0

        # Compute embeddings
        embeddings = {}
        for snapshot in snapshots:
            emb = self.embedding_agent.embed(snapshot)
            embeddings[snapshot.agent_id.value] = emb

        # Compute pairwise distances (diversity measure)
        distances = []
        agent_list = list(embeddings.keys())
        for i in range(len(agent_list)):
            for j in range(i + 1, len(agent_list)):
                emb1 = embeddings[agent_list[i]]
                emb2 = embeddings[agent_list[j]]
                # Euclidean distance
                dist = sum((a - b) ** 2 for a, b in zip(emb1, emb2)) ** 0.5
                distances.append(dist)

        if not distances:
            return 0.0

        # Normalize: higher average distance = higher dimensionality
        avg_distance = sum(distances) / len(distances)
        # Normalize to [0, 1] (assuming max distance is around 2.0 for normalized embeddings)
        dimensionality = min(1.0, avg_distance / 2.0)

        return dimensionality

    def compute_refraction_diversity(
        self,
        logger: RunLogger,
        agent_ids: Optional[List[AgentId]] = None,
    ) -> float:
        """
        Compute R_div (Refraction Diversity): diversity of responses to shared perturbation.

        Measures dispersion of downstream trajectories after a common input across manifolds.

        Args:
            logger: RunLogger with events
            agent_ids: Optional list of agent IDs (default: all)

        Returns:
            Refraction diversity score (0-1, higher = more diverse responses)
        """
        if agent_ids is None:
            agent_ids = [AgentId(aid) for aid in logger.metadata.agent_ids]

        if len(agent_ids) < 2:
            return 0.0

        # Get reasoning outputs for same tick (shared perturbation)
        # Group by tick and compute variance in responses
        tick_responses: Dict[int, List[Dict[str, Any]]] = {}
        for agent_id in agent_ids:
            events = logger.get_agent_timeline(agent_id.value)
            reasoning_events = [e for e in events if e.event_type == "reasoning"]
            for event in reasoning_events:
                tick = event.tick
                if tick not in tick_responses:
                    tick_responses[tick] = []
                tick_responses[tick].append(event.data)

        if not tick_responses:
            return 0.0

        # Compute variance in response characteristics across agents per tick
        diversities = []
        for tick, responses in tick_responses.items():
            if len(responses) < 2:
                continue

            # Measure diversity in response length, structure, etc.
            response_lengths = [r.get("notes_length", len(str(r.get("notes", "")))) for r in responses]
            if len(response_lengths) > 1:
                mean_length = sum(response_lengths) / len(response_lengths)
                if mean_length > 0:
                    variance = sum((x - mean_length) ** 2 for x in response_lengths) / len(response_lengths)
                    # Normalize variance
                    diversity = min(1.0, variance / (mean_length ** 2 + 1))
                    diversities.append(diversity)

        if not diversities:
            return 0.0

        # Average diversity across ticks
        return sum(diversities) / len(diversities)

    def compute_attractor_saturation(
        self,
        logger: RunLogger,
        agent_id: AgentId,
    ) -> float:
        """
        Compute A_sat (Attractor Saturation): proportion in deep basins vs exploratory.

        Measures degree of over-commitment vs plasticity. High A_sat = frozen in attractors,
        low A_sat = exploratory and fluid.

        Args:
            logger: RunLogger with events
            agent_id: Agent to analyze

        Returns:
            Attractor saturation score (0-1, higher = more saturated/frozen)
        """
        events = logger.get_agent_timeline(agent_id.value)
        manifold_events = [e for e in events if e.event_type == "manifold_snapshot"]

        if len(manifold_events) < 2:
            return 0.0

        # Extract attractor hints from metadata if available
        attractor_counts = []
        for event in manifold_events:
            metadata = event.data.get("metadata", {})
            attractor_hints = metadata.get("attractor_hints", [])
            attractor_counts.append(len(attractor_hints))

        if not attractor_counts:
            # Fallback: use stability as proxy
            reasoning_events = [e for e in events if e.event_type == "reasoning"]
            if len(reasoning_events) < 2:
                return 0.0

            # High stability = high saturation
            reasoning_lengths = [e.data.get("notes_length", 0) for e in reasoning_events]
            mean_length = sum(reasoning_lengths) / len(reasoning_lengths) if reasoning_lengths else 0
            if mean_length > 0:
                variance = sum((x - mean_length) ** 2 for x in reasoning_lengths) / len(reasoning_lengths)
                stability = max(0.0, 1.0 - (variance / (mean_length ** 2 + 1)))
                return stability

            return 0.0

        # Use attractor count as saturation proxy
        # More attractors = more saturated (but normalize)
        avg_attractors = sum(attractor_counts) / len(attractor_counts)
        # Normalize: assume 0-10 attractors maps to 0-1
        saturation = min(1.0, avg_attractors / 10.0)

        return saturation

    def compute_holonomy_rate(
        self,
        logger: RunLogger,
        tick_window: Optional[int] = None,
    ) -> float:
        """
        Compute H_rate (Holonomy Density): rate of irreversible actions per unit churn.

        Measures frequency of holonomy events (irreversible-ish changes) per tick.

        Args:
            logger: RunLogger with events
            tick_window: Optional window size in ticks (default: all events)

        Returns:
            Holonomy rate (events per tick)
        """
        # Count holonomy events (actions marked as holonomy)
        action_events = [e for e in logger.events if e.event_type == "action"]
        holonomy_events = [
            e for e in action_events
            if e.data.get("holonomy_marker", False)
        ]

        if not holonomy_events:
            return 0.0

        if tick_window is None:
            # Use all events
            total_ticks = logger.metadata.total_ticks
            return len(holonomy_events) / max(total_ticks, 1)

        # Count events in window
        max_tick = max(e.tick for e in holonomy_events)
        window_start = max_tick - tick_window
        recent_events = [e for e in holonomy_events if e.tick >= window_start]
        return len(recent_events) / tick_window

    def compute_temperature(
        self,
        logger: RunLogger,
        agent_id: AgentId,
    ) -> float:
        """
        Compute T (Temperature): effective ease of deformation.

        High T: fluid, chaotic (easily reshaped by perturbations)
        Low T: frozen, brittle (resistant to change)

        Args:
            logger: RunLogger with events
            agent_id: Agent to analyze

        Returns:
            Temperature score (0-1, higher = more fluid/malleable)
        """
        events = logger.get_agent_timeline(agent_id.value)
        reasoning_events = [e for e in events if e.event_type == "reasoning"]
        manifold_events = [e for e in events if e.event_type == "manifold_snapshot"]

        if len(reasoning_events) < 2:
            return 0.5  # Neutral temperature

        # Measure variance in reasoning outputs (high variance = high temperature)
        reasoning_lengths = [e.data.get("notes_length", len(str(e.data.get("notes", "")))) for e in reasoning_events]
        mean_length = sum(reasoning_lengths) / len(reasoning_lengths) if reasoning_lengths else 0

        if mean_length == 0:
            return 0.5

        variance = sum((x - mean_length) ** 2 for x in reasoning_lengths) / len(reasoning_lengths)
        # Normalize variance to [0, 1]
        normalized_variance = min(1.0, variance / (mean_length ** 2 + 1))

        # Measure update frequency (more frequent = higher temperature)
        update_frequency = len(manifold_events) / max(len(reasoning_events), 1)
        normalized_frequency = min(1.0, update_frequency)

        # Temperature is combination of variance and update frequency
        temperature = (normalized_variance + normalized_frequency) / 2.0

        return temperature

    def compute_geometric_health(
        self,
        logger: RunLogger,
        agent_ids: Optional[List[AgentId]] = None,
    ) -> Dict[str, float]:
        """
        Compute all geometric health scalars for a run.

        Returns a dict with D, R_div, A_sat (per agent), H_rate, T (per agent).

        Args:
            logger: RunLogger with events
            agent_ids: Optional list of agent IDs (default: all)

        Returns:
            Dict with all health scalars
        """
        if agent_ids is None:
            agent_ids = [AgentId(aid) for aid in logger.metadata.agent_ids]

        health = {
            "D": self.compute_dimensionality(logger, agent_ids),
            "R_div": self.compute_refraction_diversity(logger, agent_ids),
            "H_rate": self.compute_holonomy_rate(logger),
        }

        # Per-agent metrics
        health["A_sat"] = {}
        health["T"] = {}
        for agent_id in agent_ids:
            health["A_sat"][agent_id.value] = self.compute_attractor_saturation(logger, agent_id)
            health["T"][agent_id.value] = self.compute_temperature(logger, agent_id)

        return health

# synaplex/meta/cultural_drift.py

from __future__ import annotations

from typing import Any, Dict, List, Optional

from synaplex.core.ids import AgentId
from synaplex.cognition.manifolds import ManifoldStore, ManifoldEnvelope
from synaplex.meta.logging import RunLogger
from synaplex.meta.trajectories import TrajectoryAnalyzer
from synaplex.manifolds_indexers.indexer_world.agents import EmbeddingAgent


class CulturalDriftAnalyzer:
    """
    Analyzes cultural drift and convergence/divergence in populations.
    
    Tracks how worldviews evolve relative to each other over time.
    """
    
    def __init__(self, embedding_agent: Optional[EmbeddingAgent] = None) -> None:
        """
        Initialize cultural drift analyzer.
        
        Args:
            embedding_agent: Optional embedding agent
        """
        self.embedding_agent = embedding_agent or EmbeddingAgent()
        self.trajectory_analyzer = TrajectoryAnalyzer(embedding_agent=self.embedding_agent)
    
    def analyze_cultural_drift(
        self,
        store: ManifoldStore,
        agent_ids: List[AgentId],
        logger: Optional[RunLogger] = None,
    ) -> Dict[str, Any]:
        """
        Analyze cultural drift in a population.
        
        Args:
            store: Manifold store
            agent_ids: List of agent IDs in population
            logger: Optional logger for temporal analysis
            
        Returns:
            Cultural drift metrics
        """
        if len(agent_ids) < 2:
            return {
                "drift": 0.0,
                "convergence": 0.0,
                "diversity": 0.0,
            }
        
        # Get current manifolds
        manifolds = {
            agent_id: store.load_latest(agent_id)
            for agent_id in agent_ids
        }
        
        # Filter out None
        valid_manifolds = {
            agent_id: env
            for agent_id, env in manifolds.items()
            if env is not None
        }
        
        if len(valid_manifolds) < 2:
            return {
                "drift": 0.0,
                "convergence": 0.0,
                "diversity": 0.0,
            }
        
        # Compute pairwise similarities
        similarities = self._compute_pairwise_similarities(valid_manifolds)
        
        # Diversity: inverse of average similarity
        avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0
        diversity = 1.0 - avg_similarity
        
        # Temporal analysis if logger available
        temporal_metrics = {}
        if logger:
            temporal_metrics = self._analyze_temporal_drift(logger, agent_ids)
        
        return {
            "diversity": diversity,
            "avg_similarity": avg_similarity,
            "pairwise_similarities": similarities,
            "num_pairs": len(similarities),
            "temporal_metrics": temporal_metrics,
        }
    
    def _compute_pairwise_similarities(
        self,
        manifolds: Dict[AgentId, ManifoldEnvelope],
    ) -> List[float]:
        """Compute pairwise similarities between manifolds."""
        similarities = []
        agent_list = list(manifolds.keys())
        
        for i in range(len(agent_list)):
            for j in range(i + 1, len(agent_list)):
                agent1 = agent_list[i]
                agent2 = agent_list[j]
                
                env1 = manifolds[agent1]
                env2 = manifolds[agent2]
                
                # Create snapshot-like objects
                snapshot1 = type('Snapshot', (), {
                    'agent_id': agent1,
                    'version': env1.version,
                    'content': env1.content,
                    'metadata': env1.metadata,
                })()
                
                snapshot2 = type('Snapshot', (), {
                    'agent_id': agent2,
                    'version': env2.version,
                    'content': env2.content,
                    'metadata': env2.metadata,
                })()
                
                # Compute embeddings and similarity
                emb1 = self.embedding_agent.embed(snapshot1)
                emb2 = self.embedding_agent.embed(snapshot2)
                
                # Cosine similarity
                dot_product = sum(a * b for a, b in zip(emb1, emb2))
                similarity = max(0.0, min(1.0, dot_product))
                similarities.append(similarity)
        
        return similarities
    
    def _analyze_temporal_drift(
        self,
        logger: RunLogger,
        agent_ids: List[AgentId],
    ) -> Dict[str, Any]:
        """
        Analyze temporal drift patterns.
        
        Tracks how similarity changes over time.
        """
        # Get manifold snapshots over time
        # (simplified: use final snapshots for now)
        # In full implementation, would track snapshots at each tick
        
        return {
            "temporal_analysis": "simplified",  # Placeholder
        }
    
    def detect_convergence(
        self,
        store: ManifoldStore,
        agent_ids: List[AgentId],
        threshold: float = 0.8,
    ) -> Dict[str, Any]:
        """
        Detect convergence in population.
        
        Args:
            store: Manifold store
            agent_ids: Agent IDs
            threshold: Similarity threshold for convergence
            
        Returns:
            Convergence analysis
        """
        drift_metrics = self.analyze_cultural_drift(store, agent_ids)
        
        avg_similarity = drift_metrics.get("avg_similarity", 0.0)
        is_converged = avg_similarity >= threshold
        
        return {
            "is_converged": is_converged,
            "avg_similarity": avg_similarity,
            "threshold": threshold,
            "convergence_strength": min(1.0, avg_similarity / threshold) if threshold > 0 else 0.0,
        }
    
    def detect_divergence(
        self,
        store: ManifoldStore,
        agent_ids: List[AgentId],
        threshold: float = 0.3,
    ) -> Dict[str, Any]:
        """
        Detect divergence in population.
        
        Args:
            store: Manifold store
            agent_ids: Agent IDs
            threshold: Similarity threshold for divergence
            
        Returns:
            Divergence analysis
        """
        drift_metrics = self.analyze_cultural_drift(store, agent_ids)
        
        avg_similarity = drift_metrics.get("avg_similarity", 1.0)
        is_diverged = avg_similarity <= threshold
        
        return {
            "is_diverged": is_diverged,
            "avg_similarity": avg_similarity,
            "threshold": threshold,
            "divergence_strength": min(1.0, (1.0 - avg_similarity) / (1.0 - threshold)) if threshold < 1.0 else 0.0,
        }
    
    def track_cultural_evolution(
        self,
        initial_store: ManifoldStore,
        final_store: ManifoldStore,
        agent_ids: List[AgentId],
    ) -> Dict[str, Any]:
        """
        Track cultural evolution between two time points.
        
        Args:
            initial_store: Store with initial manifolds
            final_store: Store with final manifolds
            agent_ids: Agent IDs
            
        Returns:
            Evolution analysis
        """
        initial_manifolds = {
            agent_id: initial_store.load_latest(agent_id)
            for agent_id in agent_ids
        }
        final_manifolds = {
            agent_id: final_store.load_latest(agent_id)
            for agent_id in agent_ids
        }
        
        # Filter valid
        initial_valid = {k: v for k, v in initial_manifolds.items() if v is not None}
        final_valid = {k: v for k, v in final_manifolds.items() if v is not None}
        
        if len(initial_valid) < 2 or len(final_valid) < 2:
            return {
                "evolution": "insufficient_data",
            }
        
        # Compute initial and final similarities
        initial_similarities = self._compute_pairwise_similarities(initial_valid)
        final_similarities = self._compute_pairwise_similarities(final_valid)
        
        initial_avg = sum(initial_similarities) / len(initial_similarities) if initial_similarities else 0.0
        final_avg = sum(final_similarities) / len(final_similarities) if final_similarities else 0.0
        
        # Evolution direction
        change = final_avg - initial_avg
        if change > 0.1:
            direction = "converging"
        elif change < -0.1:
            direction = "diverging"
        else:
            direction = "stable"
        
        return {
            "initial_avg_similarity": initial_avg,
            "final_avg_similarity": final_avg,
            "change": change,
            "direction": direction,
            "convergence_strength": max(0.0, change) if change > 0 else 0.0,
            "divergence_strength": max(0.0, -change) if change < 0 else 0.0,
        }
    
    def identify_cultural_clusters(
        self,
        store: ManifoldStore,
        agent_ids: List[AgentId],
        n_clusters: int = 3,
    ) -> Dict[str, Any]:
        """
        Identify cultural clusters in population.
        
        Groups agents with similar worldviews.
        
        Args:
            store: Manifold store
            agent_ids: Agent IDs
            n_clusters: Number of clusters
            
        Returns:
            Cluster assignments
        """
        from synaplex.manifolds_indexers.indexer_world.agents import ClusteringAgent
        
        # Get manifolds
        manifolds = {
            agent_id: store.load_latest(agent_id)
            for agent_id in agent_ids
        }
        valid_manifolds = {k: v for k, v in manifolds.items() if v is not None}
        
        if len(valid_manifolds) < 2:
            return {
                "clusters": {},
                "num_clusters": 0,
            }
        
        # Create snapshots
        snapshots = []
        for agent_id, env in valid_manifolds.items():
            snapshot = type('Snapshot', (), {
                'agent_id': agent_id,
                'version': env.version,
                'content': env.content,
                'metadata': env.metadata,
            })()
            snapshots.append(snapshot)
        
        # Generate embeddings
        embeddings = {}
        for snapshot in snapshots:
            key = f"{snapshot.agent_id.value}_v{snapshot.version}"
            embeddings[key] = self.embedding_agent.embed(snapshot)
        
        # Cluster
        clustering_agent = ClusteringAgent(n_clusters=n_clusters)
        clusters = clustering_agent.cluster(embeddings, self.embedding_agent)
        
        # Map back to agent IDs
        agent_clusters = {}
        for key, cluster_id in clusters.items():
            # Extract agent_id from key
            agent_id_str = key.split('_v')[0]
            agent_id = AgentId(agent_id_str)
            agent_clusters[agent_id.value] = cluster_id
        
        return {
            "clusters": agent_clusters,
            "num_clusters": len(set(clusters.values())),
            "cluster_sizes": {
                cluster_id: sum(1 for cid in clusters.values() if cid == cluster_id)
                for cluster_id in set(clusters.values())
            },
        }


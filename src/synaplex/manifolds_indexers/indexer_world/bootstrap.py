# synaplex/manifolds_indexers/indexer_world/bootstrap.py

from __future__ import annotations

from typing import Dict, List, Optional

from ..types import ManifoldSnapshot
from .agents import (
    EmbeddingAgent,
    ClusteringAgent,
    TrajectoryAgent,
)


class IndexerWorld:
    """
    Indexer world for offline manifold analysis.
    
    Processes exported manifold snapshots to:
    - Generate embeddings
    - Cluster similar worldviews
    - Analyze trajectories
    """
    
    def __init__(
        self,
        embedding_dim: int = 128,
        n_clusters: int = 5,
    ) -> None:
        """
        Initialize indexer world.
        
        Args:
            embedding_dim: Dimension for embeddings
            n_clusters: Number of clusters for grouping
        """
        self.embedding_agent = EmbeddingAgent(embedding_dim=embedding_dim)
        self.clustering_agent = ClusteringAgent(n_clusters=n_clusters)
        self.trajectory_agent = TrajectoryAgent()
    
    def process_snapshots(
        self,
        snapshots: List[ManifoldSnapshot],
    ) -> Dict[str, Any]:
        """
        Process a batch of snapshots.
        
        Args:
            snapshots: List of snapshots to process
            
        Returns:
            Results including embeddings, clusters, and trajectory analyses
        """
        # Generate embeddings
        embeddings = self.embedding_agent.embed_batch(snapshots)
        
        # Cluster
        clusters = self.clustering_agent.cluster(embeddings, self.embedding_agent)
        
        # Group snapshots by agent for trajectory analysis
        by_agent: Dict[str, List[ManifoldSnapshot]] = {}
        for snapshot in snapshots:
            agent_key = snapshot.agent_id.value
            if agent_key not in by_agent:
                by_agent[agent_key] = []
            by_agent[agent_key].append(snapshot)
        
        # Analyze trajectories
        trajectories = {}
        for agent_id, agent_snapshots in by_agent.items():
            if len(agent_snapshots) > 1:
                trajectories[agent_id] = self.trajectory_agent.analyze_trajectory(
                    agent_snapshots,
                    self.embedding_agent,
                )
        
        return {
            "embeddings": embeddings,
            "clusters": clusters,
            "trajectories": trajectories,
            "num_snapshots": len(snapshots),
            "num_agents": len(by_agent),
        }
    
    def get_cluster_summary(self, clusters: Dict[str, int]) -> Dict[int, List[str]]:
        """
        Get summary of clusters.
        
        Args:
            clusters: Cluster assignments
            
        Returns:
            Dict mapping cluster_id -> list of snapshot keys
        """
        summary: Dict[int, List[str]] = {}
        for key, cluster_id in clusters.items():
            if cluster_id not in summary:
                summary[cluster_id] = []
            summary[cluster_id].append(key)
        return summary


def bootstrap_indexer_world(
    embedding_dim: int = 128,
    n_clusters: int = 5,
) -> IndexerWorld:
    """
    Bootstrap an indexer world.
    
    Args:
        embedding_dim: Dimension for embeddings
        n_clusters: Number of clusters
        
    Returns:
        Configured IndexerWorld instance
    """
    return IndexerWorld(
        embedding_dim=embedding_dim,
        n_clusters=n_clusters,
    )


"""
Indexer World for offline substrate science.

This world operates on exported substrate snapshots to:
- Generate embeddings
- Cluster similar worldviews
- Analyze trajectories over time
"""

from .agents import (
    EmbeddingAgent,
    ClusteringAgent,
    TrajectoryAgent,
    BasinDetector,
    ViscosityAnalyzer,
    GradientExtractor,
)
from .bootstrap import bootstrap_indexer_world

__all__ = [
    "EmbeddingAgent",
    "ClusteringAgent", 
    "TrajectoryAgent",
    "BasinDetector",
    "ViscosityAnalyzer",
    "GradientExtractor",
    "bootstrap_indexer_world",
]

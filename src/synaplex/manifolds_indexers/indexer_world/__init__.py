# synaplex/manifolds_indexers/indexer_world/__init__.py

"""
Indexer World for offline manifold science.

This world operates on exported manifold snapshots to:
- Generate embeddings
- Cluster similar worldviews
- Analyze trajectories over time
"""

from .agents import (
    EmbeddingAgent,
    ClusteringAgent,
    TrajectoryAgent,
    AttractorDetector,
    CurvatureAnalyzer,
    TeleologyExtractor,
)
from .bootstrap import bootstrap_indexer_world

__all__ = [
    "EmbeddingAgent",
    "ClusteringAgent", 
    "TrajectoryAgent",
    "AttractorDetector",
    "CurvatureAnalyzer",
    "TeleologyExtractor",
    "bootstrap_indexer_world",
]


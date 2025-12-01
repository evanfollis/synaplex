# synaplex/manifolds_indexers/__init__.py

"""
Offline manifold science.

This layer operates on exported snapshots only.
"""

from .types import ManifoldSnapshot
from .export import SnapshotExporter
from .indexer_world import (
    EmbeddingAgent,
    ClusteringAgent,
    TrajectoryAgent,
    bootstrap_indexer_world,
)

__all__ = [
    "ManifoldSnapshot",
    "SnapshotExporter",
    "EmbeddingAgent",
    "ClusteringAgent",
    "TrajectoryAgent",
    "bootstrap_indexer_world",
]

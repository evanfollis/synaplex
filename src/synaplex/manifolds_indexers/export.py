# synaplex/manifolds_indexers/export.py

from __future__ import annotations

from typing import Iterable, List

from synaplex.cognition.manifolds import ManifoldEnvelope
from .types import ManifoldSnapshot


class SnapshotExporter:
    """
    One-way export from live manifolds to offline snapshots.
    """

    def export(self, envelopes: Iterable[ManifoldEnvelope]) -> List[ManifoldSnapshot]:
        return [
            ManifoldSnapshot(
                agent_id=e.agent_id,
                version=e.version,
                content=e.content,
                metadata=e.metadata,
            )
            for e in envelopes
        ]

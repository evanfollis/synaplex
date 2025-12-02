# synaplex/substrate_science/export.py

from __future__ import annotations

from typing import Iterable, List

from synaplex.cognition.substrate import SubstrateEnvelope
from .types import SubstrateSnapshot


class SnapshotExporter:
    """
    One-way export from live substrates to offline snapshots.
    """

    def export(self, envelopes: Iterable[SubstrateEnvelope]) -> List[SubstrateSnapshot]:
        return [
            SubstrateSnapshot(
                agent_id=e.agent_id,
                version=e.version,
                content=e.content,
                metadata=e.metadata,
            )
            for e in envelopes
        ]

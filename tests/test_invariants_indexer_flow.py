from synaplex.cognition.manifolds import ManifoldEnvelope
from synaplex.core.ids import AgentId
from synaplex.manifolds_indexers.export import SnapshotExporter
from synaplex.manifolds_indexers.types import ManifoldSnapshot


def test_snapshot_export_is_one_way_and_shape_preserving():
    agent = AgentId("agent-1")
    env = ManifoldEnvelope(
        agent_id=agent,
        version=3,
        content="internal-worldview-text",
        metadata={"source": "test"},
    )

    exporter = SnapshotExporter()
    snapshots = exporter.export([env])

    assert len(snapshots) == 1
    snap = snapshots[0]
    assert isinstance(snap, ManifoldSnapshot)
    assert snap.agent_id == agent
    assert snap.version == 3
    assert snap.content == "internal-worldview-text"
    assert snap.metadata.get("source") == "test"

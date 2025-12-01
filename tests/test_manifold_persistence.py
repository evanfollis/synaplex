# tests/test_manifold_persistence.py

"""
Tests for file-based manifold persistence.

Tests:
- FileManifoldStore save/load
- Version management
- Latest version loading
- Multiple agents
- Corrupted file handling
"""

import json
import tempfile
from pathlib import Path

from synaplex.core.ids import AgentId
from synaplex.cognition.manifolds import (
    ManifoldEnvelope,
    InMemoryManifoldStore,
    FileManifoldStore,
)


def test_in_memory_store():
    """Test in-memory store still works."""
    store = InMemoryManifoldStore()
    agent_id = AgentId("agent-1")

    # Initial: no manifold
    assert store.load_latest(agent_id) is None

    # Save manifold
    envelope = ManifoldEnvelope(
        agent_id=agent_id,
        version=1,
        content="Initial worldview",
        metadata={"source": "test"},
    )
    store.save(envelope)

    # Load it back
    loaded = store.load_latest(agent_id)
    assert loaded is not None
    assert loaded.version == 1
    assert loaded.content == "Initial worldview"
    assert loaded.agent_id == agent_id


def test_file_store_save_load():
    """Test basic save/load with file store."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = FileManifoldStore(root=tmpdir)
        agent_id = AgentId("agent-1")

        # Initial: no manifold
        assert store.load_latest(agent_id) is None

        # Save manifold
        envelope = ManifoldEnvelope(
            agent_id=agent_id,
            version=1,
            content="Initial worldview content",
            metadata={"source": "test", "tick": 0},
        )
        store.save(envelope)

        # Load it back
        loaded = store.load_latest(agent_id)
        assert loaded is not None
        assert loaded.version == 1
        assert loaded.content == "Initial worldview content"
        assert loaded.agent_id == agent_id
        assert loaded.metadata["source"] == "test"


def test_file_store_version_management():
    """Test that latest version is loaded correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = FileManifoldStore(root=tmpdir)
        agent_id = AgentId("agent-1")

        # Save multiple versions
        for version in [1, 2, 3]:
            envelope = ManifoldEnvelope(
                agent_id=agent_id,
                version=version,
                content=f"Worldview version {version}",
                metadata={"version": version},
            )
            store.save(envelope)

        # Should load latest (v3)
        latest = store.load_latest(agent_id)
        assert latest is not None
        assert latest.version == 3
        assert "version 3" in latest.content

        # Test loading specific version
        v2 = store.load_version(agent_id, 2)
        assert v2 is not None
        assert v2.version == 2
        assert "version 2" in v2.content


def test_file_store_multiple_agents():
    """Test that multiple agents are stored separately."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = FileManifoldStore(root=tmpdir)

        agent_a = AgentId("agent-a")
        agent_b = AgentId("agent-b")

        # Save manifolds for both agents
        envelope_a = ManifoldEnvelope(
            agent_id=agent_a,
            version=1,
            content="Agent A worldview",
            metadata={},
        )
        store.save(envelope_a)

        envelope_b = ManifoldEnvelope(
            agent_id=agent_b,
            version=5,
            content="Agent B worldview",
            metadata={},
        )
        store.save(envelope_b)

        # Load each independently
        loaded_a = store.load_latest(agent_a)
        assert loaded_a is not None
        assert loaded_a.agent_id == agent_a
        assert "Agent A" in loaded_a.content
        assert loaded_a.version == 1

        loaded_b = store.load_latest(agent_b)
        assert loaded_b is not None
        assert loaded_b.agent_id == agent_b
        assert "Agent B" in loaded_b.content
        assert loaded_b.version == 5


def test_file_store_persistence_across_instances():
    """Test that manifolds persist across store instances."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save with first instance
        store1 = FileManifoldStore(root=tmpdir)
        agent_id = AgentId("agent-1")

        envelope = ManifoldEnvelope(
            agent_id=agent_id,
            version=10,
            content="Persistent worldview",
            metadata={"persisted": True},
        )
        store1.save(envelope)

        # Create new instance - should load existing
        store2 = FileManifoldStore(root=tmpdir)
        loaded = store2.load_latest(agent_id)

        assert loaded is not None
        assert loaded.version == 10
        assert loaded.content == "Persistent worldview"
        assert loaded.metadata["persisted"] is True


def test_file_store_list_versions():
    """Test listing available versions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = FileManifoldStore(root=tmpdir)
        agent_id = AgentId("agent-1")

        # Save versions out of order
        for version in [3, 1, 5, 2]:
            envelope = ManifoldEnvelope(
                agent_id=agent_id,
                version=version,
                content=f"Version {version}",
                metadata={},
            )
            store.save(envelope)

        # List should return sorted versions
        versions = store.list_versions(agent_id)
        assert versions == [1, 2, 3, 5]


def test_file_store_corrupted_file_handling():
    """Test that corrupted files are handled gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = FileManifoldStore(root=tmpdir)
        agent_id = AgentId("agent-1")

        # Save valid manifold
        envelope = ManifoldEnvelope(
            agent_id=agent_id,
            version=1,
            content="Valid content",
            metadata={},
        )
        store.save(envelope)

        # Corrupt the file
        agent_dir = store._agent_dir(agent_id)
        v1_path = agent_dir / "v1.json"
        v1_path.write_text("invalid json content")

        # Should return None (not crash)
        loaded = store.load_latest(agent_id)
        assert loaded is None


def test_file_store_agent_id_sanitization():
    """Test that agent IDs are sanitized for filesystem use."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = FileManifoldStore(root=tmpdir)
        # Use agent ID with special characters
        agent_id = AgentId("agent@with#special$chars!")

        envelope = ManifoldEnvelope(
            agent_id=agent_id,
            version=1,
            content="Test content",
            metadata={},
        )
        store.save(envelope)

        # Should be able to load it back
        loaded = store.load_latest(agent_id)
        assert loaded is not None
        assert loaded.agent_id == agent_id
        assert loaded.content == "Test content"


def test_file_store_atomic_write():
    """Test that writes are atomic (temp file then rename)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = FileManifoldStore(root=tmpdir)
        agent_id = AgentId("agent-1")

        envelope = ManifoldEnvelope(
            agent_id=agent_id,
            version=1,
            content="Atomic write test",
            metadata={},
        )
        store.save(envelope)

        # Should not have temp file left behind
        agent_dir = store._agent_dir(agent_id)
        temp_files = list(agent_dir.glob("*.tmp"))
        assert len(temp_files) == 0

        # Should have the actual file
        assert (agent_dir / "v1.json").exists()


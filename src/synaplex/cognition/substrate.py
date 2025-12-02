# synaplex/cognition/substrate.py

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from synaplex.core.ids import AgentId


@dataclass
class SubstrateEnvelope:
    """
    Opaque container for a mind's internal substrate (sediment).

    The system does not parse or interpret 'content' here.

    The 'metadata' dict may optionally contain geometric hints authored by the Mind:
    - 'viscosity_hints': Dict[str, Any] - hints about K (sensitivity patterns, risk profiles)
    - 'basin_hints': List[str] - hints about A (stable patterns, habits, equilibria)
    - 'gradient_hints': Dict[str, Any] - hints about τ (improvement directions, epistemic gradients)

    These are hints, not enforced schemas. The Mind authors them for its own future use
    and for science analysis. The runtime never parses or validates them.
    """
    agent_id: AgentId
    version: int
    content: str
    metadata: Dict[str, Any]


class SubstrateStore(ABC):
    """
    Abstract base interface for substrate storage.

    Implementations must provide:
    - load_latest(agent_id) -> Optional[SubstrateEnvelope]
    - save(envelope) -> None
    """

    @abstractmethod
    def load_latest(self, agent_id: AgentId) -> Optional[SubstrateEnvelope]:
        """Load the latest version of a substrate for an agent."""
        pass

    @abstractmethod
    def save(self, envelope: SubstrateEnvelope) -> None:
        """Save a substrate envelope."""
        pass


class InMemorySubstrateStore(SubstrateStore):
    """
    Minimal in-memory substrate store.

    Substrates are lost when the process exits.
    Useful for testing or temporary runs.
    """

    def __init__(self) -> None:
        self._by_agent: Dict[AgentId, SubstrateEnvelope] = {}

    def load_latest(self, agent_id: AgentId) -> Optional[SubstrateEnvelope]:
        return self._by_agent.get(agent_id)

    def save(self, envelope: SubstrateEnvelope) -> None:
        self._by_agent[envelope.agent_id] = envelope


class FileSubstrateStore(SubstrateStore):
    """
    File-based substrate store for persistence across restarts.

    Storage layout:
        root/
            <agent_id>/
                v<version>.json

    Each file contains a JSON representation of SubstrateEnvelope.
    The latest version is determined by the highest version number.
    """

    def __init__(self, root: str | Path = "substrates") -> None:
        """
        Initialize file-based store.

        Args:
            root: Root directory for substrate storage. Will be created if it doesn't exist.
        """
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _agent_dir(self, agent_id: AgentId) -> Path:
        """Get directory for an agent's substrates."""
        # Sanitize agent_id for filesystem use
        agent_slug = "".join(c if c.isalnum() or c in "-_" else "_" for c in agent_id.value)
        d = self.root / agent_slug
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _envelope_path(self, agent_id: AgentId, version: int) -> Path:
        """Get file path for a specific version."""
        return self._agent_dir(agent_id) / f"v{version}.json"

    def load_latest(self, agent_id: AgentId) -> Optional[SubstrateEnvelope]:
        """Load the latest version of a substrate for an agent."""
        agent_dir = self._agent_dir(agent_id)

        # Find all version files
        version_files = list(agent_dir.glob("v*.json"))
        if not version_files:
            return None

        # Extract version numbers and find latest
        def extract_version(path: Path) -> int:
            # Extract version from "v<version>.json"
            try:
                return int(path.stem[1:])  # Remove 'v' prefix
            except ValueError:
                return -1

        latest_file = max(version_files, key=extract_version)
        version = extract_version(latest_file)

        # Load envelope from file
        try:
            with open(latest_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Reconstruct AgentId
            agent_id_obj = AgentId(data["agent_id"])

            return SubstrateEnvelope(
                agent_id=agent_id_obj,
                version=data["version"],
                content=data["content"],
                metadata=data["metadata"],
            )
        except (json.JSONDecodeError, KeyError, ValueError):
            # If file is corrupted, return None (will create new substrate)
            return None

    def save(self, envelope: SubstrateEnvelope) -> None:
        """Save a substrate envelope to disk."""
        path = self._envelope_path(envelope.agent_id, envelope.version)

        # Convert to JSON-serializable dict
        data = {
            "agent_id": envelope.agent_id.value,
            "version": envelope.version,
            "content": envelope.content,
            "metadata": envelope.metadata,
        }

        # Write atomically (write to temp file then rename)
        temp_path = path.with_suffix(".tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            temp_path.replace(path)  # Atomic rename
        except Exception:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise

    def load_version(self, agent_id: AgentId, version: int) -> Optional[SubstrateEnvelope]:
        """
        Load a specific version of a substrate (optional helper method).

        Returns None if version doesn't exist.
        """
        path = self._envelope_path(agent_id, version)
        if not path.exists():
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            agent_id_obj = AgentId(data["agent_id"])

            return SubstrateEnvelope(
                agent_id=agent_id_obj,
                version=data["version"],
                content=data["content"],
                metadata=data["metadata"],
            )
        except (json.JSONDecodeError, KeyError, ValueError):
            return None

    def list_versions(self, agent_id: AgentId) -> list[int]:
        """
        List all available versions for an agent (optional helper method).

        Returns sorted list of version numbers.
        """
        agent_dir = self._agent_dir(agent_id)
        version_files = list(agent_dir.glob("v*.json"))

        versions = []
        for path in version_files:
            try:
                version = int(path.stem[1:])
                versions.append(version)
            except ValueError:
                continue

        return sorted(versions)

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from synaplex.core.types import ManifoldEnvelope


class FileStorage:
    """
    Very simple file-based storage for manifolds.

    This is intentionally boring: the point is to keep IO out of the core logic.
    """

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _manifold_dir(self, mind_id: str, world_id: str) -> Path:
        return self.root / "manifolds" / world_id / mind_id

    def save_manifold(self, env: ManifoldEnvelope) -> None:
        d = self._manifold_dir(env.mind_id, env.world_id)
        d.mkdir(parents=True, exist_ok=True)
        filename = f"{env.version:06d}_{env.created_at.isoformat()}.json"
        path = d / filename
        payload = asdict(env)
        # datetime is not JSON-serializable by default
        payload["created_at"] = env.created_at.isoformat()
        path.write_text(json.dumps(payload, indent=2))

    def load_latest_manifold(self, mind_id: str, world_id: str) -> Optional[ManifoldEnvelope]:
        d = self._manifold_dir(mind_id, world_id)
        if not d.exists():
            return None
        candidates = sorted(d.glob("*.json"))
        if not candidates:
            return None
        latest = candidates[-1]
        data = json.loads(latest.read_text())
        return ManifoldEnvelope(
            mind_id=data["mind_id"],
            world_id=data["world_id"],
            version=int(data["version"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            manifold_text=data["manifold_text"],
        )

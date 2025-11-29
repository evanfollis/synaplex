from __future__ import annotations

from pathlib import Path

from synaplex.core.agent import Agent
from synaplex.core.mind import Mind
from synaplex.core.types import Lens
from synaplex.core.world import World
from synaplex.infra.llm import DummyLLMClient
from synaplex.infra.storage import FileStorage


def test_basic_world_tick(tmp_path: Path) -> None:
    storage = FileStorage(root=tmp_path)
    llm = DummyLLMClient()

    mind = Mind(mind_id="test-mind", storage=storage, llm=llm)
    lens = Lens(keys={"TOPIC:TEST": 1.0})
    agent = Agent(id="agent-1", world_id="test-world", mind=mind, lens=lens)

    world = World(id="test-world")
    world.add_agent(agent)

    signals = world.tick(world_ctx={"foo": "bar"})
    assert len(signals) == 1
    assert signals[0].from_agent == "agent-1"

    # ensure a manifold file was written
    manifolds_dir = tmp_path / "manifolds" / "test-world" / "test-mind"
    assert manifolds_dir.exists()
    assert list(manifolds_dir.glob("*.json"))

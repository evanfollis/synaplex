from __future__ import annotations

from pathlib import Path

from synaplex.core.agent import Agent
from synaplex.core.mind import Mind
from synaplex.core.types import Lens
from synaplex.core.world import World
from synaplex.infra.llm import DummyLLMClient
from synaplex.infra.storage import FileStorage


def main() -> None:
    storage = FileStorage(root=Path(".synaplex"))
    llm = DummyLLMClient()

    mind = Mind(mind_id="mind-main", storage=storage, llm=llm)
    lens = Lens(keys={"TOPIC:AI_NATIVE": 1.0})

    agent = Agent(
        id="explorer",
        world_id="playground",
        mind=mind,
        lens=lens,
    )

    world = World(id="playground")
    world.add_agent(agent)

    signals = world.tick(world_ctx={"note": "hello from Synaplex basic_world demo"})
    for s in signals:
        print(f"[signal] from={s.from_agent} keys={s.keys} summary={s.summary}")


if __name__ == "__main__":
    main()

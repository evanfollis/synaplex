from __future__ import annotations

from pathlib import Path

from synaplex.core.agent import Agent
from synaplex.core.mind import Mind
from synaplex.core.types import Lens
from synaplex.core.world import World
from synaplex.infra.llm import DummyLLMClient
from synaplex.infra.storage import FileStorage


def main() -> None:
    """
    Experiment 1: single-mind manifold evolution.

    - Creates one Mind and one Agent in a simple World.
    - Runs several ticks with different world context.
    - Shows where manifolds were written and prints a small snippet.
    """
    storage = FileStorage(root=Path(".synaplex_exp1"))
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

    for i in range(3):
        ctx = {"tick": i + 1, "note": f"hello from Synaplex tick {i + 1}"}
        signals = world.tick(world_ctx=ctx)
        for s in signals:
            print(f"[tick {i + 1}] signal from={s.from_agent} keys={s.keys} summary={s.summary}")

    latest = mind.load_latest(world_id="playground")
    if latest:
        print("\nLatest manifold envelope:")
        print(f"  mind_id:   {latest.mind_id}")
        print(f"  world_id:  {latest.world_id}")
        print(f"  version:   {latest.version}")
        print(f"  created_at:{latest.created_at.isoformat()}")
        snippet = latest.manifold_text[:200].replace("\n", " ")
        print(f"  text[:200]: {snippet!r}")
        print(f"  storage dir: {storage._manifold_dir(mind_id='mind-main', world_id='playground')}")
    else:
        print("No manifold found; something went wrong.")


if __name__ == "__main__":
    main()

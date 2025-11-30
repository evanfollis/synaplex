from __future__ import annotations

import os
from pathlib import Path

from synaplex.core.agent import Agent
from synaplex.core.mind import Mind
from synaplex.core.types import Lens
from synaplex.core.world import World
from synaplex.infra.llm import OpenAILLMClient
from synaplex.infra.storage import FileStorage


def main() -> None:
    storage_root = Path(".synaplex_openai_branch")
    storage = FileStorage(root=storage_root)

    model_name = os.getenv("SYNAPLEX_MODEL", "gpt-4.1-mini")
    llm = OpenAILLMClient(model=model_name, max_output_tokens=900)

    # Single mind shared by multiple agents (different lenses / roles).
    mind = Mind(
        mind_id="mind-branch-shared",
        storage=storage,
        llm=llm,
    )

    lens_explorer = Lens(keys={"ROLE:EXPLORER": 1.0, "TOPIC:IDEAS": 0.9})
    lens_critic = Lens(keys={"ROLE:CRITIC": 1.0, "TOPIC:TENSIONS": 0.9})

    explorer = Agent(
        id="agent-explorer",
        world_id="world-branch-demo",
        mind=mind,
        lens=lens_explorer,
    )

    critic = Agent(
        id="agent-critic",
        world_id="world-branch-demo",
        mind=mind,
        lens=lens_critic,
    )

    world = World(id="world-branch-demo")
    world.add_agent(explorer)
    world.add_agent(critic)

    for step in range(3):
        print(f"\n=== BRANCH DEMO TICK {step} ===")
        ctx = {
            "step": step,
            "note": "branch-style demo: explorer vs critic lenses on same mind",
        }

        signals = world.tick(world_ctx=ctx)
        for s in signals:
            print(f"[signal] from={s.from_agent} keys={s.keys} summary={s.summary}")

        latest = mind.load_latest(world_id=world.id)
        if latest is None:
            print("No manifold found (this should not happen after a tick).")
            continue

        print(f"\n[shared manifold] version={latest.version}")
        snippet = latest.manifold_text[:600]
        print(snippet)
        if len(latest.manifold_text) > 600:
            print("...[truncated]...")


if __name__ == "__main__":
    main()

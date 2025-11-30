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
    # Storage root for this experiment
    storage_root = Path(".synaplex_openai_single")
    storage = FileStorage(root=storage_root)

    # Model selection (override via env if desired)
    model_name = os.getenv("SYNAPLEX_MODEL", "gpt-4.1-mini")

    llm = OpenAILLMClient(model=model_name, max_output_tokens=800)

    mind = Mind(
        mind_id="mind-single-openai",
        storage=storage,
        llm=llm,
    )

    lens = Lens(keys={"TOPIC:AI_NATIVE": 1.0, "TOPIC:MANIFOLDS": 0.8})

    agent = Agent(
        id="explorer-openai",
        world_id="world-openai-single",
        mind=mind,
        lens=lens,
    )

    world = World(id="world-openai-single")
    world.add_agent(agent)

    # Run a few ticks to see the manifold evolve.
    for step in range(3):
        print(f"\n=== TICK {step} ===")
        ctx = {
            "step": step,
            "note": "exploring AI-native research mesh via Synaplex",
        }

        signals = world.tick(world_ctx=ctx)
        for s in signals:
            print(f"[signal] from={s.from_agent} keys={s.keys} summary={s.summary}")

        # Inspect the latest manifold checkpoint
        latest = mind.load_latest(world_id=world.id)
        if latest is None:
            print("No manifold found (this should not happen after a tick).")
            continue

        print(f"\n[manifold] version={latest.version} created_at={latest.created_at.isoformat()}")
        snippet = latest.manifold_text[:600]
        print(snippet)
        if len(latest.manifold_text) > 600:
            print("...[truncated]...")


if __name__ == "__main__":
    main()

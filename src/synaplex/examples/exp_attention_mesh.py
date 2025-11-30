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
    Experiment 2: two agents with different lenses and attention-based routing.

    - Creates two Minds and Agents with different lenses.
    - Runs a single tick_with_attention.
    - Prints which agents received projections and from whom.
    """
    storage = FileStorage(root=Path(".synaplex_exp2"))
    llm = DummyLLMClient()

    # Agent 1: cares about AI-native systems.
    mind_explorer = Mind(mind_id="mind-explorer", storage=storage, llm=llm)
    lens_explorer = Lens(keys={"TOPIC:AI_NATIVE": 0.9, "TOPIC:CODE": 0.4})

    explorer = Agent(
        id="explorer",
        world_id="mesh",
        mind=mind_explorer,
        lens=lens_explorer,
    )

    # Agent 2: cares about biases and tensions.
    mind_critic = Mind(mind_id="mind-critic", storage=storage, llm=llm)
    lens_critic = Lens(keys={"TOPIC:BIAS": 1.0, "TOPIC:AI_NATIVE": 0.2})

    critic = Agent(
        id="critic",
        world_id="mesh",
        mind=mind_critic,
        lens=lens_critic,
    )

    world = World(id="mesh")
    world.add_agent(explorer)
    world.add_agent(critic)

    world_ctx = {"note": "attention mesh demo", "topics": ["AI_NATIVE", "BIAS"]}
    signals, projections_by_receiver = world.tick_with_attention(
        world_ctx=world_ctx,
        attention_threshold=0.3,
    )

    print("Signals:")
    for s in signals:
        print(f"  from={s.from_agent} keys={s.keys} summary={s.summary}")

    print("\nProjections (by receiver):")
    if not projections_by_receiver:
        print("  (none; try lowering the attention_threshold)")
    else:
        for receiver_id, projections in projections_by_receiver.items():
            print(f"  receiver={receiver_id}")
            for p in projections:
                print(f"    from={p.from_agent} world={p.world_id} content_keys={list(p.content.keys())}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Multi-agent interaction example demonstrating Synaplex message routing.

This example shows:
- Two agents with subscriptions
- Signal emission and filtering
- Projection gathering
- EnvState updates
- The unified cognitive loop in action
"""

from synaplex.core.ids import AgentId, WorldId
from synaplex.core.runtime_inprocess import InProcessRuntime, GraphConfig, EdgeConfig
from synaplex.core.env_state import EnvState
from synaplex.core.dna import DNA
from synaplex.core.lenses import Lens
from synaplex.core.messages import MessageId, Signal
from synaplex.cognition.llm_client import LLMClient
from synaplex.cognition.mind import Mind


class DummyLLM(LLMClient):
    """Dummy LLM that returns simple responses."""
    def complete(self, prompt: str, **kwargs):
        return type("Resp", (), {"text": f"Reasoning about: {prompt[:50]}...", "raw": {}})()


class SignalEmittingMind(Mind):
    """A Mind that emits signals in its outward behavior."""
    
    def act(self, reasoning_output):
        """Emit a signal with structured payload."""
        return {
            "signals": [
                {
                    "payload": {
                        "type": "status",
                        "agent": self.agent_id.value,
                        "message": "I am active",
                    }
                }
            ],
            "env_updates": {
                f"{self.agent_id.value}_tick": reasoning_output.get("context", {}).get("tick", 0),
            },
        }


def main():
    """Run a multi-agent interaction example."""
    print("=== Synaplex Multi-Agent Example ===\n")
    
    # Create world
    world_id = WorldId("example-world")
    env_state = EnvState()
    graph_config = GraphConfig(
        edges=[
            # Agent B subscribes to Agent A
            EdgeConfig(subscriber=AgentId("agent-b"), publisher=AgentId("agent-a")),
        ]
    )
    runtime = InProcessRuntime(world_id=world_id, env_state=env_state, graph_config=graph_config)
    
    # Create agents with DNA
    dna_a = DNA(
        agent_id=AgentId("agent-a"),
        role="publisher",
        subscriptions=[],  # A doesn't subscribe to anyone
    )
    
    dna_b = DNA(
        agent_id=AgentId("agent-b"),
        role="subscriber",
        subscriptions=[AgentId("agent-a")],  # B subscribes to A
    )
    
    # Create minds
    mind_a = SignalEmittingMind(agent_id=AgentId("agent-a"), llm_client=DummyLLM())
    mind_b = Mind(agent_id=AgentId("agent-b"), llm_client=DummyLLM())
    
    # Register with DNA and default lenses
    default_lens = Lens(name="default")
    runtime.register_agent(mind_a, dna=dna_a, lens=default_lens)
    runtime.register_agent(mind_b, dna=dna_b, lens=default_lens)
    
    print("Registered 2 agents:")
    print(f"  - Agent A (publisher)")
    print(f"  - Agent B (subscriber, subscribes to A)\n")
    
    # Run a few ticks
    for tick in range(3):
        print(f"--- Tick {tick} ---")
        runtime.tick(tick)
        
        # Show EnvState updates
        updates = {k: v for k, v in env_state.data.items() if k.endswith("_tick")}
        if updates:
            print(f"EnvState updates: {updates}")
        print()
    
    print("=== Example Complete ===")
    print("\nWhat happened:")
    print("1. Each tick, Agent B received a projection from Agent A")
    print("2. Agent A emitted signals that were visible to Agent B")
    print("3. EnvState was updated with agent tick counts")
    print("4. The unified loop (Perception → Reasoning → Internal Update) ran for each agent")


if __name__ == "__main__":
    main()


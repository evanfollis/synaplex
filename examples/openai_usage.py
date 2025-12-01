#!/usr/bin/env python3
"""
Example usage of OpenAILLMClient with Synaplex.

Make sure your .env file contains:
    OPENAI_API_KEY=sk-...

Run with:
    python examples/openai_usage.py
"""

from synaplex.core.ids import AgentId, WorldId
from synaplex.core.runtime_inprocess import InProcessRuntime
from synaplex.core.env_state import EnvState
from synaplex.core.world_modes import WorldMode
from synaplex.cognition.openai_client import OpenAILLMClient
from synaplex.cognition.mind import Mind


def main():
    # Create an OpenAI client (loads all config from .env automatically)
    # Reads: OPENAI_API_KEY, OPENAI_LLM_MODEL, OPENAI_LLM_REASONING, OPENAI_LLM_VERBOSITY
    llm = OpenAILLMClient()  # Uses env vars by default
    
    # Create a mind with manifold enabled
    mind = Mind(
        agent_id=AgentId("example-agent"),
        llm_client=llm,
        world_mode=WorldMode.MANIFOLD,
    )
    
    # Create a runtime and register the agent
    world_id = WorldId("example-world")
    runtime = InProcessRuntime(world_id=world_id, env_state=EnvState())
    runtime.register_agent(mind)
    
    # Run a tick (this will call the LLM)
    print("Running tick 0...")
    runtime.tick(0)
    print("✓ Tick complete!")
    
    # The mind should have:
    # - Received a percept (even if empty for now)
    # - Performed reasoning via OpenAI
    # - Updated its manifold (if in MANIFOLD mode)
    
    print("\nMind reasoning complete. Check manifold store for internal worldview.")


if __name__ == "__main__":
    main()


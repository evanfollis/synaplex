# synaplex/quick_start.py

"""
Quick start helper for Synaplex.

Provides a simple way to get up and running with minimal setup.
"""

from __future__ import annotations

from typing import Optional

from synaplex.core.ids import AgentId, WorldId
from synaplex.core.runtime_inprocess import InProcessRuntime, GraphConfig
from synaplex.core.env_state import EnvState
from synaplex.core.dna import DNA
from synaplex.core.lenses import Lens
from synaplex.cognition.llm_client import LLMClient, LLMResponse
from synaplex.cognition.mind import Mind
from synaplex.cognition.manifolds import ManifoldStore, InMemoryManifoldStore


class DummyLLMClient(LLMClient):
    """
    Simple dummy LLM client for quick testing.
    
    Returns placeholder responses without making actual API calls.
    Useful for testing the runtime and cognitive loop structure.
    """
    
    def complete(self, prompt: str, **kwargs) -> LLMResponse:
        """Return a simple placeholder response."""
        return LLMResponse(
            text=f"Reasoning about: {prompt[:100]}...",
            raw={"model": "dummy", "prompt_length": len(prompt)}
        )


def quick_start(
    agent_id: str = "agent-1",
    world_id: str = "quick-start-world",
    llm_client: Optional[LLMClient] = None,
    manifold_store: Optional[ManifoldStore] = None,
) -> InProcessRuntime:
    """
    Create a minimal Synaplex runtime ready to use.
    
    Sets up a runtime with a single agent that can immediately run ticks.
    This is the fastest way to get started experimenting with Synaplex.
    
    Args:
        agent_id: ID for the agent (default: "agent-1")
        world_id: ID for the world (default: "quick-start-world")
        llm_client: Optional LLM client. If None, uses DummyLLMClient for testing.
        manifold_store: Optional manifold store. If None, uses InMemoryManifoldStore.
    
    Returns:
        InProcessRuntime configured with one agent, ready to call tick()
    
    Example:
        >>> from synaplex.quick_start import quick_start
        >>> runtime = quick_start()
        >>> runtime.tick(0)
    """
    # Create world and environment
    world_id_obj = WorldId(world_id)
    env_state = EnvState()
    graph_config = GraphConfig()  # Empty graph by default
    
    # Create runtime
    runtime = InProcessRuntime(
        world_id=world_id_obj,
        env_state=env_state,
        graph_config=graph_config,
    )
    
    # Create agent ID
    agent_id_obj = AgentId(agent_id)
    
    # Create DNA with sensible defaults
    dna = DNA(
        agent_id=agent_id_obj,
        role="explorer",
        subscriptions=[],  # No subscriptions by default
        tools=[],  # No tools by default
    )
    
    # Create default lens
    lens = Lens(name="default")
    
    # Create LLM client if not provided
    if llm_client is None:
        llm_client = DummyLLMClient()
    
    # Create manifold store if not provided
    if manifold_store is None:
        manifold_store = InMemoryManifoldStore()
    
    # Create Mind
    mind = Mind(
        agent_id=agent_id_obj,
        llm_client=llm_client,
        manifold_store=manifold_store,
    )
    
    # Register agent
    runtime.register_agent(mind, dna=dna, lens=lens)
    
    return runtime


#!/usr/bin/env python3
"""
Comprehensive Synaplex example demonstrating:
- Multiple agents with subscriptions
- Signal emission and filtering
- Projection gathering
- Manifold persistence
- Tool usage
- World modes
- Multi-tick evolution
"""

from synaplex.core.ids import AgentId, WorldId
from synaplex.core.runtime_inprocess import InProcessRuntime, GraphConfig, EdgeConfig
from synaplex.core.env_state import EnvState
from synaplex.core.dna import DNA
from synaplex.core.lenses import Lens
from synaplex.core.messages import Signal
from synaplex.core.world_modes import WorldMode
from synaplex.cognition.openai_client import OpenAILLMClient
from synaplex.cognition.mind import Mind
from synaplex.cognition.manifolds import FileManifoldStore
from synaplex.cognition.tools import ToolRegistry, FunctionTool
import tempfile
import shutil


class CustomLens(Lens):
    """Custom lens that filters signals by type."""
    
    def should_attend(self, signal_payload: dict) -> bool:
        """Only attend to signals with type 'important'."""
        return signal_payload.get("type") == "important"
    
    def transform_projection(self, raw_projection: dict) -> dict:
        """Transform projection to include metadata."""
        return {
            **raw_projection,
            "transformed_by": "CustomLens",
        }


def create_example_tools() -> ToolRegistry:
    """Create a tool registry with example tools."""
    registry = ToolRegistry()
    
    def calculate_sum(a: float, b: float) -> float:
        """Add two numbers."""
        return a + b
    
    def get_factorial(n: int) -> int:
        """Calculate factorial of n."""
        if n <= 1:
            return 1
        return n * get_factorial(n - 1)
    
    registry.register_function(
        name="calculate_sum",
        description="Adds two numbers together",
        func=calculate_sum,
    )
    
    registry.register_function(
        name="get_factorial",
        description="Calculates the factorial of a number",
        func=get_factorial,
    )
    
    return registry


def main():
    """Run comprehensive example."""
    print("=== Synaplex Comprehensive Example ===\n")
    
    # Create temporary directory for manifolds
    temp_dir = tempfile.mkdtemp()
    print(f"Using temporary manifold store: {temp_dir}\n")
    
    try:
        # Create world
        world_id = WorldId("comprehensive-world")
        env_state = EnvState()
        
        # Create graph with subscriptions
        graph_config = GraphConfig(
            edges=[
                # Agent B subscribes to Agent A
                EdgeConfig(
                    subscriber=AgentId("agent-b"),
                    publisher=AgentId("agent-a")
                ),
                # Agent C subscribes to both A and B
                EdgeConfig(
                    subscriber=AgentId("agent-c"),
                    publisher=AgentId("agent-a")
                ),
                EdgeConfig(
                    subscriber=AgentId("agent-c"),
                    publisher=AgentId("agent-b")
                ),
            ]
        )
        
        runtime = InProcessRuntime(
            world_id=world_id,
            env_state=env_state,
            graph_config=graph_config,
        )
        
        # Create tool registry
        tool_registry = create_example_tools()
        
        # Create agents with different configurations
        llm_client = OpenAILLMClient()
        
        # Agent A: Publisher with tools, manifold mode
        dna_a = DNA(
            agent_id=AgentId("agent-a"),
            role="publisher",
            subscriptions=[],
            tools=["calculate_sum", "get_factorial"],
            behavior_params={"activity": 0.9},
        )
        
        store_a = FileManifoldStore(root=f"{temp_dir}/agent-a")
        mind_a = Mind(
            agent_id=AgentId("agent-a"),
            llm_client=llm_client,
            manifold_store=store_a,
            tool_registry=tool_registry,
            world_mode=WorldMode.MANIFOLD,
        )
        
        # Agent B: Subscriber with custom lens, reasoning-only mode
        dna_b = DNA(
            agent_id=AgentId("agent-b"),
            role="subscriber",
            subscriptions=[AgentId("agent-a")],
            tools=[],
        )
        
        mind_b = Mind(
            agent_id=AgentId("agent-b"),
            llm_client=llm_client,
            world_mode=WorldMode.REASONING_ONLY,  # No persistent worldview
        )
        
        # Agent C: Subscriber with manifold, default lens
        dna_c = DNA(
            agent_id=AgentId("agent-c"),
            role="subscriber",
            subscriptions=[AgentId("agent-a"), AgentId("agent-b")],
            tools=[],
        )
        
        store_c = FileManifoldStore(root=f"{temp_dir}/agent-c")
        mind_c = Mind(
            agent_id=AgentId("agent-c"),
            llm_client=llm_client,
            manifold_store=store_c,
            world_mode=WorldMode.MANIFOLD,
        )
        
        # Create custom lens for agent B
        custom_lens = CustomLens(name="custom")
        default_lens = Lens(name="default")
        
        # Register agents
        runtime.register_agent(mind_a, dna=dna_a, lens=default_lens)
        runtime.register_agent(mind_b, dna=dna_b, lens=custom_lens)
        runtime.register_agent(mind_c, dna=dna_c, lens=default_lens)
        
        print("Registered 3 agents:")
        print("  - Agent A: Publisher, MANIFOLD mode, has tools")
        print("  - Agent B: Subscriber to A, REASONING_ONLY mode, custom lens")
        print("  - Agent C: Subscriber to A and B, MANIFOLD mode\n")
        
        # Custom agent class that emits signals
        class SignalEmittingMind(Mind):
            def act(self, reasoning_output):
                """Emit signals based on reasoning."""
                tick = reasoning_output.get("context", {}).get("tick", 0)
                
                signals = []
                if tick % 2 == 0:
                    # Emit important signal on even ticks
                    signals.append({
                        "payload": {
                            "type": "important",
                            "message": f"Important update from {self.agent_id.value} at tick {tick}",
                        }
                    })
                else:
                    # Emit regular signal on odd ticks
                    signals.append({
                        "payload": {
                            "type": "regular",
                            "message": f"Regular update from {self.agent_id.value} at tick {tick}",
                        }
                    })
                
                return {
                    "signals": signals,
                    "env_updates": {
                        f"{self.agent_id.value}_tick": tick,
                    },
                }
        
        # Replace agent A with signal-emitting version
        mind_a_signal = SignalEmittingMind(
            agent_id=AgentId("agent-a"),
            llm_client=llm_client,
            manifold_store=store_a,
            tool_registry=tool_registry,
            world_mode=WorldMode.MANIFOLD,
        )
        runtime.register_agent(mind_a_signal, dna=dna_a, lens=default_lens)
        
        # Run multiple ticks
        print("Running 5 ticks...\n")
        for tick in range(5):
            print(f"--- Tick {tick} ---")
            runtime.tick(tick)
            
            # Show EnvState updates
            updates = {k: v for k, v in env_state.data.items() if k.endswith("_tick")}
            if updates:
                print(f"EnvState updates: {updates}")
            
            # Show manifold versions for agents with manifolds
            if tick > 0:
                env_a = store_a.load_latest(AgentId("agent-a"))
                env_c = store_c.load_latest(AgentId("agent-c"))
                if env_a:
                    print(f"Agent A manifold: version {env_a.version}")
                if env_c:
                    print(f"Agent C manifold: version {env_c.version}")
            print()
        
        print("=== Example Complete ===\n")
        print("What happened:")
        print("1. Agent A emitted signals (important on even ticks, regular on odd)")
        print("2. Agent B (with custom lens) only saw 'important' signals")
        print("3. Agent C (with default lens) saw all signals")
        print("4. Agent B received projections from Agent A (subscription)")
        print("5. Agent C received projections from both A and B")
        print("6. Agents A and C maintained persistent manifolds (MANIFOLD mode)")
        print("7. Agent B had no persistent worldview (REASONING_ONLY mode)")
        print("8. EnvState was updated with agent tick counts")
        print("9. Tools were available to Agent A (listed in DNA)")
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory: {temp_dir}")


if __name__ == "__main__":
    main()


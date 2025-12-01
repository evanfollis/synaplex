#!/usr/bin/env python3
"""
Quick Start Example - Get up and running with Synaplex in just a few lines.

This minimal example demonstrates the simplest way to start using Synaplex.
"""

from synaplex.quick_start import quick_start


def main():
    """Run a minimal Synaplex example."""
    print("=== Synaplex Quick Start ===\n")
    
    # Create a runtime with one agent - that's it!
    runtime = quick_start()
    
    print("Created runtime with one agent. Running a few ticks...\n")
    
    # Run a few ticks to see the cognitive loop in action
    for tick in range(3):
        print(f"--- Tick {tick} ---")
        runtime.tick(tick)
        print()
    
    print("=== Done! ===")
    print("\nWhat happened:")
    print("1. A runtime was created with one agent")
    print("2. Each tick ran the unified cognitive loop:")
    print("   - Perception: built a Percept from the environment")
    print("   - Reasoning: the Mind processed the Percept")
    print("   - Internal Update: the Mind updated its manifold")
    print("\nNext steps:")
    print("- See examples/multi_agent_example.py for multiple agents")
    print("- See examples/comprehensive_example.py for advanced features")
    print("- Read README.md for the full mental model")


if __name__ == "__main__":
    main()


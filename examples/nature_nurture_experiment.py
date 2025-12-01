#!/usr/bin/env python3
"""
Nature/Nurture Experiment Example

Demonstrates how to run experiments that independently vary
DNA (nature) vs manifolds (nurture) to study their effects.
"""

from synaplex.core.ids import AgentId, WorldId
from synaplex.core.dna import DNA
from synaplex.core.runtime_inprocess import InProcessRuntime
from synaplex.core.env_state import EnvState
from synaplex.core.lenses import Lens
from synaplex.cognition.openai_client import OpenAILLMClient
from synaplex.cognition.mind import Mind
from synaplex.cognition.manifolds import InMemoryManifoldStore, ManifoldEnvelope
from synaplex.meta.dna_utils import DNAUtils
from synaplex.meta.manifold_utils import ManifoldUtils
from synaplex.meta.experiments import NatureNurtureExperiment, NurtureNatureExperiment


class DummyLLM:
    """Dummy LLM for testing."""
    def complete(self, prompt: str, **kwargs):
        return type("Resp", (), {"text": f"Reasoning: {prompt[:50]}...", "raw": {}})()


def make_mind(agent_id: AgentId, store) -> Mind:
    """Factory for creating minds."""
    llm = DummyLLM()
    return Mind(
        agent_id=agent_id,
        llm_client=llm,
        manifold_store=store,
    )


def nature_nurture_example():
    """Example: Same DNA, different initial manifolds."""
    print("=== Nature/Nurture Experiment ===")
    print("Same DNA (nature), different initial manifolds (nurture)\n")
    
    # Base DNA
    base_dna = DNA(
        agent_id=AgentId("base"),
        role="researcher",
        subscriptions=[],
        tools=[],
        behavior_params={"curiosity": 0.8},
    )
    
    # Different initial manifolds
    initial_manifolds = [
        "I am focused on understanding systems.",
        "I am focused on understanding patterns.",
        "I am focused on understanding connections.",
    ]
    
    # Run experiment
    experiment = NatureNurtureExperiment(
        base_dna=base_dna,
        initial_manifolds=initial_manifolds,
        mind_factory=make_mind,
        num_ticks=5,
    )
    
    results = experiment.run()
    
    print("Results:")
    for result in results:
        print(f"  Variant {result['variant']}:")
        print(f"    Initial length: {result['initial_content_length']}")
        print(f"    Final version: {result['final_version']}")
        print(f"    Final length: {result['final_content_length']}")
    print()


def nurture_nature_example():
    """Example: Same initial manifold, different DNA."""
    print("=== Nurture/Nature Experiment ===")
    print("Same initial manifold (nurture), different DNA (nature)\n")
    
    # Base manifold content
    base_manifold = "I understand that systems evolve through interaction."
    
    # Different DNA variants
    dna_variants = [
        DNA(
            agent_id=AgentId("variant-0"),
            role="researcher",
            subscriptions=[],
            behavior_params={"curiosity": 0.5},
        ),
        DNA(
            agent_id=AgentId("variant-1"),
            role="analyst",
            subscriptions=[],
            behavior_params={"curiosity": 0.9},
        ),
        DNA(
            agent_id=AgentId("variant-2"),
            role="synthesizer",
            subscriptions=[],
            behavior_params={"synthesis_tendency": 0.8},
        ),
    ]
    
    # Run experiment
    experiment = NurtureNatureExperiment(
        base_manifold_content=base_manifold,
        dna_variants=dna_variants,
        mind_factory=make_mind,
        num_ticks=5,
    )
    
    results = experiment.run()
    
    print("Results:")
    for result in results:
        print(f"  Variant {result['variant']} ({result['dna_role']}):")
        print(f"    Subscriptions: {result['dna_subscriptions']}")
        print(f"    Final version: {result['final_version']}")
        print(f"    Final length: {result['final_content_length']}")
    print()


def dna_manipulation_example():
    """Example: DNA cloning and mutation."""
    print("=== DNA Manipulation Example ===\n")
    
    # Original DNA
    original = DNA(
        agent_id=AgentId("original"),
        role="researcher",
        subscriptions=[AgentId("source-1")],
        tools=["search", "analyze"],
        behavior_params={"curiosity": 0.7, "patience": 0.6},
        tags=["research", "analysis"],
    )
    
    # Clone with modifications
    cloned = DNAUtils.clone_dna(
        original,
        new_agent_id=AgentId("cloned"),
        modifications={
            "role": "analyst",
            "subscriptions": [AgentId("source-1"), AgentId("source-2")],
        },
    )
    
    print(f"Original: {original.role}, {len(original.subscriptions)} subscriptions")
    print(f"Cloned: {cloned.role}, {len(cloned.subscriptions)} subscriptions")
    
    # Mutate
    mutated = DNAUtils.mutate_dna(original, mutation_rate=0.5)
    print(f"Mutated: {mutated.role}, {len(mutated.subscriptions)} subscriptions")
    
    # Create population
    population = DNAUtils.create_population(original, population_size=3, mutation_rate=0.3)
    print(f"Population: {len(population)} variants created\n")


def manifold_manipulation_example():
    """Example: Manifold cloning and transplantation."""
    print("=== Manifold Manipulation Example ===\n")
    
    store1 = InMemoryManifoldStore()
    store2 = InMemoryManifoldStore()
    
    # Create source manifold
    source_env = ManifoldEnvelope(
        agent_id=AgentId("source"),
        version=5,
        content="I have learned that systems evolve through interaction.",
        metadata={"source": True},
    )
    store1.save(source_env)
    
    # Clone to new agent
    cloned = ManifoldUtils.clone_manifold(
        store1, store2, AgentId("source"), AgentId("target")
    )
    
    if cloned:
        print(f"Cloned manifold:")
        print(f"  Source: version {source_env.version}")
        print(f"  Target: version {cloned.version}")
        print(f"  Content length: {len(cloned.content)}")
        print(f"  Metadata: {cloned.metadata}\n")


if __name__ == "__main__":
    print("Synaplex Nature/Nurture Experiment Examples\n")
    
    nature_nurture_example()
    nurture_nature_example()
    dna_manipulation_example()
    manifold_manipulation_example()
    
    print("=== Examples Complete ===")


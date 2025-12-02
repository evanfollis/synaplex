"""
Example demonstrating geometric operators in Synaplex.

This example shows:
- Frottage generation in projections (F)
- Lens refraction (Φ_sem, Φ_tel)
- Holonomy tracking (H)
- Health metric computation (D, R_div, A_sat, H_rate, T)
- Geometric metadata (A, K, τ)
"""

from synaplex.core.ids import AgentId, WorldId, MessageId
from synaplex.core.dna import DNA
from synaplex.core.lenses import Lens
from synaplex.core.messages import Request, Signal
from synaplex.core.runtime_inprocess import InProcessRuntime, GraphConfig, EdgeConfig
from synaplex.core.env_state import EnvState
from synaplex.cognition.mind import Mind
from synaplex.cognition.manifolds import ManifoldEnvelope, InMemoryManifoldStore
from synaplex.cognition.llm_client import LLMClient
from synaplex.meta.evaluation import MetricsEngine
from synaplex.manifolds_indexers.indexer_world import (
    AttractorDetector,
    CurvatureAnalyzer,
    TeleologyExtractor,
    EmbeddingAgent,
)


def demonstrate_frottage():
    """Frottage: pure unstructured semantic soup between Minds."""
    print("=== Frottage (F) Example ===")

    agent_id = AgentId("example_agent")
    llm_client = LLMClient()
    mind = Mind(agent_id=agent_id, llm_client=llm_client)

    request = Request(
        id=MessageId("req-1"),
        sender=AgentId("receiver"),
        receiver=agent_id,
        shape={},
    )

    projection = mind.create_projection(request)

    print(f"Frottage present: {projection.frottage is not None}")
    if projection.frottage:
        print(f"Length: {len(projection.frottage)} chars")
        print("(Raw text - no schema, no structure, receiver interprets)")


def demonstrate_holonomy():
    """Demonstrate holonomy tracking (H)."""
    print("\n=== Holonomy (H) Example ===")

    # Create runtime
    world_id = WorldId("example_world")
    runtime = InProcessRuntime(world_id=world_id, env_state=EnvState())

    # Create agent with holonomy action
    agent_id = AgentId("agent_with_holonomy")
    llm_client = LLMClient()
    mind = Mind(agent_id=agent_id, llm_client=llm_client)

    runtime.register_agent(mind)

    # Simulate a tick with holonomy action
    # (In real usage, this would come from the agent's reasoning)
    class HolonomyMind(Mind):
        def act(self, reasoning_output: dict) -> dict:
            behavior = super().act(reasoning_output)
            # Mark as holonomy (irreversible action)
            behavior["holonomy_marker"] = True
            behavior["holonomy_type"] = "commitment"
            behavior["holonomy_description"] = "Made irreversible commitment"
            behavior["env_updates"] = {"committed": True}
            return behavior

    holonomy_mind = HolonomyMind(agent_id=agent_id, llm_client=llm_client)
    runtime.register_agent(holonomy_mind)

    # Run a tick
    runtime.tick(tick_id=1)

    # Check holonomy events
    holonomy_events = runtime.get_holonomy_events()
    print(f"Holonomy events: {len(holonomy_events)}")
    if holonomy_events:
        print(f"First holonomy event: {holonomy_events[0]}")

    # Compute holonomy rate
    h_rate = runtime.get_holonomy_rate()
    print(f"Holonomy rate (H_rate): {h_rate}")


def demonstrate_geometric_metadata():
    """Demonstrate geometric metadata (A, K, τ)."""
    print("\n=== Geometric Metadata (A, K, τ) Example ===")

    # Create manifold with geometric hints
    envelope = ManifoldEnvelope(
        agent_id=AgentId("geometric_agent"),
        version=1,
        content="Internal worldview content...",
        metadata={
            "curvature_hints": {
                "high_sensitivity_regions": ["risk_analysis", "decision_points"],
                "low_sensitivity_regions": ["stable_patterns"],
            },
            "attractor_hints": [
                "pattern_recognition",
                "structural_thinking",
                "risk_awareness",
            ],
            "teleology_hints": {
                "improvement_direction": "maximize_robustness",
                "epistemic_gradient": "toward_falsifiability",
            },
        },
    )

    print(f"Manifold version: {envelope.version}")
    print(f"Curvature hints (K): {envelope.metadata.get('curvature_hints')}")
    print(f"Attractor hints (A): {envelope.metadata.get('attractor_hints')}")
    print(f"Teleology hints (τ): {envelope.metadata.get('teleology_hints')}")


def demonstrate_health_metrics():
    """Demonstrate geometric health scalar computation."""
    print("\n=== Health Metrics (D, R_div, A_sat, H_rate, T) Example ===")

    # Create metrics engine
    embedding_agent = EmbeddingAgent()
    metrics_engine = MetricsEngine(embedding_agent=embedding_agent)

    # Note: In a real example, you would use a RunLogger with actual events
    # This is a placeholder showing the interface
    print("Health scalar methods available:")
    print("  - compute_dimensionality() → D")
    print("  - compute_refraction_diversity() → R_div")
    print("  - compute_attractor_saturation() → A_sat")
    print("  - compute_holonomy_rate() → H_rate")
    print("  - compute_temperature() → T")
    print("  - compute_geometric_health() → All scalars")


def demonstrate_indexer_agents():
    """Demonstrate indexer world agents."""
    print("\n=== Indexer World Agents Example ===")

    embedding_agent = EmbeddingAgent()

    # Create example snapshots (simplified)
    from synaplex.manifolds_indexers.types import ManifoldSnapshot

    snapshots = [
        ManifoldSnapshot(
            agent_id=AgentId("agent1"),
            version=i,
            content=f"Worldview content version {i}",
            metadata={},
        )
        for i in range(1, 5)
    ]

    # Attractor detector
    attractor_detector = AttractorDetector(embedding_agent=embedding_agent)
    attractors = attractor_detector.detect_attractors(snapshots)
    print(f"Attractors detected: {len(attractors.get('attractors', []))}")
    print(f"Attractor hints: {attractors.get('attractor_hints', [])}")

    # Curvature analyzer
    curvature_analyzer = CurvatureAnalyzer(embedding_agent=embedding_agent)
    curvature = curvature_analyzer.analyze_curvature(snapshots)
    print(f"Curvature profile: {curvature.get('curvature_profile')}")
    print(f"Avg change magnitude: {curvature.get('avg_change_magnitude')}")

    # Teleology extractor
    teleology_extractor = TeleologyExtractor(embedding_agent=embedding_agent)
    teleology = teleology_extractor.extract_teleology(snapshots)
    print(f"Teleology direction: {teleology.get('teleology_direction')}")
    print(f"Avg content growth: {teleology.get('avg_content_growth')}")


def main():
    """Run all geometric operator examples."""
    print("Synaplex Geometric Operators Example")
    print("=" * 50)

    demonstrate_frottage()
    demonstrate_holonomy()
    demonstrate_geometric_metadata()
    demonstrate_health_metrics()
    demonstrate_indexer_agents()

    print("\n" + "=" * 50)
    print("All examples completed!")


if __name__ == "__main__":
    main()


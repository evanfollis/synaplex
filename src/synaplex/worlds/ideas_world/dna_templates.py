from synaplex.core.dna import DNA
from synaplex.core.ids import AgentId


def make_idea_ingest_agent(agent_id: str = "idea_ingest") -> DNA:
    """
    IDEA_INGEST: P-heavy ingestion agent.

    - Reads messy idea sources (markdown, later chat logs, execution feedback, etc.)
    - Emits high-entropy idea signals (P) into the graph.
    - No subscriptions: it treats the outside world as its upstream.
    """
    return DNA(
        agent_id=AgentId(agent_id),
        role="idea_ingest",
        subscriptions=[],
        tools=[],
        behavior_params={
            "frottage_mode": True,     # lean toward on-topic noise
            "max_preview_chars": 400,
        },
        tags=["ideas", "ingest", "perturbations", "P"],
    )


def make_idea_architect_agent(agent_id: str = "idea_architect") -> DNA:
    """
    IDEA_ARCHITECT: structure + attractors (M/A).

    - Subscribes to idea_ingest (P).
    - Builds / maintains manifold about global idea space.
    - Tracks clusters, gaps, and emergent attractors.
    """
    return DNA(
        agent_id=AgentId(agent_id),
        role="idea_architect",
        subscriptions=[AgentId("idea_ingest")],
        tools=[],
        behavior_params={
            "synthesis_tendency": 0.9,
            "gap_hunting": 0.8,
        },
        tags=["ideas", "structure", "attractors", "M", "A"],
    )


def make_idea_critic_agent(agent_id: str = "idea_critic") -> DNA:
    """
    IDEA_CRITIC: tensions + contradictions (M/A).

    - Subscribes to idea_ingest (P).
    - Maintains manifold focused on tensions, duplicates, blind spots.
    - Feeds IdeaPM with risk / downside / redundancy signals.
    """
    return DNA(
        agent_id=AgentId(agent_id),
        role="idea_critic",
        subscriptions=[AgentId("idea_ingest")],
        tools=[],
        behavior_params={
            "skepticism": 0.85,
            "pattern_detection": 0.9,
        },
        tags=["ideas", "critique", "tensions", "M", "A"],
    )


def make_idea_pm_agent(agent_id: str = "idea_pm") -> DNA:
    """
    IDEA_PM: portfolio + curvature (A/K).

    - Subscribes to: idea_ingest, idea_architect, idea_critic.
    - Owns the idea portfolio (A): which ideas are live, hot, dormant.
    - Encodes curvature (K): how sensitive priorities are to new evidence.
    - Emits 'ready_for_execution' signals and 'deprioritized' signals.
    """
    return DNA(
        agent_id=AgentId(agent_id),
        role="idea_pm",
        subscriptions=[
            AgentId("idea_ingest"),
            AgentId("idea_architect"),
            AgentId("idea_critic"),
        ],
        tools=[],
        behavior_params={
            "risk_tolerance": 0.6,    # how easily to promote to execution
            "focus_limit": 7,         # max concurrently 'hot' ideas
        },
        tags=["ideas", "portfolio", "curvature", "A", "K"],
    )


def make_execution_agent(agent_id: str = "execution") -> DNA:
    """
    EXECUTION: holonomy (H).

    - Subscribes to: idea_pm (which ideas to act on).
    - In future: also subscribes to external action results.
    - Owns H: logs action plans / 'irreversible-ish' moves into EnvState.
    - Does not itself mutate manifolds of others; just acts and reports.
    """
    return DNA(
        agent_id=AgentId(agent_id),
        role="execution",
        subscriptions=[AgentId("idea_pm")],
        tools=[
            # later: cursor / api-based tools go here
        ],
        behavior_params={
            "max_parallel_actions": 3,
        },
        tags=["execution", "holonomy", "H"],
    )


def make_geometry_steward_agent(agent_id: str = "geometry_steward") -> DNA:
    """
    GEOMETRY_STEWARD: Φ/Ω-focused meta-mind for this world.

    - Subscribes to: idea_architect, idea_critic, idea_pm.
    - Maintains manifold about:

        * how well IDEA_WORLD is respecting GEOMETRIC_CONSTITUTION
        * where Φ (lenses) are misaligned
        * candidate Ω moves (config/spec changes) to improve health.

    - Does NOT directly change DNA / configs at runtime:
      it emits structured proposals for a human/meta process.
    """
    return DNA(
        agent_id=AgentId(agent_id),
        role="geometry_steward",
        subscriptions=[
            AgentId("idea_architect"),
            AgentId("idea_critic"),
            AgentId("idea_pm"),
        ],
        tools=[],
        behavior_params={
            "constitution_guardian": True,
            "suggest_omega_moves": True,
        },
        tags=["geometry", "steward", "Phi", "Omega"],
    )

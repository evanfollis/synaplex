from __future__ import annotations

from pathlib import Path

from synaplex.core.ids import WorldId, AgentId
from synaplex.core.runtime_inprocess import InProcessRuntime, GraphConfig, EdgeConfig
from synaplex.core.env_state import EnvState

from .dna_templates import (
    make_idea_ingest_agent,
    make_idea_architect_agent,
    make_idea_critic_agent,
    make_idea_pm_agent,
    make_execution_agent,
    make_geometry_steward_agent,
)
from .agents import (
    make_idea_ingest_mind,
    make_idea_architect_mind,
    make_idea_critic_mind,
    make_idea_pm_mind,
    make_execution_mind,
    make_geometry_steward_mind,
)
from .lenses import (
    IdeaIngestLens,
    IdeaArchitectLens,
    IdeaCriticLens,
    IdeaPMLens,
    ExecutionLens,
    GeometryStewardLens,
)


def bootstrap_idea_world(
    ideas_dir: str | Path = "docs/ideas",
    manifold_store_root: str = "manifolds/ideas_world",
    world_id: str = "idea-world",
) -> InProcessRuntime:
    """
    Bootstrap IDEA_WORLD under the geometric constitution.

    Agents & flows:

        P: IdeaIngestMind
            → emits 'idea' signals

        M/A: IdeaArchitectMind
            ← subscribes to idea_ingest

        M/A: IdeaCriticMind
            ← subscribes to idea_ingest

        A/K: IdeaPMMind
            ← subscribes to idea_ingest, idea_architect, idea_critic
            → emits 'ready_for_execution', 'idea_portfolio_state'

        H: ExecutionMind
            ← subscribes to idea_pm
            → writes execution plans to EnvState, emits 'execution_planned'

        Φ/Ω: GeometryStewardMind
            ← subscribes to idea_architect, idea_critic, idea_pm
            → emits 'omega_proposal' signals for human/meta consumption
    """
    world_id_obj = WorldId(world_id)
    env_state = EnvState()

    graph_config = GraphConfig(
        edges=[
            # Architect & Critic subscribe to ingest
            EdgeConfig(subscriber=AgentId("idea_architect"), publisher=AgentId("idea_ingest")),
            EdgeConfig(subscriber=AgentId("idea_critic"), publisher=AgentId("idea_ingest")),

            # IdeaPM sees ingest + architect + critic
            EdgeConfig(subscriber=AgentId("idea_pm"), publisher=AgentId("idea_ingest")),
            EdgeConfig(subscriber=AgentId("idea_pm"), publisher=AgentId("idea_architect")),
            EdgeConfig(subscriber=AgentId("idea_pm"), publisher=AgentId("idea_critic")),

            # Execution listens to PM for ready-for-execution choices
            EdgeConfig(subscriber=AgentId("execution"), publisher=AgentId("idea_pm")),

            # Geometry steward inspects structure, tensions, and portfolio state
            EdgeConfig(subscriber=AgentId("geometry_steward"), publisher=AgentId("idea_architect")),
            EdgeConfig(subscriber=AgentId("geometry_steward"), publisher=AgentId("idea_critic")),
            EdgeConfig(subscriber=AgentId("geometry_steward"), publisher=AgentId("idea_pm")),
        ]
    )

    runtime = InProcessRuntime(
        world_id=world_id_obj,
        env_state=env_state,
        graph_config=graph_config,
    )

    # DNA
    idea_ingest_dna = make_idea_ingest_agent()
    idea_architect_dna = make_idea_architect_agent()
    idea_critic_dna = make_idea_critic_agent()
    idea_pm_dna = make_idea_pm_agent()
    execution_dna = make_execution_agent()
    geometry_steward_dna = make_geometry_steward_agent()

    # Lenses (Φ)
    idea_ingest_lens = IdeaIngestLens(name="idea_ingest_lens")
    architect_lens = IdeaArchitectLens(name="idea_architect_lens")
    critic_lens = IdeaCriticLens(name="idea_critic_lens")
    pm_lens = IdeaPMLens(name="idea_pm_lens")
    execution_lens = ExecutionLens(name="execution_lens")
    geometry_steward_lens = GeometryStewardLens(name="geometry_steward_lens")

    # Minds
    idea_ingest = make_idea_ingest_mind(
        agent_id=idea_ingest_dna.agent_id.value,
        ideas_dir=ideas_dir,
    )

    idea_architect = make_idea_architect_mind(
        agent_id=idea_architect_dna.agent_id.value,
        store_root=manifold_store_root,
    )

    idea_critic = make_idea_critic_mind(
        agent_id=idea_critic_dna.agent_id.value,
        store_root=manifold_store_root,
    )

    idea_pm = make_idea_pm_mind(
        agent_id=idea_pm_dna.agent_id.value,
        store_root=manifold_store_root,
    )

    execution = make_execution_mind(
        agent_id=execution_dna.agent_id.value,
        store_root=manifold_store_root,
    )

    geometry_steward = make_geometry_steward_mind(
        agent_id=geometry_steward_dna.agent_id.value,
        store_root=manifold_store_root,
    )

    # Registration: nature (DNA) + Φ (lens) + nurture (manifolds)
    runtime.register_agent(idea_ingest, dna=idea_ingest_dna, lens=idea_ingest_lens)
    runtime.register_agent(idea_architect, dna=idea_architect_dna, lens=architect_lens)
    runtime.register_agent(idea_critic, dna=idea_critic_dna, lens=critic_lens)
    runtime.register_agent(idea_pm, dna=idea_pm_dna, lens=pm_lens)
    runtime.register_agent(execution, dna=execution_dna, lens=execution_lens)
    runtime.register_agent(geometry_steward, dna=geometry_steward_dna, lens=geometry_steward_lens)

    return runtime

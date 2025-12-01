# synaplex/meta/population.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable

from synaplex.core.ids import AgentId, WorldId
from synaplex.core.dna import DNA
from synaplex.core.runtime_inprocess import InProcessRuntime, GraphConfig
from synaplex.cognition.manifolds import ManifoldStore, ManifoldEnvelope
from synaplex.cognition.mind import Mind
from synaplex.meta.dna_utils import DNAUtils
from synaplex.meta.manifold_utils import ManifoldUtils
from synaplex.meta.evaluation import MetricsEngine
from synaplex.meta.logging import RunLogger


@dataclass
class PopulationConfig:
    """Configuration for a population."""
    base_dna: DNA
    population_size: int
    mutation_rate: float = 0.1
    initial_manifold_content: Optional[str] = None
    manifold_variant_strategy: str = "identical"  # identical, empty, numbered
    graph_config: Optional[GraphConfig] = None


class Population:
    """
    Manages a population of agents for population-level experiments.
    
    Supports:
    - Population bootstrap with varied DNA/manifolds
    - Population-level metrics
    - Cultural drift tracking
    """
    
    def __init__(
        self,
        config: PopulationConfig,
        mind_factory: Callable[[AgentId, ManifoldStore], Mind],
        manifold_store: ManifoldStore,
        world_id: Optional[WorldId] = None,
    ) -> None:
        """
        Initialize population.
        
        Args:
            config: Population configuration
            mind_factory: Function to create Mind instances
            manifold_store: Store for manifolds
            world_id: Optional world ID
        """
        self.config = config
        self.mind_factory = mind_factory
        self.manifold_store = manifold_store
        self.world_id = world_id or WorldId("population")
        
        self.dna_list: List[DNA] = []
        self.agents: Dict[AgentId, Mind] = {}
        self.runtime: Optional[InProcessRuntime] = None
        self.logger: Optional[RunLogger] = None
    
    def bootstrap(self) -> None:
        """Bootstrap the population with agents."""
        # Create DNA variants
        self.dna_list = DNAUtils.create_population(
            self.config.base_dna,
            self.config.population_size,
            mutation_rate=self.config.mutation_rate,
        )
        
        # Create initial manifolds
        agent_ids = [dna.agent_id for dna in self.dna_list]
        if self.config.initial_manifold_content:
            ManifoldUtils.create_initial_manifold_variants(
                self.config.initial_manifold_content,
                self.manifold_store,
                agent_ids,
                variant_strategy=self.config.manifold_variant_strategy,
            )
        
        # Create minds
        self.agents = {
            dna.agent_id: self.mind_factory(dna.agent_id, self.manifold_store)
            for dna in self.dna_list
        }
        
        # Create runtime
        self.runtime = InProcessRuntime(
            world_id=self.world_id,
            graph_config=self.config.graph_config,
        )
        
        # Register agents
        for dna in self.dna_list:
            self.runtime.register_agent(
                self.agents[dna.agent_id],
                dna=dna,
            )
        
        # Create logger
        self.logger = RunLogger(self.world_id)
        self.logger.set_agent_ids([dna.agent_id for dna in self.dna_list])
        self.runtime.logger = self.logger
    
    def run(self, num_ticks: int) -> None:
        """
        Run the population for a number of ticks.
        
        Args:
            num_ticks: Number of ticks to run
        """
        if self.runtime is None:
            raise RuntimeError("Population not bootstrapped. Call bootstrap() first.")
        
        for tick in range(num_ticks):
            self.runtime.tick(tick)
        
        # Finalize logger
        if self.logger:
            self.logger.finalize()
    
    def get_population_metrics(self) -> Dict[str, Any]:
        """
        Get population-level metrics.
        
        Returns:
            Population statistics
        """
        if not self.logger:
            return {}
        
        metrics_engine = MetricsEngine()
        metrics = metrics_engine.evaluate_run(self.logger)
        
        # Add population-specific metrics
        population_metrics = metrics.get("population_metrics", {})
        
        # Cultural metrics (simplified)
        cultural_metrics = self._compute_cultural_metrics()
        
        return {
            **population_metrics,
            "cultural_metrics": cultural_metrics,
            "population_size": len(self.dna_list),
            "dna_diversity": self._compute_dna_diversity(),
        }
    
    def _compute_cultural_metrics(self) -> Dict[str, Any]:
        """Compute cultural drift metrics."""
        if not self.agents:
            return {}
        
        # Get final manifolds
        final_manifolds = {}
        for agent_id in self.agents.keys():
            env = self.manifold_store.load_latest(agent_id)
            if env:
                final_manifolds[agent_id] = env
        
        if len(final_manifolds) < 2:
            return {
                "cultural_drift": 0.0,
                "convergence": 0.0,
            }
        
        # Compute pairwise content similarities
        # (simplified: use content length as proxy)
        content_lengths = [len(env.content) for env in final_manifolds.values()]
        avg_length = sum(content_lengths) / len(content_lengths) if content_lengths else 0
        
        # Variance in content length as proxy for cultural diversity
        if len(content_lengths) > 1:
            variance = sum((x - avg_length) ** 2 for x in content_lengths) / len(content_lengths)
            cultural_drift = variance / (avg_length ** 2 + 1)  # Normalized
        else:
            cultural_drift = 0.0
        
        return {
            "cultural_drift": cultural_drift,
            "avg_content_length": avg_length,
            "content_length_variance": variance if len(content_lengths) > 1 else 0.0,
        }
    
    def _compute_dna_diversity(self) -> float:
        """Compute diversity of DNA in population."""
        if len(self.dna_list) < 2:
            return 0.0
        
        # Simple diversity metric: count unique combinations of key DNA features
        unique_roles = len(set(dna.role for dna in self.dna_list))
        unique_subscription_counts = len(set(len(dna.subscriptions) for dna in self.dna_list))
        unique_tool_counts = len(set(len(dna.tools) for dna in self.dna_list))
        
        # Normalized diversity score
        max_diversity = len(self.dna_list)
        diversity = (
            unique_roles + unique_subscription_counts + unique_tool_counts
        ) / (3.0 * max_diversity)
        
        return min(1.0, diversity)
    
    def get_agent_manifolds(self) -> Dict[AgentId, Optional[ManifoldEnvelope]]:
        """Get latest manifolds for all agents."""
        return {
            agent_id: self.manifold_store.load_latest(agent_id)
            for agent_id in self.agents.keys()
        }
    
    def clone_agent(
        self,
        source_agent_id: AgentId,
        new_agent_id: AgentId,
        clone_manifold: bool = True,
    ) -> None:
        """
        Clone an agent (DNA and optionally manifold).
        
        Args:
            source_agent_id: Source agent ID
            new_agent_id: New agent ID
            clone_manifold: Whether to clone manifold too
        """
        # Clone DNA
        source_dna = next((dna for dna in self.dna_list if dna.agent_id == source_agent_id), None)
        if source_dna is None:
            raise ValueError(f"Source agent {source_agent_id} not found")
        
        new_dna = DNAUtils.clone_dna(source_dna, new_agent_id=new_agent_id)
        self.dna_list.append(new_dna)
        
        # Clone manifold if requested
        if clone_manifold:
            ManifoldUtils.clone_manifold(
                self.manifold_store,
                self.manifold_store,
                source_agent_id,
                new_agent_id,
            )
        
        # Create mind
        self.agents[new_agent_id] = self.mind_factory(new_agent_id, self.manifold_store)
        
        # Register with runtime
        if self.runtime:
            self.runtime.register_agent(
                self.agents[new_agent_id],
                dna=new_dna,
            )


def bootstrap_population(
    base_dna: DNA,
    population_size: int,
    mind_factory: Callable[[AgentId, ManifoldStore], Mind],
    manifold_store: ManifoldStore,
    mutation_rate: float = 0.1,
    initial_manifold_content: Optional[str] = None,
    graph_config: Optional[GraphConfig] = None,
) -> Population:
    """
    Bootstrap a population.
    
    Args:
        base_dna: Base DNA for population
        population_size: Size of population
        mind_factory: Function to create Mind instances
        manifold_store: Store for manifolds
        mutation_rate: DNA mutation rate
        initial_manifold_content: Initial manifold content
        graph_config: Graph configuration
        
    Returns:
        Bootstrapped population
    """
    config = PopulationConfig(
        base_dna=base_dna,
        population_size=population_size,
        mutation_rate=mutation_rate,
        initial_manifold_content=initial_manifold_content,
        graph_config=graph_config,
    )
    
    population = Population(
        config=config,
        mind_factory=mind_factory,
        manifold_store=manifold_store,
    )
    
    population.bootstrap()
    return population


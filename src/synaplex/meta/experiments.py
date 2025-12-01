# synaplex/meta/experiments.py

from __future__ import annotations

from typing import Any, Dict, List, Optional

from synaplex.core.ids import AgentId, WorldId
from synaplex.core.dna import DNA
from synaplex.core.runtime_inprocess import InProcessRuntime
from synaplex.cognition.manifolds import ManifoldStore, ManifoldEnvelope
from synaplex.cognition.mind import Mind
from synaplex.meta.logging import RunLogger
from synaplex.meta.dna_utils import DNAUtils
from synaplex.meta.manifold_utils import ManifoldUtils


class NatureNurtureExperiment:
    """
    Experiment harness for nature/nurture studies.
    
    Runs the same DNA (nature) with different initial manifolds (nurture)
    to study how nurture affects behavior given fixed nature.
    """
    
    def __init__(
        self,
        base_dna: DNA,
        initial_manifolds: List[str],
        mind_factory: callable[[AgentId, ManifoldStore], Mind],
        num_ticks: int = 10,
    ) -> None:
        """
        Initialize experiment.
        
        Args:
            base_dna: Base DNA to use (will be cloned for each variant)
            initial_manifolds: List of initial manifold contents
            mind_factory: Function to create Mind instances
            num_ticks: Number of ticks to run
        """
        self.base_dna = base_dna
        self.initial_manifolds = initial_manifolds
        self.mind_factory = mind_factory
        self.num_ticks = num_ticks
        self.results: List[Dict[str, Any]] = []
    
    def run(self) -> List[Dict[str, Any]]:
        """
        Run the experiment.
        
        Returns:
            List of results, one per variant
        """
        from synaplex.cognition.manifolds import InMemoryManifoldStore
        
        results = []
        
        for i, initial_content in enumerate(self.initial_manifolds):
            # Create variant DNA
            variant_dna = DNAUtils.clone_dna(
                self.base_dna,
                new_agent_id=AgentId(f"variant-{i}"),
            )
            
            # Create store and seed initial manifold
            store = InMemoryManifoldStore()
            initial_env = ManifoldEnvelope(
                agent_id=variant_dna.agent_id,
                version=0,
                content=initial_content,
                metadata={"experiment": "nature_nurture", "variant": i},
            )
            store.save(initial_env)
            
            # Create mind
            mind = self.mind_factory(variant_dna.agent_id, store)
            
            # Create runtime and run
            world_id = WorldId(f"experiment-{i}")
            runtime = InProcessRuntime(world_id=world_id)
            runtime.register_agent(mind, dna=variant_dna)
            
            # Run ticks
            for tick in range(self.num_ticks):
                runtime.tick(tick)
            
            # Collect results
            final_manifold = store.load_latest(variant_dna.agent_id)
            results.append({
                "variant": i,
                "initial_content_length": len(initial_content),
                "final_version": final_manifold.version if final_manifold else 0,
                "final_content_length": len(final_manifold.content) if final_manifold else 0,
            })
        
        self.results = results
        return results


class NurtureNatureExperiment:
    """
    Experiment harness for nurture/nature studies.
    
    Runs the same initial manifold (nurture) with different DNA (nature)
    to study how nature affects behavior given fixed nurture.
    """
    
    def __init__(
        self,
        base_manifold_content: str,
        dna_variants: List[DNA],
        mind_factory: callable[[AgentId, ManifoldStore], Mind],
        num_ticks: int = 10,
    ) -> None:
        """
        Initialize experiment.
        
        Args:
            base_manifold_content: Initial manifold content (same for all)
            dna_variants: List of DNA variants to test
            mind_factory: Function to create Mind instances
            num_ticks: Number of ticks to run
        """
        self.base_manifold_content = base_manifold_content
        self.dna_variants = dna_variants
        self.mind_factory = mind_factory
        self.num_ticks = num_ticks
        self.results: List[Dict[str, Any]] = []
    
    def run(self) -> List[Dict[str, Any]]:
        """
        Run the experiment.
        
        Returns:
            List of results, one per variant
        """
        from synaplex.cognition.manifolds import InMemoryManifoldStore
        
        results = []
        
        for i, dna_variant in enumerate(self.dna_variants):
            # Create store and seed initial manifold
            store = InMemoryManifoldStore()
            initial_env = ManifoldEnvelope(
                agent_id=dna_variant.agent_id,
                version=0,
                content=self.base_manifold_content,
                metadata={"experiment": "nurture_nature", "variant": i},
            )
            store.save(initial_env)
            
            # Create mind
            mind = self.mind_factory(dna_variant.agent_id, store)
            
            # Create runtime and run
            world_id = WorldId(f"experiment-{i}")
            runtime = InProcessRuntime(world_id=world_id)
            runtime.register_agent(mind, dna=dna_variant)
            
            # Run ticks
            for tick in range(self.num_ticks):
                runtime.tick(tick)
            
            # Collect results
            final_manifold = store.load_latest(dna_variant.agent_id)
            results.append({
                "variant": i,
                "dna_role": dna_variant.role,
                "dna_subscriptions": len(dna_variant.subscriptions),
                "final_version": final_manifold.version if final_manifold else 0,
                "final_content_length": len(final_manifold.content) if final_manifold else 0,
            })
        
        self.results = results
        return results


class PopulationExperiment:
    """
    Experiment harness for population-level studies.
    
    Runs populations of agents with varied configurations to study
    cultural drift, convergence, and population-level phenomena.
    """
    
    def __init__(
        self,
        base_dna: DNA,
        population_size: int,
        mind_factory: callable[[AgentId, ManifoldStore], Mind],
        num_ticks: int = 10,
        mutation_rate: float = 0.1,
    ) -> None:
        """
        Initialize experiment.
        
        Args:
            base_dna: Base DNA for population
            population_size: Number of agents in population
            mind_factory: Function to create Mind instances
            num_ticks: Number of ticks to run
            mutation_rate: DNA mutation rate for population diversity
        """
        self.base_dna = base_dna
        self.population_size = population_size
        self.mind_factory = mind_factory
        self.num_ticks = num_ticks
        self.mutation_rate = mutation_rate
        self.results: Dict[str, Any] = {}
    
    def run(self) -> Dict[str, Any]:
        """
        Run the experiment.
        
        Returns:
            Results including population statistics
        """
        from synaplex.cognition.manifolds import InMemoryManifoldStore
        
        # Create population DNA variants
        population_dna = DNAUtils.create_population(
            self.base_dna,
            self.population_size,
            mutation_rate=self.mutation_rate,
        )
        
        # Create runtime with all agents
        world_id = WorldId("population-experiment")
        runtime = InProcessRuntime(world_id=world_id)
        
        # Create and register all agents
        stores = {}
        for dna in population_dna:
            store = InMemoryManifoldStore()
            stores[dna.agent_id] = store
            mind = self.mind_factory(dna.agent_id, store)
            runtime.register_agent(mind, dna=dna)
        
        # Run ticks
        for tick in range(self.num_ticks):
            runtime.tick(tick)
        
        # Collect results
        final_manifolds = {
            agent_id: store.load_latest(agent_id)
            for agent_id, store in stores.items()
        }
        
        self.results = {
            "population_size": self.population_size,
            "num_ticks": self.num_ticks,
            "final_versions": {
                agent_id.value: env.version if env else 0
                for agent_id, env in final_manifolds.items()
            },
            "content_lengths": {
                agent_id.value: len(env.content) if env else 0
                for agent_id, env in final_manifolds.items()
            },
        }
        
        return self.results


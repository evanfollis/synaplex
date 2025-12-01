# synaplex/meta/evolution.py

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from synaplex.core.dna import DNA
from synaplex.core.ids import AgentId
from synaplex.core.runtime_inprocess import GraphConfig, EdgeConfig
from synaplex.meta.dna_utils import DNAUtils


class EvolutionEngine:
    """
    Evolution engine for DNA and graph topology.
    
    Enables selection-blind evolution based on metrics.
    """
    
    def __init__(
        self,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.3,
    ) -> None:
        """
        Initialize evolution engine.
        
        Args:
            mutation_rate: Probability of mutation per DNA
            crossover_rate: Probability of crossover between pairs
        """
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
    
    def mutate_dna(
        self,
        dna_list: List[DNA],
        mutation_rate: Optional[float] = None,
        mutation_types: Optional[List[str]] = None,
    ) -> List[DNA]:
        """
        Mutate a list of DNA objects.
        
        Args:
            dna_list: List of DNA to mutate
            mutation_rate: Override default mutation rate
            mutation_types: Which aspects to mutate
            
        Returns:
            List of mutated DNA objects
        """
        mutation_rate = mutation_rate or self.mutation_rate
        
        mutated = []
        for dna in dna_list:
            if random.random() < mutation_rate:
                mutated_dna = DNAUtils.mutate_dna(
                    dna,
                    mutation_rate=1.0,  # Always mutate if selected
                    mutation_types=mutation_types,
                )
                mutated.append(mutated_dna)
            else:
                mutated.append(dna)
        
        return mutated
    
    def evolve(
        self,
        dna_list: List[DNA],
        metrics: Dict[str, Any],
        selection_strategy: str = "random",
        elite_size: int = 0,
    ) -> List[DNA]:
        """
        Evolve DNA based on metrics.
        
        Args:
            dna_list: Current population of DNA
            metrics: Performance metrics (selection-blind to agents)
            selection_strategy: How to select for evolution
                - "random": Random selection
                - "elite": Keep top performers, mutate rest
                - "tournament": Tournament selection
            elite_size: Number of elite to preserve (for "elite" strategy)
            
        Returns:
            New evolved population
        """
        if selection_strategy == "random":
            return self._evolve_random(dna_list, metrics)
        elif selection_strategy == "elite":
            return self._evolve_elite(dna_list, metrics, elite_size)
        elif selection_strategy == "tournament":
            return self._evolve_tournament(dna_list, metrics)
        else:
            raise ValueError(f"Unknown selection_strategy: {selection_strategy}")
    
    def _evolve_random(
        self,
        dna_list: List[DNA],
        metrics: Dict[str, Any],
    ) -> List[DNA]:
        """Random evolution: mutate all with some probability."""
        return self.mutate_dna(dna_list)
    
    def _evolve_elite(
        self,
        dna_list: List[DNA],
        metrics: Dict[str, Any],
        elite_size: int,
    ) -> List[DNA]:
        """
        Elite evolution: preserve top performers, evolve rest.
        
        Note: This is selection-blind - we don't know which DNA
        corresponds to which agent's metrics. So we use a proxy:
        assume metrics are ordered or use random selection.
        """
        if elite_size >= len(dna_list):
            return dna_list
        
        # Randomly select elite (in real implementation, would use metrics)
        elite_indices = random.sample(range(len(dna_list)), elite_size)
        elite = [dna_list[i] for i in elite_indices]
        
        # Evolve non-elite
        non_elite = [dna for i, dna in enumerate(dna_list) if i not in elite_indices]
        evolved = self.mutate_dna(non_elite)
        
        return elite + evolved
    
    def _evolve_tournament(
        self,
        dna_list: List[DNA],
        metrics: Dict[str, Any],
    ) -> List[DNA]:
        """
        Tournament selection evolution.
        
        Randomly select pairs, keep "winner" (random for now),
        mutate loser.
        """
        evolved = []
        
        while len(evolved) < len(dna_list):
            # Tournament: select two random DNA
            pair = random.sample(dna_list, min(2, len(dna_list)))
            
            if len(pair) == 2:
                # Randomly choose winner and loser
                winner, loser = random.sample(pair, 2)
                evolved.append(winner)
                # Mutate loser
                mutated_loser = DNAUtils.mutate_dna(loser, mutation_rate=1.0)
                evolved.append(mutated_loser)
            else:
                evolved.extend(pair)
        
        return evolved[:len(dna_list)]
    
    def crossover(
        self,
        dna1: DNA,
        dna2: DNA,
        new_agent_id: AgentId,
    ) -> DNA:
        """
        Crossover two DNA to create offspring.
        
        Args:
            dna1: First parent DNA
            dna2: Second parent DNA
            new_agent_id: Agent ID for offspring
            
        Returns:
            New DNA combining traits from both parents
        """
        return DNAUtils.combine_dna(
            dna1,
            dna2,
            new_agent_id,
            combination_strategy="merge",
        )
    
    def evolve_graph_config(
        self,
        graph_config: GraphConfig,
        mutation_rate: Optional[float] = None,
    ) -> GraphConfig:
        """
        Evolve graph topology.
        
        Args:
            graph_config: Current graph configuration
            mutation_rate: Probability of mutation
            
        Returns:
            Evolved graph configuration
        """
        mutation_rate = mutation_rate or self.mutation_rate
        
        new_edges = graph_config.edges.copy()
        
        # Randomly add or remove edges
        if random.random() < mutation_rate:
            if random.random() < 0.5 and new_edges:
                # Remove random edge
                new_edges.pop(random.randint(0, len(new_edges) - 1))
            else:
                # Add random edge (would need agent IDs from runtime)
                # For now, skip addition
                pass
        
        return GraphConfig(edges=new_edges)
    
    def create_population_variants(
        self,
        base_dna: DNA,
        population_size: int,
        mutation_rate: Optional[float] = None,
    ) -> List[DNA]:
        """
        Create a population of DNA variants.
        
        Args:
            base_dna: Base DNA to vary
            population_size: Size of population
            mutation_rate: Mutation rate
            
        Returns:
            List of DNA variants
        """
        return DNAUtils.create_population(
            base_dna,
            population_size,
            mutation_rate=mutation_rate or self.mutation_rate,
        )
    
    def select_best(
        self,
        dna_list: List[DNA],
        metrics: Dict[str, Any],
        top_k: int = 1,
    ) -> List[DNA]:
        """
        Select best performing DNA based on metrics.
        
        Note: This is selection-blind - we don't know which DNA
        corresponds to which metrics. In practice, this would
        require tracking DNA -> metrics mapping.
        
        Args:
            dna_list: List of DNA
            metrics: Performance metrics
            top_k: Number of top performers to return
            
        Returns:
            List of top-k DNA (random for now, since selection-blind)
        """
        # Since we're selection-blind, randomly select
        # In real implementation, would use metrics to rank
        return random.sample(dna_list, min(top_k, len(dna_list)))

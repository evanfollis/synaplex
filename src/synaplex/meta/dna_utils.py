# synaplex/meta/dna_utils.py

from __future__ import annotations

import copy
import random
from typing import Any, Dict, List, Optional

from synaplex.core.dna import DNA
from synaplex.core.ids import AgentId


class DNAUtils:
    """
    Utilities for manipulating DNA (nature) for experiments.
    
    Enables nature/nurture experiments by allowing independent
    manipulation of structural constraints.
    """
    
    @staticmethod
    def clone_dna(
        original: DNA,
        new_agent_id: Optional[AgentId] = None,
        modifications: Optional[Dict[str, Any]] = None,
    ) -> DNA:
        """
        Clone DNA with optional modifications.
        
        Args:
            original: DNA to clone
            new_agent_id: New agent ID (defaults to original)
            modifications: Dict of field modifications:
                - "role": new role
                - "subscriptions": new subscription list
                - "tools": new tools list
                - "behavior_params": dict of param updates
                - "tags": new tags list
        
        Returns:
            New DNA object
        """
        modifications = modifications or {}
        
        return DNA(
            agent_id=new_agent_id or original.agent_id,
            role=modifications.get("role", original.role),
            subscriptions=modifications.get("subscriptions", original.subscriptions.copy()),
            tools=modifications.get("tools", original.tools.copy()),
            behavior_params=modifications.get("behavior_params", original.behavior_params.copy()),
            tags=modifications.get("tags", original.tags.copy()),
            config=modifications.get("config", original.config.copy()),
        )
    
    @staticmethod
    def mutate_dna(
        dna: DNA,
        mutation_rate: float = 0.1,
        mutation_types: Optional[List[str]] = None,
    ) -> DNA:
        """
        Randomly mutate DNA.
        
        Args:
            dna: DNA to mutate
            mutation_rate: Probability of each mutation
            mutation_types: Which aspects to mutate (default: all)
                Options: "subscriptions", "tools", "behavior_params", "tags"
        
        Returns:
            New mutated DNA object
        """
        mutation_types = mutation_types or ["subscriptions", "tools", "behavior_params", "tags"]
        modifications: Dict[str, Any] = {}
        
        if "subscriptions" in mutation_types and random.random() < mutation_rate:
            # Randomly add or remove a subscription
            subs = dna.subscriptions.copy()
            if subs and random.random() < 0.5:
                subs.pop(random.randint(0, len(subs) - 1))
            modifications["subscriptions"] = subs
        
        if "tools" in mutation_types and random.random() < mutation_rate:
            # Randomly add or remove a tool
            tools = dna.tools.copy()
            if tools and random.random() < 0.5:
                tools.pop(random.randint(0, len(tools) - 1))
            modifications["tools"] = tools
        
        if "behavior_params" in mutation_types and random.random() < mutation_rate:
            # Mutate a random behavior parameter
            params = dna.behavior_params.copy()
            if params:
                param_name = random.choice(list(params.keys()))
                # Add small random change
                params[param_name] = params[param_name] + random.uniform(-0.1, 0.1)
                params[param_name] = max(0.0, min(1.0, params[param_name]))  # Clamp to [0, 1]
            modifications["behavior_params"] = params
        
        if "tags" in mutation_types and random.random() < mutation_rate:
            # Randomly add or remove a tag
            tags = dna.tags.copy()
            if tags and random.random() < 0.5:
                tags.pop(random.randint(0, len(tags) - 1))
            modifications["tags"] = tags
        
        return DNAUtils.clone_dna(dna, modifications=modifications)
    
    @staticmethod
    def combine_dna(
        dna1: DNA,
        dna2: DNA,
        new_agent_id: AgentId,
        combination_strategy: str = "merge",
    ) -> DNA:
        """
        Combine two DNA objects.
        
        Args:
            dna1: First DNA
            dna2: Second DNA
            new_agent_id: Agent ID for new DNA
            combination_strategy: How to combine
                - "merge": Merge all fields (union for lists)
                - "dna1_dominant": Prefer dna1, fallback to dna2
                - "dna2_dominant": Prefer dna2, fallback to dna1
                - "random": Randomly choose from each
        
        Returns:
            New combined DNA object
        """
        if combination_strategy == "merge":
            return DNA(
                agent_id=new_agent_id,
                role=dna1.role,  # Use dna1's role
                subscriptions=list(set(dna1.subscriptions + dna2.subscriptions)),
                tools=list(set(dna1.tools + dna2.tools)),
                behavior_params={**dna2.behavior_params, **dna1.behavior_params},  # dna1 overrides
                tags=list(set(dna1.tags + dna2.tags)),
                config={**dna2.config, **dna1.config},  # dna1 overrides
            )
        elif combination_strategy == "dna1_dominant":
            return DNA(
                agent_id=new_agent_id,
                role=dna1.role,
                subscriptions=dna1.subscriptions or dna2.subscriptions,
                tools=dna1.tools or dna2.tools,
                behavior_params=dna1.behavior_params or dna2.behavior_params,
                tags=dna1.tags or dna2.tags,
                config=dna1.config or dna2.config,
            )
        elif combination_strategy == "dna2_dominant":
            return DNA(
                agent_id=new_agent_id,
                role=dna2.role,
                subscriptions=dna2.subscriptions or dna1.subscriptions,
                tools=dna2.tools or dna1.tools,
                behavior_params=dna2.behavior_params or dna1.behavior_params,
                tags=dna2.tags or dna1.tags,
                config=dna2.config or dna1.config,
            )
        elif combination_strategy == "random":
            return DNA(
                agent_id=new_agent_id,
                role=random.choice([dna1.role, dna2.role]),
                subscriptions=random.choice([dna1.subscriptions, dna2.subscriptions]),
                tools=random.choice([dna1.tools, dna2.tools]),
                behavior_params=random.choice([dna1.behavior_params, dna2.behavior_params]),
                tags=random.choice([dna1.tags, dna2.tags]),
                config=random.choice([dna1.config, dna2.config]),
            )
        else:
            raise ValueError(f"Unknown combination_strategy: {combination_strategy}")
    
    @staticmethod
    def create_population(
        base_dna: DNA,
        population_size: int,
        mutation_rate: float = 0.1,
        agent_id_prefix: str = "agent",
    ) -> List[DNA]:
        """
        Create a population of DNA variants from a base DNA.
        
        Args:
            base_dna: Base DNA to mutate
            population_size: Number of variants to create
            mutation_rate: Mutation rate for each variant
            agent_id_prefix: Prefix for agent IDs
        
        Returns:
            List of DNA objects
        """
        population = []
        for i in range(population_size):
            mutated = DNAUtils.mutate_dna(base_dna, mutation_rate=mutation_rate)
            new_id = AgentId(f"{agent_id_prefix}-{i}")
            population.append(
                DNAUtils.clone_dna(mutated, new_agent_id=new_id)
            )
        return population


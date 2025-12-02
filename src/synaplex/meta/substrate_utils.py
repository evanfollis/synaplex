# synaplex/meta/substrate_utils.py

from __future__ import annotations

from typing import List, Optional

from synaplex.cognition.substrate import SubstrateEnvelope, SubstrateStore
from synaplex.core.ids import AgentId


class SubstrateUtils:
    """
    Utilities for manipulating substrates (nurture) for experiments.
    
    Enables nature/nurture experiments by allowing independent
    manipulation of internal worldviews.
    """
    
    @staticmethod
    def clone_substrate(
        source_store: SubstrateStore,
        target_store: SubstrateStore,
        source_agent_id: AgentId,
        target_agent_id: AgentId,
    ) -> Optional[SubstrateEnvelope]:
        """
        Clone a substrate from one agent to another.
        
        Args:
            source_store: Store containing source substrate
            target_store: Store to write cloned substrate to
            source_agent_id: Agent ID of source
            target_agent_id: Agent ID of target
        
        Returns:
            Cloned substrate envelope, or None if source doesn't exist
        """
        source = source_store.load_latest(source_agent_id)
        if source is None:
            return None
        
        cloned = SubstrateEnvelope(
            agent_id=target_agent_id,
            version=0,  # Start at version 0 for new agent
            content=source.content,  # Copy content verbatim
            metadata={
                **source.metadata,
                "cloned_from": source_agent_id.value,
                "clone_version": source.version,
            },
        )
        target_store.save(cloned)
        return cloned
    
    @staticmethod
    def transplant_substrate(
        source_store: SubstrateStore,
        target_store: SubstrateStore,
        source_agent_id: AgentId,
        target_agent_id: AgentId,
    ) -> Optional[SubstrateEnvelope]:
        """
        Transplant a substrate to a new agent (same as clone, but semantic difference).
        
        This is useful for nurture experiments: same worldview, different nature (DNA).
        """
        return SubstrateUtils.clone_substrate(
            source_store, target_store, source_agent_id, target_agent_id
        )
    
    @staticmethod
    def merge_substrates(
        store: SubstrateStore,
        agent_ids: List[AgentId],
        target_agent_id: AgentId,
        merge_strategy: str = "concatenate",
    ) -> Optional[SubstrateEnvelope]:
        """
        Merge multiple substrates into one.
        
        Args:
            store: Store containing all source substrates
            agent_ids: List of agent IDs to merge
            target_agent_id: Agent ID for merged result
            merge_strategy: How to merge
                - "concatenate": Simple concatenation
                - "interleave": Interleave content from all sources
        
        Returns:
            Merged substrate envelope, or None if no sources exist
        """
        sources = []
        for agent_id in agent_ids:
            env = store.load_latest(agent_id)
            if env:
                sources.append(env)
        
        if not sources:
            return None
        
        if merge_strategy == "concatenate":
            merged_content = "\n\n---\n\n".join(
                f"From {env.agent_id.value} (v{env.version}):\n{env.content}"
                for env in sources
            )
        elif merge_strategy == "interleave":
            # Interleave line by line (simplified)
            lines = []
            max_lines = max(len(env.content.split("\n")) for env in sources)
            for i in range(max_lines):
                for env in sources:
                    env_lines = env.content.split("\n")
                    if i < len(env_lines):
                        lines.append(f"[{env.agent_id.value}]: {env_lines[i]}")
            merged_content = "\n".join(lines)
        else:
            raise ValueError(f"Unknown merge_strategy: {merge_strategy}")
        
        merged = SubstrateEnvelope(
            agent_id=target_agent_id,
            version=0,
            content=merged_content,
            metadata={
                "merged_from": [a.value for a in agent_ids],
                "merge_strategy": merge_strategy,
                "source_versions": {env.agent_id.value: env.version for env in sources},
            },
        )
        store.save(merged)
        return merged
    
    @staticmethod
    def create_initial_substrate_variants(
        base_content: str,
        store: SubstrateStore,
        agent_ids: List[AgentId],
        variant_strategy: str = "identical",
    ) -> List[SubstrateEnvelope]:
        """
        Create multiple initial substrates with variations.
        
        Useful for seeding populations with different initial worldviews.
        
        Args:
            base_content: Base substrate content
            store: Store to write substrates to
            agent_ids: List of agent IDs to create substrates for
            variant_strategy: How to vary
                - "identical": All identical
                - "empty": All empty
                - "numbered": Add agent number to content
        
        Returns:
            List of created substrate envelopes
        """
        envelopes = []
        for i, agent_id in enumerate(agent_ids):
            if variant_strategy == "identical":
                content = base_content
            elif variant_strategy == "empty":
                content = ""
            elif variant_strategy == "numbered":
                content = f"{base_content}\n\n[Initialized for agent {agent_id.value}, variant {i}]"
            else:
                content = base_content
            
            env = SubstrateEnvelope(
                agent_id=agent_id,
                version=0,
                content=content,
                metadata={
                    "initial": True,
                    "variant_strategy": variant_strategy,
                    "variant_index": i,
                },
            )
            store.save(env)
            envelopes.append(env)
        
        return envelopes

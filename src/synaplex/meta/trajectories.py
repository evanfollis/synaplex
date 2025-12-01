# synaplex/meta/trajectories.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from synaplex.cognition.manifolds import ManifoldEnvelope, ManifoldStore
from synaplex.core.ids import AgentId
from synaplex.manifolds_indexers.indexer_world.agents import EmbeddingAgent


@dataclass
class TrajectoryPoint:
    """A single point in a manifold trajectory."""
    version: int
    content_length: int
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ManifoldTrajectory:
    """
    Represents the evolution of a manifold over time.
    
    Tracks version history and provides analysis capabilities.
    """
    agent_id: AgentId
    points: List[TrajectoryPoint] = field(default_factory=list)
    
    def add_point(self, envelope: ManifoldEnvelope, embedding: Optional[List[float]] = None) -> None:
        """Add a point to the trajectory."""
        point = TrajectoryPoint(
            version=envelope.version,
            content_length=len(envelope.content),
            embedding=embedding,
            metadata=envelope.metadata.copy(),
        )
        self.points.append(point)
        # Keep sorted by version
        self.points.sort(key=lambda p: p.version)
    
    def get_version_range(self) -> tuple[int, int]:
        """Get min and max versions."""
        if not self.points:
            return (0, 0)
        versions = [p.version for p in self.points]
        return (min(versions), max(versions))
    
    def get_content_growth(self) -> List[int]:
        """Get content length changes between versions."""
        if len(self.points) < 2:
            return []
        return [
            self.points[i + 1].content_length - self.points[i].content_length
            for i in range(len(self.points) - 1)
        ]
    
    def get_similarity_over_time(self, embedding_agent: EmbeddingAgent) -> List[float]:
        """
        Compute similarity between consecutive versions.
        
        Returns list of similarity scores (0-1) between adjacent versions.
        """
        if len(self.points) < 2:
            return []
        
        similarities = []
        for i in range(len(self.points) - 1):
            # If embeddings not computed, compute them
            if self.points[i].embedding is None or self.points[i + 1].embedding is None:
                # Would need actual content to compute embeddings
                # For now, return placeholder
                similarities.append(0.5)
            else:
                # Cosine similarity
                emb1 = self.points[i].embedding
                emb2 = self.points[i + 1].embedding
                dot_product = sum(a * b for a, b in zip(emb1, emb2))
                similarities.append(max(0.0, min(1.0, dot_product)))
        
        return similarities


class TrajectoryAnalyzer:
    """
    Analyzes manifold trajectories for patterns and changes.
    """
    
    def __init__(self, embedding_agent: Optional[EmbeddingAgent] = None) -> None:
        """
        Initialize trajectory analyzer.
        
        Args:
            embedding_agent: Optional embedding agent for similarity computation
        """
        self.embedding_agent = embedding_agent or EmbeddingAgent()
    
    def build_trajectory(
        self,
        store: ManifoldStore,
        agent_id: AgentId,
        max_versions: Optional[int] = None,
    ) -> Optional[ManifoldTrajectory]:
        """
        Build trajectory from manifold store.
        
        Note: This requires the store to support version history.
        For now, we only load the latest version.
        In a full implementation, stores would support version queries.
        
        Args:
            store: Manifold store
            agent_id: Agent ID
            max_versions: Maximum number of versions to include
            
        Returns:
            Trajectory or None if no manifold exists
        """
        # Load latest (in full implementation, would load all versions)
        latest = store.load_latest(agent_id)
        if latest is None:
            return None
        
        trajectory = ManifoldTrajectory(agent_id=agent_id)
        
        # For now, just add the latest version
        # In full implementation, would iterate through all versions
        embedding = self.embedding_agent.embed(
            type('Snapshot', (), {
                'agent_id': agent_id,
                'version': latest.version,
                'content': latest.content,
                'metadata': latest.metadata,
            })()
        )
        trajectory.add_point(latest, embedding=embedding)
        
        return trajectory
    
    def analyze_trajectory(self, trajectory: ManifoldTrajectory) -> Dict[str, Any]:
        """
        Analyze a trajectory for patterns.
        
        Args:
            trajectory: Trajectory to analyze
            
        Returns:
            Analysis results
        """
        if not trajectory.points:
            return {
                "num_versions": 0,
                "stability": 1.0,
                "growth_rate": 0.0,
            }
        
        similarities = trajectory.get_similarity_over_time(self.embedding_agent)
        content_growth = trajectory.get_content_growth()
        
        stability = sum(similarities) / len(similarities) if similarities else 1.0
        
        avg_growth = sum(content_growth) / len(content_growth) if content_growth else 0.0
        
        version_range = trajectory.get_version_range()
        
        return {
            "num_versions": len(trajectory.points),
            "version_range": version_range,
            "stability": stability,
            "avg_similarity": stability,
            "content_growth": content_growth,
            "avg_growth": avg_growth,
            "total_growth": trajectory.points[-1].content_length - trajectory.points[0].content_length if len(trajectory.points) > 1 else 0,
        }
    
    def compare_trajectories(
        self,
        trajectory1: ManifoldTrajectory,
        trajectory2: ManifoldTrajectory,
    ) -> Dict[str, Any]:
        """
        Compare two trajectories.
        
        Args:
            trajectory1: First trajectory
            trajectory2: Second trajectory
            
        Returns:
            Comparison results
        """
        if not trajectory1.points or not trajectory2.points:
            return {
                "initial_similarity": 0.0,
                "final_similarity": 0.0,
                "divergence": 0.0,
                "convergence": 0.0,
            }
        
        # Get final embeddings
        final1_emb = trajectory1.points[-1].embedding
        final2_emb = trajectory2.points[-1].embedding
        
        if final1_emb is None or final2_emb is None:
            return {
                "initial_similarity": 0.0,
                "final_similarity": 0.0,
                "divergence": 0.0,
                "convergence": 0.0,
            }
        
        # Final similarity
        dot_product = sum(a * b for a, b in zip(final1_emb, final2_emb))
        final_similarity = max(0.0, min(1.0, dot_product))
        
        # Initial similarity
        initial1_emb = trajectory1.points[0].embedding
        initial2_emb = trajectory2.points[0].embedding
        
        if initial1_emb is None or initial2_emb is None:
            initial_similarity = 0.0
        else:
            dot_init = sum(a * b for a, b in zip(initial1_emb, initial2_emb))
            initial_similarity = max(0.0, min(1.0, dot_init))
        
        divergence = max(0.0, initial_similarity - final_similarity)
        convergence = max(0.0, final_similarity - initial_similarity)
        
        return {
            "initial_similarity": initial_similarity,
            "final_similarity": final_similarity,
            "divergence": divergence,
            "convergence": convergence,
            "net_change": final_similarity - initial_similarity,
        }
    
    def detect_patterns(self, trajectory: ManifoldTrajectory) -> Dict[str, Any]:
        """
        Detect patterns in trajectory evolution.
        
        Args:
            trajectory: Trajectory to analyze
            
        Returns:
            Detected patterns
        """
        if len(trajectory.points) < 3:
            return {"patterns": []}
        
        similarities = trajectory.get_similarity_over_time(self.embedding_agent)
        content_growth = trajectory.get_content_growth()
        
        patterns = []
        
        # Detect stability pattern
        if all(s > 0.8 for s in similarities):
            patterns.append("high_stability")
        elif all(s < 0.5 for s in similarities):
            patterns.append("high_volatility")
        
        # Detect growth pattern
        if all(g > 0 for g in content_growth):
            patterns.append("monotonic_growth")
        elif all(g < 0 for g in content_growth):
            patterns.append("monotonic_shrinkage")
        elif any(abs(g) > 1000 for g in content_growth):
            patterns.append("sudden_changes")
        
        # Detect convergence/divergence
        if len(similarities) > 1:
            if similarities[-1] > similarities[0] + 0.2:
                patterns.append("converging")
            elif similarities[-1] < similarities[0] - 0.2:
                patterns.append("diverging")
        
        return {
            "patterns": patterns,
            "similarities": similarities,
            "content_growth": content_growth,
        }


# synaplex/manifolds_indexers/indexer_world/agents.py

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional

from ..types import ManifoldSnapshot


class EmbeddingAgent:
    """
    Agent that converts manifold snapshots to embeddings.
    
    Uses a simple hash-based embedding for now (deterministic, no external deps).
    Can be extended to use sentence transformers or other embedding models.
    """
    
    def __init__(self, embedding_dim: int = 128) -> None:
        """
        Initialize embedding agent.
        
        Args:
            embedding_dim: Dimension of embedding vectors
        """
        self.embedding_dim = embedding_dim
        self._cache: Dict[str, List[float]] = {}
    
    def embed(self, snapshot: ManifoldSnapshot) -> List[float]:
        """
        Generate embedding for a manifold snapshot.
        
        Uses a simple hash-based approach for determinism.
        In production, this could use sentence transformers or other models.
        
        Args:
            snapshot: Manifold snapshot to embed
            
        Returns:
            Embedding vector as list of floats
        """
        # Create cache key
        cache_key = f"{snapshot.agent_id.value}_{snapshot.version}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Simple hash-based embedding (deterministic)
        # In production, replace with proper embedding model
        content_hash = hashlib.sha256(snapshot.content.encode()).hexdigest()
        
        # Convert hash to embedding vector
        embedding = []
        for i in range(0, min(len(content_hash), self.embedding_dim * 2), 2):
            hex_pair = content_hash[i:i+2]
            # Convert hex to float in [0, 1]
            embedding.append(int(hex_pair, 16) / 255.0)
        
        # Pad or truncate to exact dimension
        while len(embedding) < self.embedding_dim:
            # Use content length as additional signal
            padding = (len(snapshot.content) + len(embedding)) % 100 / 100.0
            embedding.append(padding)
        
        embedding = embedding[:self.embedding_dim]
        
        # Normalize
        norm = sum(x * x for x in embedding) ** 0.5
        if norm > 0:
            embedding = [x / norm for x in embedding]
        
        self._cache[cache_key] = embedding
        return embedding
    
    def embed_batch(self, snapshots: List[ManifoldSnapshot]) -> Dict[str, List[float]]:
        """
        Embed multiple snapshots.
        
        Args:
            snapshots: List of snapshots to embed
            
        Returns:
            Dict mapping agent_id_version -> embedding
        """
        results = {}
        for snapshot in snapshots:
            key = f"{snapshot.agent_id.value}_v{snapshot.version}"
            results[key] = self.embed(snapshot)
        return results


class ClusteringAgent:
    """
    Agent that clusters similar worldviews.
    
    Uses simple k-means-like clustering on embeddings.
    """
    
    def __init__(self, n_clusters: int = 5) -> None:
        """
        Initialize clustering agent.
        
        Args:
            n_clusters: Number of clusters to create
        """
        self.n_clusters = n_clusters
    
    def cluster(
        self,
        embeddings: Dict[str, List[float]],
        embedding_agent: EmbeddingAgent,
    ) -> Dict[str, int]:
        """
        Cluster embeddings into groups.
        
        Uses a simple distance-based approach.
        
        Args:
            embeddings: Dict mapping snapshot_key -> embedding
            embedding_agent: Embedding agent (for consistency)
            
        Returns:
            Dict mapping snapshot_key -> cluster_id
        """
        if not embeddings:
            return {}
        
        if len(embeddings) <= self.n_clusters:
            # Fewer items than clusters: assign each to its own cluster
            return {key: i for i, key in enumerate(embeddings.keys())}
        
        # Simple k-means-like clustering
        # Initialize centroids randomly
        keys = list(embeddings.keys())
        centroids = [embeddings[keys[i % len(keys)]] for i in range(self.n_clusters)]
        
        # Iterate to convergence (simple version)
        assignments: Dict[str, int] = {}
        for _ in range(10):  # Max iterations
            # Assign to nearest centroid
            new_assignments = {}
            for key, emb in embeddings.items():
                distances = [
                    sum((a - b) ** 2 for a, b in zip(emb, centroid)) ** 0.5
                    for centroid in centroids
                ]
                new_assignments[key] = distances.index(min(distances))
            
            # Update centroids
            for cluster_id in range(self.n_clusters):
                cluster_embs = [
                    embeddings[key]
                    for key, cid in new_assignments.items()
                    if cid == cluster_id
                ]
                if cluster_embs:
                    centroids[cluster_id] = [
                        sum(embs[i] for embs in cluster_embs) / len(cluster_embs)
                        for i in range(len(cluster_embs[0]))
                    ]
            
            assignments = new_assignments
        
        return assignments


class TrajectoryAgent:
    """
    Agent that analyzes manifold evolution over time.
    
    Tracks version-to-version changes and evolution patterns.
    """
    
    def __init__(self) -> None:
        """Initialize trajectory agent."""
        pass
    
    def analyze_trajectory(
        self,
        snapshots: List[ManifoldSnapshot],
        embedding_agent: EmbeddingAgent,
    ) -> Dict[str, Any]:
        """
        Analyze evolution trajectory for a sequence of snapshots.
        
        Args:
            snapshots: List of snapshots in chronological order (same agent)
            embedding_agent: Embedding agent for similarity computation
            
        Returns:
            Analysis results including:
            - version_changes: List of changes between versions
            - similarity_over_time: Similarity scores between consecutive versions
            - content_growth: Content length changes
            - stability_score: Overall stability metric
        """
        if len(snapshots) < 2:
            return {
                "version_changes": [],
                "similarity_over_time": [],
                "content_growth": [],
                "stability_score": 1.0,
            }
        
        # Sort by version
        sorted_snapshots = sorted(snapshots, key=lambda s: s.version)
        
        version_changes = []
        similarities = []
        content_growth = []
        
        for i in range(len(sorted_snapshots) - 1):
            prev = sorted_snapshots[i]
            curr = sorted_snapshots[i + 1]
            
            # Compute similarity
            prev_emb = embedding_agent.embed(prev)
            curr_emb = embedding_agent.embed(curr)
            
            # Cosine similarity
            dot_product = sum(a * b for a, b in zip(prev_emb, curr_emb))
            similarity = max(0.0, min(1.0, dot_product))  # Already normalized
            
            similarities.append(similarity)
            
            # Content change
            content_diff = len(curr.content) - len(prev.content)
            content_growth.append(content_diff)
            
            # Version change metadata
            version_changes.append({
                "from_version": prev.version,
                "to_version": curr.version,
                "similarity": similarity,
                "content_diff": content_diff,
            })
        
        # Stability score: average similarity (higher = more stable)
        stability_score = sum(similarities) / len(similarities) if similarities else 1.0
        
        return {
            "version_changes": version_changes,
            "similarity_over_time": similarities,
            "content_growth": content_growth,
            "stability_score": stability_score,
            "num_versions": len(sorted_snapshots),
            "total_evolution": sorted_snapshots[-1].version - sorted_snapshots[0].version,
        }
    
    def compare_trajectories(
        self,
        trajectory1: List[ManifoldSnapshot],
        trajectory2: List[ManifoldSnapshot],
        embedding_agent: EmbeddingAgent,
    ) -> Dict[str, Any]:
        """
        Compare two trajectories to find divergence/convergence patterns.
        
        Args:
            trajectory1: First trajectory
            trajectory2: Second trajectory
            embedding_agent: Embedding agent
            
        Returns:
            Comparison results
        """
        if not trajectory1 or not trajectory2:
            return {"divergence": 0.0, "convergence": 0.0}
        
        # Get final embeddings
        final1 = embedding_agent.embed(trajectory1[-1])
        final2 = embedding_agent.embed(trajectory2[-1])
        
        # Final similarity
        dot_product = sum(a * b for a, b in zip(final1, final2))
        final_similarity = max(0.0, min(1.0, dot_product))
        
        # Initial similarity (if available)
        initial_similarity = 1.0
        if len(trajectory1) > 0 and len(trajectory2) > 0:
            init1 = embedding_agent.embed(trajectory1[0])
            init2 = embedding_agent.embed(trajectory2[0])
            dot_init = sum(a * b for a, b in zip(init1, init2))
            initial_similarity = max(0.0, min(1.0, dot_init))
        
        # Divergence: decrease in similarity
        divergence = max(0.0, initial_similarity - final_similarity)
        # Convergence: increase in similarity
        convergence = max(0.0, final_similarity - initial_similarity)
        
        return {
            "initial_similarity": initial_similarity,
            "final_similarity": final_similarity,
            "divergence": divergence,
            "convergence": convergence,
            "net_change": final_similarity - initial_similarity,
        }


# synaplex/substrate_science/indexer_world/agents.py

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional

from ..types import SubstrateSnapshot


class EmbeddingAgent:
    """
    Agent that converts substrate snapshots to embeddings.
    
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
    
    def embed(self, snapshot: SubstrateSnapshot) -> List[float]:
        """
        Generate embedding for a substrate snapshot.
        
        Uses a simple hash-based approach for determinism by default.
        Can be extended to use sentence-transformers or other embedding models.
        
        To use real embeddings, subclass and override this method, or pass
        a custom embedding function to the constructor.
        
        Args:
            snapshot: Substrate snapshot to embed
            
        Returns:
            Embedding vector as list of floats
        """
        # Create cache key
        cache_key = f"{snapshot.agent_id.value}_{snapshot.version}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Try to use real embedding model if available
        # (This is a placeholder - in production, use sentence-transformers)
        try:
            # Attempt to use real embedding model
            # Uncomment and configure when sentence-transformers is available:
            # from sentence_transformers import SentenceTransformer
            # model = SentenceTransformer('all-MiniLM-L6-v2')
            # embedding = model.encode(snapshot.content).tolist()
            # if len(embedding) == self.embedding_dim:
            #     self._cache[cache_key] = embedding
            #     return embedding
            pass
        except ImportError:
            # Fall back to hash-based embedding
            pass
        
        # Simple hash-based embedding (deterministic fallback)
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
    
    def embed_batch(self, snapshots: List[SubstrateSnapshot]) -> Dict[str, List[float]]:
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
    Agent that analyzes substrate evolution over time.
    
    Tracks version-to-version changes and evolution patterns.
    """
    
    def __init__(self) -> None:
        """Initialize trajectory agent."""
        pass
    
    def analyze_trajectory(
        self,
        snapshots: List[SubstrateSnapshot],
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
        trajectory1: List[SubstrateSnapshot],
        trajectory2: List[SubstrateSnapshot],
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


class BasinDetector:
    """
    Agent that detects basins (stable patterns A) in substrates.
    
    Analyzes substrate snapshots to identify:
    - Recurring themes and patterns
    - Stable conceptual equilibria
    - Habits and persistent structures
    """
    
    def __init__(self, embedding_agent: Optional[EmbeddingAgent] = None) -> None:
        """
        Initialize basin detector.
        
        Args:
            embedding_agent: Optional embedding agent for similarity computation
        """
        self.embedding_agent = embedding_agent or EmbeddingAgent()
    
    def detect_basins(
        self,
        snapshots: List[SubstrateSnapshot],
        min_stability: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Detect basins (stable patterns) from a sequence of snapshots.
        
        Args:
            snapshots: List of snapshots in chronological order (same agent)
            min_stability: Minimum similarity threshold for basin stability
            
        Returns:
            Dict with detected basins and their properties
        """
        if len(snapshots) < 2:
            return {"basins": [], "stability_scores": []}
        
        # Sort by version
        sorted_snapshots = sorted(snapshots, key=lambda s: s.version)
        
        # Compute embeddings
        embeddings = [self.embedding_agent.embed(s) for s in sorted_snapshots]
        
        # Detect stable regions (high similarity over time)
        basins = []
        stability_scores = []
        
        # Look for patterns that persist across versions
        for i in range(len(embeddings) - 1):
            similarity = sum(a * b for a, b in zip(embeddings[i], embeddings[i + 1]))
            stability_scores.append(similarity)
            
            if similarity >= min_stability:
                # This region is stable (basin)
                basins.append({
                    "version_range": (sorted_snapshots[i].version, sorted_snapshots[i + 1].version),
                    "stability": similarity,
                    "snapshot_indices": (i, i + 1),
                })
        
        # Extract basin hints from metadata if available
        basin_hints = []
        for snapshot in sorted_snapshots:
            metadata = snapshot.metadata or {}
            hints = metadata.get("basin_hints", [])
            basin_hints.extend(hints)
        
        # Deduplicate
        basin_hints = list(set(basin_hints))
        
        return {
            "basins": basins,
            "stability_scores": stability_scores,
            "basin_hints": basin_hints,
            "avg_stability": sum(stability_scores) / len(stability_scores) if stability_scores else 0.0,
        }


class ViscosityAnalyzer:
    """
    Agent that analyzes viscosity (K) patterns in substrates.
    
    Viscosity encodes resistance to perturbations. This analyzer detects:
    - High-viscosity regions (resistant to change)
    - Low-viscosity regions (sensitive to change, "mud")
    - Sensitivity patterns and risk profiles
    """
    
    def __init__(self, embedding_agent: Optional[EmbeddingAgent] = None) -> None:
        """
        Initialize viscosity analyzer.
        
        Args:
            embedding_agent: Optional embedding agent for similarity computation
        """
        self.embedding_agent = embedding_agent or EmbeddingAgent()
    
    def analyze_viscosity(
        self,
        snapshots: List[SubstrateSnapshot],
    ) -> Dict[str, Any]:
        """
        Analyze viscosity patterns from substrate evolution.
        
        High viscosity = low sensitivity (resistant to perturbations)
        Low viscosity = high sensitivity (muddy, accepts deep tracks)
        
        Note: This is inverse to curvature in some metaphors, but here:
        K = Resistance. High K = Granite. Low K = Mud.
        
        Args:
            snapshots: List of snapshots in chronological order (same agent)
            
        Returns:
            Dict with viscosity analysis
        """
        if len(snapshots) < 2:
            return {"viscosity_profile": "unknown", "sensitivity_regions": []}
        
        sorted_snapshots = sorted(snapshots, key=lambda s: s.version)
        
        # Compute change magnitudes between versions
        change_magnitudes = []
        for i in range(len(sorted_snapshots) - 1):
            prev = sorted_snapshots[i]
            curr = sorted_snapshots[i + 1]
            
            # Embedding distance as proxy for change magnitude
            prev_emb = self.embedding_agent.embed(prev)
            curr_emb = self.embedding_agent.embed(curr)
            distance = sum((a - b) ** 2 for a, b in zip(prev_emb, curr_emb)) ** 0.5
            
            # Content length change
            content_diff = abs(len(curr.content) - len(prev.content))
            
            change_magnitudes.append({
                "version_range": (prev.version, curr.version),
                "embedding_distance": distance,
                "content_diff": content_diff,
                "change_magnitude": distance + (content_diff / 1000.0),  # Normalized
            })
        
        # High change magnitude = LOW viscosity (accepted change easily)
        # Low change magnitude = HIGH viscosity (resisted change)
        avg_change = sum(m["change_magnitude"] for m in change_magnitudes) / len(change_magnitudes) if change_magnitudes else 0.0
        
        # Extract viscosity hints from metadata if available
        viscosity_hints = {}
        for snapshot in sorted_snapshots:
            metadata = snapshot.metadata or {}
            hints = metadata.get("viscosity_hints", {})
            if hints:
                viscosity_hints.update(hints)
        
        # Classify viscosity profile
        if avg_change > 0.5:
            profile = "low"  # High change = Low viscosity (Mud)
        elif avg_change > 0.2:
            profile = "moderate"
        else:
            profile = "high"  # Low change = High viscosity (Granite)
        
        return {
            "viscosity_profile": profile,
            "avg_change_magnitude": avg_change,
            "change_magnitudes": change_magnitudes,
            "viscosity_hints": viscosity_hints,
            "sensitivity_regions": [
                m for m in change_magnitudes if m["change_magnitude"] > avg_change
            ],
        }


class GradientExtractor:
    """
    Agent that extracts gradient (τ) patterns from substrates.
    
    Gradient is the internal sense of "improvement direction" - what the agent
    is optimizing for, what directions of reasoning seem promising.
    """
    
    def __init__(self, embedding_agent: Optional[EmbeddingAgent] = None) -> None:
        """
        Initialize gradient extractor.
        
        Args:
            embedding_agent: Optional embedding agent for similarity computation
        """
        self.embedding_agent = embedding_agent or EmbeddingAgent()
    
    def extract_gradient(
        self,
        snapshots: List[SubstrateSnapshot],
    ) -> Dict[str, Any]:
        """
        Extract gradient (improvement direction) from substrate evolution.
        
        Analyzes what directions of change seem to represent "improvement"
        from the agent's perspective.
        
        Args:
            snapshots: List of snapshots in chronological order (same agent)
            
        Returns:
            Dict with gradient analysis
        """
        if len(snapshots) < 2:
            return {"gradient_direction": "unknown", "improvement_patterns": []}
        
        sorted_snapshots = sorted(snapshots, key=lambda s: s.version)
        
        # Extract gradient hints from metadata
        gradient_hints = {}
        for snapshot in sorted_snapshots:
            metadata = snapshot.metadata or {}
            hints = metadata.get("gradient_hints", {})
            if hints:
                gradient_hints.update(hints)
        
        # Analyze evolution direction
        # Look for patterns in how the substrate evolves (what changes are "improvements")
        evolution_patterns = []
        for i in range(len(sorted_snapshots) - 1):
            prev = sorted_snapshots[i]
            curr = sorted_snapshots[i + 1]
            
            # Content growth suggests active improvement
            content_growth = len(curr.content) - len(prev.content)
            
            # Version increment suggests intentional update
            version_increment = curr.version - prev.version
            
            evolution_patterns.append({
                "version_range": (prev.version, curr.version),
                "content_growth": content_growth,
                "version_increment": version_increment,
                "active_evolution": content_growth > 0 or version_increment > 0,
            })
        
        # Determine gradient direction
        active_evolutions = [p for p in evolution_patterns if p["active_evolution"]]
        if active_evolutions:
            direction = "active"  # Actively improving
        else:
            direction = "static"  # Stable, not actively evolving
        
        return {
            "gradient_direction": direction,
            "gradient_hints": gradient_hints,
            "evolution_patterns": evolution_patterns,
            "improvement_patterns": active_evolutions,
            "avg_content_growth": sum(p["content_growth"] for p in evolution_patterns) / len(evolution_patterns) if evolution_patterns else 0,
        }

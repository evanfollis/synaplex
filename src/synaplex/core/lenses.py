# synaplex/core/lenses.py

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Lens:
    """
    Receiver-owned semantics for perception.

    Lenses define how a Mind interprets incoming information through its own
    geometric perspective. Geometrically, lenses implement the projection/refraction
    operator Φ, which has two aspects:

    - Φ_sem (semantic compression): how raw projections are restructured and
      compressed into the receiver's coordinate system
    - Φ_tel (teleological filtering): how projections are filtered and prioritized
      based on the receiver's teleology field τ

    Lenses define:
    - how signals are filtered / attended to,
    - how projections are requested and interpreted.
    """

    name: str
    # Freeform configuration; concrete worlds can subclass this.
    config: Dict[str, Any] = field(default_factory=dict)

    def should_attend(self, signal_payload: Dict[str, Any]) -> bool:
        """
        Decide whether to attend to a given signal.

        This is part of the teleological filtering (Φ_tel) aspect of the lens:
        signals that don't align with the Mind's current teleology τ are filtered out.

        Default: attend to everything.
        Worlds can override with richer semantics.
        """
        return True

    def build_request_shape(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a request shape for a projection given current context.

        This shapes what information the receiver requests, which influences
        what frottage envelope the sender produces.

        Default: echo context.
        """
        return context

    def transform_projection(self, raw_projection: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform a raw projection into the receiver's perceptual space.

        This implements the projection/refraction operator Φ, which has two coupled parts:

        1. **Φ_sem (semantic compression)**: 
           - Input: frottage envelope E_F(R_i) from sender's manifold M_i
           - Action: infer local operators (M̃_j, Ã_j, K̃_j) compatible with receiver's geometry
           - Compress redundant shards, discard incompatible ones
           - Restructure into receiver's coordinate system
           - Output: compressed region R'_j in receiver's manifold M_j

        2. **Φ_tel (teleological filtering)**:
           - Filter and reweight based on alignment with receiver's teleology τ
           - Partially align τ_j with epistemic gradient implicit in envelope
           - Prioritize information that aligns with receiver's "improvement direction"

        Geometrically:
        - The raw projection is an overloaded, on-topic frottage envelope
        - Φ_sem does semantic inference + compression
        - Φ_tel does teleological filtering and alignment
        - Together they produce a compressed, teleologically-aligned view

        Default: identity (no transformation).
        Worlds should override to implement domain-specific refraction semantics.

        Example implementation pattern:
        ```python
        def transform_projection(self, raw_projection):
            # Extract frottage envelope
            frottage = raw_projection.get("frottage", {})
            frames = frottage.get("frames", [])
            
            # Φ_sem: Semantic compression
            compressed = self._semantic_compress(frames)
            
            # Φ_tel: Teleological filtering
            filtered = self._teleological_filter(compressed)
            
            return filtered
        ```
        """
        return raw_projection

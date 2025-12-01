# synaplex/worlds/ideas_world/lenses.py

from typing import Any, Dict

from synaplex.core.lenses import Lens


class IdeasArchitectLens(Lens):
    """Lens for architect agent: focuses on structure, clustering, and gaps."""
    
    def should_attend(self, signal_payload: Dict[str, Any]) -> bool:
        """Attend to idea-related signals."""
        return signal_payload.get("type") == "idea" or "idea" in str(signal_payload).lower()
    
    def transform_projection(self, raw_projection: Dict[str, Any]) -> Dict[str, Any]:
        """Transform to emphasize structural and clustering information."""
        transformed = dict(raw_projection)
        # Add emphasis on structural elements
        if "tags" in transformed:
            transformed["_structural_tags"] = transformed["tags"]
        return transformed


class IdeasCriticLens(Lens):
    """Lens for critic agent: focuses on tensions, contradictions, and blind spots."""
    
    def should_attend(self, signal_payload: Dict[str, Any]) -> bool:
        """Attend to idea-related signals."""
        return signal_payload.get("type") == "idea" or "idea" in str(signal_payload).lower()
    
    def transform_projection(self, raw_projection: Dict[str, Any]) -> Dict[str, Any]:
        """Transform to emphasize contradictions and tensions."""
        transformed = dict(raw_projection)
        # Add emphasis on potential tensions
        if "tags" in transformed:
            transformed["_tension_focus"] = True
        return transformed


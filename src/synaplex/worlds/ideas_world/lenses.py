from typing import Any, Dict, List

from synaplex.core.lenses import Lens


class IdeaIngestLens(Lens):
    """
    Lens for IdeaIngestMind.

    In practice this is rarely used (IdeaIngest mostly reads from files),
    but we keep it for symmetry: if other agents ever signal back to
    idea_ingest, it can choose to attend only to idea-related signals.
    """

    def should_attend(self, signal_payload: Dict[str, Any]) -> bool:
        return signal_payload.get("type") in {"idea", "execution_feedback"}

    def transform_projection(self, raw_projection: Dict[str, Any]) -> Dict[str, Any]:
        return dict(raw_projection)


class IdeaArchitectLens(Lens):
    """
    Φ for IDEA_ARCHITECT.

    Demonstrates both aspects of the projection operator Φ:
    - Φ_sem (semantic compression): restructures frottage into structural view
    - Φ_tel (teleological filtering): prioritizes structural/organizational information

    - Attends to idea signals.
    - Emphasizes structural cues (tags, domain, inferred clusters).
    """

    def should_attend(self, signal_payload: Dict[str, Any]) -> bool:
        return signal_payload.get("type") == "idea"

    def transform_projection(self, raw_projection: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform projection using Φ_sem and Φ_tel.

        Φ_sem: Compress frottage envelope into structural representation
        Φ_tel: Filter for information aligned with structural organization goals
        """
        # Extract frottage envelope if present
        frottage = raw_projection.get("frottage", {})
        frames = frottage.get("frames", [])

        # Φ_sem: Semantic compression
        # Extract structural information from multiple frames
        transformed = dict(raw_projection)
        
        # Compress frames into structural view
        structural_info = {}
        for frame in frames:
            frame_type = frame.get("type", "")
            if frame_type == "direct_state":
                # Extract tags, domain, clusters from direct state
                state = frame.get("content", {})
                tags: List[str] = list(state.get("tags", []))
                structural_info["tags"] = tags
                structural_info["domain"] = state.get("domain")
            elif frame_type == "contextual_hints":
                # Extract structural implications
                hints = frame.get("content", {})
                structural_info["related_concepts"] = hints.get("related_concepts", [])

        # Merge structural info into transformed projection
        transformed["_structural_tags"] = structural_info.get("tags", [])
        transformed["_idea_id"] = transformed.get("id") or transformed.get("title")
        transformed["_domain"] = structural_info.get("domain")
        transformed["_related_concepts"] = structural_info.get("related_concepts", [])

        # Φ_tel: Teleological filtering
        # Filter and prioritize based on structural organization goals
        # (In this case, prioritize structural information over other aspects)
        if "_structural_tags" not in transformed or not transformed["_structural_tags"]:
            # If no structural tags, this projection is less aligned with architect's teleology
            transformed["_teleological_weight"] = 0.3
        else:
            # Rich structural information aligns with architect's goals
            transformed["_teleological_weight"] = 1.0

        return transformed


class IdeaCriticLens(Lens):
    """
    Φ for IDEA_CRITIC.

    - Attends to idea signals.
    - Emphasizes tension–relevant cues (duplicates, contradictions, low-signal).
    """

    def should_attend(self, signal_payload: Dict[str, Any]) -> bool:
        return signal_payload.get("type") == "idea"

    def transform_projection(self, raw_projection: Dict[str, Any]) -> Dict[str, Any]:
        transformed = dict(raw_projection)
        transformed["_tension_focus"] = True
        return transformed


class IdeaPMLens(Lens):
    """
    Φ for IDEA_PM.

    - Attends to idea_ingest, architect, and critic signals.
    - Normalizes them into 'portfolio candidate' view.
    """

    def should_attend(self, signal_payload: Dict[str, Any]) -> bool:
        return signal_payload.get("type") in {"idea", "idea_structure", "idea_tension"}

    def transform_projection(self, raw_projection: Dict[str, Any]) -> Dict[str, Any]:
        transformed = dict(raw_projection)
        # Basic normalization of priority fields
        transformed.setdefault("status", "seed")
        transformed.setdefault("importance_hint", 0.5)
        transformed.setdefault("risk_hint", 0.5)
        return transformed


class ExecutionLens(Lens):
    """
    Φ for EXECUTION.

    - Attends primarily to 'ready_for_execution' signals from IdeaPM.
    """

    def should_attend(self, signal_payload: Dict[str, Any]) -> bool:
        return signal_payload.get("type") == "ready_for_execution"

    def transform_projection(self, raw_projection: Dict[str, Any]) -> Dict[str, Any]:
        return dict(raw_projection)


class GeometryStewardLens(Lens):
    """
    Φ for GEOMETRY_STEWARD.

    - Attends to structural/tension/portfolio signals.
    - Emphasizes anything that smells like a spec/config drift issue.
    """

    def should_attend(self, signal_payload: Dict[str, Any]) -> bool:
        return signal_payload.get("type") in {
            "idea_structure",
            "idea_tension",
            "idea_portfolio_state",
        }

    def transform_projection(self, raw_projection: Dict[str, Any]) -> Dict[str, Any]:
        transformed = dict(raw_projection)
        transformed["_geometry_inspection_target"] = True
        return transformed

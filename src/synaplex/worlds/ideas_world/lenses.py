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

    - Attends to idea signals.
    - Emphasizes structural cues (tags, domain, inferred clusters).
    """

    def should_attend(self, signal_payload: Dict[str, Any]) -> bool:
        return signal_payload.get("type") == "idea"

    def transform_projection(self, raw_projection: Dict[str, Any]) -> Dict[str, Any]:
        transformed = dict(raw_projection)
        tags: List[str] = list(transformed.get("tags", []))
        transformed["_structural_tags"] = tags
        transformed["_idea_id"] = transformed.get("id") or transformed.get("title")
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

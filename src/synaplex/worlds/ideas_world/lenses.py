from typing import Any, Dict

from synaplex.core.lenses import Lens


# Lenses only filter. They don't add metadata. They don't transform.
# Receiver-owned semantics: the Mind decides what things mean.


class IdeaIngestLens(Lens):
    """Attends to ideas and execution feedback."""

    def should_attend(self, signal_payload: Dict[str, Any]) -> bool:
        return True  # Ingest attends to everything


class IdeaArchitectLens(Lens):
    """Attends to ideas."""

    def should_attend(self, signal_payload: Dict[str, Any]) -> bool:
        return True  # Let the Mind decide what's relevant


class IdeaCriticLens(Lens):
    """Attends to ideas."""

    def should_attend(self, signal_payload: Dict[str, Any]) -> bool:
        return True


class IdeaPMLens(Lens):
    """Attends to everything relevant to portfolio."""

    def should_attend(self, signal_payload: Dict[str, Any]) -> bool:
        return True


class ExecutionLens(Lens):
    """Attends to execution-relevant signals."""

    def should_attend(self, signal_payload: Dict[str, Any]) -> bool:
        return True


class GeometryStewardLens(Lens):
    """Attends to everything for constitutional monitoring."""

    def should_attend(self, signal_payload: Dict[str, Any]) -> bool:
        return True

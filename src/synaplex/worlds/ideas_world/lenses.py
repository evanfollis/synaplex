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


class SynaplexLens(Lens):
    """Lens for Synaplex agent: focuses on Synaplex-related and architecture content."""
    
    def should_attend(self, signal_payload: Dict[str, Any]) -> bool:
        """Attend to Synaplex-related or architecture-related signals."""
        if signal_payload.get("type") != "idea":
            return False
        
        tags = signal_payload.get("tags", [])
        title = signal_payload.get("title", "").lower()
        domain = signal_payload.get("domain", "").lower()
        
        # Attend to Synaplex-related content
        synaplex_keywords = ["synaplex", "architecture", "multi-agent", "manifold", "nature-nurture"]
        return (
            any(kw in str(tags).lower() for kw in synaplex_keywords) or
            any(kw in title for kw in synaplex_keywords) or
            any(kw in domain for kw in synaplex_keywords)
        )
    
    def transform_projection(self, raw_projection: Dict[str, Any]) -> Dict[str, Any]:
        """Transform to emphasize architectural and conceptual connections."""
        transformed = dict(raw_projection)
        transformed["_synaplex_focus"] = True
        # Preserve all information for deep synthesis
        return transformed


class TopicLens(Lens):
    """Base lens for topic agents: filters by domain/tags relevant to their topic."""
    
    def __init__(self, name: str, topic_keywords: list[str], config: Dict[str, Any] = None):
        """
        Initialize topic lens.
        
        Args:
            name: Lens name
            topic_keywords: List of keywords that indicate relevance to this topic
            config: Optional configuration dict
        """
        super().__init__(name=name, config=config or {})
        self.topic_keywords = [kw.lower() for kw in topic_keywords]
    
    def should_attend(self, signal_payload: Dict[str, Any]) -> bool:
        """Attend to signals relevant to this topic."""
        if signal_payload.get("type") != "idea":
            return False
        
        tags = signal_payload.get("tags", [])
        title = signal_payload.get("title", "").lower()
        domain = signal_payload.get("domain", "").lower()
        content = signal_payload.get("content_preview", "").lower()
        
        # Check if any topic keyword appears
        search_text = f"{tags} {title} {domain} {content}"
        return any(kw in search_text for kw in self.topic_keywords)
    
    def transform_projection(self, raw_projection: Dict[str, Any]) -> Dict[str, Any]:
        """Transform to emphasize topic-relevant information."""
        transformed = dict(raw_projection)
        transformed["_topic_focus"] = self.name
        return transformed


# Specialized topic lenses
class LLMsLens(TopicLens):
    """Lens for LLMs topic agent."""
    def __init__(self, name: str = "llms_lens"):
        super().__init__(
            name=name,
            topic_keywords=["llm", "large language model", "transformer", "gpt", "prompting", "fine-tuning", "nlp", "foundation model"],
        )


class WorldModelsLens(TopicLens):
    """Lens for World Models topic agent."""
    def __init__(self, name: str = "world_models_lens"):
        super().__init__(
            name=name,
            topic_keywords=["world model", "simulation", "prediction", "model-based", "rl", "reinforcement learning"],
        )


class AgenticSystemsLens(TopicLens):
    """Lens for Agentic Systems topic agent."""
    def __init__(self, name: str = "agentic_systems_lens"):
        super().__init__(
            name=name,
            topic_keywords=["multi-agent", "agentic", "coordination", "communication", "agent framework", "swarm"],
        )


class CognitiveArchitecturesLens(TopicLens):
    """Lens for Cognitive Architectures topic agent."""
    def __init__(self, name: str = "cognitive_architectures_lens"):
        super().__init__(
            name=name,
            topic_keywords=["cognitive architecture", "reasoning", "knowledge representation", "symbolic", "hybrid"],
        )


class ManifoldsLens(TopicLens):
    """Lens for Manifolds topic agent."""
    def __init__(self, name: str = "manifolds_lens"):
        super().__init__(
            name=name,
            topic_keywords=["manifold", "internal representation", "worldview", "embedding", "latent space", "internal state"],
        )


class MessageGraphsLens(TopicLens):
    """Lens for Message Graphs topic agent."""
    def __init__(self, name: str = "message_graphs_lens"):
        super().__init__(
            name=name,
            topic_keywords=["graph", "message passing", "distributed", "topology", "network", "routing"],
        )


class NatureNurtureLens(TopicLens):
    """Lens for Nature vs Nurture topic agent."""
    def __init__(self, name: str = "nature_nurture_lens"):
        super().__init__(
            name=name,
            topic_keywords=["nature", "nurture", "structure", "constraint", "learned", "innate", "evolution"],
        )


# synaplex/worlds/ideas_world/agents.py

from pathlib import Path
from typing import Any, Dict, List, Optional

from synaplex.core.ids import AgentId
from synaplex.core.messages import MessageId, Signal
from synaplex.cognition.openai_client import OpenAILLMClient
from synaplex.cognition.mind import Mind
from synaplex.cognition.substrate import FileSubstrateStore


# ---------------------------------------------------------------------------
# Frottage generation for IDEAS_WORLD
# ---------------------------------------------------------------------------

def _generate_idea_frottage(
    idea: Dict[str, Any],
    llm_client: Optional[Any] = None,
) -> Optional[str]:
    """
    Generate frottage for an idea.
    
    Frottage is semantic soup: dump everything—latent ideas, contradictions,
    tangents, interdisciplinary possibilities. The receiver makes sense of it
    with no special prompting. Just context.
    """
    if llm_client is None:
        return _generate_idea_frottage_fallback(idea)
    
    # Simple: just dump everything about this idea
    prompt = f"""Write everything you know, think, suspect, or wonder about this idea.
Include half-formed thoughts, contradictions, tangents, connections to other fields.
Don't structure it. Don't summarize. Just dump.

{idea}"""
    
    try:
        response = llm_client.complete(prompt)
        text = getattr(response, "text", None)
        if text is None:
            text = str(response)
        return text if text.strip() else _generate_idea_frottage_fallback(idea)
    except Exception:
        return _generate_idea_frottage_fallback(idea)


def _generate_idea_frottage_fallback(idea: Dict[str, Any]) -> str:
    """Fallback when LLM unavailable: just dump the idea content."""
    content = idea.get('content', '')
    if content:
        return content
    return str(idea)


class IdeasArchivistMind(Mind):
    """
    Archivist mind that reads markdown idea files and emits idea signals.

    Geometry-pure version:

    - Still a full Mind: it has a substrate and runs the unified loop.
    - In v0, it *uses* the substrate minimally; behavior is mostly driven by EnvState + filesystem.
    - Over time, its substrate can learn about your own idea-ingest habits.
    """

    def __init__(
        self,
        agent_id: AgentId,
        ideas_dir: Path,
        substrate_store: Optional[FileSubstrateStore] = None,
        llm_client: Optional[OpenAILLMClient] = None,
        **kwargs: Any,
    ):
        super().__init__(
            agent_id=agent_id,
            llm_client=llm_client or OpenAILLMClient(),
            substrate_store=substrate_store or FileSubstrateStore(
                root="substrates/ideas_world/archivist"
            ),
            **kwargs,
        )
        self.ideas_dir = Path(ideas_dir)
        self._processed_files: Dict[str, float] = {}  # file -> mtime

    def get_visible_state(self) -> Dict[str, Any]:
        """Expose current idea processing state as structured EnvState-like data."""
        return {
            "ideas_dir": str(self.ideas_dir),
            "processed_files": list(self._processed_files.keys()),
        }

    def _extract_ideas_from_markdown(
        self, content: str, filepath: str
    ) -> List[Dict[str, Any]]:
        """
        Extract idea atoms from markdown content.

        Looks for sections like:

            ## Idea: Title
            - Domain: ...
            - Tags: ...
            - Status: ...
            - Question: ...

        Everything else is treated as freeform content attached to that idea.
        """
        ideas: List[Dict[str, Any]] = []
        lines = content.split("\n")
        current_idea: Optional[Dict[str, Any]] = None
        current_content: List[str] = []

        for line in lines:
            if line.startswith("## Idea:"):
                # Save previous idea if exists
                if current_idea is not None:
                    current_idea["content"] = "\n".join(current_content).strip()
                    ideas.append(current_idea)

                title = line.replace("## Idea:", "").strip()
                current_idea = {
                    "title": title,
                    "source_file": filepath,
                    "domain": None,
                    "tags": [],
                    "status": None,
                    "question": None,
                }
                current_content = []
            elif current_idea is not None:
                # Parse metadata lines
                if line.startswith("- Domain:"):
                    current_idea["domain"] = line.replace("- Domain:", "").strip()
                elif line.startswith("- Tags:"):
                    tags_str = line.replace("- Tags:", "").strip()
                    tags_str = tags_str.strip("[]")
                    current_idea["tags"] = [
                        t.strip() for t in tags_str.split(",") if t.strip()
                    ]
                elif line.startswith("- Status:"):
                    current_idea["status"] = line.replace("- Status:", "").strip()
                elif line.startswith("- Question:"):
                    current_idea["question"] = line.replace(
                        "- Question:", ""
                    ).strip()
                elif line.startswith("##"):  # New section; close current idea
                    current_idea["content"] = "\n".join(current_content).strip()
                    ideas.append(current_idea)
                    current_idea = None
                    current_content = []
                else:
                    current_content.append(line)

        # Last idea
        if current_idea is not None:
            current_idea["content"] = "\n".join(current_content).strip()
            ideas.append(current_idea)

        return ideas

    def act(self, reasoning_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process markdown files and emit idea signals with frottage.

        Each idea signal includes:
        - payload: small, structured meta for routing/filtering
        - frottage: dense, on-topic text for receiver substrate perturbation
        
        Per FROTTAGE_CONTRACT:
        - Frottage is sender-authored and opaque to core
        - Never parsed by infrastructure; passed through as-is
        - Compression happens in receiver Mind's reasoning/update
        - Token cost is cheap; we prefer rich perturbations
        """
        signals: List[Dict[str, Any]] = []

        if not self.ideas_dir.exists():
            return {"signals": [], "requests": [], "env_updates": {}}

        markdown_files = list(self.ideas_dir.glob("*.md"))

        for md_file in markdown_files:
            mtime = md_file.stat().st_mtime
            if md_file.name in self._processed_files:
                if mtime <= self._processed_files[md_file.name]:
                    continue

            try:
                content = md_file.read_text(encoding="utf-8")
                ideas = self._extract_ideas_from_markdown(content, md_file.name)

                for idea in ideas:
                    # Generate frottage for this idea
                    # Use LLM if available for richer perturbations
                    frottage = _generate_idea_frottage(idea, llm_client=self._llm)
                    
                    signals.append(
                        {
                            # Structured payload: small, schema-aware, for routing
                            "payload": {
                                "kind": "idea",
                                "type": "idea",  # backward compat
                                "title": idea["title"],
                                "domain": idea.get("domain"),
                                "tags": idea.get("tags", []),
                                "status": idea.get("status", "seed"),
                                "question": idea.get("question"),
                                "source_file": idea["source_file"],
                                # Note: content_preview removed from payload
                                # Full content is in frottage, not structured meta
                            },
                            # Frottage: dense, unstructured text for substrate perturbation
                            "frottage": frottage,
                        }
                    )

                self._processed_files[md_file.name] = mtime
            except Exception:
                # In v0, we silently skip problematic files; meta layers can audit logs later.
                continue

        return {
            "signals": signals,
            "requests": [],
            "env_updates": {},
        }


def make_archivist_mind(
    agent_id: str = "archivist",
    ideas_dir: str | Path = "docs/ideas",
    store_root: Optional[str] = None,
    **kwargs: Any,
) -> IdeasArchivistMind:
    """Factory for archivist mind (full-loop, substrate-native)."""
    store = FileSubstrateStore(
        root=(store_root or "substrates/ideas_world/archivist")
    )
    return IdeasArchivistMind(
        agent_id=AgentId(agent_id),
        ideas_dir=Path(ideas_dir),
        substrate_store=store,
        **kwargs,
    )


def _make_substrate_mind(
    agent_id: str,
    store_root: Optional[str],
    **kwargs: Any,
) -> Mind:
    """Helper: full-loop, substrate-native Mind for idea-centric roles."""
    llm = OpenAILLMClient()
    store = FileSubstrateStore(
        root=(store_root or "substrates/ideas_world")
    )
    return Mind(
        agent_id=AgentId(agent_id),
        llm_client=llm,
        substrate_store=store,
        **kwargs,
    )


def make_architect_mind(
    agent_id: str = "architect",
    store_root: Optional[str] = None,
    **kwargs: Any,
) -> Mind:
    return _make_substrate_mind(agent_id=agent_id, store_root=store_root, **kwargs)


def make_critic_mind(
    agent_id: str = "critic",
    store_root: Optional[str] = None,
    **kwargs: Any,
) -> Mind:
    return _make_substrate_mind(agent_id=agent_id, store_root=store_root, **kwargs)


def make_synaplex_mind(
    agent_id: str = "synaplex",
    store_root: Optional[str] = None,
    **kwargs: Any,
) -> Mind:
    return _make_substrate_mind(agent_id=agent_id, store_root=store_root, **kwargs)


def make_topic_mind(
    agent_id: str,
    store_root: Optional[str] = None,
    **kwargs: Any,
) -> Mind:
    return _make_substrate_mind(agent_id=agent_id, store_root=store_root, **kwargs)


# Topic convenience factories

def make_llms_mind(
    agent_id: str = "llms",
    store_root: Optional[str] = None,
    **kwargs: Any,
) -> Mind:
    return make_topic_mind(agent_id=agent_id, store_root=store_root, **kwargs)


def make_world_models_mind(
    agent_id: str = "world_models",
    store_root: Optional[str] = None,
    **kwargs: Any,
) -> Mind:
    return make_topic_mind(agent_id=agent_id, store_root=store_root, **kwargs)


def make_agentic_systems_mind(
    agent_id: str = "agentic_systems",
    store_root: Optional[str] = None,
    **kwargs: Any,
) -> Mind:
    return make_topic_mind(agent_id=agent_id, store_root=store_root, **kwargs)


def make_cognitive_architectures_mind(
    agent_id: str = "cognitive_architectures",
    store_root: Optional[str] = None,
    **kwargs: Any,
) -> Mind:
    return make_topic_mind(agent_id=agent_id, store_root=store_root, **kwargs)


def make_substrates_mind(
    agent_id: str = "substrates",
    store_root: Optional[str] = None,
    **kwargs: Any,
) -> Mind:
    return make_topic_mind(agent_id=agent_id, store_root=store_root, **kwargs)


def make_message_graphs_mind(
    agent_id: str = "message_graphs",
    store_root: Optional[str] = None,
    **kwargs: Any,
) -> Mind:
    return make_topic_mind(agent_id=agent_id, store_root=store_root, **kwargs)


def make_nature_nurture_mind(
    agent_id: str = "nature_nurture",
    store_root: Optional[str] = None,
    **kwargs: Any,
) -> Mind:
    return make_topic_mind(agent_id=agent_id, store_root=store_root, **kwargs)

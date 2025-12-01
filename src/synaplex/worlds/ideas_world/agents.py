# synaplex/worlds/ideas_world/agents.py

from pathlib import Path
from typing import Any, Dict, List, Optional

from synaplex.core.ids import AgentId
from synaplex.core.messages import MessageId, Signal
from synaplex.cognition.openai_client import OpenAILLMClient
from synaplex.cognition.mind import Mind
from synaplex.cognition.manifolds import FileManifoldStore


class IdeasArchivistMind(Mind):
    """
    Archivist mind that reads markdown idea files and emits idea signals.

    Geometry-pure version:

    - Still a full Mind: it has a manifold and runs the unified loop.
    - In v0, it *uses* the manifold minimally; behavior is mostly driven by EnvState + filesystem.
    - Over time, its manifold can learn about your own idea-ingest habits.
    """

    def __init__(
        self,
        agent_id: AgentId,
        ideas_dir: Path,
        manifold_store: Optional[FileManifoldStore] = None,
        llm_client: Optional[OpenAILLMClient] = None,
        **kwargs: Any,
    ):
        super().__init__(
            agent_id=agent_id,
            llm_client=llm_client or OpenAILLMClient(),
            manifold_store=manifold_store or FileManifoldStore(
                root="manifolds/ideas_world/archivist"
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
        Process markdown files and emit idea signals.

        Geometry note: this lives in the Mind's outward behavior step,
        but it does not depend on special modes or on the absence of a manifold.
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
                    signals.append(
                        {
                            "payload": {
                                "type": "idea",
                                "title": idea["title"],
                                "domain": idea.get("domain"),
                                "tags": idea.get("tags", []),
                                "status": idea.get("status", "seed"),
                                "question": idea.get("question"),
                                "content_preview": idea.get("content", "")[:200],
                                "source_file": idea["source_file"],
                            }
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
    """Factory for archivist mind (full-loop, manifold-native)."""
    store = FileManifoldStore(
        root=(store_root or "manifolds/ideas_world/archivist")
    )
    return IdeasArchivistMind(
        agent_id=AgentId(agent_id),
        ideas_dir=Path(ideas_dir),
        manifold_store=store,
        **kwargs,
    )


def _make_manifold_mind(
    agent_id: str,
    store_root: Optional[str],
    **kwargs: Any,
) -> Mind:
    """Helper: full-loop, manifold-native Mind for idea-centric roles."""
    llm = OpenAILLMClient()
    store = FileManifoldStore(
        root=(store_root or "manifolds/ideas_world")
    )
    return Mind(
        agent_id=AgentId(agent_id),
        llm_client=llm,
        manifold_store=store,
        **kwargs,
    )


def make_architect_mind(
    agent_id: str = "architect",
    store_root: Optional[str] = None,
    **kwargs: Any,
) -> Mind:
    return _make_manifold_mind(agent_id=agent_id, store_root=store_root, **kwargs)


def make_critic_mind(
    agent_id: str = "critic",
    store_root: Optional[str] = None,
    **kwargs: Any,
) -> Mind:
    return _make_manifold_mind(agent_id=agent_id, store_root=store_root, **kwargs)


def make_synaplex_mind(
    agent_id: str = "synaplex",
    store_root: Optional[str] = None,
    **kwargs: Any,
) -> Mind:
    return _make_manifold_mind(agent_id=agent_id, store_root=store_root, **kwargs)


def make_topic_mind(
    agent_id: str,
    store_root: Optional[str] = None,
    **kwargs: Any,
) -> Mind:
    return _make_manifold_mind(agent_id=agent_id, store_root=store_root, **kwargs)


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


def make_manifolds_mind(
    agent_id: str = "manifolds",
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

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from synaplex.core.ids import AgentId
from synaplex.cognition.openai_client import OpenAILLMClient
from synaplex.cognition.manifolds import FileManifoldStore
from synaplex.cognition.mind import Mind
from synaplex.core.world_modes import WorldMode


# ---------------------------------------------------------------------
# IDEA_INGEST: P-heavy frottage from markdown (v0)
# ---------------------------------------------------------------------


class IdeaIngestMind(Mind):
    """
    IDEA_INGEST (P):

    - Reads messy idea sources from a directory (initially markdown files).
    - Treats headings + following text as candidate idea blobs, even if they
      don't fully match the strict schema.
    - Emits 'idea' signals with enough structure for downstream Φ to work.

    This is a P-focused agent: it does not maintain a manifold (REASONING_ONLY).
    """

    def __init__(
        self,
        agent_id: AgentId,
        ideas_dir: Path,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            agent_id=agent_id,
            llm_client=None,  # no LLM needed for simple v0 ingest
            manifold_store=None,
            world_mode=WorldMode.REASONING_ONLY,
            **kwargs,
        )
        self.ideas_dir = Path(ideas_dir)
        self._processed_files: Dict[str, float] = {}  # file -> mtime

    def get_visible_state(self) -> Dict[str, Any]:
        return {
            "ideas_dir": str(self.ideas_dir),
            "processed_files": list(self._processed_files.keys()),
        }

    # --- Local helpers -------------------------------------------------

    def _extract_ideas_frottage(self, content: str, filepath: str) -> List[Dict[str, Any]]:
        """
        Frottage-style extraction:

        - Prefer structured sections starting with '## Idea:'.
        - Fallback: any '##' heading becomes a 'blob idea' with minimal metadata.
        """
        ideas: List[Dict[str, Any]] = []
        lines = content.splitlines()
        current: Optional[Dict[str, Any]] = None
        current_body: List[str] = []

        def flush_current() -> None:
            nonlocal current, current_body
            if current is not None:
                current["content"] = "\n".join(current_body).strip()
                ideas.append(current)
                current = None
                current_body = []

        for line in lines:
            stripped = line.strip()

            if stripped.startswith("## "):
                # New heading; flush prior idea if present
                flush_current()

                title = stripped[2:].strip()
                if title.lower().startswith("idea:"):
                    title = title[len("idea:") :].strip()

                current = {
                    "title": title or f"Untitled ({filepath})",
                    "source_file": filepath,
                    "domain": None,
                    "tags": [],
                    "status": "seed",
                    "question": None,
                    "is_structured": stripped.lower().startswith("## idea:"),
                }
                current_body = []
                continue

            if current is not None:
                # Lightweight structured parsing for common metadata
                if stripped.startswith("- Domain:"):
                    current["domain"] = stripped.replace("- Domain:", "").strip() or None
                elif stripped.startswith("- Tags:"):
                    tags_str = stripped.replace("- Tags:", "").strip().strip("[]")
                    current["tags"] = [
                        t.strip() for t in tags_str.split(",") if t.strip()
                    ]
                elif stripped.startswith("- Status:"):
                    current["status"] = stripped.replace("- Status:", "").strip() or "seed"
                elif stripped.startswith("- Question:"):
                    current["question"] = stripped.replace("- Question:", "").strip() or None
                else:
                    current_body.append(line)

        flush_current()
        return ideas

    # --- Core outward behavior ----------------------------------------

    def act(self, reasoning_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scan the ideas directory, extract idea blobs (P), and emit signals.

        Returns:
            {
                "signals": [ ... idea payloads ... ],
                "requests": [],
                "env_updates": {},
            }
        """
        signals: List[Dict[str, Any]] = []

        if not self.ideas_dir.exists():
            return {"signals": [], "requests": [], "env_updates": {}}

        markdown_files = list(self.ideas_dir.glob("*.md"))

        for md_file in markdown_files:
            mtime = md_file.stat().st_mtime
            if self._processed_files.get(md_file.name, 0) >= mtime:
                continue

            try:
                content = md_file.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue

            ideas = self._extract_ideas_frottage(content, md_file.name)
            for idx, idea in enumerate(ideas):
                idea_id = f"{md_file.name}#{idx}"
                preview = (idea.get("content") or "").strip()[:400]

                signal = {
                    "payload": {
                        "type": "idea",
                        "id": idea_id,
                        "title": idea["title"],
                        "domain": idea.get("domain"),
                        "tags": idea.get("tags", []),
                        "status": idea.get("status", "seed"),
                        "question": idea.get("question"),
                        "content_preview": preview,
                        "source_file": idea["source_file"],
                        "is_structured": idea.get("is_structured", False),
                    }
                }
                signals.append(signal)

            self._processed_files[md_file.name] = mtime

        return {
            "signals": signals,
            "requests": [],
            "env_updates": {},
        }


def make_idea_ingest_mind(
    agent_id: str = "idea_ingest",
    ideas_dir: str | Path = "docs/ideas",
    **kwargs: Any,
) -> IdeaIngestMind:
    return IdeaIngestMind(
        agent_id=AgentId(agent_id),
        ideas_dir=Path(ideas_dir),
        **kwargs,
    )


# ---------------------------------------------------------------------
# Generic manifold-backed minds (Architect / Critic / PM / Execution / Steward)
# ---------------------------------------------------------------------


def _make_manifold_mind(
    agent_id: str,
    store_root: Optional[str],
    world_mode: WorldMode = WorldMode.MANIFOLD,
    **kwargs: Any,
) -> Mind:
    llm = OpenAILLMClient()
    store = (
        FileManifoldStore(root=store_root or "manifolds/ideas_world")
        if store_root
        else None
    )
    return Mind(
        agent_id=AgentId(agent_id),
        llm_client=llm,
        manifold_store=store,
        world_mode=world_mode,
        **kwargs,
    )


def make_idea_architect_mind(
    agent_id: str = "idea_architect",
    store_root: Optional[str] = None,
    **kwargs: Any,
) -> Mind:
    """
    IDEA_ARCHITECT (M/A):

    - Uses its manifold to maintain global structure over ideas.
    - In prompts, you frame this agent as 'cartographer of idea space'.
    """
    return _make_manifold_mind(agent_id, store_root, **kwargs)


def make_idea_critic_mind(
    agent_id: str = "idea_critic",
    store_root: Optional[str] = None,
    **kwargs: Any,
) -> Mind:
    """
    IDEA_CRITIC (M/A):

    - Uses its manifold to accumulate tensions, contradictions, and
      patterns of redundancy or missing coverage.
    """
    return _make_manifold_mind(agent_id, store_root, **kwargs)


def make_idea_pm_mind(
    agent_id: str = "idea_pm",
    store_root: Optional[str] = None,
    **kwargs: Any,
) -> Mind:
    """
    IDEA_PM (A/K):

    - Manifold encodes portfolio (attractors) and curvature (how
      quickly priorities reshuffle).
    - In practice, prompts instruct it to:

        * maintain a ranked list of ideas,
        * track evidence for/against each,
        * decide when to emit 'ready_for_execution' or 'deprioritized'
          signals.

    """
    return _make_manifold_mind(agent_id, store_root, **kwargs)


def make_execution_mind(
    agent_id: str = "execution",
    store_root: Optional[str] = None,
    **kwargs: Any,
) -> Mind:
    """
    EXECUTION (H):

    - For now, treats 'ready_for_execution' projections as requests to:

        * generate an execution plan,
        * log that plan into EnvState (via env_updates),
        * emit 'execution_planned' signals.

    - In the future this mind becomes the bridge to cursor / APIs.
    """
    return _make_manifold_mind(agent_id, store_root, **kwargs)


def make_geometry_steward_mind(
    agent_id: str = "geometry_steward",
    store_root: Optional[str] = None,
    **kwargs: Any,
) -> Mind:
    """
    GEOMETRY_STEWARD (M/Φ/Ω):

    - Manifold encodes 'IDEA_WORLD health' and candidate Ω moves.
    - Prompts tell it to:

        * inspect structure/tension/portfolio signals,
        * identify where Φ (lenses) and DNA are misaligned with
          GEOMETRIC_CONSTITUTION,
        * propose Ω moves as structured notes written to its manifold
          and signaled outward as 'omega_proposal' messages.
    """
    return _make_manifold_mind(agent_id, store_root, **kwargs)

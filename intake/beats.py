"""Beat definitions.

Each beat has a definition string (fed into the Sonnet scorer's system
prompt) plus a keyword bank (used by the heuristic scorer + search-filters
on broad-sweep sources like arxiv). Definitions are prose, not regex —
they capture the analytical frame a reader brings to the beat.

First pass ships `agent-platforms`. `systematic-trading` (atlas) and
`venture-discovery` (skillfoundry) queue for subsequent waves.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Beat:
    id: str
    name: str
    definition: str
    keywords: tuple[str, ...] = field(default_factory=tuple)
    rss_feeds: tuple[str, ...] = field(default_factory=tuple)
    arxiv_categories: tuple[str, ...] = field(default_factory=tuple)


AGENT_PLATFORMS = Beat(
    id="agent-platforms",
    name="Agent platforms",
    definition=(
        "Engineering and architecture of agent platforms — harnesses, memory "
        "systems, context infrastructure, integrations (MCP, function calling), "
        "orchestration frameworks, and the emerging patterns under serious agent "
        "teams. Reader audience: engineers building agent platforms, not end "
        "users. In-scope: Claude Code / Codex CLI / Aider / OpenDevin / Cline / "
        "Devin and other harnesses; Letta / mem0 / MemGPT and other memory systems; "
        "LangGraph / CrewAI / Inngest Agents / AutoGen and other orchestration; MCP "
        "servers and clients; tool-use and agent reliability; evaluation and "
        "benchmark methodology for agents; inference-time compute and agent-loop "
        "engineering. Out-of-scope: generic 'I tried ChatGPT for X' content, "
        "hype posts without technical substance, pure research that doesn't "
        "touch production agent systems."
    ),
    keywords=(
        # harnesses
        "claude code", "codex cli", "codex", "aider", "opendevin", "open devin",
        "cline", "devin", "agent harness", "agentic harness", "coding agent",
        # memory
        "letta", "mem0", "memgpt", "agent memory", "long-term memory",
        "episodic memory", "working memory",
        # context
        "context repository", "context engineering", "context window",
        "context infrastructure", "rag", "retrieval augmented",
        # orchestration
        "langgraph", "crewai", "inngest agents", "autogen", "agent orchestration",
        "agentic workflow", "multi-agent",
        # integrations
        "mcp", "model context protocol", "tool use", "tool calling", "function calling",
        # eval
        "agent eval", "swe-bench", "agent benchmark", "agent reliability",
        # patterns
        "agent loop", "planning agent", "react agent", "reflection",
        "inference-time compute", "test-time compute",
    ),
    rss_feeds=(
        # Curated first-pass feed list from the handoff + canonical agent-platform voices.
        "https://simonwillison.net/atom/everything/",
        "https://www.anthropic.com/news/rss.xml",
        "https://openai.com/blog/rss.xml",
        "https://lilianweng.github.io/index.xml",
        "https://huyenchip.com/feed.xml",
        "https://karpathy.github.io/feed.xml",
        "https://magazine.sebastianraschka.com/feed",
        "https://eugeneyan.com/rss/",
        "https://www.latent.space/feed",
        "https://www.interconnects.ai/feed",
    ),
    arxiv_categories=("cs.AI", "cs.CL", "cs.LG", "cs.MA"),
)


BEATS: dict[str, Beat] = {
    AGENT_PLATFORMS.id: AGENT_PLATFORMS,
}


def get_beat(beat_id: str) -> Beat:
    if beat_id not in BEATS:
        raise KeyError(f"unknown beat: {beat_id!r}. available: {sorted(BEATS)}")
    return BEATS[beat_id]

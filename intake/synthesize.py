"""Weekly synthesis.

Reads the last 7 days of per-beat digests (or as many as exist), writes a
~1-page synthesis file to `runtime/intake/synthesis/<beat>-<iso-week>.md`,
and refreshes the `<beat>-latest.md` symlink so executive sessions auto-load
the most recent synthesis via the workspace `context-always-load` mechanism.

Synthesis is heuristic-only, mirroring `score.py` (ADR-0036: no metered API
spend).

The former `if ANTHROPIC_API_KEY: _render_sonnet(...)` branch was latent metered
spend, not a dormant feature: the systemd unit loads
`EnvironmentFile=-/opt/workspace/runtime/.secrets/synaplex.env`, so a key landing
in that file would have started billing on the weekly cron with nothing to
announce it. It is removed, not gated — a gate is the same loaded gun with a
safety catch.

The heuristic path produces a structured digest-of-digests
(top items across the week grouped by theme); the Sonnet path produces
prose synthesis with a beat editor's voice.

The weekly file is designed to fit under the 30KB context-always-load
aggregate cap. Target: ≤8KB per weekly synthesis.
"""

from __future__ import annotations

import json
import os
from datetime import date as _date, datetime, timedelta, timezone
from pathlib import Path

from .beats import Beat, get_beat
from .digest import _load_scored
from .friction import emit_failure, emit_stuck, emit_success
from .paths import (
    SYNTHESIS_ROOT,
    digest_path,
    scored_path,
    synthesis_latest_path,
    synthesis_path,
)

# Synthesis must fit comfortably under the workspace context-always-load cap
# (30KB aggregate, shared with ~47KB of existing governance files). Keep the
# briefing terse: headlines + one-line-per-item, not full summaries.
TARGET_BYTES = 3 * 1024
MAX_ITEMS = 12


def _iso_week_for(d: _date) -> str:
    year, week, _ = d.isocalendar()
    return f"{year}-W{week:02d}"


def _gather_week(beat_id: str, end_date: str) -> tuple[list[dict], list[str]]:
    """Return (scored items across last 7 days, list of dates covered).

    Dedupes by `content_id`: an article that appears in multiple days'
    scored files (e.g., a long-tail RSS post that stayed in source's
    recent window for several days, getting re-scored each day) is
    represented exactly once. The highest-scoring instance wins on
    collision so the synthesis never demotes a stronger reading of the
    same item.
    """
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    by_id: dict[str, dict] = {}
    dates_covered: list[str] = []
    for i in range(7):
        d = end - timedelta(days=i)
        date_str = d.isoformat()
        day_items = _load_scored(beat_id, date_str)
        if not day_items:
            continue
        dates_covered.append(date_str)
        for item in day_items:
            iid = item.get("id")
            if not iid:
                continue
            existing = by_id.get(iid)
            if existing is None or item.get("score", 0) > existing.get("score", 0):
                by_id[iid] = item
    return list(by_id.values()), sorted(set(dates_covered))


def _themed_heuristic(
    beat: Beat, items: list[dict]
) -> tuple[list[tuple[str, list[dict]]], dict]:
    """Group top-N items into simple themes from the beat's keyword taxonomy."""
    themes = {
        "harnesses": (
            "claude code", "codex", "aider", "opendevin", "cline",
            "devin", "harness",
        ),
        "memory": (
            "letta", "mem0", "memgpt", "memory",
        ),
        "orchestration": (
            "langgraph", "crewai", "autogen", "inngest", "multi-agent", "orchestration",
        ),
        "integrations": (
            "mcp", "model context protocol", "tool use", "tool calling", "function calling",
        ),
        "eval": (
            "swe-bench", "agent eval", "benchmark", "reliability",
        ),
        "context": (
            "context window", "context engineering", "context repository", "rag",
            "retrieval",
        ),
    }
    buckets: dict[str, list[dict]] = {k: [] for k in themes}
    for item in items:
        text = (item.get("title", "") + " " + item.get("summary", "")).lower()
        placed = False
        for theme, kws in themes.items():
            if any(k in text for k in kws):
                buckets[theme].append(item)
                placed = True
                break
        if not placed:
            buckets.setdefault("other", []).append(item)
    # limit per-theme (tight cap — briefing not digest)
    for k in buckets:
        buckets[k].sort(key=lambda x: -x.get("score", 0))
        buckets[k] = buckets[k][:2]
    ordered = [(k, buckets[k]) for k in (
        "harnesses", "memory", "orchestration", "integrations", "eval", "context", "other"
    ) if buckets.get(k)]
    stats = {
        "total_items": len(items),
        "themes_with_content": sum(1 for _, b in ordered if b),
    }
    return ordered, stats


def _render_heuristic(
    beat: Beat,
    iso_week: str,
    end_date: str,
    dates_covered: list[str],
    items: list[dict],
) -> str:
    # Keep top-by-score items overall, not just within theme
    top = sorted(items, key=lambda i: -i.get("score", 0))[:MAX_ITEMS]
    themed, stats = _themed_heuristic(beat, top)

    lines: list[str] = []
    lines.append("---")
    lines.append(f"name: {beat.name} weekly synthesis — {iso_week}")
    lines.append(
        f"description: Auto-injected into executive sessions. Synthesis of "
        f"the last week of scored intake for the {beat.id} beat."
    )
    lines.append(f"beat: {beat.id}")
    lines.append(f"iso_week: {iso_week}")
    lines.append(f"end_date: {end_date}")
    lines.append(f"updated: {end_date}")
    lines.append(f"dates_covered: {','.join(dates_covered) if dates_covered else '[]'}")
    lines.append(f"synthesis_provider: heuristic")
    lines.append("---")
    lines.append("")
    lines.append(f"# {beat.name} — weekly synthesis · {iso_week}")
    lines.append("")
    lines.append(
        f"Window: {dates_covered[0] if dates_covered else end_date} → "
        f"{dates_covered[-1] if dates_covered else end_date}. "
        f"{stats['total_items']} scored items across "
        f"{len(dates_covered)} day(s) of digests."
    )
    lines.append("")
    if not items:
        lines.append("_No scored intake items for this week._")
        return "\n".join(lines) + "\n"

    for theme, bucket in themed:
        lines.append(f"## {theme}")
        for item in bucket:
            title = item.get("title", "(untitled)").replace("\n", " ").strip()[:120]
            url = item.get("url", "")
            src = item.get("source", "?")
            score = item.get("score", 0)
            lines.append(f"- [{title}]({url}) — {src} · {score:.2f}")
        lines.append("")

    lines.append(
        "_Synaplex Layer 1 intake — heuristic briefing. This is the intended path, not a "
        "degraded one: ADR-0036 caps AI spend at the two subscription plans and authorizes no "
        "metered API. See ADR-0029 and intake/README.md._"
    )
    return "\n".join(lines) + "\n"


SONNET_SYNTHESIS_SYSTEM = (
    "You are the weekly beat editor for synaplex.ai. Given 7 days of scored "
    "intake items for a named beat, write a concise 1-page synthesis that "
    "(a) names the 3-5 most consequential developments of the week, (b) "
    "clusters them by theme (harnesses / memory / orchestration / "
    "integrations / eval / context / other), (c) flags anything that should "
    "pressure-test existing canon claims, and (d) ends with one 'what this "
    "implies for next week' paragraph. Avoid hype. Cite items by their URL. "
    "Output clean markdown. Target length: 600-900 words."
)


def _update_latest_symlink(beat_id: str, target: Path) -> Path:
    link = synthesis_latest_path(beat_id)
    if link.exists() or link.is_symlink():
        link.unlink()
    # use a relative symlink so moves of the runtime tree don't break it
    link.symlink_to(target.name)
    return link


def synthesize(beat_id: str, end_date: str | None = None) -> dict:
    """Produce the weekly synthesis for `beat_id` ending at `end_date`.

    `end_date` defaults to today (UTC). `iso_week` is derived from end_date.
    Returns a summary dict including the final path and the symlink target.
    """
    beat = get_beat(beat_id)
    end_str = end_date or datetime.now(timezone.utc).date().isoformat()
    end_dt = datetime.strptime(end_str, "%Y-%m-%d").date()
    iso_week = _iso_week_for(end_dt)

    items, dates_covered = _gather_week(beat_id, end_str)

    # Heuristic, unconditionally. There is no credential branch here and there must never be
    # one again — see the module docstring for why the metered renderer was removed rather
    # than gated. `test_no_metered_spend.py` fails if a credential name reappears in this
    # function at all, including in a comment, because a comment is how the next one starts.
    body = _render_heuristic(beat, iso_week, end_str, dates_covered, items)

    # size guard — trim if over target
    encoded = body.encode("utf-8")
    if len(encoded) > TARGET_BYTES * 2:
        # hard cap: truncate tail
        encoded = encoded[: TARGET_BYTES * 2]
        body = encoded.decode("utf-8", errors="ignore") + "\n\n_[truncated for context-always-load byte cap]_\n"

    out = synthesis_path(beat_id, iso_week)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(body, encoding="utf-8")
    link = _update_latest_symlink(beat_id, out)

    if not items:
        emit_stuck(
            "intake", "synthesize",
            f"no scored items in week ending {end_str} for beat {beat_id}",
            str(out),
        )
    else:
        emit_success(
            "intake", "synthesize",
            f"synthesis {iso_week} ({len(items)} items over {len(dates_covered)} day(s))",
            str(out),
        )
    return {
        "beat": beat_id,
        "iso_week": iso_week,
        "end_date": end_str,
        "dates_covered": dates_covered,
        "total_items": len(items),
        "out": str(out),
        "latest_symlink": str(link),
        "bytes": len(body.encode("utf-8")),
    }

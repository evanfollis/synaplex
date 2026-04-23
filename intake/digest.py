"""Daily digest rendering.

Reads the scored JSONL for (beat, date), applies a cutoff, groups by score
band, and writes a human-readable markdown file to
`runtime/intake/digests/<beat>-<date>.md`.

The digest is not a newsletter. It's a daily briefing for the executive +
editorial surfaces — what the beat's sources produced today, scored and
linked. No synthesis (that's the weekly pass).
"""

from __future__ import annotations

import json
from pathlib import Path

from .beats import get_beat
from .friction import emit_stuck, emit_success
from .paths import digest_path, scored_path
from .score import SCORE_THRESHOLD_DEFAULT


def _load_scored(beat_id: str, date: str) -> list[dict]:
    p = scored_path(beat_id, date)
    if not p.exists():
        return []
    out: list[dict] = []
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def _band(score: float) -> str:
    if score >= 0.8:
        return "on-point"
    if score >= 0.6:
        return "on-beat"
    if score >= SCORE_THRESHOLD_DEFAULT:
        return "worth-a-look"
    return "below-threshold"


def _source_tag(item: dict) -> str:
    src = item.get("source", "?")
    if src == "rss":
        feed = item.get("feed") or ""
        # derive a compact host tag from the feed URL
        from urllib.parse import urlparse
        host = urlparse(feed).hostname or "rss"
        return f"rss:{host}"
    if src == "hackernews":
        points = item.get("points", 0)
        comments = item.get("comment_count", 0)
        kind = item.get("hn_type", "story")
        return f"hn:{kind} · {points}▲ · {comments}💬"
    if src == "arxiv":
        cats = item.get("categories", [])[:3]
        return f"arxiv:{'/'.join(cats)}" if cats else "arxiv"
    return src


def render(beat_id: str, date: str, cutoff: float = SCORE_THRESHOLD_DEFAULT) -> Path:
    beat = get_beat(beat_id)
    items = _load_scored(beat_id, date)

    kept = [i for i in items if i.get("score", 0) >= cutoff]
    kept.sort(key=lambda i: (-i.get("score", 0), i.get("source", "")))

    total = len(items)
    total_kept = len(kept)

    bands: dict[str, list[dict]] = {
        "on-point": [],
        "on-beat": [],
        "worth-a-look": [],
    }
    for i in kept:
        bands[_band(i["score"])].append(i)

    lines: list[str] = []
    lines.append("---")
    lines.append(f"name: {beat.name} digest — {date}")
    lines.append(f"description: Daily intake digest for the {beat.id} beat.")
    lines.append(f"beat: {beat.id}")
    lines.append(f"date: {date}")
    lines.append(f"updated: {date}")
    lines.append(f"total_items_scored: {total}")
    lines.append(f"total_items_kept: {total_kept}")
    lines.append(f"score_cutoff: {cutoff}")
    provider = next(
        (i.get("score_provider") for i in items if i.get("score_provider")),
        "heuristic",
    )
    lines.append(f"score_provider: {provider}")
    lines.append("---")
    lines.append("")
    lines.append(f"# {beat.name} — {date}")
    lines.append("")
    lines.append(
        f"Scored {total} items across rss, arxiv, and hackernews sources; "
        f"{total_kept} cleared the {cutoff:.2f} cutoff. Provider: `{provider}`."
    )
    lines.append("")

    if total_kept == 0:
        lines.append("_No items cleared the cutoff today._")
        out = digest_path(beat_id, date)
        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        emit_stuck(
            "intake", "digest",
            f"0 items cleared cutoff for {beat_id} {date}", str(out),
        )
        return out

    for band_name in ("on-point", "on-beat", "worth-a-look"):
        bucket = bands[band_name]
        if not bucket:
            continue
        lines.append(f"## {band_name} ({len(bucket)})")
        lines.append("")
        for item in bucket:
            title = item.get("title", "(untitled)").replace("\n", " ").strip()
            url = item.get("url", "")
            score = item.get("score", 0)
            tag = _source_tag(item)
            rationale = item.get("score_rationale", "")
            lines.append(f"- **[{title}]({url})** — `{tag}` · score {score:.2f}")
            if item.get("summary"):
                summary = item["summary"].replace("\n", " ")[:300]
                lines.append(f"  {summary}")
            if rationale:
                lines.append(f"  <small>_scored: {rationale}_</small>")
            lines.append("")
        lines.append("")

    out = digest_path(beat_id, date)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    emit_success(
        "intake", "digest",
        f"{total_kept}/{total} items in digest for {beat_id} {date}",
        str(out),
    )
    return out

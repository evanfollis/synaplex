"""Per-beat scoring.

The scorer is unconditionally heuristic (ADR-0036: no metered API spend).
Ambient API keys do not select a provider and are not a blocker.

Scored item shape (added to raw fields):
    {
      ...raw...,
      "score": 0.73,
      "score_provider": "heuristic",
      "score_rationale": "matched keywords: mcp, tool use"
    }

Every run emits the same shape with `score_provider: heuristic`. A score is
in [0.0, 1.0]; the digest uses a cutoff
(default 0.5) to decide what gets rendered.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .beats import Beat, get_beat
from .friction import emit_failure, emit_stuck, emit_success
from .paths import raw_path, scored_path

SCORE_THRESHOLD_DEFAULT = 0.45

_WORD_RE = re.compile(r"[a-z0-9\+\#\-\./]+")


# --------------------------------------------------------------------------
# Heuristic scorer (no external calls)
# --------------------------------------------------------------------------


def _tokenize(text: str) -> list[str]:
    return _WORD_RE.findall((text or "").lower())


def _keyword_match(text: str, keywords: Iterable[str]) -> list[str]:
    low = (text or "").lower()
    return [k for k in keywords if k in low]


def score_heuristic(item: dict, beat: Beat) -> tuple[float, str]:
    """Score an item against the beat.

    Signal components:
    - hit count against beat keywords in (title + summary)
    - title bonus (keyword in title is worth more than in body)
    - penalties for obvious noise patterns (e.g., job postings, generic
      LLM chat posts)
    """
    title = item.get("title", "")
    summary = item.get("summary", "")

    title_hits = _keyword_match(title, beat.keywords)
    body_hits = _keyword_match(summary, beat.keywords)

    # raw signal: 0.25 per title hit + 0.12 per body hit, capped
    raw = 0.25 * len(title_hits) + 0.12 * len(body_hits)
    score = min(raw, 1.0)

    # soft penalty for likely-noise
    low_title = title.lower()
    if any(
        noise in low_title
        for noise in (" is hiring", "hiring ", "job posting", " jobs ", "salary")
    ):
        score *= 0.4

    # small arxiv bonus if categories overlap with beat's arxiv categories
    if item.get("source") == "arxiv":
        item_cats = {c.upper() for c in item.get("categories", [])}
        beat_cats = {c.upper() for c in beat.arxiv_categories}
        if item_cats & beat_cats:
            score = min(1.0, score + 0.15)

    # HN: comment-count / score bump (popular + on-topic is worth more)
    if item.get("source") == "hackernews":
        points = item.get("points", 0) or 0
        comments = item.get("comment_count", 0) or 0
        if points >= 100 or comments >= 50:
            score = min(1.0, score + 0.1)

    rationale_parts = []
    if title_hits:
        rationale_parts.append(f"title matches: {', '.join(title_hits[:4])}")
    if body_hits:
        rationale_parts.append(f"body matches: {', '.join(body_hits[:4])}")
    if not rationale_parts:
        rationale_parts.append("no beat-keyword matches")
    rationale = "; ".join(rationale_parts)
    return score, rationale


# --------------------------------------------------------------------------
# Dispatcher
# --------------------------------------------------------------------------


def _chosen_provider() -> str:
    """Always `heuristic`. There is no other provider, and that is deliberate.

    ADR-0036 (accepted 2026-06-11, principal directive) caps AI spend at the two subscription
    plans and forbids metered API keys. The heuristic scorer is the **intended** path, not a
    degraded fallback waiting for a key.

    This function used to return `"sonnet"` whenever ANTHROPIC_API_KEY was present. That was
    latent metered spend: the systemd units load `EnvironmentFile=runtime/.secrets/synaplex.env`,
    so a key appearing in that file — for any reason, set by anyone — would have silently
    started billing metered tokens on a 6x/day cron. Nobody would have noticed until the
    invoice. Gating it behind a flag would have left the same loaded gun with a safety catch;
    the path is removed instead, so there is nothing to re-enable by accident.

    If LLM-assisted scoring is ever authorized, it goes through the subscription CLIs
    (`lab.runner.providers.SubscriptionPool`), not a metered SDK.
    """
    return "heuristic"


def _read_raw_for_date(date: str) -> list[dict]:
    items: list[dict] = []
    for source in ("rss", "arxiv", "hackernews"):
        p = raw_path(source, date)
        if not p.exists():
            continue
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return items


def score_day(beat_id: str, date: str) -> dict:
    beat = get_beat(beat_id)
    provider = _chosen_provider()
    raws = _read_raw_for_date(date)

    # cross-source dedup on id (same story appearing on multiple feeds/HN)
    by_id: dict[str, dict] = {}
    for item in raws:
        item_id = item.get("id")
        if not item_id:
            continue
        existing = by_id.get(item_id)
        if not existing:
            by_id[item_id] = item
        else:
            # prefer the richer source order: arxiv > rss > hackernews
            rank = {"arxiv": 3, "rss": 2, "hackernews": 1}
            if rank.get(item.get("source"), 0) > rank.get(existing.get("source"), 0):
                by_id[item_id] = item
    deduped = len(raws) - len(by_id)
    items = list(by_id.values())

    if not items:
        emit_stuck("intake", "score", f"no raw items for {date}", "")
        out = scored_path(beat_id, date)
        out.write_text("", encoding="utf-8")
        return {"provider": provider, "count": 0, "deduped": deduped, "out": str(out)}

    scores = [score_heuristic(i, beat) for i in items]

    out = scored_path(beat_id, date)
    kept = 0
    with open(out, "w", encoding="utf-8") as f:
        for item, (score, rationale) in zip(items, scores):
            enriched = dict(item)
            enriched["score"] = round(float(score), 4)
            enriched["score_provider"] = provider
            enriched["score_rationale"] = rationale
            f.write(json.dumps(enriched, ensure_ascii=False) + "\n")
            kept += 1
    emit_success(
        "intake", "score",
        f"{kept} items scored via {provider} ({deduped} cross-source dedup)",
        str(out),
    )
    return {"provider": provider, "count": kept, "deduped": deduped, "out": str(out)}

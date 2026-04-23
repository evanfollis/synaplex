"""Per-beat scoring.

Two providers behind a common interface. Chosen at run-time via
`SYNAPLEX_SCORE_PROVIDER`; default is `heuristic` when no API key is
available, `sonnet` otherwise.

Scored item shape (added to raw fields):
    {
      ...raw...,
      "score": 0.73,
      "score_provider": "heuristic",
      "score_rationale": "matched keywords: mcp, tool use"
    }

The two providers emit the *same* shape so downstream layers don't care
which scorer ran. A score is in [0.0, 1.0]; the digest uses a cutoff
(default 0.5) to decide what gets rendered.

Per the `claude-api` skill, the Sonnet provider caches the system prompt +
beat definition. Beat definitions are stable across a scoring run; the
system prompt is constant.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

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
# Sonnet scorer
# --------------------------------------------------------------------------


def _have_anthropic_key() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


SONNET_MODEL = os.environ.get("SYNAPLEX_SONNET_MODEL", "claude-sonnet-4-6")
SONNET_SYSTEM_PROMPT = (
    "You are a beat editor for synaplex.ai, a system that discovers the "
    "structure of AI systems. Your job is to score intake items 0-100 "
    "on their relevance to a named beat and return a single JSON object "
    'of the form {"score": <0-100>, "rationale": "<one sentence>"}. '
    "Score 0 means 'irrelevant, off-beat, or noise'; score 100 means "
    "'a reader building in this beat would cite this in a technical "
    "design review'. Reserve 80+ for genuinely technical, primary-source, "
    "or clearly load-bearing items. Do not inflate scores for hype."
)


def _sonnet_user_message(item: dict, beat: Beat) -> str:
    return (
        f"Beat: {beat.name}\n"
        f"Beat definition:\n{beat.definition}\n\n"
        f"Item:\n"
        f"  source: {item.get('source','')}\n"
        f"  title: {item.get('title','')}\n"
        f"  url: {item.get('url','')}\n"
        f"  summary: {(item.get('summary','') or '')[:1000]}\n\n"
        'Return ONLY the JSON object, no prose. Format: {"score": <0-100>, "rationale": "<one sentence>"}'
    )


def score_sonnet_batch(items: list[dict], beat: Beat) -> list[tuple[float, str]]:
    """Score a batch via the Anthropic SDK, with prompt caching.

    Cached:
      - system prompt
      - beat definition (prepended as an ephemeral-cached user block)

    Uncached:
      - the per-item title/url/summary

    First-pass implementation scores items one at a time (one API call per
    item) but with prompt caching the repeated system+beat tokens hit the
    cache on the second and subsequent calls in a run. Batch-packing
    multiple items per call is a second-pass optimization.
    """
    try:
        import anthropic  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError("anthropic SDK not installed in this venv") from exc

    client = anthropic.Anthropic()
    results: list[tuple[float, str]] = []
    beat_block_text = (
        f"Beat: {beat.name}\nBeat definition:\n{beat.definition}"
    )
    for item in items:
        try:
            msg = client.messages.create(
                model=SONNET_MODEL,
                max_tokens=256,
                system=[{
                    "type": "text",
                    "text": SONNET_SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }],
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": beat_block_text,
                                "cache_control": {"type": "ephemeral"},
                            },
                            {"type": "text", "text": _sonnet_user_message(item, beat)},
                        ],
                    }
                ],
            )
            text = "".join(
                b.text for b in msg.content if getattr(b, "type", None) == "text"
            ).strip()
            # tolerate a stray code fence
            if text.startswith("```"):
                text = text.strip("`").split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            data = json.loads(text)
            raw_score = float(data.get("score", 0))
            score = max(0.0, min(1.0, raw_score / 100.0))
            rationale = str(data.get("rationale", ""))[:240]
            results.append((score, rationale))
        except Exception as exc:
            # fall back to heuristic for this item; record the fact in rationale
            h_score, h_rat = score_heuristic(item, beat)
            results.append((h_score, f"sonnet-fallback({type(exc).__name__}); {h_rat}"))
    return results


# --------------------------------------------------------------------------
# Dispatcher
# --------------------------------------------------------------------------


def _chosen_provider() -> str:
    explicit = os.environ.get("SYNAPLEX_SCORE_PROVIDER")
    if explicit:
        return explicit.lower()
    return "sonnet" if _have_anthropic_key() else "heuristic"


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

    if provider == "sonnet":
        try:
            scores = score_sonnet_batch(items, beat)
        except Exception as exc:
            emit_failure(
                "intake", "score",
                f"sonnet init failed, falling back to heuristic: {type(exc).__name__}: {exc}",
                "",
            )
            provider = "heuristic"
            scores = [score_heuristic(i, beat) for i in items]
    else:
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

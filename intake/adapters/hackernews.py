"""HackerNews adapter via the Firebase API.

Sources: top + new. Show HN / Ask HN are captured by filtering `type` and
`title` from the same base streams.

Raw item shape:
    {
      "id": "<sha256[:16]>",
      "source": "hackernews",
      "hn_id": 12345678,
      "hn_type": "story|ask|show",
      "url": "<story url or hn link>",
      "title": "<hn title>",
      "summary": "<truncated text field for Ask/Show HN, empty for links>",
      "author": "<hn username>",
      "points": 123,
      "comment_count": 45,
      "published": "<iso>",
      "fetched_at": "<iso>",
      "beat": "<beat id>"
    }

Filter: keep items that either (a) link to an external URL, or (b) are
Ask/Show HN with a non-empty text field. Comments are not ingested.
Default take: top 50 from /topstories and top 50 from /newstories.
"""

from __future__ import annotations

import json
import ssl
from datetime import datetime, timezone
from urllib.request import Request, urlopen

from ..beats import Beat
from ..friction import emit_failure, emit_stuck, emit_success, emit_throttled
from ..hashing import content_id
from ..limits import layer1_cap
from ..paths import raw_path
from . import IngestResult, merge_jsonl_by_id

BASE = "https://hacker-news.firebaseio.com/v0"
USER_AGENT = "synaplex-intake/0.1 (+https://synaplex.ai/intake)"
TIMEOUT = 10.0
TAKE_TOP = 50
TAKE_NEW = 50


def _get(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    ctx = ssl.create_default_context()
    with urlopen(req, timeout=TIMEOUT, context=ctx) as r:
        return r.read()


def _json(url: str):
    raw = _get(url)
    return json.loads(raw.decode("utf-8"))


def _fetch_item(hn_id: int) -> dict | None:
    try:
        return _json(f"{BASE}/item/{hn_id}.json")
    except Exception:
        return None


def _classify(item: dict) -> str | None:
    title = (item.get("title") or "").lower()
    if title.startswith("ask hn"):
        return "ask"
    if title.startswith("show hn"):
        return "show"
    if item.get("type") == "story":
        return "story"
    return None


def ingest(beat: Beat, date: str) -> IngestResult:
    out = raw_path("hackernews", date)
    out.parent.mkdir(parents=True, exist_ok=True)

    try:
        top = _json(f"{BASE}/topstories.json")[:TAKE_TOP]
        new = _json(f"{BASE}/newstories.json")[:TAKE_NEW]
    except Exception as exc:
        # No-clobber: stream-fetch failure must NOT destroy the existing
        # daily file. Emit failure and bail; existing items are intact.
        emit_failure(
            "intake", "hackernews",
            f"stream fetch failed: {type(exc).__name__}: {exc}", str(out),
        )
        return IngestResult(source="hackernews", count=0, deduped=0, out_path=str(out))

    ids = list(dict.fromkeys(list(top) + list(new)))  # preserve order, dedup
    deduped = 0
    capped = 0
    cap = layer1_cap()
    seen: set[str] = set()
    new_items: list[dict] = []
    fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    for hn_id in ids:
        item = _fetch_item(hn_id)
        if not item:
            continue
        kind = _classify(item)
        if kind is None:
            continue
        title = (item.get("title") or "").strip()
        if not title:
            continue
        url = (item.get("url") or "").strip()
        if not url:
            url = f"https://news.ycombinator.com/item?id={hn_id}"
        # hn 'text' field is HTML but short; we keep it as-is for summary
        summary = (item.get("text") or "")[:1200]
        if not url and not summary:
            continue
        item_id = content_id(url, title)
        if item_id in seen:
            deduped += 1
            continue
        if len(new_items) >= cap:
            capped += 1
            continue
        seen.add(item_id)
        published = ""
        if item.get("time"):
            try:
                published = datetime.fromtimestamp(item["time"], tz=timezone.utc).isoformat(
                    timespec="seconds"
                ).replace("+00:00", "Z")
            except Exception:
                pass
        new_items.append({
            "id": item_id,
            "source": "hackernews",
            "hn_id": hn_id,
            "hn_type": kind,
            "url": url,
            "title": title,
            "summary": summary,
            "author": item.get("by") or "",
            "points": int(item.get("score") or 0),
            "comment_count": int(item.get("descendants") or 0),
            "published": published,
            "fetched_at": fetched_at,
            "beat": beat.id,
        })

    new_added, preserved, total = merge_jsonl_by_id(out, new_items)
    ref = str(out)
    if not new_items:
        emit_stuck(
            "intake", "hackernews",
            f"no hackernews items classified (preserved {preserved} from prior runs)",
            ref,
        )
    else:
        reason = f"{new_added} new, {preserved} preserved, {total} total"
        if deduped:
            reason += f", {deduped} within-run dedup"
        if capped:
            reason += f", {capped} dropped by daily cap ({cap})"
        emit_success("intake", "hackernews", reason, ref)
    if capped:
        emit_throttled(
            "intake", "hackernews",
            f"daily cap hit: {capped} items dropped past {cap}-item cap",
            ref,
        )
    return IngestResult(
        source="hackernews", count=new_added, deduped=deduped,
        out_path=ref, total=total, preserved=preserved,
    )

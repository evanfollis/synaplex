"""arxiv adapter via the public arxiv API.

First pass: query the arxiv API for the beat's categories, filtered to the
last N days (default 3 to allow for reruns catching up after outages).
`http://export.arxiv.org/api/query` returns Atom; feedparser digests it.

Raw item shape mirrors rss.py, with source="arxiv" and a `categories` field
captured from the entry's arxiv:primary_category + tags.
"""

from __future__ import annotations

import json
import re
import ssl
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import feedparser  # type: ignore[import-untyped]

from ..beats import Beat
from ..friction import emit_failure, emit_stuck, emit_success, emit_throttled
from ..hashing import content_id
from ..limits import layer1_cap
from ..paths import raw_path
from . import IngestResult, merge_jsonl_by_id

API_BASE = "http://export.arxiv.org/api/query"
USER_AGENT = "synaplex-intake/0.1 (+https://synaplex.ai/intake)"
TIMEOUT = 25.0
WINDOW_DAYS = 3
MAX_RESULTS = 100
_WS_RE = re.compile(r"\s+")


def _category_query(categories: tuple[str, ...]) -> str:
    return "+OR+".join(f"cat:{c}" for c in categories)


def _fetch(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/atom+xml"})
    ctx = ssl.create_default_context()
    with urlopen(req, timeout=TIMEOUT, context=ctx) as r:
        return r.read()


def _normalize(text: str) -> str:
    return _WS_RE.sub(" ", (text or "").strip())


def _within_window(entry, window_start: datetime) -> bool:
    for key in ("published_parsed", "updated_parsed"):
        parsed = entry.get(key)
        if parsed:
            try:
                dt = datetime(*parsed[:6], tzinfo=timezone.utc)
                return dt >= window_start
            except Exception:
                continue
    return True


def ingest(beat: Beat, date: str) -> IngestResult:
    out = raw_path("arxiv", date)
    out.parent.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    window_start = now - timedelta(days=WINDOW_DAYS)

    params = {
        "search_query": _category_query(beat.arxiv_categories),
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "start": 0,
        "max_results": MAX_RESULTS,
    }
    # manual encoding so `+OR+` isn't double-encoded
    qs = "&".join(
        f"{k}={v}" if k == "search_query" else f"{k}={urlencode({k: v}).split('=', 1)[1]}"
        for k, v in params.items()
    )
    url = f"{API_BASE}?{qs}"

    try:
        raw = _fetch(url)
    except Exception as exc:
        # No-clobber: a fetch error must NOT destroy the existing daily file.
        # Just emit failure and return — the file (if any) is left intact.
        emit_failure("intake", "arxiv", f"fetch failed: {type(exc).__name__}: {exc}", str(out))
        return IngestResult(source="arxiv", count=0, deduped=0, out_path=str(out))

    # arxiv rate-limits; respect the 3s guideline
    time.sleep(1.0)

    parsed = feedparser.parse(raw)
    deduped = 0
    capped = 0
    cap = layer1_cap()
    seen: set[str] = set()
    new_items: list[dict] = []
    fetched_at = now.isoformat(timespec="seconds").replace("+00:00", "Z")

    for entry in parsed.entries:
        if not _within_window(entry, window_start):
            continue
        link = (entry.get("link") or "").strip()
        title = _normalize(entry.get("title") or "")
        if not link or not title:
            continue
        item_id = content_id(link, title)
        if item_id in seen:
            deduped += 1
            continue
        if len(new_items) >= cap:
            capped += 1
            continue
        seen.add(item_id)
        summary = _normalize(entry.get("summary") or "")[:1200]
        authors = [
            (a.get("name") if isinstance(a, dict) else str(a))
            for a in entry.get("authors", [])
        ]
        categories = []
        for tag in entry.get("tags", []) or []:
            term = tag.get("term") if isinstance(tag, dict) else None
            if term:
                categories.append(term)
        published_parsed = entry.get("published_parsed") or entry.get("updated_parsed")
        published = ""
        if published_parsed:
            try:
                published = datetime(*published_parsed[:6], tzinfo=timezone.utc).isoformat(
                    timespec="seconds"
                ).replace("+00:00", "Z")
            except Exception:
                pass
        new_items.append({
            "id": item_id,
            "source": "arxiv",
            "url": link,
            "title": title,
            "summary": summary,
            "authors": authors,
            "categories": categories,
            "published": published,
            "fetched_at": fetched_at,
            "beat": beat.id,
        })

    new_added, preserved, total = merge_jsonl_by_id(out, new_items)
    ref = str(out)
    if not new_items:
        # `stuck` is the right signal — fetch returned 0 — but the daily file
        # is preserved (no clobber). emit_stuck still fires so meta-scan sees
        # the upstream zero-result; ref points at the (preserved) file.
        emit_stuck(
            "intake", "arxiv",
            f"no arxiv items in {WINDOW_DAYS}d window (preserved {preserved} from prior runs)",
            ref,
        )
    else:
        reason = f"{new_added} new, {preserved} preserved, {total} total"
        if deduped:
            reason += f", {deduped} within-run dedup"
        if capped:
            reason += f", {capped} dropped by daily cap ({cap})"
        emit_success("intake", "arxiv", reason, ref)
    if capped:
        emit_throttled(
            "intake", "arxiv",
            f"daily cap hit: {capped} items dropped past {cap}-item cap",
            ref,
        )
    return IngestResult(
        source="arxiv", count=new_added, deduped=deduped,
        out_path=ref, total=total, preserved=preserved,
    )

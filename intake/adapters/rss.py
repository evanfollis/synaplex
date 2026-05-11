"""RSS/Atom adapter via feedparser.

Consumes a curated list of per-beat feeds. Emits one raw item per entry with
a stable `id` from `intake.hashing.content_id`. The raw item shape:

    {
      "id": "<sha256[:16]>",
      "source": "rss",
      "feed": "<feed url>",
      "url": "<entry link>",
      "title": "<entry title>",
      "summary": "<entry summary, stripped to plaintext>",
      "author": "<entry author, optional>",
      "published": "<iso timestamp, optional>",
      "fetched_at": "<iso timestamp>",
      "beat": "<beat id>"
    }

The adapter dedupes within a single run against an in-file seen-set; cross-run
dedup is downstream (scored merges + digest de-dupes by id).
"""

from __future__ import annotations

import json
import re
import ssl
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from urllib.request import Request, urlopen

import feedparser  # type: ignore[import-untyped]

from ..beats import Beat
from ..escalation import record_stuck, reset_stuck
from ..friction import emit, emit_failure, emit_stuck, emit_success, emit_throttled
from ..hashing import content_id
from ..limits import layer1_cap
from ..paths import raw_path
from . import IngestResult, merge_jsonl_by_id

USER_AGENT = "synaplex-intake/0.1 (+https://synaplex.ai/intake)"
TIMEOUT = 15.0
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _fetch(url: str) -> bytes:
    # feedparser.parse accepts URLs directly, but using urllib lets us apply a
    # consistent User-Agent + timeout across adapters and handle 403-on-default-UA
    # sources uniformly.
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    ctx = ssl.create_default_context()
    with urlopen(req, timeout=TIMEOUT, context=ctx) as r:
        return r.read()


def _plain_text(html: str) -> str:
    if not html:
        return ""
    text = _TAG_RE.sub(" ", html)
    text = unescape(text)
    text = _WS_RE.sub(" ", text).strip()
    return text[:1200]  # per-item bound; digests render the first ~300 chars


def _entry_iso(entry) -> str:
    for key in ("published_parsed", "updated_parsed"):
        parsed = entry.get(key)
        if parsed:
            try:
                return datetime(*parsed[:6], tzinfo=timezone.utc).isoformat(
                    timespec="seconds"
                ).replace("+00:00", "Z")
            except Exception:
                pass
    return ""


def ingest(beat: Beat, date: str) -> IngestResult:
    out = raw_path("rss", date)
    out.parent.mkdir(parents=True, exist_ok=True)

    deduped = 0
    capped = 0
    cap = layer1_cap()
    seen: set[str] = set()
    new_items: list[dict] = []
    errored_feeds: list[str] = []
    fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    for feed_url in beat.rss_feeds:
        try:
            raw = _fetch(feed_url)
        except Exception as exc:
            errored_feeds.append(f"{feed_url} -> {type(exc).__name__}: {exc}")
            continue
        parsed = feedparser.parse(raw)
        if parsed.bozo and not parsed.entries:
            errored_feeds.append(f"{feed_url} -> bozo_empty")
            continue
        for entry in parsed.entries:
            url = (entry.get("link") or "").strip()
            title = (entry.get("title") or "").strip()
            if not url or not title:
                continue
            item_id = content_id(url, title)
            if item_id in seen:
                deduped += 1
                continue
            if len(new_items) >= cap:
                capped += 1
                continue
            seen.add(item_id)
            summary_html = entry.get("summary") or entry.get("description") or ""
            new_items.append({
                "id": item_id,
                "source": "rss",
                "feed": feed_url,
                "url": url,
                "title": title,
                "summary": _plain_text(summary_html),
                "author": entry.get("author") or "",
                "published": _entry_iso(entry),
                "fetched_at": fetched_at,
                "beat": beat.id,
            })

    new_added, preserved, total = merge_jsonl_by_id(out, new_items)
    ref = str(out)
    if not new_items:
        # All feeds errored or returned nothing. Existing daily file is
        # preserved (no clobber); we still emit `stuck` so meta-scan sees
        # the upstream zero-result.
        reason = "no rss items"
        if errored_feeds:
            reason += f" ({len(errored_feeds)} feed errors; first: {errored_feeds[0]})"
        if preserved:
            reason += f"; preserved {preserved} from prior runs"
        emit_stuck("intake", "rss", reason, ref)
        n, crossed = record_stuck("rss")
        if crossed:
            emit(
                layer="intake", source="rss", eventType="escalated",
                reason=f"consecutive stuck count {n} crossed S3-P2 threshold",
                ref=ref, extra={"consecutive_stuck": n, "threshold": 3},
            )
    else:
        reset_stuck("rss")
        reason = f"{new_added} new, {preserved} preserved, {total} total"
        if deduped:
            reason += f", {deduped} within-run dedup"
        if capped:
            reason += f", {capped} dropped by daily cap ({cap})"
        if errored_feeds:
            reason += f", {len(errored_feeds)} feed errors"
        # Single event per run: throttled when cap-hit, success otherwise.
        # The dual-emit (success + throttled) had been carry-forward-flagged
        # for 9+ reflection cycles for inflating time-windowed event counts;
        # throttled is the precise signal when the cap fires, and its reason
        # field carries the same new/preserved/total counts that a non-capped
        # success would.
        if capped:
            emit_throttled("intake", "rss", reason, ref)
        else:
            emit_success("intake", "rss", reason, ref)
    if errored_feeds:
        # Name the failing feed(s) inline so the friction log is actionable
        # without re-running the adapter with debug tracing. S3-P2
        # generalization: a silent failure is indistinguishable from stuck.
        from ..friction import emit as _emit
        _emit(
            layer="intake",
            source="rss",
            eventType="failure",
            reason="feed failures (see extra.failing_feeds)",
            ref=ref,
            extra={"failing_feeds": errored_feeds},
        )
    return IngestResult(
        source="rss", count=new_added, deduped=deduped,
        out_path=ref, total=total, preserved=preserved,
    )

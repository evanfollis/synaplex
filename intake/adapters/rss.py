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
from ..friction import emit_failure, emit_stuck, emit_success
from ..hashing import content_id
from ..paths import raw_path
from . import IngestResult

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

    count = 0
    deduped = 0
    seen: set[str] = set()
    errored_feeds: list[str] = []
    fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    with open(out, "w", encoding="utf-8") as fp:
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
                seen.add(item_id)
                summary_html = entry.get("summary") or entry.get("description") or ""
                item = {
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
                }
                fp.write(json.dumps(item, ensure_ascii=False) + "\n")
                count += 1

    ref = str(out)
    if count == 0:
        reason = "no rss items"
        if errored_feeds:
            reason += f" ({len(errored_feeds)} feed errors; first: {errored_feeds[0]})"
        emit_stuck("intake", "rss", reason, ref)
    else:
        reason = f"{count} items, {deduped} deduped"
        if errored_feeds:
            reason += f", {len(errored_feeds)} feed errors"
        emit_success("intake", "rss", reason, ref)
    if errored_feeds and count > 0:
        # also surface partial-failure; downstream synthesis may need to know
        # which feeds were missing.
        emit_failure(
            "intake", "rss",
            f"{len(errored_feeds)} of {len(beat.rss_feeds)} feeds failed",
            ref,
        )

    return IngestResult(source="rss", count=count, deduped=deduped, out_path=ref)

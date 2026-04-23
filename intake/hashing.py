"""Shared dedup contract for intake adapters (S1-P3).

Every adapter MUST use `content_id(url, title)` to produce item IDs. Divergent
hash schemes across write paths silently corrupt cross-path joins in
`runtime/intake/`. Keep this module small, deterministic, and documented.

Algorithm:
    sha256( canonicalize_url(url) + "\\n" + normalize_title(title) )[:16]

- `canonicalize_url` strips tracking params (utm_*, ref, fbclid), lowercases
  the host, drops fragments, and removes default ports.
- `normalize_title` lowercases, collapses whitespace, and strips surrounding
  punctuation — tolerant to minor re-formats without being permissive enough
  to collide unrelated items.
- sha256[:16] matches the atlas canon emitter's id scheme (16 hex chars).
"""

from __future__ import annotations

import hashlib
import re
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

_TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "mc_cid", "mc_eid", "ref", "ref_src", "ref_url",
    "igshid", "src",
}

_WHITESPACE_RE = re.compile(r"\s+")
_TITLE_STRIP_RE = re.compile(r"^[\s\"'“”‘’—\-–—_•]+|[\s\"'“”‘’—\-–—_•]+$")


def canonicalize_url(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url.strip())
    host = (parsed.hostname or "").lower()
    if parsed.port and not (
        (parsed.scheme == "http" and parsed.port == 80)
        or (parsed.scheme == "https" and parsed.port == 443)
    ):
        host = f"{host}:{parsed.port}"
    path = parsed.path or "/"
    if path.endswith("/") and path != "/":
        path = path.rstrip("/")
    query_pairs = [
        (k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=False)
        if k.lower() not in _TRACKING_PARAMS
    ]
    query_pairs.sort()
    query = urlencode(query_pairs)
    return urlunparse((parsed.scheme.lower(), host, path, "", query, ""))


def normalize_title(title: str) -> str:
    if not title:
        return ""
    t = title.strip()
    t = _WHITESPACE_RE.sub(" ", t)
    t = _TITLE_STRIP_RE.sub("", t)
    return t.lower()


def content_id(url: str, title: str) -> str:
    key = f"{canonicalize_url(url)}\n{normalize_title(title)}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]

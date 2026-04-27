"""CLI dispatcher for intake.

Usage:
    python -m intake ingest --source rss --beat agent-platforms
    python -m intake ingest --source arxiv --beat agent-platforms
    python -m intake ingest --source hackernews --beat agent-platforms
    python -m intake score --beat agent-platforms --date 2026-04-24
    python -m intake digest --beat agent-platforms --date 2026-04-24
    python -m intake synthesize --beat agent-platforms
    python -m intake run-daily --beat agent-platforms
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

from . import digest as digest_mod
from . import score as score_mod
from . import synthesize as synthesize_mod
from .adapters import arxiv as arxiv_adapter
from .adapters import hackernews as hn_adapter
from .adapters import rss as rss_adapter
from .beats import get_beat
from .paths import ensure_dirs

ADAPTERS = {
    "rss": rss_adapter.ingest,
    "arxiv": arxiv_adapter.ingest,
    "hackernews": hn_adapter.ingest,
}


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def cmd_ingest(args) -> int:
    beat = get_beat(args.beat)
    source = args.source
    date = args.date or _today()
    if source == "all":
        results = []
        for name, fn in ADAPTERS.items():
            r = fn(beat, date)
            results.append(r)
            print(f"[{name}] {r.count} new, {r.preserved} preserved, {r.total} total -> {r.out_path}")
        return 0
    fn = ADAPTERS.get(source)
    if not fn:
        print(f"unknown source: {source}; expected one of rss|arxiv|hackernews|all", file=sys.stderr)
        return 2
    r = fn(beat, date)
    print(f"[{source}] {r.count} new, {r.preserved} preserved, {r.total} total -> {r.out_path}")
    return 0


def cmd_score(args) -> int:
    date = args.date or _today()
    r = score_mod.score_day(args.beat, date)
    print(
        f"[score] provider={r['provider']} count={r['count']} "
        f"deduped={r['deduped']} -> {r['out']}"
    )
    return 0


def cmd_digest(args) -> int:
    date = args.date or _today()
    cutoff = args.cutoff if args.cutoff is not None else score_mod.SCORE_THRESHOLD_DEFAULT
    out = digest_mod.render(args.beat, date, cutoff=cutoff)
    print(f"[digest] -> {out}")
    return 0


def cmd_synthesize(args) -> int:
    end_date = args.date or _today()
    r = synthesize_mod.synthesize(args.beat, end_date=end_date)
    print(
        f"[synthesize] week={r['iso_week']} items={r['total_items']} "
        f"days={len(r['dates_covered'])} bytes={r['bytes']} -> {r['out']}"
    )
    print(f"[synthesize] latest symlink -> {r['latest_symlink']}")
    return 0


def cmd_run_daily(args) -> int:
    beat = get_beat(args.beat)
    date = args.date or _today()
    ensure_dirs()
    print(f"== run-daily beat={beat.id} date={date} ==")
    for name, fn in ADAPTERS.items():
        r = fn(beat, date)
        print(f"[{name}] {r.count} new, {r.preserved} preserved, {r.total} total -> {r.out_path}")
    s = score_mod.score_day(beat.id, date)
    print(f"[score] provider={s['provider']} count={s['count']} -> {s['out']}")
    d = digest_mod.render(beat.id, date)
    print(f"[digest] -> {d}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="intake", description="synaplex intake CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    ping = sub.add_parser("ingest", help="run one source adapter")
    ping.add_argument("--source", required=True, choices=["rss", "arxiv", "hackernews", "all"])
    ping.add_argument("--beat", required=True)
    ping.add_argument("--date", help="ISO date; defaults to today UTC")
    ping.set_defaults(func=cmd_ingest)

    psc = sub.add_parser("score", help="score raw items for a beat/date")
    psc.add_argument("--beat", required=True)
    psc.add_argument("--date")
    psc.set_defaults(func=cmd_score)

    pdg = sub.add_parser("digest", help="render daily digest markdown")
    pdg.add_argument("--beat", required=True)
    pdg.add_argument("--date")
    pdg.add_argument("--cutoff", type=float)
    pdg.set_defaults(func=cmd_digest)

    pwk = sub.add_parser("synthesize", help="render weekly synthesis + update latest symlink")
    pwk.add_argument("--beat", required=True)
    pwk.add_argument("--date", help="ISO end date; defaults to today UTC")
    pwk.set_defaults(func=cmd_synthesize)

    prd = sub.add_parser("run-daily", help="ingest all sources, score, and write digest")
    prd.add_argument("--beat", required=True)
    prd.add_argument("--date")
    prd.set_defaults(func=cmd_run_daily)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

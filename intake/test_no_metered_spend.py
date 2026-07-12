"""Verifiable assertions that intake cannot spend metered tokens (ADR-0036).

    .venv/bin/python intake/test_no_metered_spend.py

## The bug this pins

`score._chosen_provider()` returned `"sonnet"` whenever `ANTHROPIC_API_KEY` was present, and
`synthesize()` had `if os.environ.get("ANTHROPIC_API_KEY"): _render_sonnet(...)`.

That was **latent metered spend**, not a dormant feature. The systemd units load
`EnvironmentFile=-/opt/workspace/runtime/.secrets/synaplex.env`, so a key landing in that file
— set by anyone, for any reason — would have silently started billing metered tokens on a
6×/day scoring cron and a weekly synthesis cron. Nothing would have announced it. Nobody would
have noticed until the invoice.

ADR-0036 (accepted 2026-06-11, principal directive) is explicit: the heuristic path is the
**intended** one, *"a deliberate cost decision, not a credential blocker."*

Gating the metered path behind a flag would have left the same loaded gun with a safety catch.
The path is **removed**, so there is nothing to re-enable by accident — and these assertions
fail loudly if it ever grows back.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _ok(msg: str) -> None:
    print(f"  ok   {msg}")


def test_no_metered_client_in_intake() -> None:
    """No module under intake/ may import or construct a metered API client."""
    intake = Path(__file__).parent
    offenders = []
    for path in sorted(intake.glob("*.py")):
        if path.name.startswith("test_"):
            continue
        for lineno, line in enumerate(path.read_text().splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith('"'):
                continue  # prose explaining the removal is fine; code is not
            for banned in ("import anthropic", "anthropic.Anthropic", "import openai"):
                if banned in line:
                    offenders.append(f"{path.name}:{lineno}: {stripped}")
    assert not offenders, "metered API client back in intake:\n  " + "\n  ".join(offenders)
    _ok("no intake module imports or constructs a metered API client")


def test_scorer_is_heuristic_even_with_a_key_present() -> None:
    """The regression itself: a key in the environment must not select a metered provider."""
    from intake.score import _chosen_provider

    saved = os.environ.get("ANTHROPIC_API_KEY")
    os.environ["ANTHROPIC_API_KEY"] = "POISON-would-have-billed"
    try:
        provider = _chosen_provider()
        assert provider == "heuristic", (
            f"_chosen_provider() returned {provider!r} with a metered key present. That is "
            f"latent metered spend on a 6x/day cron — the systemd unit loads "
            f"runtime/.secrets/synaplex.env, so a key landing there starts billing silently."
        )
    finally:
        if saved is None:
            os.environ.pop("ANTHROPIC_API_KEY", None)
        else:
            os.environ["ANTHROPIC_API_KEY"] = saved
    assert _chosen_provider() == "heuristic", "heuristic must be unconditional"
    _ok("scorer stays heuristic with a metered key present (and without one)")


def test_synthesizer_has_no_key_conditional() -> None:
    """`synthesize()` must not branch on a credential at all."""
    import inspect

    from intake import synthesize as mod

    src = inspect.getsource(mod.synthesize)
    assert "ANTHROPIC_API_KEY" not in src, (
        "synthesize() branches on ANTHROPIC_API_KEY again — that is latent metered spend on "
        "the weekly cron"
    )
    assert "_render_heuristic" in src
    assert not hasattr(mod, "_render_sonnet"), "the metered renderer is back"
    _ok("synthesize() has no credential branch; the metered renderer is gone")


TESTS = [
    test_no_metered_client_in_intake,
    test_scorer_is_heuristic_even_with_a_key_present,
    test_synthesizer_has_no_key_conditional,
]


def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    print("intake — no metered spend (ADR-0036)\n")
    failed = 0
    for t in TESTS:
        try:
            t()
        except AssertionError as e:
            failed += 1
            print(f"  FAIL {t.__name__}:\n       {e}")
    print()
    if failed:
        print(f"{failed}/{len(TESTS)} FAILED")
        return 1
    print(f"All {len(TESTS)} assertions pass — intake cannot spend metered tokens.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

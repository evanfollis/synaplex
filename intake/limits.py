"""Layer 1 per-source rate limits (ADR-0029 §Adversarial review response §6).

# Cap policy — what the code actually does (vs ADR-0029 §6 stated intent)

ADR-0029 §6 states: "Layer 1: max 200 raw items per source per day."

The shipping implementation is **per-source-per-fetch**, not per-day.
Each adapter run caps at 200 NEW items; the no-clobber/union-merge in
`intake.adapters.merge_jsonl_by_id` then merges those new items with the
existing daily file. Multiple cron firings per day (every 4h) can each
add up to 200 fresh items, so a daily file may exceed 200 when the
union of fetches contains more distinct content_ids than the cap.

Concrete: HN reaches ~450 items/day; arxiv ~200; rss ~200-205. None of
this corrupts data — the union is correct by-id — but it does deviate
from the literal ADR text.

Three possible reconciliations (principal call, see handoff
`runtime/.handoff/general-synaplex-cap-policy-decision-…`):

- **A**: post-merge truncate by score (requires `scored_at` plumbing)
- **B**: post-merge truncate by recency
- **C**: ratify per-fetch semantic + reframe ADR-0029 §6 wording, accept
  unbounded daily totals until Layer 2 reasoning consumes intake natively

Until that decision lands, the per-fetch cap stands as deployed. Call
sites (`adapters/*.py`) check `len(new_items) >= cap` mid-fetch and emit
`eventType: throttled` when overflow occurs at the FETCH boundary; they
do NOT throttle on post-merge totals exceeding 200.

The constant name retains its historical wording (referenced by other
documentation); a new name aliases it for clarity at call sites.
"""

from __future__ import annotations

# Historical name kept for backward-compat with prior docs/handoffs.
LAYER1_MAX_ITEMS_PER_SOURCE_PER_DAY = 200

# Clearer name: this is enforced PER-FETCH, not PER-DAY (see module docstring).
LAYER1_MAX_ITEMS_PER_FETCH = LAYER1_MAX_ITEMS_PER_SOURCE_PER_DAY

# Layer 2 caps (proposed, not yet enforced — Layer 2 reasoning is not built).
LAYER2_MAX_CANDIDATES_PER_BEAT_PER_DAY_BOOTSTRAP = 5
LAYER2_MAX_CANDIDATES_PER_BEAT_PER_DAY_STEADY = 10


def layer1_cap() -> int:
    """Return the per-fetch cap. See module docstring for the per-fetch
    vs per-day reconciliation question."""
    return LAYER1_MAX_ITEMS_PER_FETCH

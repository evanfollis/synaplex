---
name: synaplex current state
description: Front door for the synaplex.ai system — publication + evaluation lab + operational pipeline. Read first every session.
updated: 2026-04-29T15:35Z (post-reflection: friction `timestamp` field + S3-P2 gate covers exceptions)
owner: executive (principal: evan)
phase: rebrand landed; Layer 1 intake running autonomously on systemd timers
---

# synaplex — current state

## One-line status

Repo rebranded from `agentstack` → `synaplex` per ADR-0027. Layer 1
intake subsystem (ADR-0029) shipped first pass: RSS + arxiv + HN
adapters, dual-provider (heuristic / Sonnet) scoring for the
`agent-platforms` beat, daily digest, weekly synthesis + `latest.md`
symlink, friction event log, systemd unit files authored. Synthesis
briefing is auto-injected into workspace-root executive sessions via
the amended `/opt/workspace/CLAUDE.md` context-always-load block.
First pipeline run produced 2026-04-23 digest (17 items) and 2026-W17
synthesis (1.7KB). 2026-04-24 digest rendered (11 items — Anthropic feed
removed from list after 404 confirmed, see below). Systemd timers
**confirmed active** via `systemctl list-timers`: synaplex-intake
(4h), synaplex-score (hourly), synaplex-digest (daily 06:57Z),
synaplex-synthesize (Sun 04:07Z), synaplex-integrity (daily 04:37Z)
— all emit `sourceType: "cron"` correctly.

## Commits on this repo

```
d538038  Update CURRENT_STATE at session end — all Week 0-2 work landed
9aa35b7  Scaffold Astro site (Week 1 Track 3) — landing, lab, editorial, directory
e09e6e3  Pre-register memory-systems-v1 lab eval (first canon-native emission)
61aa752  Scaffold agentstack — publication + evaluation lab (Week 0)
```

Rebrand commits on this handoff land on top of the above; see `git log`.

Cross-repo work preserved:
- `atlas@1d627c3` — canon adapter + .canon/ backfill (47 Claims + 123
  Evidence + 82 EventLogEntries + 1 Policy; 97/97 tests passing).
- `skillfoundry-harness@4d6050d` — canon adapter code (51/51 tests passing).
- `skillfoundry-valuation-context@dcfd7e4` — canon envelopes backfill.
- `supervisor` — ADR-0027 accepted, ADR-0029 proposed, session + projects
  registered.

## Live canon envelope counts

| Domain | Claims | Evidence | Events | Policies | Total |
|---|---|---|---|---|---|
| atlas | 47 | 123 | 82 | 1 | 253 |
| skillfoundry-valuation-context | 3 | 3 | 4 | 1 | 11 |
| synaplex/lab | 1 | 0 | 0 | 0 | 1 |

Extraction of L2 `discovery-runtime` remains correctly deferred until
synaplex has executed several evals.

## What's in flight

- **Layer 1 intake (this handoff)**: RSS + arxiv + HN adapters, per-beat
  scoring for `agent-platforms`, daily digest, friction event emission,
  systemd unit files authored. First digest due within 24h of handoff.
- **memory-systems-v1 first lab execution**: pre-registration live at
  `lab/.canon/claims/b7ff216f4eec6e58.json` (immutable — id and
  methodology hash preserved through the rebrand). Execution scheduled
  Week 6; eval-running code not yet written.
- **Site deploy**: `site/dist/` builds locally; deploy to `synaplex.ai`
  (or staging subdomain) is a separate handoff.

## What's next (deployable)

1. **Site deploy handoff**: per ADR-0027 deploy target is `synaplex.ai`
   (apex or `www.synaplex.ai`); CF zone already provisioned. Principal
   confirmation before final DNS cut-over.
2. **Layer 2 reasoning (subsequent handoff)**: per-beat daily job that
   loads pod canon state + intake synthesis and writes candidate
   envelopes to pod `.canon/candidates/`.
3. **Podcast + Reddit + GitHub + Substack intake** (wave 2).
4. **First eval execution** (memory-systems-v1, Week 6 per plan).

Resolved this turn (three <30min fixes from reflection's P1–P3):
- ✓ RSS feed URL now named inline in friction event `extra.failing_feeds`.
- ✓ Failing Anthropic feed (`/news/rss.xml` → 404) removed from
  `beats.py` with a comment explaining rediscovery probe.
- ✓ `throttled` eventType added (`friction.py`); cap hits on rss +
  arxiv + hn now emit `throttled` not `failure`.
- ✓ `layer1_cap()` applied to arxiv + HN for symmetry.

## Known infra gotchas

- **Node.js is v20.20.2; Astro 6 requires 22.12+.** Site pinned to Astro
  5 / Tailwind 3 / `@astrojs/tailwind` 6 for Node-20 compatibility.
  Upgrade path: install Node 22 via nvm before bumping Astro.
- **Cloudflare Pages deploy** still requires principal authorization for
  the CF API call (same blocker as the original agentstack handoff).
- **Canon envelope rebrand**: the memory-systems-v1 Claim retains
  `emitter: "L3:synaplex"` and `instance_id: "synaplex"` after edit;
  id `b7ff216f4eec6e58` preserved (id hashes the statement, not
  emitter); methodology.md left untouched to preserve ArtifactPointer
  hash. The one `agentstack.dev/lab/memory-systems-v1` URL inside
  methodology.md is now a historical reference — pre-registration
  immutability means we don't edit it retroactively.
- **No GitHub remote yet.** Handoff suggests `evanfollis/synaplex`;
  creation deferred to explicit principal confirmation.

## Gates (carried from approved plan, updated for synaplex framing)

- **Week 4**: atlas adapter valid on all 47 hypotheses ✓; Layer 1
  intake running ≥10 consecutive days (new gate, in flight); first
  daily digest shipped.
- **Week 8**: first eval published with canon ledger entry; site
  deployed; ≥3 editorial pieces live.
- **Week 12**: 2 evals published; Layer 2 reasoning promoting candidate
  envelopes at steady cadence.
- **Week 26**: ≥6 evals; L2 runtime extraction re-evaluated.

## Active risks

- **Site unreachable** (no deploy yet → no audience → no feedback).
  Mitigation: site deploy handoff (separate from this one).
- **First-eval methodology credibility**: methodology drafted;
  adversarial review has not yet run. Must route through
  `supervisor/scripts/lib/adversarial-review.sh` before any result
  publishes.
- **Intake dedup drift**: multiple adapters write to
  `runtime/intake/raw/`. S1-P3 rule: shared content-hash helper is the
  single dedup contract. Any adapter that short-cuts this produces
  silent corruption across joins.
- **Silent layer rule (S3-P2)**: every layer must emit typed friction
  events for success + failure + stuck + escalated + throttled states. A
  layer that only emits on the happy path is indistinguishable from stuck.

## Truth sources (non-transcript)

- `supervisor/decisions/0027-synaplex-is-the-system.md` — accepted
  governance ADR (supersedes ADR-0026).
- `supervisor/decisions/0029-synaplex-loop-five-layer-pipeline.md` —
  proposed operational pipeline.
- `supervisor/projects/products/synaplex.md` — shaping surface.
- `/opt/workspace/projects/context-repository/spec/discovery-framework/`
  — L1 canon (v0.1.0, frozen).
- `lab/.canon/` — this repo's canon envelope store.
- `runtime/intake/` — Layer 1 raw + scored + digest + synthesis surface.
- `/opt/workspace/runtime/friction/events.jsonl` — cross-layer typed-event log (workspace-level path).

## Pending principal actions

(carried forward across turns — session handoff file has more detail)

1. ~~context-always-load cap collision~~ — **RESOLVED 2026-04-25T15:50Z**:
   `active-issues.md` has been trimmed from ~24KB to 3.8KB (likely
   archived to a separate file by the principal/supervisor session).
   Empirical hook check: aggregate is now 29.6KB total across all 7
   files, no truncation, synthesis injects. The original URGENT was
   archived to `runtime/.handoff/ARCHIVE/2026-04-25/`. Left here for
   one cycle as a trail.
2. **GitHub remote name confirmation** — handoff suggests
   `evanfollis/synaplex`; repo creation is irreversible external action
   so awaits explicit confirmation.
3. **Cloudflare Pages deploy authorization** (carries over).
4. **Kernel reboot** — 6.8.0-110 installed, still running 6.8.0-107.
5. ~~Layer 1 systemd timer enable~~ — **RESOLVED**: timers were
   enabled after the original handoff; `systemctl list-timers`
   confirms all five are active (intake 4h, score hourly, digest
   daily 06:57Z, synthesize Sun 04:07Z, integrity daily 04:37Z).
   Left here for one cycle as a trail.
6. **ANTHROPIC_API_KEY provisioning** — intake currently runs on the
   heuristic scorer (no LLM calls). When the key lands in
   `runtime/.secrets/synaplex.env`, the Sonnet scorer + Sonnet
   synthesizer activate automatically at the next cron firing.

## Known broken or degraded
(updated 2026-04-29T14:30Z — reflection pass)

- ~~`layer1_cap()` not applied to arxiv/hackernews adapters~~ **FIXED**
  this turn — `layer1_cap()` now applied symmetrically in all three
  adapters; cap hits emit `eventType: throttled`.
- ~~RSS feeds emit `eventType: failure` for expected cap-hit
  truncation~~ **FIXED** this turn — new `throttled` eventType in
  `friction.py`; meta-scan's failure channel stays clean.
- ~~One RSS feed fails on every run~~ **FIXED** this turn —
  `https://www.anthropic.com/news/rss.xml` returns 404, removed from
  `beats.py` with rediscovery note. `rss.py` now names the failing
  feed URLs inline in the friction event's `extra.failing_feeds`
  field so future regressions are actionable from the log alone.
- ~~`score:stuck` at midnight~~ **FIXED** 2026-04-25T15:50Z, **CONFIRMED** 2026-04-26T00:21Z —
  `synaplex-score.timer` shifted to `OnCalendar=*-*-* *:20:00`; score now lags
  intake's :18 firing by ~3 minutes. No `stuck` event at 2026-04-26T00:01Z —
  fix verified working on first midnight after deployment.
- ~~synthesis-translator emits malformed ISO timestamps~~ **FIXED** in supervisor session 2026-04-25 —
  `supervisor/scripts/lib/synthesis-translator.sh` now uses separate `ISO_FILENAME` (dashes,
  for file paths) and `ISO_TS` (colons, for JSON `ts` field). Confirmed by 2026-04-25T15:42:22Z
  friction event carrying valid ISO 8601 timestamp.
- ~~Heuristic weekly synthesis has duplicate items~~ **FIXED** 2026-04-27T05:05Z —
  `_gather_week` now dedupes by `content_id` (highest-scoring instance wins on
  collision). Verified: today's gather returns 985 items, 985 distinct IDs.
- ~~arxiv adapter destroys daily data on stuck runs~~ **FIXED** 2026-04-27T05:05Z —
  no-clobber discipline applied to all three adapters via shared
  `intake.adapters.merge_jsonl_by_id` helper. Adapters now collect new items
  in memory, merge with existing file by `content_id`, and write atomically.
  Empty fetch + existing content → file preserved (verified manually:
  arxiv-2026-04-27.jsonl held at 100 items through a "0 new" run that
  previously would have destroyed it). IngestResult dataclass extended with
  `total` and `preserved` fields; CLI + friction events report new/preserved/
  total. arxiv-2026-04-26.jsonl is permanently lost (collected destruction
  occurred before the fix).
- ~~S3-P2 escalation gate missing~~ **FIXED** 2026-04-29T03:05Z — `intake/escalation.py`
  ships per-source consecutive-stuck counters; arxiv/rss/hackernews emit
  `eventType: escalated` after 3 consecutive stuck events (and every 3rd thereafter).
  Reset on success. Smoke-tested. Counters at `runtime/intake/.state/`.
- **RSS merged file exceeds 200-item cap** — rss-2026-04-28.jsonl holds 202 items against
  declared 200-item cap. Root cause: `layer1_cap()` is applied to the incoming fetch, not to
  the post-merge total. arxiv now likewise grows past 200 with the new union semantics
  (200 in arxiv-2026-04-29 after two cron runs). Pending principal decision on truncation
  policy (score vs. recency) before mechanical fix lands. See handoff
  `runtime/.handoff/general-synaplex-cap-and-review-followups-2026-04-29T03-10Z.md`.
- **HN daily file accumulates beyond 200-item cap** — reached 409 items by end-of-day Apr 28.
  Same root cause and same pending principal decision as above.
- **Adversarial review §4 §6 §7 carried forward** — review of commit 5814658 surfaced four
  larger design issues beyond the §1+§2+§3 fixes that landed: §4 file lock for concurrent
  writers, §6 day-boundary race on the 00:17 cron, §7 `_gather_week` rubric-drift tiebreak
  (currently "highest-score wins" which can amplify scorer changes; should be
  "newest-scored-at wins" once `scored_at` is plumbed). All low priority while
  scoring is heuristic-only and there is one writer per source. See handoff above.
- ~~S3-P2 escalation gate does not cover network failures~~ **FIXED**
  2026-04-29T15:35Z — arxiv + hackernews exception handlers now also call
  `record_stuck()` and emit `escalated` if the threshold is crossed.
  RSS's per-feed errors don't short-circuit the function; the all-feeds-
  fail case still routes through the existing stuck path which already
  counts. Semantic widened to "consecutive stuck OR exception".
- ~~Friction log missing `timestamp` field (schema violation)~~ **FIXED**
  2026-04-29T15:35Z — `intake/friction.py` now emits both `ts` (ISO,
  human-readable) and `timestamp` (epoch-ms integer, workspace minimum
  event shape per CLAUDE.md §Telemetry events). Additive change; existing
  consumers continue working, time-windowed consumers now see the field.
  Verified live: latest event carries `timestamp: 1777476699109`.

## What the next agent must read first

1. This file.
2. `/opt/workspace/runtime/friction/events.jsonl` — live evidence of what the pipeline is actually doing. Read before touching any adapter or friction emitter. Note: this is workspace-level, not repo-local.
3. `intake/README.md` — Layer 1 boundary semantics; includes systemd enable instructions and data layout.
4. Latest reflection at `/opt/workspace/runtime/.meta/synaplex-reflection-2026-04-29T14-30-01Z.md` — escalation gate gap (network failures not counted); friction `ts`/`timestamp` schema mismatch (time-windowed queries broken); cap policy still pending principal decision.
5. **always-load cap collision**: RESOLVED 2026-04-25T15:50Z — `active-issues.md` trimmed to 3.8KB, aggregate 29.6KB (no truncation). URGENT archived.

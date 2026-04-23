---
name: synaplex current state
description: Front door for the synaplex.ai system — publication + evaluation lab + operational pipeline. Read first every session.
updated: 2026-04-23
owner: executive (principal: evan)
phase: rebrand landed; Layer 1 intake first pass in flight
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
First pipeline run produced 2026-04-23 digest (17 items through
cutoff; top at 0.86 "Unrolling the Codex agent loop") and 2026-W17
synthesis (1.7KB). Systemd timers NOT enabled (pending operator
coordination).

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

1. **Complete Layer 1 first pass**: adapters running on timer, daily
   digest written, friction events accumulating.
2. **Site deploy handoff**: per ADR-0027 deploy target is `synaplex.ai`
   (apex or `www.synaplex.ai`); CF zone already provisioned. Principal
   confirmation before final DNS cut-over.
3. **Layer 2 reasoning (subsequent handoff)**: per-beat daily job that
   loads pod canon state + intake synthesis and writes candidate
   envelopes to pod `.canon/candidates/`.
4. **Podcast + Reddit + GitHub + Substack intake** (wave 2).
5. **First eval execution** (memory-systems-v1, Week 6 per plan).

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
  events for success + failure + stuck + escalated states. A layer
  that only emits on the happy path is indistinguishable from stuck.

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
- `runtime/friction/events.jsonl` — cross-layer typed-event log.

## Pending principal actions

(carried forward across turns — session handoff file has more detail)

1. **context-always-load cap collision (URGENT)** —
   `/opt/workspace/CLAUDE.md` always-load aggregate is ~49KB vs the 30KB
   hook cap. `active-issues.md` alone is 24KB. Synthesis amendment did
   NOT cause the collision (was pre-existing) but escalation rule says
   URGENT when touched. See
   `runtime/.handoff/URGENT-synaplex-always-load-cap-collision-2026-04-23T17-35Z.md`.
   Principal decision needed: trim active-issues (recommended) or raise
   hook cap.
2. **GitHub remote name confirmation** — handoff suggests
   `evanfollis/synaplex`; repo creation is irreversible external action
   so awaits explicit confirmation.
3. **Cloudflare Pages deploy authorization** (carries over).
4. **Kernel reboot** — 6.8.0-110 installed, still running 6.8.0-107.
5. **Layer 1 systemd enable** — timer units authored but
   `systemctl enable --now` requires coordination with supervisor per
   handoff constraint. Without enable, intake + score + digest +
   synthesize must run manually.
6. **ANTHROPIC_API_KEY provisioning** — intake currently runs on the
   heuristic scorer (no LLM calls). When the key lands in
   `runtime/.secrets/synaplex.env`, the Sonnet scorer + Sonnet
   synthesizer activate automatically at the next cron firing.

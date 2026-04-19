---
name: Agentstack current state
description: Front door for the agentstack publication + evaluation lab. Read first every session.
updated: 2026-04-19
owner: executive (principal: evan)
phase: week-0-to-week-2 / scaffold complete, site built local, deploy pending
---

# Agentstack — current state

## One-line status

Scaffold + governance + canon adapters (atlas + skillfoundry) + first lab Claim + Astro site all shipped 2026-04-19. Deploy to `agentstack.pages.dev` blocked on principal permission for Cloudflare Pages API call.

## Commits on this repo

```
9aa35b7  Scaffold Astro site (Week 1 Track 3) — landing, lab, editorial, directory
e09e6e3  Pre-register memory-systems-v1 lab eval (first canon-native emission)
61aa752  Scaffold agentstack — publication + evaluation lab (Week 0)
```

Cross-repo commits landed this session:
- `atlas@1d627c3` — canon adapter + .canon/ backfill (47 Claims + 123 Evidence + 82 EventLogEntries + 1 Policy; 16 new tests; 97/97 total passing)
- `skillfoundry-harness@4d6050d` — canon adapter code (12 new tests; 51/51 total passing)
- `skillfoundry-valuation-context@dcfd7e4` — canon envelopes backfill (3+3+2+4+1)
- `supervisor@78a88ae` — ADR-0026 accepted + `projects/products/agentstack.md` shaping file

## Live canon envelope counts

| Domain | Claims | Evidence | Events | Policies | Total |
|---|---|---|---|---|---|
| atlas | 47 | 123 | 82 | 1 | 253 |
| skillfoundry-valuation-context | 3 | 3 | 4 | 1 | 11 |
| agentstack/lab | 1 | 0 | 0 | 0 | 1 |

**L2 runtime extraction gate (per ADR-0026)**: requires ≥50 envelopes each across all three domains. Atlas is over; skillfoundry at 11; agentstack at 1. Extraction correctly deferred — stays deferred until agentstack has executed 6–8 evals.

## What's in flight

- **First lab execution (memory-systems-v1)**: pre-registration is live at `lab/.canon/claims/b7ff216f4eec6e58.json`. Methodology at `lab/evals/memory-systems-v1/methodology.md` hash-bound. Execution is Week 6 (per plan); eval-running code not yet written.
- **Site deploy**: `site/dist/` builds cleanly (6 pages + sitemap). Deploy command blocked by Bash permission guard — awaiting principal authorization.

## What's next (deployable)

1. **Deploy site to `agentstack.pages.dev`** (blocked on principal permission):
   ```bash
   export CLOUDFLARE_API_TOKEN="$(cat /opt/workspace/runtime/.secrets/cloudflare_api_token)"
   cd /opt/workspace/projects/agentstack/site
   npm install  # node_modules is gitignored — reinstall from package-lock.json
   npm run build
   npx wrangler pages project create agentstack --production-branch main
   npx wrangler pages deploy ./dist --project-name agentstack --branch main
   ```

2. **Custom domain** `agentstack.dev` (blocked on principal cost confirmation ~$12/yr):
   - Register via CF Registrar API or dashboard
   - Attach to the Pages project via API

3. **Newsletter integration**: replace Buttondown stub with real user. Set `PUBLIC_BUTTONDOWN_USER` env var at build time (default placeholder is `agentstack`).

4. **Editorial**:
   - Author first 3 seed deep-dives (drafted agentically + principal review). Topics pre-declared in `/editorial/` landing.
   - Stand up daily news scan under `scan/` — agentic cron feeding HN / r/LocalLLaMA / arxiv agents / tracked GitHub repos.

5. **First eval execution (Week 6)**: build the eval runner under `lab/evals/memory-systems-v1/`. Run N≥10 × 4 systems × 5 tasks. Write transcripts hash-bound into Evidence envelopes.

## Known infra gotchas

- **Node.js is v20.20.2; Astro 6 requires 22.12+.** Current site is pinned to Astro 5 / Tailwind 3 / `@astrojs/tailwind` 6 for Node-20 compatibility. Upgrade path: install Node 22 via nvm before bumping Astro.
- **Bash permission guard** gated the initial CF Pages API call even though ExitPlanMode approved it. Next session either: (a) re-prompt with explicit "deploy it" language in-turn, (b) adjust `.claude/settings.json` Bash permissions durably.
- **skillfoundry probe outlier**: `probes/preflight-distribution-signal.md` uses prose/bold format instead of the canonical backtick-header. Adapter is strict — skillfoundry PM needs to reformat that one file.

## Gates (from approved plan)

- **Week 4**: atlas adapter valid on all 47 hypotheses ✓ (landed this session); editorial daily scan running ≥10 consecutive days (not started); ≥300 newsletter signups (not started — site not yet deployed).
- **Week 8**: first eval published with canon ledger entry; ≥1000 subs; ≥3 editorial pieces live.
- **Week 12**: 2 evals published; ≥2000 subs; ≥5 sponsor conversations opened.
- **Week 26**: ≥5000 subs; ≥6 evals; ≥$3k/mo revenue; L2 extraction evaluation complete.

## Active risks

- **Site unreachable** (no deploy yet → no audience → no feedback). Mitigation: principal authorization for deploy unblocks Week 3 editorial cadence.
- **Competitor timing**: "harness engineering" vocabulary is young; window is ~12 months. Editorial content pipeline needs to start producing so brand presence begins compounding.
- **First-eval methodology credibility**: per plan, pre-register → execute → adversarial review → publish. Methodology drafted; adversarial review has not yet run. Must route through `supervisor/scripts/lib/adversarial-review.sh` before any result publishes.

## Truth sources (non-transcript)

- `/root/.claude/plans/calm-squishing-peacock.md` — approved plan
- `supervisor/decisions/0026-agentstack-lab-third-canon-instance.md` — governance ADR
- `supervisor/projects/products/agentstack.md` — shaping surface
- `/opt/workspace/projects/context-repository/spec/discovery-framework/` — L1 canon (v0.1.0, frozen)
- `lab/.canon/` — this repo's canon envelope store
- Git history: agentstack, atlas, skillfoundry-harness, skillfoundry-valuation-context, supervisor

## What pending principal actions are outstanding

(carried forward across turns — session handoff file has more detail)

1. **Deploy authorization** for Cloudflare Pages API calls (see "What's next" item 1).
2. **Kernel reboot** — still on 6.8.0-107; 6.8.0-110 installed (see `supervisor/system/verified-state.md`).
3. **`agentstack.dev` domain registration** — ~$12/yr, optional; `agentstack.pages.dev` works for first deploy.
4. **Tally form for Preflight Pro waitlist** — unchanged from earlier turns; not blocked by agentstack.

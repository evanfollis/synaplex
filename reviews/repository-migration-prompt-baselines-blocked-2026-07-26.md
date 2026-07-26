# Repository migration prompt baselines — blocked by subscription availability

Date: 2026-07-26  
Disposition: `BLOCKED_PROVIDER_AVAILABILITY`  
Baseline mutation: none

The July 2026 repository and lineage migration requires all governed prompt
baselines to pass a fresh, no-cache release before public deployment or
predecessor-repository changes. The required runs were attempted with metered
credential variables removed and the shared subscription-CLI fallback harness.

## Receipts

- `artifact-delivery-v2-method-review`:
  `run-20260726T201056Z-5b739c`. Claude Opus timed out after the configured
  45-second bound; Codex gpt-5.4 fallback also timed out after 45 seconds.
- `cross-domain-conjecture-v2`:
  `run-20260726T201237Z-10bc38`. Claude Sonnet timed out after 45 seconds;
  Codex was skipped because the immediately preceding timeout had opened its
  availability circuit.
- `synaplex-charter`:
  `run-20260726T201330Z-4bfbeb`. Many fresh Claude executor and judge calls
  succeeded. The run stopped when Claude reported its subscription session
  limit; Codex remained inside its timeout circuit cooldown.

Primary per-call receipts are append-only under
`runtime/prompteval/.provenance/<run-id>.jsonl`. They include provider, model,
status, latency, fallback source, run, prompt, case, role, and trial. The durable
circuit state is `runtime/.prompteval/circuit-breaker.json`.

`prompteval check .` therefore still reports the pre-existing 17 baseline
contract findings. No cached result, manual baseline rewrite, model substitution,
or metered API key was used. Holdouts and frozen study inputs were not opened or
edited.

## Delivery boundary

The migration implementation is committed to a non-main branch for durability.
Cloudflare deployment, `main` promotion, GitHub metadata/security mutation,
predecessor README changes, and predecessor archival remain blocked until fresh
passing releases make `make check` green. The typed lineage records honestly
remain `archive-planned`; they are not represented as live or archived.

Phase B remains `BLOCKED_PRE_ENTRY`. This availability receipt is operational
evidence only and creates no Claim, Evidence, Decision, finding, or study result.

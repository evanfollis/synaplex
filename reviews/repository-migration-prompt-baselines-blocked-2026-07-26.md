# Repository migration prompt baselines — capacity recovered; scientific gate blocked

Date: 2026-07-26  
Disposition: `BLOCKED_FROZEN_PHASE_A_CONTRACT`
Baseline mutation: two unaffected baselines refreshed; artifact-delivery baseline absent

The July 2026 repository and lineage migration requires all governed prompt
baselines to pass a fresh, no-cache release before public deployment or
predecessor-repository changes. The required runs were attempted with metered
credential variables removed and the shared subscription-CLI fallback harness.

## Initial provider-availability receipts

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

These receipts remain the historical reason for the first blocked handoff. They
were not treated as scientific outcomes.

## Reentry release receipts

After circuit cooldown, an absolute-path Codex subscription probe using
`gpt-5.4` succeeded. The governed executor bounds were corrected from the stale
45-second setting to 180 seconds, with explicit `gpt-5.4` fallback and durable
timeout/empty-response circuit behavior. No metered key was present.

- `cross-domain-conjecture-v2`:
  `run-20260726T223212Z-fc15f1`, 14/14 pass, aggregate 1.0, both holdouts
  passed; baseline refreshed at `pv-38258c6e2891c210`.
- `synaplex-charter`:
  `run-20260726T223736Z-d8648e`, 14/14 pass, aggregate 1.0, both holdouts
  passed; baseline refreshed at `pv-672b0c68035e587d`.
- `artifact-delivery-v2-method-review-v2`:
  the old never-baselined contract was retired with its cases and old holdout
  byte-preserved. Active-case iterations were preserved in run receipts. When
  the exact frozen Phase A files and canon envelopes were supplied as one
  self-contained active record, fresh run
  `run-20260726T221835Z-864f2c` passed 9/10 and correctly rejected that record.

The opposing review identified four material frozen-contract defects:

1. `artifact.schema.json` permits an `aborted` run containing three
   `complete`, classified samples.
2. Archive acknowledgements are not structurally required to cover raw objects
   bijectively by URI, digest, and byte length.
3. The provisioner and executor monotonic clock domain is not frozen as shared
   or translated into the executor epoch.
4. Mandatory raw streams and empty-stream placeholders are stated in prose but
   are not enforced by the frozen schema.

The migration did not edit methodology, fixture contract, artifact schema,
frozen-input manifest, canon Claim/Policy, or any subject state. A baseline
rewrite, cached result, holdout edit, model substitution, or gate weakening was
not used. `prompteval check .` now fails only because
`artifact-delivery-v2-method-review-v2` has no accepted baseline.

## Delivery boundary

The migration implementation and reentry evidence are committed to a non-main
branch for durability.
Cloudflare deployment, `main` promotion, GitHub metadata/security mutation,
predecessor README changes, and predecessor archival remain blocked until fresh
passing releases make `make check` green. The typed lineage records honestly
remain `archive-planned`; they are not represented as live or archived.

Phase B remains `BLOCKED_PRE_ENTRY`. These eval receipts are review/control-plane
evidence only and create no Claim, Evidence, Decision, finding, or study result.

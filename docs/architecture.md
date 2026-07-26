# Synaplex repository architecture

Synaplex is a flat, multi-surface research system, represented by the
`monorepo` profile in `repo.toml`. It is not a single Python service.

## Authority and flow

1. `sources/` stores typed SourceObservation inputs.
2. `reasoning/` may produce conjectures and Programme-local drafts. Neither is
   canon.
3. `lab/` owns preregistration, measurement tooling, frozen study inputs, and
   typed canon validation.
4. `lab/.canon/` is the scientific authority boundary. Only the existing legal
   transition path may write it.
5. `knowledge/` produces a default-deny public projection. It cannot emit canon.
6. `site/` renders the public projection. Its JSON copies are packaging outputs,
   never additional authorities.
7. `intake/` and `integrity/` operate the runtime signal and guard surfaces.

Sources, conjectures, engineering cases, historical lineage, Claims, Evidence,
Decisions, and findings remain distinct types. A finding requires an accepting
Decision that cites existing Evidence for the same Claim. Zero findings is a
valid and currently truthful state.

## Generated artifacts

`knowledge/public-projection.json` is the only tracked authoritative generated
projection. `scripts/prepare_site_projection.py` verifies that file against its
JSON Schema and makes byte-identical, ignored packaging copies under
`site/src/data/` and `site/public/` immediately before an Astro build.

## Runtime configuration

`synaplex_paths.py` provides compatible defaults for the current host while
supporting `SYNAPLEX_REPO_ROOT`, `WORKSPACE_ROOT`, `SYNAPLEX_RUNTIME_ROOT`,
`SYNAPLEX_SUPERVISOR_ROOT`, and `SYNAPLEX_CONTEXT_REPOSITORY_ROOT`. Deployment
launchers use those variables and absolute subscription CLI paths. The current
root service identity is retained as a dated compatibility exception; moving it
to a dedicated user requires a separately reviewed operational migration.

## Commands

`make help` lists stable commands. `make check` composes lint, scoped static
typing, deterministic tests, prompt-baseline contract checks, site build, and
deployment-source validation. It does not run models or automate scientific
state transitions.

## Deployment and rollback

Cloudflare Pages deploys only a built `site/dist`. Versioned `*-v2.service`
sources are canaried before replacing installed units. Rollback is the prior
unit file plus `systemctl daemon-reload`; no canary writes canon.

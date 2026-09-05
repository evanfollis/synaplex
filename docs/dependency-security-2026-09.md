# Dependency security closure — September 2026

## Scope

GitHub Dependabot reported two open high-severity npm alerts on the default
branch on 2026-09-05. Both were transitive runtime dependencies in
`site/package-lock.json`; neither required an application dependency or
framework major change.

| Alert | Advisory | Dependency path | Vulnerable | Patched lock |
|---|---|---|---|---|
| #21 | `GHSA-5p4m-2wfm-xmqj` | Astro / internal helpers → `js-yaml` | 4.3.0 | 4.3.2 |
| #23 | `GHSA-2v37-7h3g-55p8` / `CVE-2026-67213` | Tailwind Vite → Vite → PostCSS → `nanoid` | 3.3.16 | 3.3.18 |

The `js-yaml` advisory covers versions 4.0.0 through 4.3.0 and fixes in
4.3.1. The `nanoid` advisory covers versions below 3.3.18. Existing parent
ranges accept the patched releases, so the remediation updates only the two
resolved lockfile nodes and their integrity metadata.

## Verification

Node 24.18.0 and npm 11.16.0 performed a clean `npm ci --ignore-scripts` from
the updated lockfile. `npm audit --omit=dev` then reported zero vulnerabilities,
and `npm ls js-yaml nanoid --all` resolved one deduplicated `js-yaml@4.3.2`
and `nanoid@3.3.18` through the paths above.

The full repository `make check` passed: Ruff, mypy, 54 unittests, the typed
quarantined-experiment guard, 10 subscription-launcher assertions, all 19
canon conformance fixtures, Programme and canon guards, two accepted prompt
baseline contracts, the zero-finding public projection, a 24-page Astro build,
and deployment-contract validation.

No research artifact, frozen input, Claim, Policy, prompt baseline, or
quarantine disposition changed.

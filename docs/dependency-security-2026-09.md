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

---

## Second batch — 2026-09-11

### Scope

GitHub Dependabot reported six open alerts on 2026-09-11: two critical Astro
alerts (GHSA-26w7-cxv4-gfx2, GHSA-376h-93r7-7g6f) and one high SVGO alert
(GHSA-w27v-7q3p-w38r, GHSA-4vpr-x523-8j87) plus three medium alerts, all
rooted in `astro ≤7.2.7` and `svgo 4.0.0–4.0.2`. A separate high alert
covered `sharp <0.35.4` (GHSA-rgj7-g3m4-5g8c).

The repository resolved astro 7.1.3, svgo 4.0.2, and sharp 0.35.3.

| Alert | Advisory | Dependency | Vulnerable | Patched |
|---|---|---|---|---|
| critical | `GHSA-26w7-cxv4-gfx2` | `astro` | ≤7.2.7 | 7.3.2 |
| critical | `GHSA-376h-93r7-7g6f` | `astro` | ≤7.2.7 | 7.3.2 |
| high | `GHSA-w27v-7q3p-w38r` | `svgo` | 4.0.0–4.0.2 | 4.1.0 |
| high | `GHSA-4vpr-x523-8j87` | `svgo` | 4.0.0–4.0.2 | 4.1.0 |
| high | `GHSA-rgj7-g3m4-5g8c` | `sharp` | <0.35.4 | 0.35.4 |

### Approach

A single direct-dependency upgrade (`astro` 7.1.3 → 7.3.2 in
`site/package.json`) was sufficient. Astro 7.3.2 requires `svgo ^4.0.1`
and optional `sharp ^0.35.4`, so `npm install` followed by `npm update svgo`
resolved both transitive vulnerabilities without separate lockfile overrides.

Transitive shifts from the Astro 7.1.3 → 7.3.2 upgrade (all Astro-internal
packages; no application-layer or observable behavior change):

| Package | Before | After |
|---|---|---|
| astro | 7.1.3 | 7.3.2 |
| svgo | 4.0.2 | 4.1.0 |
| sharp / @img/sharp-* | 0.35.3 | 0.35.4 |
| undici | 5.x / 8.0.4 | 8.10.2 |
| Several internal Astro-ecosystem packages | various | updated with Astro |

`@astrojs/mdx@7.0.3` (`astro ^7.0.0`) and `@astrojs/sitemap@3.7.3` are
compatible with astro 7.3.2 without changes.

### Verification

Node 24.18.0 / npm 11.16.0 clean install. `npm audit --audit-level=moderate`
reported zero vulnerabilities.

The full repository `make check` passed under Node 24.18.0: Ruff, mypy, 54
unittests, the typed quarantined-experiment guard, 10 subscription-launcher
assertions, all 19 canon conformance fixtures, Programme and canon guards, two
accepted prompt baseline contracts, the public projection (v1.3.0,
`sha256:4ae99babff63e92c607978f80e18a89c235868fd91b2bbf1a21c104945585e98`, 0
findings), a 24-page Astro build, and deployment-contract validation.

No research artifact, frozen input, Claim, Policy, prompt baseline, or
quarantine disposition changed. The public projection digest and zero-findings
state are identical to the pre-upgrade build.

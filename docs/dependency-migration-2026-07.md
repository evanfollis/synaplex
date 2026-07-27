# July 2026 dependency migration

This receipt records the deliberate consolidated upgrade of the public site and
Python repository gates. It is a maintenance result, not scientific Evidence.

## Adopted runtime and packages

- Node 24 LTS locally and in GitHub CI; `site/package.json` constrains the site
  build to Node 24.
- Astro 7.1.3, `@astrojs/mdx` 7.0.3, and `@astrojs/sitemap` 3.7.3.
- Tailwind CSS 4.3.3 and `@tailwindcss/vite` 4.3.3. The deprecated
  `@astrojs/tailwind` integration was removed.
- Ruff 0.16.0 and mypy 2.3.0.
- Range-compatible transitive security updates to sharp 0.35.3 and svgo 4.0.2.
  The consolidated lock also contains devalue 5.8.2 and postcss 8.5.23.

## Breaking-change assessment

Astro 7 moves the site to Vite 8 and removes or changes deprecated interfaces.
This static site does not use the removed database, transition-internals,
container-renderer, or reserved `src/fetch.ts` paths. Its production build is
therefore covered by the normal static-output route inventory.

Astro documents the Tailwind Vite plugin as the preferred Tailwind 4 path and
the old Astro integration as deprecated. Tailwind 4 replaces the `@tailwind`
directives with a CSS import and raises its browser floor to Safari 16.4,
Chrome 111, and Firefox 128. The site uses no Tailwind utility classes whose
names or semantics changed. Retaining Tailwind Preflight was necessary to
preserve the existing reset and presentation.

Ruff 0.16 expands its default rules substantially and changes Markdown
formatting behavior. Synaplex selects only `E9`, `F63`, `F7`, and `F82`, excludes
the governed eval corpus, and does not invoke `ruff format`; the expanded
defaults and Markdown formatter therefore do not silently broaden the gate.
The upgraded binary passed the complete repository lint target.

Mypy 2.x drops Python 3.9 as a host runtime and changes several defaults,
including local partial types and strict bytes. Synaplex already requires and
checks Python 3.12, and mypy 2.3.0 passed the maintained publication and
configuration boundary without suppressions or compatibility edits. The
upcoming native-parser default remains outside this migration.

Primary upgrade references:

- <https://docs.astro.build/en/guides/upgrade-to/v7/>
- <https://docs.astro.build/en/guides/styling/#tailwind>
- <https://tailwindcss.com/docs/upgrade-guide>
- <https://github.com/astral-sh/ruff/releases/tag/0.16.0>
- <https://mypy.readthedocs.io/en/stable/changelog.html#mypy-2-3>

## Deterministic and visual verification

`make check` passed under Node 24.18.0, including Ruff, mypy, 54 unittests,
strict JSON Schema validation, the mechanically blocked experiment check,
19/19 external canon conformance fixtures, two accepted prompt baseline
contracts, projection generation, deploy-contract validation, and a 24-page
Astro build. `npm audit --audit-level=high` reported zero vulnerabilities.

Chromium 1440x1000 full-page comparisons used the same browser executable and
viewport before and after the migration:

| Route | Pre/post dimensions | Mean absolute RGB delta | Changed-channel ratio |
| --- | --- | ---: | ---: |
| `/` | 1440x2950 / 1440x2950 | 0.0220 | 0.000245 |
| `/lineage/ai-native/` | 1440x2032 / 1440x2032 | 0.0113 | 0.000198 |

Both retained `rgb(242, 240, 233)` as the root background and the same body font
stack; the lineage headline remained 100.8px. The new
`/lineage/cadence/` route was separately rendered and inspected, including its
“Not a Claim. Not Evidence. Not a finding. Not a current study.” boundary.

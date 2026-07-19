# Adversarial review target: public evidence surface

Review the implementation, not the still-blocked Phase B scientific study.

## Public claims and boundaries

- `knowledge/generate.py` produces projection v1.1.0 from canon research plus
  separately schema-validated sources, curated conjectures, and engineering cases.
- A finding is emitted only for `Decision(kind=promote)` with at least one cited,
  existing Evidence record belonging to the same Claim. Current findings are zero.
- `sources/registry.json` contains SourceObservations. A source is provenance and
  input, never local Evidence.
- `reasoning/conjectures/conjectures.json` contains curated cross-domain
  conjectures. They are neither Claims nor findings.
- `knowledge/engineering-cases.json` is a separate, explicitly non-scientific
  track. Each case names an epistemic limit and links to source artifacts.
- `reasoning/conjectures/result.schema.json` discriminates a full conjecture from
  a rejection. `engine.py` marks only conjectures eligible for public curation.
- Runtime model traces are losslessly appended outside the repository at mode
  0600. They are excluded from the public projection; optional telemetry remains
  non-blocking.

## Inspect these files

- `knowledge/generate.py`
- `knowledge/public-projection.schema.json`
- `knowledge/test_projection.py`
- `sources/registry.schema.json`, `sources/registry.py`, `sources/test_registry.py`
- `reasoning/conjectures/conjecture-prompt.md`
- `reasoning/conjectures/result.schema.json`
- `reasoning/conjectures/engine.py`, `reasoning/conjectures/test_engine.py`
- `site/src/pages/index.astro`, `method/index.astro`, `research/index.astro`
- `site/src/pages/sources/index.astro`, `conjectures/index.astro`
- `site/src/pages/case-studies/index.astro`, `case-studies/[slug].astro`

## Review question

Find unsupported public claims, category leakage among SourceObservation,
conjecture, Claim, Evidence, Decision, finding, and engineering case study, or a
path by which a rejection/runtime trace can enter the public conjecture registry.
Treat attention scores as routing metadata only. Do not reinterpret any Phase B
scientific state.

# Programmes

Programmes are the discovery-plane substrate defined by
`/opt/workspace/supervisor/decisions/0038-programmes-as-discovery-plane.md`.

A Programme is a durable conjectural workspace. It may hold leads, signals,
source pointers, mechanisms, analogies, platform patterns, open questions,
tensions, draft claims, and a graduation ledger. It has zero epistemic
authority.

## Contract

- Programmes may point to canon object ids, intake content ids, friction event
  ids, and external URLs.
- Programmes must not copy or re-ingest external content into a parallel intake
  surface.
- Canon envelopes and reader-facing writeups must never cite Programme paths.
- Graduation provenance lives in the Programme graduation ledger, not in canon
  envelopes.
- A draft claim from a Programme graduates only through the normal canon Claim
  emission path. Graduation carries no privilege.
- Programme lifecycle values are `active`, `dormant`, and `archived`.

## Structure

Use `TEMPLATE.md` for new Programmes. Do not create a Programme until there is a
real conjectural workspace to preserve; the template is the only exemplar.

The graduation ledger is the rent surface reviewed by reflection. Falsified
graduates can count as successful rent when they were useful, decidable
conjectures. Many weak drafts that never graduate do not.

## Guard

Run the guard from the repository root:

```bash
.venv/bin/python reasoning/check_programmes.py
```

The guard enforces two mechanical parts of ADR-0038:

- no canon envelope or site/editorial source may reference
  `reasoning/programmes`;
- Programme-local structure must not use canon-reserved labels.

The vocabulary guard derives candidates from the canon schemas, then applies a
small allowlist in service of ADR-0038. For example, canon has a `sources`
field, but `sources` is explicitly allowed for Programmes because they hold
source pointers. The guard prints whether it used schemas or the pinned local
fallback.

The path guard cannot detect copied external content. Reflection review owns
that convention.

If a canon envelope ever references a Programme path, do not edit the envelope
in place. Supersede it through the normal canon path.


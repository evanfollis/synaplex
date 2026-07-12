# Frozen fixture interface contract (non-runnable)

This is a declarative Phase A contract. It contains no implementation and may
not be imported or instantiated.

Each post-entry arm must expose one origin with `/`, `/app.css`, `/app.js`, and
`/api/items`. The document contains exactly one
`[data-study-action="compute"]` control and one `[data-study-output]` node.
Readiness is signaled once by `study:ready`. Activation dispatches exactly one
`study:result` event and updates the output node.

All arms use identical document bytes, stylesheet bytes, API bytes, and visible
initial state. Only the prescribed delivery defect varies:

- `coherent`: all declared resources return the sealed bytes; activation emits
  `{"items":[2,2,3],"result":7,"schema":"v2"}` and renders
  `sum=7;items=3;schema=v2`.
- `transport_broken`: `/app.js` terminates without a complete HTTP response;
  therefore transport must fail and application behavior need not occur.
- `semantic_mismatch_200`: every resource returns HTTP 200 with no passive
  browser error, but the script implements incompatible `schema=v1` behavior
  and deterministically emits/renders a value unequal to the v2 oracle.

Fixture identity is provisioner-owned and follows `methodology.md §Identity and
isolation`. The executor may observe and verify identity but cannot supply it.
No arm may reveal its arm id through document text, headers, DOM attributes,
console messages, URLs, or event details. The arm-to-identity mapping remains in
the sealed provisioner manifest and is joined only after classifications seal.

---
name: artifact coherence transfer v1
status: pre-registered; not executed
predeclared_at: 2026-07-12
authority: ADR-0047
---

# Prospective transfer: mutable artifact risk predicate

## Epistemic boundary

This is a prospective transfer prediction, not a replay of the 2026-07-12
Command incident. No browser observation of the transfer subject may occur until
the Claim and its frozen gate are in canon. The known Command outcome is excluded
from the transfer population and may be used only as the retrospective regression
fixture described in `command-retrospective-regression-fixture.md`.

This phase pre-registers only. It does not run either subject, emit Evidence, or
support a Decision or invariant.

## Named population

The population is fixed from the workspace's generated verified-state snapshot
dated 2026-07-12T11:27:24Z. Inclusion requires all of:

1. an active workspace-scoped, long-lived application service;
2. a public browser-addressable application route in that same snapshot;
3. application source and deployment configuration available in the workspace;
4. not the motivating Command incident; and
5. safe read-only observation without changing the live service.

Exactly one service qualifies: **launchpad-lint** (`launchpad-lint.service`,
`https://skillfoundry.synaplex.ai/products/launchpad-lint/`). The population is
closed at N=1. Command is excluded by rule 4; cloudflared is transport rather than
an application; preflight services and workspace sessions have no public
application route. No later-discovered service may be added to this Claim.

## Static predicate and prediction

Predicate P is true exactly when a long-lived process resolves behavior-critical
application assets at request time from a directory that a build or deploy job can
mutate in place while that process remains active. Source modules imported into
process memory at startup are not request-time artifact resolution. Mutable data
stores are not build artifacts.

Classification is performed only from unit/deploy/source configuration, before
browser observation:

| subject | P | predeclared prediction |
|---|---:|---|
| launchpad-lint | false | Across the fixed observation schedule, browser-visible application behavior remains coherent; no sample has a primary behavioral failure attributable to artifact-set incoherence. |

The classification basis is that the service imports the ASGI application into a
long-lived Python process and its routes do not read HTML, JavaScript, CSS,
templates, or other behavior-critical build artifacts from the working tree at
request time. Its feedback and telemetry files are mutable data, not deployed
behavioral assets.

## Observation protocol

The run is read-only against the live subject. It must not build, deploy, restart,
write application state, or deliberately impair the service. A run manifest must
record the subject, URL, source SHA and dirty state, unit identity, timestamps,
code hashes, and every request artifact hash. Aborted or partial observations are
neutral and resumable; they do not shrink the denominator.

Observation barriers are fixed before execution:

1. **B0**: capture service liveness and deployment/source identity.
2. **B1**: start a clean browser context and load the public application route.
3. **B2**: after load completion, wait 1 second and capture visible content,
   browser console errors, failed requests, final URL, and response identity.
4. **B3**: repeat B1-B2 after 30 seconds in a new clean browser context.
5. **B4**: repeat B1-B2 after 120 seconds in a new clean browser context.

There are exactly three browser samples. Retries caused by tooling failure are
recorded as retries and cannot replace a completed failing sample. Because the
subject has no authenticated browser UI, authentication is **not applicable** for
the public browser route; the authenticated MCP endpoint is outside the browser
primary outcome and must not be invoked as a substitute.

## Outcomes

The primary outcome is browser-visible application behavior. A sample passes only
when the browser reaches the declared route, receives the expected application
identity (`Launchpad Lint MCP product is running.`), and records no failed
behavior-critical request or JavaScript error. Liveness (`systemd` state and
`/health`) is recorded separately and cannot make a failed browser sample pass.

HTTP status, redirects, response content hashes, and any referenced asset identity
are diagnostics. They explain a browser result; they are not an independent success
oracle.

## Falsification and limits

The Claim is falsified if any completed browser sample has an artifact-coherence
behavioral failure while P is false. It is also falsified as a useful classifier if
the static inspection later proves P was scored incorrectly under the definition
above. Network, TLS, authentication, or unrelated application failures are recorded
but do not count as artifact-coherence failures; if attribution cannot be resolved,
the result is inconclusive rather than supportive.

With N=1 and only a predicate-false subject, even a clean run supports at most the
predeclared launchpad-lint transfer prediction. It cannot establish causality,
estimate a rate, or justify a cross-service invariant. A three-arm isolated
mechanism fixture (mutable/in-place; immutable/non-atomic; immutable/atomic) would
require a separate pre-registration and is not part of this run. The rejected
two-arm Command test must not be run.

# Preregistered methodology: artifact-delivery instrument v2

Status: **PRE-ENTRY / NO SUBJECT MAY EXIST**  
Study type: controlled instrument validation, not a live-service claim  
Authority boundary: Phase A freezes this document. A later executor may read it
but has no authority to edit, replace, reinterpret, or supersede it.

## Claim and estimand

The instrument is valid for this prescribed three-arm population if, without
post-observation adjustment, it classifies exactly:

1. `coherent` as `PASS`;
2. `transport_broken` as `TRANSPORT_FAILURE`; and
3. `semantic_mismatch_200` as `BEHAVIOR_FAILURE`.

This does not estimate prevalence or make a claim about any live service. One
sample per prescribed arm is a complete census of the controlled population.
The Claim is falsified if any completed arm receives a different classification,
or if the instrument cannot complete all three samples under this method.

## Frozen inputs and entry gate

The frozen inputs are this methodology, `fixture-contract.md`,
`artifact.schema.json`, `expected-classifications.json`, and
`review-prompt.md`. `frozen-inputs.json` records their SHA-256 digests. The
Claim thresholds repeat the complete manifest and the frozen Policy is derived
mechanically from `/thresholds`.

`PROTOCOL_READY` from the prescribed opposing Claude review is necessary but
not sufficient for probe entry. Entry is forbidden until all are true:

- the Claim and frozen Policy exist in `lab/.canon/` and validate;
- the reviewed commit contains every frozen input and its digest manifest;
- the review verdict is exactly `PROTOCOL_READY` and confirms every acceptance
  item in `review-prompt.md`;
- no runnable subject, arm implementation, subject-specific adapter, fixture
  process, or generated fixture material existed before the reviewed commit;
- an independent next session verifies every frozen digest and records a
  methodology-log and probe-entry event through the reviewed canon emitter.

Any read, import, construction, launch, request, browser visit, source
inspection, or other access to a prospective subject before entry is
contamination: stop immediately, write a protocol-deviation record, emit zero
Evidence, seek an opposing methodological disposition, and do not repair the
study by declaring the information void. A successor study requires a new
Claim and gate.

## Identity and isolation

Phase B must create three isolated subjects only after entry. Each subject must
be built from the same post-entry fixture generator version and a controller-
generated 256-bit nonce. Identity is the SHA-256 of canonical JSON containing
`study_id`, `arm_id`, `generator_commit`, `build_manifest_hash`, and `nonce`.
The generator writes a signed identity file inside the immutable subject root.

The executor receives one read-only, canonically sorted run manifest whose
three identity records and endpoints are produced by the post-entry fixture
provisioner. It has no CLI flag, environment variable, constructor parameter,
callback, import hook, or API for replacing an endpoint, identity, expected
arm, clock, sampler, assertion, or schedule. It re-computes identity from the
immutable root and requires byte equality with the provisioner manifest before
each sample. Identity mismatch, duplicate nonce/root/endpoint, mutable root, or
unexpected process ancestry aborts the whole run. An executor unit test may use
generic data, but cannot establish subject identity or count as a sample.

The executor must contain the frozen input digests as constants generated from
the reviewed commit. At start it compares those constants, the checked-in
manifest, and the canon Policy. Any mismatch is a pre-entry refusal, never a
runtime override. No next executor or provisioner may write Phase A paths or
canon.

## Instrument and assertions

Every arm is observed in a fresh browser context with cache disabled. The only
allowed browser-originating traffic is GET/HEAD to the exact origin and paths
declared by the post-entry subject manifest. No retries occur inside a sample.

Transport assertions (all must pass for `PASS` or `BEHAVIOR_FAILURE`):

- navigation, document, stylesheet, script, and declared API response complete;
- every declared resource returns HTTP 200, with no redirect;
- response bytes hash to the subject build manifest;
- no request failure, console error, page error, or uncaught exception occurs.

Application-behavior assertion (primary semantic detector): after readiness,
the executor clicks `[data-study-action="compute"]`, waits for exactly one
`study:result` event, and asserts that `[data-study-output]` equals the canonical
UTF-8 text `sum=7;items=3;schema=v2`. It also asserts the event detail equals
canonical JSON `{"items":[2,2,3],"result":7,"schema":"v2"}`. The semantic-
mismatch arm must serve HTTP 200 assets without passive errors but produce a
different deterministic output/event detail. This behavior assertion, not
fixture labels or passive telemetry, distinguishes that arm.

Classification is deterministic and closed:

- any failed transport assertion -> `TRANSPORT_FAILURE`;
- otherwise any failed behavior assertion -> `BEHAVIOR_FAILURE`;
- otherwise -> `PASS`.

Arm labels are unavailable to the classification function. They are joined to
results only after the run is sealed, using the provisioner manifest, for the
frozen expected-versus-observed comparison.

## Schedule, barriers, anchors, timeouts, retries, tolerances

The provisioner seals all three immutable subjects, proves readiness, then
releases one barrier token at monotonic time `T0`. Sampling order is fixed:
`coherent`, `transport_broken`, `semantic_mismatch_200`. Each arm's navigation
starts at `T0 + offset`, with offsets 0 s, 30 s, and 60 s respectively.

The executor polls its monotonic clock without network traffic and starts when
`now >= anchor`. Permitted start lateness is `[0, 250]` ms. Starting early or
later than 250 ms aborts the entire run. Wall-clock timestamps are recorded but
never schedule or adjudicate. Per sample: navigation timeout 5.000 s; readiness
timeout 2.000 s after load; action-to-event timeout 2.000 s; post-event quiet
window exactly 1.000 s. Timeout boundaries are half-open: completion at elapsed
`< limit` succeeds; `>= limit` fails the corresponding assertion. Clock
resolution must be <=1 ms and every duration is stored as integer nanoseconds.

There are zero request, navigation, action, sample, and run retries. A process
interruption, identity fault, archive pressure, clock fault, or unexpected
event aborts the run. Re-running requires a new run id and new subjects; no
result from the aborted run is carried forward.

## Sample atomicity and Evidence boundary

A sample becomes `complete` only after all raw streams close, hashes verify,
the quiet window ends, and a completion record is atomically renamed from a
temporary file. The run becomes `sealed_complete` only when exactly three
unique complete samples exist, every expected raw artifact validates, the
asynchronous archive acknowledges durable copies, and the run manifest hash is
sealed. Partial/aborted samples have no classification and cannot be joined,
promoted, or cited as Evidence. A partial run exits nonzero and cannot contain a
`sealed_complete` marker.

The executor emits no canon object. A later human-reviewed Phase C may emit at
most one Evidence envelope for the sealed run, pointing to the lossless sealed
manifest and using the actual observation timestamp. No marker, summary,
classification, or partial artifact is Evidence by itself.

## Lossless retention, backpressure, and bounded indexes

The raw artifact contract is `artifact.schema.json`. It retains response bytes
and headers, request/response timing, DOM snapshot, event stream, console/page/
network records (including empty streams), screenshots, identity proofs, clock
samples, tool versions, exit status, and hashes. Raw records are append-only;
summaries never replace them.

Capture writes to a local append-only spool and asynchronously copies every
closed object to an operator-private archive outside the repository hot path.
The archive acknowledges content hash and byte length. A sample cannot complete
until all acknowledgements arrive. If spool use reaches 80% or any archive copy
or acknowledgement fails, capture pauses before the next action and applies
backpressure; timeout then aborts the run. Failure never authorizes deletion,
truncation, downsampling, or summary substitution.

The hot path holds only the current run manifest and at most 100 recent run
index entries, each containing ids, states, timestamps, sizes, and hashes but no
raw payload. Indexes and manifests are derived from immutable archived objects,
bounded, disposable, and rebuildable by hash scan. Source objects have no
age-based deletion. Compression may occur only after hash verification and must
preserve exact decompressed bytes.

## Stopping and disposition

Stop immediately with `INVALID_CONTAMINATED` for pre-entry subject access;
`INVALID_IDENTITY` for identity/substitution failure; `ABORTED_INSTRUMENT` for
clock, process, timeout infrastructure, missing raw artifact, archive, or
atomicity failure; and `COMPLETE` only for a sealed three-sample run.

For `COMPLETE`, exact match of all three frozen classifications supports the
instrument Claim; any mismatch contradicts it. Mixed, partial, ambiguous, or
manually interpreted outcomes never support it. No post-entry edit, tolerance
change, retry, arm relabel, missing-value imputation, or assertion waiver is
permitted. Unexpected cases require a successor Claim and protocol.

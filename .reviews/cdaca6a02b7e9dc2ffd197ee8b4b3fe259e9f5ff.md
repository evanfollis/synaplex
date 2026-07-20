# Review receipt — stable quarantine record reads

Executive review verified the exact delta against the immediately preceding
independent review: pending JSON is counted without non-JSON starvation, opened
with `O_NOFOLLOW`, validated through `fstat`, and read from that same bounded
descriptor. The active-candidate limit counts only schema-addressable candidate
names inside the private 0700 classifier-owned directory.

Source review transcript: `/opt/workspace/runtime/.meta/friction-classifier-final-review-d84e99b-2026-07-20.txt`
SHA-256: `40d173e86bcc287353b22b9d5db3a7e9bb144103b954f43dcb8f68b4244cbd7d`

Verification: 25 focused classifier tests and all 47 repository tests passed;
the production oneshot exited `0/SUCCESS` with `quarantine_deferred=0`.

Disposition: accepted.

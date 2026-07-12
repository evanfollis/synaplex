"""Study-specific executor for artifact-coherence-transfer-v1. Raw artifacts only.

Not a framework. ADR-0049 gives this cycle *one* instrumented vertical slice and no generic
controller, so this module hard-binds the single pre-registered subject and the single
pre-registered schedule and knows how to do nothing else. The generic `lab/runner/` was
deliberately not reused: it conflates an aborted cell with a completed one (`completed += 1`
runs on both branches), and this study's whole denominator argument depends on that
distinction being airtight.

## What this file may and may not do

- **It does not emit Evidence.** Evidence closes the frozen gate's pre-registration window
  permanently (canon rule 10). That is a reviewed epistemic act performed *from* these
  artifacts, never a side effect of a script finishing. `lab.canon.emit` is not imported here
  and `test_executor.py` asserts that on the import and call graph, not on this promise.
- **It does not attribute.** It records what the browser saw and applies the mechanical pass
  criterion that `methodology.md` fixed in advance. Whether a *failure* is attributable to
  artifact-set incoherence is the reviewed step, and a failure this module cannot mechanically
  attribute is inconclusive — not favorable, not unfavorable.
- **It is read-only against the subject, by construction.** Every browser request passes through
  a route interceptor that *aborts* any method outside `ALLOWED_METHODS` before it reaches the
  network. Read-only used to be a property this module observed after the fact; it is now one it
  enforces. A blocked attempt is recorded and makes the sample protocol-invalid.

## The denominator cannot be shrunk from here

`BARRIERS` and `REQUIRED_SAMPLES` are cross-checked against the frozen gate in canon
(`Policy 5273e9a31e92f6c3`, `class: frozen`, `amendment_authority: []`) and the run refuses to
start if they disagree. The denominator does not live in this file — it lives in an append-only,
hash-validated, unamendable envelope. Editing the constants here makes the executor *refuse to
run*: an eval whose sample count can be edited by the party reading the results has no
pre-registration at all.

## The run is anchored in absolute time, not in process time

A resume must not be able to splice yesterday's B1 with today's B120 and file the result as one
run. The absolute anchor is persisted in `run.json` **before** the subject is consulted, and every
barrier deadline is computed from it. On resume, a barrier whose window has closed is recorded as
a neutral `missed_barrier` abort and is **never sampled late**. A fresh complete attempt needs a
new run id. This is the difference between three samples of one run and three samples of nothing
in particular.

## Aborts carry no outcome — but they do not pretend nothing happened

A completed sample is written atomically, hash-sidecarred, and **never** replaced on resume. An
abort has no `mechanical_outcome` and no `observed_at`, so coding "the tool broke" as "the subject
failed" is structurally unavailable. But if the browser had already consulted reality before the
capture threw, the abort records `consulted_at`, the stage it died at, and every partial fact
safely available. An abort is not Evidence; it is also not a claim that the subject was never
touched.

## Barrier semantics — an interpretive choice, declared not hidden

`methodology.md` is ambiguous and this module does not get to resolve that quietly. The frozen
gate fixes `browser_barriers_seconds: [1, 30, 120]` but not their semantics, and the prose admits
two readings:

    (a) post-load dwell:    each sample loads, then waits 1s / 30s / 120s before capturing.
    (b) elapsed-from-anchor: each sample is *taken* at t=1s / 30s / 120s from the run anchor,
                             each with the fixed 1s post-load dwell that B2 names.

This module implements **(b)**, because B2 fixes the dwell at "wait 1 second" for the repeated
unit B1-B2, and B3/B4 say to *repeat that unit* "after 30 seconds" / "after 120 seconds" — which
makes 30 and 120 offsets between samples, not dwells within them. Under (a), B2's explicit "wait
1 second" would contradict the 30s and 120s samples.

`BARRIER_TOLERANCE_S` is a second declared interpretive parameter with no basis in the frozen
text: a barrier deadline needs *some* slack or a scheduler hiccup silently voids a sample. Both
choices are recorded in the run manifest and both go to opposing review **before** any sample is
taken. If the reviewer prefers otherwise, this module changes before the run — never after seeing
results.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import time
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Callable, Final

from lab.canon.ids import hash_file
from lab.canon.store import REPO_ROOT, load_all

EVAL_ID = "artifact-coherence-transfer-v1"
CLAIM_ID = "bda4396c7638e63f"
GATE_ID = "5273e9a31e92f6c3"

# The one pre-registered subject. `methodology.md` closes the population at N=1.
SUBJECT = "launchpad-lint"
SUBJECT_URL = "https://skillfoundry.synaplex.ai/products/launchpad-lint/"
SUBJECT_UNIT = "launchpad-lint.service"
SUBJECT_HEALTH_URL = "https://skillfoundry.synaplex.ai/products/launchpad-lint/health"
SUBJECT_REPO = Path("/opt/workspace/projects/skillfoundry/skillfoundry-products")

# Fixed by methodology.md §Outcomes. A sample passes only when the browser receives this.
EXPECTED_IDENTITY = "Launchpad Lint MCP product is running."

# The production schedule. Cross-checked against the frozen gate before the run starts.
#
# These are constants, and the production entry point takes **no** parameter that can displace
# them: `execute_run()` accepts a run id and nothing else. The fixture suite drives `_execute()`
# with an explicit `RunPlan` instead, which is how it finishes in milliseconds without the real
# 1/30/120 waits — and which is why a fast test can never silently become the shape of the real
# run.
BARRIERS: Final[tuple[int, ...]] = (1, 30, 120)
REQUIRED_SAMPLES: Final[int] = 3
POST_LOAD_DWELL_S: Final[float] = 1.0

# Declared interpretive parameter. See module docstring. A barrier may be sampled up to this many
# seconds late; past that, the window is closed and the sample is a neutral `missed_barrier`.
BARRIER_TOLERANCE_S: Final[float] = 10.0

# Read-only, enforced. Anything else is aborted at the route layer before it hits the network.
ALLOWED_METHODS: Final[frozenset[str]] = frozenset({"GET", "HEAD"})

# Pinned so the measurement is reproducible rather than a function of whatever the host happened
# to have. `TOOLING.md` records the exact provisioning commands and the host packages they added.
PINNED_PLAYWRIGHT: Final[str] = "1.61.0"

BARRIER_INTERPRETATION = (
    "elapsed-from-anchor: sample k is taken when wall-clock reaches (anchor + BARRIERS[k]) "
    "seconds, in a fresh browser context, capturing after the fixed 1s post-load dwell that "
    "methodology.md B2 names. The anchor is absolute and persisted before the subject is "
    "consulted, so a resume cannot re-time the schedule. A barrier more than BARRIER_TOLERANCE_S "
    "late is never sampled; it becomes a neutral missed_barrier. See executor.py docstring."
)

METHODOLOGY = f"lab/evals/{EVAL_ID}/methodology.md"
DEVIATION = f"lab/evals/{EVAL_ID}/PROTOCOL-DEVIATION-2026-07-12-preprobe-target-consultation.md"
EXECUTOR_SRC = f"lab/evals/{EVAL_ID}/executor.py"
RUNS_ROOT = REPO_ROOT / "lab" / "runs"

NAV_TIMEOUT_MS = 30_000
RUN_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")


class ProtocolRefusal(RuntimeError):
    """The run may not proceed. Raised before the subject is touched, or on corruption."""


class CaptureAborted(RuntimeError):
    """A sample died. Carries what was already observed, and never an outcome.

    `consulted_at` is None only when the browser never reached the subject. When it is set, the
    subject *was* touched and the artifact must say so — an abort that looks identical whether or
    not reality was consulted is how an unlogged observation happens (see the recorded protocol
    deviation for what that costs).
    """

    def __init__(self, stage: str, reason: str, *, consulted_at: str | None = None,
                 partial: dict | None = None) -> None:
        super().__init__(reason)
        self.stage = stage
        self.reason = reason
        self.consulted_at = consulted_at
        self.partial = partial or {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _iso(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )


def _sha256_bytes(b: bytes) -> str:
    return f"sha256:{hashlib.sha256(b).hexdigest()}"


def _normalize(text: str) -> str:
    """Collapse whitespace. The identity comparison is exact *after* this, never a substring."""
    return " ".join(text.split())


# --- durable, tamper-evident artifact IO ---------------------------------------------


def _write_json(path: Path, obj: dict) -> None:
    """Atomic write + fsync + hash sidecar. A torn artifact must not read as a good one.

    `write_text` can tear: a crash mid-write leaves a truncated JSON file that a later resume
    would treat as a completed sample. Write to a temp file in the same directory, fsync it,
    `os.replace` (atomic within a filesystem), then fsync the directory so the rename itself is
    durable. The sidecar records the hash of what was written, so corruption after the fact is
    detectable rather than silently inherited.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    body = (json.dumps(obj, indent=2, sort_keys=True) + "\n").encode("utf-8")
    tmp = path.parent / f".{path.name}.tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
    try:
        os.write(fd, body)
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(tmp, path)
    dfd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)
    path.with_suffix(path.suffix + ".sha256").write_text(
        _sha256_bytes(body) + "\n", encoding="utf-8"
    )


def _read_json_verified(path: Path) -> dict:
    """Read an artifact, refusing symlinks and hash mismatches.

    Corruption **refuses**. It does not silently re-run (which would replace a completed sample)
    and it does not silently count (which would let a truncated file fill a slot in the
    denominator).
    """
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except OSError as e:
        raise ProtocolRefusal(f"{path.name}: cannot be read without following a symlink: {e}")
    try:
        raw = b""
        while chunk := os.read(fd, 65536):
            raw += chunk
    finally:
        os.close(fd)

    sidecar = path.with_suffix(path.suffix + ".sha256")
    if not sidecar.is_file():
        raise ProtocolRefusal(f"{path.name}: no hash sidecar; artifact integrity is unverifiable")
    expected = sidecar.read_text(encoding="utf-8").strip()
    actual = _sha256_bytes(raw)
    if actual != expected:
        raise ProtocolRefusal(
            f"{path.name}: hash mismatch (recorded {expected}, found {actual}). The artifact was "
            "modified or torn after it was written. Refusing rather than counting or re-running it."
        )
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ProtocolRefusal(f"{path.name}: not valid JSON despite matching its hash: {e}")


_SAMPLE_REQUIRED = ("barrier_seconds", "status", "observed_at", "response", "visible_text",
                    "console_errors", "page_errors", "failed_requests",
                    "bad_behavior_critical_responses", "mechanical_outcome")


def _validate_completed_sample(sample: dict, barrier: int, path: Path) -> None:
    """A file on disk is not a completed sample until it proves it is one."""
    missing = [k for k in _SAMPLE_REQUIRED if k not in sample]
    if missing:
        raise ProtocolRefusal(f"{path.name}: missing required field(s) {missing}")
    if sample["status"] != "completed":
        raise ProtocolRefusal(f"{path.name}: status is {sample['status']!r}, not 'completed'")
    if sample["barrier_seconds"] != barrier:
        raise ProtocolRefusal(
            f"{path.name}: holds barrier {sample['barrier_seconds']}, filed under barrier {barrier}"
        )
    if not sample.get("observed_at"):
        raise ProtocolRefusal(f"{path.name}: completed sample carries no observed_at")


# --- preflight: the run refuses to start against a drifted or unentered pre-registration ---


def tooling() -> dict:
    """The measuring instrument, recorded into the run. A result produced by a different browser
    is a different result, and a manifest that cannot name its instrument cannot support a
    replay. `TOOLING.md` holds the provisioning commands that produce this state."""
    try:
        pw = version("playwright")
    except PackageNotFoundError:  # pragma: no cover
        pw = "MISSING"
    return {"playwright": pw, "playwright_pinned": PINNED_PLAYWRIGHT, "browser": "chromium"}


def _frozen_gate() -> dict:
    gates = [p for p in load_all("Policy") if p.get("bound_to_claim_id") == CLAIM_ID]
    if len(gates) != 1:
        raise ProtocolRefusal(f"expected exactly 1 frozen gate on {CLAIM_ID}, found {len(gates)}")
    gate = gates[0]
    if gate["id"] != GATE_ID or gate["class"] != "frozen" or gate["amendment_authority"] != []:
        raise ProtocolRefusal(f"gate {gate['id']} is not the unamendable frozen gate {GATE_ID}")
    return gate


def verify_pre_registration() -> dict:
    """Claim, frozen gate, methodology hash, schedule, and instrument. No probe requirement.

    Split out from `preflight()` so the *schedule* check is testable without a probe-entry event
    existing, and so the probe-entry check below cannot be quietly satisfied by a test fixture.
    """
    claims = {c["id"]: c for c in load_all("Claim")}
    if CLAIM_ID not in claims:
        raise ProtocolRefusal(f"Claim {CLAIM_ID} is not in canon")
    claim = claims[CLAIM_ID]

    live_hash = hash_file(REPO_ROOT / METHODOLOGY)
    bound_hash = claim["artifact"]["content_hash"]
    if live_hash != bound_hash:
        raise ProtocolRefusal(
            "methodology.md no longer hashes to the value bound into the Claim "
            f"({live_hash} != {bound_hash}). The pre-registration was edited; the run is void."
        )

    gate = _frozen_gate()
    value = gate["value"]
    if tuple(value["browser_barriers_seconds"]) != BARRIERS:
        raise ProtocolRefusal(
            f"barrier schedule {BARRIERS} does not match the frozen gate "
            f"{tuple(value['browser_barriers_seconds'])}. The denominator lives in canon, not "
            "in this file."
        )
    if value["required_completed_samples"] != REQUIRED_SAMPLES:
        raise ProtocolRefusal(
            f"required sample count {REQUIRED_SAMPLES} does not match the frozen gate "
            f"{value['required_completed_samples']}"
        )
    if value["population"] != [SUBJECT]:
        raise ProtocolRefusal(
            f"subject {SUBJECT!r} is not the frozen population {value['population']}"
        )
    if value["primary_outcome"] != "browser_behavior":
        raise ProtocolRefusal("frozen gate does not name browser_behavior as the primary outcome")

    tools = tooling()
    if tools["playwright"] != PINNED_PLAYWRIGHT:
        raise ProtocolRefusal(
            f"playwright {tools['playwright']} is installed but the study pins "
            f"{PINNED_PLAYWRIGHT}. Reprovision per TOOLING.md rather than measuring with an "
            "instrument the pre-registration never declared."
        )

    return {
        "claim_id": CLAIM_ID,
        "claim_emitted_at": claim["emitted_at"],
        "gate_id": gate["id"],
        "gate_emitted_at": gate["emitted_at"],
        "methodology_hash": live_hash,
        "barriers_from_frozen_gate": list(value["browser_barriers_seconds"]),
        "required_completed_samples": value["required_completed_samples"],
        "tooling": tools,
    }


def verify_probe_entry(pre: dict) -> dict:
    """The Claim must actually be *in probe* before its subject is observed.

    `canon.md` §Phase invariants: phase is not a field on the Claim — it lives in the event log,
    and a Claim enters `probe` only via a `phase_transition`. Canon also requires a
    `methodology_log` on probe entry. Without both, an observation is happening against a Claim
    that, on replay, was never in a state where observation was authorized.

    This is the check whose absence let the recorded protocol deviation happen at all. Making it a
    *refusal* means the ordering is enforced by the executor rather than remembered by the operator.
    """
    events = load_all("EventLogEntry")

    logs = [
        e for e in events
        if e.get("event_kind") == "methodology_log" and e.get("subject_id") == CLAIM_ID
    ]
    if not logs:
        raise ProtocolRefusal(
            f"no EventLogEntry(methodology_log) for Claim {CLAIM_ID}. Canon requires one on probe "
            "entry. Emit probe entry through the reviewed canon emitter before observing."
        )
    hashes = {e["methodology_log"]["artifact"]["content_hash"] for e in logs}
    if pre["methodology_hash"] not in hashes:
        raise ProtocolRefusal(
            f"the methodology_log in canon points at {hashes}, but the live methodology hashes to "
            f"{pre['methodology_hash']}. The methodology changed after probe entry; the run is void."
        )

    transitions = [
        e for e in events
        if e.get("event_kind") == "phase_transition"
        and e.get("subject_id") == CLAIM_ID
        and e.get("phase_transition", {}).get("to_phase") == "probe"
    ]
    if not transitions:
        raise ProtocolRefusal(
            f"Claim {CLAIM_ID} has never entered probe. No phase_transition(-> probe) exists, so "
            "no observation of its subject is authorized."
        )

    entered_at = min(e["emitted_at"] for e in transitions)
    if not (pre["claim_emitted_at"] <= pre["gate_emitted_at"] <= entered_at):
        raise ProtocolRefusal(
            "probe entry ordering is illegal (canon rule 10 requires "
            f"claim <= gate <= probe entry): claim={pre['claim_emitted_at']}, "
            f"gate={pre['gate_emitted_at']}, probe={entered_at}"
        )

    from lab.canon.guard import check_canon_integrity

    violations = check_canon_integrity()
    if violations:
        raise ProtocolRefusal(
            "canon integrity is not clean; refusing to observe against a store that does not "
            "validate:\n" + "\n".join(v.render() for v in violations)
        )

    return {
        "probe_entered_at": entered_at,
        "methodology_log_ids": sorted(e["id"] for e in logs),
        "phase_transition_ids": sorted(e["id"] for e in transitions),
    }


def preflight() -> dict:
    """Everything that must be true before the subject is consulted. Every failure is a refusal
    to observe, not a warning."""
    pre = verify_pre_registration()
    return {**pre, **verify_probe_entry(pre)}


# --- B0: identity and liveness (diagnostic, never a success oracle) ------------------


def _run_cmd(argv: list[str]) -> dict:
    """Run a read-only command and record what actually happened.

    A non-zero exit used to vanish into an empty string, which then rendered as a verified-looking
    identity of `""`. A diagnostic that cannot fail loudly is worse than no diagnostic.
    """
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=30)
    except Exception as e:  # noqa: BLE001
        return {"argv": argv, "ok": False, "returncode": None, "stdout": "",
                "stderr": f"{type(e).__name__}: {e}"}
    return {
        "argv": argv,
        "ok": p.returncode == 0,
        "returncode": p.returncode,
        "stdout": p.stdout.strip(),
        "stderr": p.stderr.strip()[:2000],
    }


def _git_identity(repo: Path) -> dict:
    head = _run_cmd(["git", "-C", str(repo), "rev-parse", "HEAD"])
    status = _run_cmd(["git", "-C", str(repo), "status", "--porcelain"])
    ok = head["ok"] and status["ok"]
    out: dict = {"repo": str(repo), "ok": ok, "commands": [head, status]}
    if ok:
        out["commit"] = head["stdout"]
        out["dirty"] = bool(status["stdout"])
        out["dirty_paths"] = status["stdout"].splitlines()[:50]
    else:
        # No `commit` key at all. An unknown commit must not be representable as a known one.
        out["error"] = "git identity could not be established; see commands"
    return out


def _unit_identity(unit: str) -> dict:
    """`systemctl show` is a read. It does not start, stop, restart, or reload anything."""
    props = "ActiveState,SubState,MainPID,ExecStart,FragmentPath,ActiveEnterTimestamp,NRestarts"
    r = _run_cmd(["systemctl", "show", unit, "-p", props])
    out: dict = {"unit": unit, "ok": r["ok"], "command": r}
    if r["ok"]:
        out["properties"] = dict(
            line.split("=", 1) for line in r["stdout"].splitlines() if "=" in line
        )
    else:
        out["error"] = "unit identity could not be established"
    return out


def _health(url: str) -> dict:
    """Liveness. methodology.md §Outcomes: recorded separately, and it *cannot make a failed
    browser sample pass*. It explains a browser result; it never overrides one."""
    started = _now()
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:  # GET. Read-only.
            body = resp.read()
            return {
                "url": url,
                "ok": True,
                "status": resp.status,
                "body_sha256": _sha256_bytes(body),
                "body_bytes": len(body),
                "body_text": body.decode("utf-8", "replace")[:500],
                "observed_at": started,
                "error": None,
            }
    except Exception as e:  # noqa: BLE001 — a dead liveness probe is data, not a crash
        return {"url": url, "ok": False, "status": None, "observed_at": started,
                "error": f"{type(e).__name__}: {e}"}


def b0_identity(*, unit: str = SUBJECT_UNIT, health_url: str | None = SUBJECT_HEALTH_URL) -> dict:
    return {
        "observed_at": _now(),
        "unit": _unit_identity(unit),
        "subject_source": _git_identity(SUBJECT_REPO) if SUBJECT_REPO.is_dir() else None,
        "observer_source": _git_identity(REPO_ROOT),
        "liveness": _health(health_url) if health_url else None,
    }


# --- the browser sample --------------------------------------------------------------


def capture_sample(url: str, *, barrier_seconds: int, dwell_s: float = POST_LOAD_DWELL_S) -> dict:
    """One browser sample in a fresh context. Returns raw facts; concludes nothing.

    Read-only is **enforced** here, not merely recorded: a route interceptor aborts any request
    whose method is outside `ALLOWED_METHODS` before it reaches the network. A subject page that
    tries to POST cannot. The attempt is recorded and makes the sample protocol-invalid.

    Any failure after the browser has reached the subject raises `CaptureAborted` carrying
    `consulted_at` and every partial fact already collected — never a result.
    """
    from playwright.sync_api import sync_playwright

    console_errors: list[dict] = []
    page_errors: list[str] = []
    failed_requests: list[dict] = []
    requests: list[dict] = []
    responses: list[dict] = []
    blocked_requests: list[dict] = []

    started_at = _now()
    consulted_at: str | None = None
    stage = "launch"
    t0 = time.monotonic()

    def _partial() -> dict:
        return {
            "console_errors": console_errors,
            "page_errors": page_errors,
            "failed_requests": failed_requests,
            "requests": requests,
            "responses": responses,
            "blocked_requests": blocked_requests,
        }

    with sync_playwright() as p:
        browser = p.chromium.launch()  # fresh browser => fresh cache/storage, per B1
        tool = {**tooling(), "browser_version": browser.version}
        try:
            context = browser.new_context()

            def _gate(route, request) -> None:
                """Read-only, enforced at the network boundary."""
                if request.method.upper() in ALLOWED_METHODS:
                    route.continue_()
                    return
                blocked_requests.append(
                    {"method": request.method, "url": request.url,
                     "resource_type": request.resource_type}
                )
                route.abort()

            context.route("**/*", _gate)
            page = context.new_page()

            page.on("console", lambda m: console_errors.append({"type": m.type, "text": m.text})
                    if m.type == "error" else None)
            page.on("pageerror", lambda e: page_errors.append(str(e)))
            page.on("request", lambda r: requests.append(
                {"method": r.method, "url": r.url, "resource_type": r.resource_type}))
            page.on("requestfailed", lambda r: failed_requests.append(
                {"method": r.method, "url": r.url, "resource_type": r.resource_type,
                 "failure": (r.failure or "unknown")}))
            page.on("response", lambda r: responses.append(
                {"url": r.url, "status": r.status, "ok": r.ok,
                 "resource_type": r.request.resource_type}))

            stage = "navigate"
            response = page.goto(url, wait_until="load", timeout=NAV_TIMEOUT_MS)
            consulted_at = _now()  # reality has now been touched. Everything below must say so.

            stage = "dwell"
            time.sleep(dwell_s)  # B2: after load completion, wait 1 second, then capture.

            stage = "capture"
            observed_at = _now()
            body = response.body() if response else b""
            redirect_chain: list[dict] = []
            r = response.request.redirected_from if response else None
            while r is not None:
                redirect_chain.append({"url": r.url, "method": r.method})
                r = r.redirected_from
            redirect_chain.reverse()

            visible_text = page.inner_text("body")
            content = page.content()

            sample = {
                "barrier_seconds": barrier_seconds,
                "status": "completed",
                "observed_at": observed_at,
                "consulted_at": consulted_at,
                "started_at": started_at,
                "elapsed_s": round(time.monotonic() - t0, 3),
                "url_requested": url,
                "url_final": page.url,
                "redirect_chain": redirect_chain,
                "response": {
                    "status": response.status if response else None,
                    "ok": response.ok if response else False,
                    "headers": dict(response.headers) if response else {},
                    "body_sha256": _sha256_bytes(body),
                    "body_bytes": len(body),
                },
                "visible_text": visible_text,
                "content_sha256": _sha256_bytes(content.encode("utf-8")),
                "console_errors": console_errors,
                "page_errors": page_errors,
                "failed_requests": failed_requests,
                "bad_behavior_critical_responses": [
                    x for x in responses
                    if not x["ok"] and x["resource_type"] in BEHAVIOR_CRITICAL
                ],
                "blocked_requests": blocked_requests,
                "requests": requests,
                "responses": responses,
                "tool": tool,
            }
        except Exception as e:  # noqa: BLE001
            raise CaptureAborted(
                stage, f"{type(e).__name__}: {e}", consulted_at=consulted_at, partial=_partial()
            ) from e
        finally:
            browser.close()

    sample["mechanical_outcome"] = mechanical_outcome(sample)
    return sample


# Resource types whose failure changes what the application *does*, as opposed to how it looks.
# A stale document referencing a hashed bundle that no longer exists is the canonical
# artifact-incoherence symptom, and it arrives as an HTTP 404 on a `script` or a `fetch`.
#
# This channel exists because `methodology.md` names "no failed behavior-critical request" as a
# condition in its own right, and the only faithful way to check that is to look at the response
# status of behavior-critical requests.
#
# It is *not* the sole detector, and the fixture suite established that rather than the author's
# guess: Chromium aborts a 404'd `<script>` (so `requestfailed` fires) and console-logs "Failed to
# load resource" for a 404'd `fetch` (so `console_errors` fires). Both would catch a stale bundle
# today. But both are Chromium *logging policy*, not the criterion — inferring "a behavior-critical
# request failed" from an English console string is inference, and it silently changes meaning when
# the browser does. This channel observes what the methodology actually names. The overlap is
# redundancy, which is the correct posture for the one failure mode the study exists to detect.
BEHAVIOR_CRITICAL = frozenset({"document", "script", "stylesheet", "fetch", "xhr"})


def mechanical_outcome(sample: dict) -> dict:
    """Apply the pass criterion `methodology.md` §Outcomes fixed *before* the run.

    Deterministic and pre-registered, so computing it here is measurement, not selection: a sample
    passes only when the browser reached the declared route, received the expected application
    identity, and recorded no failed behavior-critical request and no JavaScript error.

    **Identity is compared exactly, after whitespace normalization — not by substring.** A page
    that renders the expected sentence *plus* an error banner contains the identity string while
    plainly not being the healthy application, and substring containment would pass it. Given that
    this executor's author already knew the subject was serving healthy, the permissive comparator
    was exactly the kind of quiet leniency that contamination produces. The raw
    `identity_contains` fact is still recorded for the reviewed step; only the *criterion* is strict.

    **Attribution is deliberately absent.** Whether a failure is due to artifact-set incoherence —
    as opposed to network, TLS, or an unrelated application fault — is the reviewed epistemic step,
    and §Falsification says an unresolvable attribution is *inconclusive*, not supportive. This
    function never writes that word.
    """
    reasons: list[str] = []
    visible = sample.get("visible_text", "")
    identity_exact = _normalize(visible) == _normalize(EXPECTED_IDENTITY)
    identity_contains = _normalize(EXPECTED_IDENTITY) in _normalize(visible)

    if not sample["response"]["ok"]:
        reasons.append(f"http status {sample['response']['status']} is not ok")
    if not identity_exact:
        reasons.append(
            f"visible text is not exactly the pre-registered application identity "
            f"(contains={identity_contains})"
        )
    if sample["failed_requests"]:
        reasons.append(f"{len(sample['failed_requests'])} network-failed request(s)")
    bad = sample.get("bad_behavior_critical_responses", [])
    if bad:
        reasons.append(
            f"{len(bad)} behavior-critical request(s) returned an error status: "
            + ", ".join(f"{r['status']} {r['resource_type']}" for r in bad[:5])
        )
    if sample["console_errors"]:
        reasons.append(f"{len(sample['console_errors'])} console error(s)")
    if sample["page_errors"]:
        reasons.append(f"{len(sample['page_errors'])} uncaught javascript error(s)")

    blocked = sample.get("blocked_requests", [])
    protocol_invalid = bool(blocked)
    if blocked:
        reasons.append(
            f"{len(blocked)} mutating request(s) were attempted and blocked — the observation is "
            "protocol-invalid, not merely failing"
        )

    return {
        "pass": not reasons,
        "protocol_invalid": protocol_invalid,
        "reasons": reasons,
        "identity_exact": identity_exact,
        "identity_contains": identity_contains,
        "criterion": "methodology.md §Outcomes (pre-registered, hash-bound)",
        "attribution": "NOT COMPUTED — reviewed epistemic step, see §Falsification",
    }


# --- the run -------------------------------------------------------------------------


@dataclass(frozen=True)
class RunPlan:
    """Everything `_execute` needs, supplied explicitly. The seam between the real run and the
    fixture suite.

    The fixture suite builds one of these with a no-op `sleep`, a fake `clock`, a stub `sampler`
    and a fixture URL, so it exercises the *real* [1,30,120] schedule in milliseconds. The
    production path builds one via `production_plan()`, which takes those values from the frozen
    gate and cannot be told otherwise. Nothing on the CLI reaches this object.

    `b0_fn` is a callable, not a dict: B0 consults the subject, and it must not run until the run
    boundary exists on disk to receive it.
    """

    run_id: str
    url: str
    barriers: tuple[int, ...]
    runs_root: Path
    sampler: Callable[..., dict]
    sleep: Callable[[float], None]
    b0_fn: Callable[[], dict]
    clock: Callable[[], float] = time.time
    preflight_result: dict | None = None
    extra: dict = field(default_factory=dict)

    @property
    def is_preregistered_subject(self) -> bool:
        return self.url == SUBJECT_URL


def production_plan(run_id: str) -> RunPlan:
    """The one real plan. Barriers come from the frozen gate; the clock is the real clock."""
    return RunPlan(
        run_id=run_id,
        url=SUBJECT_URL,
        barriers=BARRIERS,
        runs_root=RUNS_ROOT,
        sampler=capture_sample,
        sleep=time.sleep,
        b0_fn=b0_identity,
        clock=time.time,
        preflight_result=preflight(),
    )


def execute_run(run_id: str) -> Path:
    """Production entry point. Takes a run id and **nothing else** — no barrier override, no
    sampler injection, no URL, no preflight skip. The pre-registered schedule is not a parameter."""
    return _execute(production_plan(run_id))


def _resolve_run_dir(runs_root: Path, run_id: str) -> Path:
    """A run id names a directory. It does not get to choose where that directory is."""
    if not RUN_ID_RE.match(run_id):
        raise ProtocolRefusal(
            f"run_id {run_id!r} is not a conservative slug (^[a-z0-9][a-z0-9._-]{{0,63}}$)"
        )
    if run_id in (".", "..") or "/" in run_id or "\\" in run_id:
        raise ProtocolRefusal(f"run_id {run_id!r} contains a path separator or dot segment")

    root = (runs_root / EVAL_ID).resolve()
    run_dir = (root / run_id).resolve()
    if run_dir.parent != root:
        raise ProtocolRefusal(f"run_id {run_id!r} escapes the study run root {root}")
    return run_dir


def _code_identity() -> dict:
    """The executing source is part of the measurement. A run whose manifest cannot say which code
    produced it cannot support a replay."""
    return {
        "executor": hash_file(REPO_ROOT / EXECUTOR_SRC),
        "methodology": hash_file(REPO_ROOT / METHODOLOGY),
        "protocol_deviation": hash_file(REPO_ROOT / DEVIATION),
    }


def _execute(plan: RunPlan) -> Path:
    """Execute a plan idempotently against an absolute, persisted anchor.

    Order matters and is the point:
      1. resolve and create the run boundary;
      2. persist `run.json` — the **absolute anchor** — before anything touches the subject;
      3. capture B0 and write it atomically the moment it happens;
      4. sample each barrier against the anchor, never against this process's start time.

    A barrier whose window has closed is a neutral `missed_barrier`. It is never sampled late,
    because a B120 taken a day after its B1 is not a sample of the same run.
    """
    run_dir = _resolve_run_dir(plan.runs_root, plan.run_id)
    (run_dir / "samples").mkdir(parents=True, exist_ok=True)
    (run_dir / "aborts").mkdir(parents=True, exist_ok=True)

    # (2) The anchor. Written before the subject is consulted; reused verbatim on resume.
    run_path = run_dir / "run.json"
    if run_path.exists():
        run_record = _read_json_verified(run_path)
        if run_record["eval_id"] != EVAL_ID or run_record["run_id"] != plan.run_id:
            raise ProtocolRefusal(f"{run_path} belongs to a different run")
        resumed_run = True
    else:
        run_record = {
            "eval_id": EVAL_ID,
            "run_id": plan.run_id,
            "claim_id": CLAIM_ID,
            "frozen_gate_id": GATE_ID,
            "anchor_epoch": plan.clock(),
            "subject": {"name": SUBJECT, "url": plan.url, "unit": SUBJECT_UNIT},
            "is_preregistered_subject": plan.is_preregistered_subject,
            "barrier_schedule": list(plan.barriers),
            "barrier_interpretation": BARRIER_INTERPRETATION,
            "barrier_tolerance_s": BARRIER_TOLERANCE_S,
            "post_load_dwell_s": POST_LOAD_DWELL_S,
            "required_completed_samples": REQUIRED_SAMPLES,
            "expected_identity": EXPECTED_IDENTITY,
            "preflight": plan.preflight_result,
            "code": _code_identity(),
            "tooling": tooling(),
            "emits_evidence": False,
            "read_only_enforced": sorted(ALLOWED_METHODS),
        }
        run_record["anchor_at"] = _iso(run_record["anchor_epoch"])
        _write_json(run_path, run_record)
        resumed_run = False

    anchor = run_record["anchor_epoch"]

    # (3) B0. Consults the subject, so it may not happen until the boundary above exists.
    b0_path = run_dir / "b0.json"
    if b0_path.exists():
        _read_json_verified(b0_path)  # refuse on tamper; do not re-consult the subject
    else:
        _write_json(b0_path, plan.b0_fn())

    completed = aborted = resumed = missed = 0

    for barrier in plan.barriers:
        slot = run_dir / "samples" / f"b{barrier}s.json"
        if slot.exists():
            sample = _read_json_verified(slot)          # refuses on tamper/tear/symlink
            _validate_completed_sample(sample, barrier, slot)  # refuses on shape/status/barrier
            resumed += 1
            completed += 1
            continue

        deadline = anchor + barrier + BARRIER_TOLERANCE_S
        now = plan.clock()
        if now > deadline:
            missed += 1
            _write_json(
                run_dir / "aborts" / f"b{barrier}s-missed.json",
                {
                    "barrier_seconds": barrier,
                    "status": "aborted",
                    "abort_kind": "missed_barrier",
                    "consulted_at": None,
                    "recorded_at": _now(),
                    "anchor_at": run_record["anchor_at"],
                    "deadline_at": _iso(deadline),
                    "now_at": _iso(now),
                    "abort_reason": (
                        f"barrier {barrier}s closed {round(now - deadline, 1)}s ago. A sample taken "
                        "now would not belong to this run's schedule. Never sampled late; a fresh "
                        "complete attempt needs a new run id."
                    ),
                },
            )
            continue

        wait = anchor + barrier - now
        if wait > 0:
            plan.sleep(wait)

        try:
            sample = plan.sampler(plan.url, barrier_seconds=barrier)
        except CaptureAborted as e:
            aborted += 1
            n = len(list((run_dir / "aborts").glob(f"b{barrier}s-attempt-*.json"))) + 1
            # No observed_at. No mechanical_outcome. An abort has nowhere to put a result — but it
            # does record whether reality was already consulted, and what was seen before it died.
            _write_json(
                run_dir / "aborts" / f"b{barrier}s-attempt-{n}.json",
                {
                    "barrier_seconds": barrier,
                    "status": "aborted",
                    "abort_kind": "capture_failed",
                    "attempt": n,
                    "stage": e.stage,
                    "consulted_at": e.consulted_at,
                    "subject_was_consulted": e.consulted_at is not None,
                    "recorded_at": _now(),
                    "abort_reason": e.reason,
                    "partial_observations": e.partial,
                    "note": "An abort carries no outcome and does not fill its sample slot. It is "
                            "not a claim that the subject was never touched.",
                },
            )
            continue
        except Exception as e:  # noqa: BLE001 — a sampler that failed before reaching the browser
            aborted += 1
            n = len(list((run_dir / "aborts").glob(f"b{barrier}s-attempt-*.json"))) + 1
            _write_json(
                run_dir / "aborts" / f"b{barrier}s-attempt-{n}.json",
                {
                    "barrier_seconds": barrier,
                    "status": "aborted",
                    "abort_kind": "sampler_error",
                    "attempt": n,
                    "stage": "unknown",
                    "consulted_at": None,
                    "subject_was_consulted": None,  # unknown, and said so
                    "recorded_at": _now(),
                    "abort_reason": f"{type(e).__name__}: {e}",
                },
            )
            continue

        _validate_completed_sample(sample, barrier, slot)
        _write_json(slot, sample)
        completed += 1

    # (7) One reproducible root. The hash list covers every raw artifact and the executing source;
    # the manifest binds its digest. The manifest is not in the list — nothing hashes itself.
    hashes = {
        str(p.relative_to(run_dir)): hash_file(p)
        for p in sorted(run_dir.rglob("*.json"))
        if p.name != "manifest.json"
    }
    hashes.update({f"src::{k}": v for k, v in _code_identity().items()})
    hash_body = (json.dumps(hashes, indent=2, sort_keys=True) + "\n").encode("utf-8")
    (run_dir / "artifact-hashes.json").write_bytes(hash_body)

    manifest = {
        "eval_id": EVAL_ID,
        "run_id": plan.run_id,
        "generated_at": _now(),
        "claim_id": CLAIM_ID,
        "frozen_gate_id": GATE_ID,
        "anchor_at": run_record["anchor_at"],
        "resumed_run": resumed_run,
        "subject": run_record["subject"],
        "is_preregistered_subject": plan.is_preregistered_subject,
        "barrier_schedule": list(plan.barriers),
        "barrier_interpretation": BARRIER_INTERPRETATION,
        "barrier_tolerance_s": BARRIER_TOLERANCE_S,
        "post_load_dwell_s": POST_LOAD_DWELL_S,
        "expected_identity": EXPECTED_IDENTITY,
        "required_completed_samples": REQUIRED_SAMPLES,
        "samples_completed": completed,
        "samples_resumed": resumed,
        "samples_aborted": aborted,
        "barriers_missed": missed,
        "partial": completed < REQUIRED_SAMPLES,
        "preflight": plan.preflight_result,
        "code": _code_identity(),
        "tooling": tooling(),
        "read_only_enforced": sorted(ALLOWED_METHODS),
        "artifacts_digest": _sha256_bytes(hash_body),
        "protocol_deviation": {
            "path": DEVIATION,
            "content_hash": hash_file(REPO_ROOT / DEVIATION),
            "note": "The subject was consulted out-of-band before probe entry. That access is "
                    "recorded, void, and inadmissible; it appears in the subject's logs and is "
                    "referenced here so no future reader finds it unexplained.",
        },
        "emits_evidence": False,
        "note": (
            "Raw artifacts only. This run emits no Evidence, attributes nothing, and concludes "
            "nothing. Evidence emission closes the frozen gate's pre-registration window "
            "permanently and is a reviewed act performed from these artifacts. `artifacts_digest` "
            "is the sha256 of artifact-hashes.json, which covers every raw artifact and the "
            "executing source: cite this manifest as the reproducible root."
        ),
    }
    _write_json(run_dir / "manifest.json", manifest)
    return run_dir


def main() -> int:
    """The production CLI. It accepts a run id. It accepts nothing else, on purpose."""
    import sys

    if len(sys.argv) != 2:
        print("usage: executor.py <run_id>", file=sys.stderr)
        return 2
    try:
        run_dir = execute_run(sys.argv[1])
    except ProtocolRefusal as r:
        print(f"REFUSED: {r}", file=sys.stderr)
        return 3
    manifest = json.loads((run_dir / "manifest.json").read_text())
    print(f"run dir: {run_dir}")
    print(
        f"completed {manifest['samples_completed']}/{manifest['required_completed_samples']}, "
        f"aborted {manifest['samples_aborted']}, missed {manifest['barriers_missed']}, "
        f"partial={manifest['partial']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

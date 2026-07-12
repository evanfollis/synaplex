"""Study-specific executor for artifact-coherence-transfer-v1. Raw artifacts only.

Not a framework. ADR-0049 is explicit that this cycle gets *one* instrumented vertical
slice and no generic controller, so this module hard-binds the single pre-registered
subject and the single pre-registered schedule and knows how to do nothing else. The
generic `lab/runner/` exists and was deliberately not reused: it conflates an aborted cell
with a completed one (`completed += 1` runs on both branches), and this study's whole
denominator argument depends on that distinction being airtight.

## What this file may and may not do

- **It does not emit Evidence.** Evidence closes the frozen gate's pre-registration window
  permanently (canon rule 10). That is a reviewed epistemic act performed *from* these
  artifacts, never a side effect of a script finishing. `lab.canon.emit` is not imported
  here and `test_executor.py` asserts against the source that it never will be.
- **It does not attribute.** It records what the browser saw and applies the mechanical
  pass criterion that `methodology.md` fixed in advance. Whether a *failure* is
  attributable to artifact-set incoherence is the reviewed step, and a failure this module
  cannot mechanically attribute is inconclusive — not favorable, not unfavorable.
- **It is read-only against the subject.** Browser `GET` navigation plus `systemctl show`
  plus a `/health` read. No build, deploy, restart, application-state write, authenticated
  endpoint substitution, or deliberate impairment. The subject's `/mcp/` endpoint is never
  invoked; `methodology.md` forbids substituting it for the browser outcome.

## The denominator cannot be shrunk from here

`BARRIERS` and `REQUIRED_SAMPLES` below are **cross-checked against the frozen gate in
canon** (`Policy 5273e9a31e92f6c3`, `class: frozen`, `amendment_authority: []`) and the run
refuses to start if they disagree. The denominator therefore does not live in this file —
it lives in an append-only, hash-validated, unamendable envelope. Editing the constants here
to quietly drop a sample makes the executor *refuse to run*, which is the point: an eval
whose sample count can be edited by the party reading the results has no pre-registration at
all.

## Aborts carry no outcome

A completed sample is written to `samples/` and is **never** replaced on resume. An abort is
written to `aborts/` and carries no `observed_at` and no `mechanical_outcome` — the schema
gives it nowhere to put a result, so coding "the tool broke" as "the subject failed" is
structurally unavailable rather than merely discouraged. A run that aborts a sample is
*partial*, and a partial run is reported as such rather than concluding from two samples out
of three.

## Barrier semantics — an interpretive choice, declared not hidden

`methodology.md` is ambiguous here and this module does not get to resolve that quietly.
The frozen gate fixes `browser_barriers_seconds: [1, 30, 120]` but not their semantics, and
the prose admits two readings:

    (a) post-load dwell:    each sample loads, then waits 1s / 30s / 120s before capturing.
    (b) elapsed-from-start: each sample is *taken* at t=1s / 30s / 120s from run start,
                            each with the fixed 1s post-load dwell that B2 names.

This module implements **(b)**, because B2 fixes the dwell at "wait 1 second" for the
repeated unit B1-B2, and B3/B4 say to *repeat that unit* "after 30 seconds" / "after 120
seconds" — which makes 30 and 120 offsets between samples, not dwells within them. Under (a),
the "1" in the barrier list would be a dwell while 30 and 120 would also be dwells, and B2's
explicit "wait 1 second" would contradict the 30s and 120s samples.

The choice is recorded in the run manifest as `barrier_interpretation` and was put to
opposing review **before** any sample was taken. If the reviewer prefers (a), this module
changes before the run — not after seeing results.
"""

from __future__ import annotations

import hashlib
import json
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
# with an explicit `RunPlan` instead, which is how it finishes in seconds without the real
# 1/30/120 waits — and which is why a fast test can never silently become the shape of the real
# run. A test-only barrier schedule that could reach the production CLI would be a way to run a
# 3-sample study with 3 one-second samples and file it as the pre-registered one.
BARRIERS: Final[tuple[int, ...]] = (1, 30, 120)
REQUIRED_SAMPLES: Final[int] = 3
POST_LOAD_DWELL_S: Final[float] = 1.0

# Pinned so the measurement is reproducible rather than a function of whatever the host happened
# to have. `TOOLING.md` records the exact provisioning commands and the host packages they added.
PINNED_PLAYWRIGHT: Final[str] = "1.61.0"

BARRIER_INTERPRETATION = (
    "elapsed-from-run-start: sample k is taken when elapsed >= BARRIERS[k] seconds measured "
    "from B0 completion, each in a fresh browser context, each capturing after the fixed 1s "
    "post-load dwell that methodology.md B2 names. See executor.py module docstring."
)

METHODOLOGY = f"lab/evals/{EVAL_ID}/methodology.md"
DEVIATION = f"lab/evals/{EVAL_ID}/PROTOCOL-DEVIATION-2026-07-12-preprobe-target-consultation.md"
RUNS_ROOT = REPO_ROOT / "lab" / "runs"

NAV_TIMEOUT_MS = 30_000

# Resource types whose failure changes what the application *does*, as opposed to how it looks.
# A stale document referencing a hashed bundle that no longer exists is the canonical
# artifact-incoherence symptom, and it arrives as an HTTP 404 on a `script` or a `fetch`.
#
# This channel exists because `methodology.md` names "no failed behavior-critical request" as a
# condition in its own right, and the only faithful way to check that is to look at the response
# status of behavior-critical requests.
#
# It is *not* the sole detector, and the fixture suite is what established that rather than the
# author's guess: Chromium happens to abort a 404'd `<script>` (so `requestfailed` fires) and to
# console-log "Failed to load resource" for a 404'd `fetch` (so `console_errors` fires). Both
# would catch a stale bundle today. But both are Chromium *logging policy*, not the criterion —
# inferring "a behavior-critical request failed" from the presence of an English console string
# is inference, and it silently changes meaning when the browser does. This channel observes the
# thing the methodology actually names. The overlap is redundancy, and redundancy is the correct
# posture for the one failure mode the study exists to detect.
BEHAVIOR_CRITICAL = frozenset({"document", "script", "stylesheet", "fetch", "xhr"})


class ProtocolRefusal(RuntimeError):
    """The run may not proceed. Raised before the subject is touched, never after."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _sha256_bytes(b: bytes) -> str:
    return f"sha256:{hashlib.sha256(b).hexdigest()}"


# --- preflight: the run refuses to start against a drifted pre-registration ----------


def _frozen_gate() -> dict:
    gates = [p for p in load_all("Policy") if p.get("bound_to_claim_id") == CLAIM_ID]
    if len(gates) != 1:
        raise ProtocolRefusal(f"expected exactly 1 frozen gate on {CLAIM_ID}, found {len(gates)}")
    gate = gates[0]
    if gate["id"] != GATE_ID or gate["class"] != "frozen" or gate["amendment_authority"] != []:
        raise ProtocolRefusal(f"gate {gate['id']} is not the unamendable frozen gate {GATE_ID}")
    return gate


def tooling() -> dict:
    """The measuring instrument, recorded into the run. A result produced by a different browser
    is a different result, and a manifest that cannot name its instrument cannot support a
    replay. See `TOOLING.md` for the provisioning commands that produce this state."""
    try:
        pw = version("playwright")
    except PackageNotFoundError:  # pragma: no cover
        pw = "MISSING"
    return {"playwright": pw, "playwright_pinned": PINNED_PLAYWRIGHT, "browser": "chromium"}


def preflight() -> dict:
    """Verify the pre-registration is intact and this module still agrees with it.

    Runs before the subject is consulted. Every failure here is a refusal to observe, not a
    warning: an executor that runs a schedule the frozen gate does not authorize is not
    measuring the Claim that was pre-registered.
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
        raise ProtocolRefusal(f"subject {SUBJECT!r} is not the frozen population {value['population']}")
    if value["primary_outcome"] != "browser_behavior":
        raise ProtocolRefusal("frozen gate does not name browser_behavior as the primary outcome")

    tools = tooling()
    if tools["playwright"] != PINNED_PLAYWRIGHT:
        raise ProtocolRefusal(
            f"playwright {tools['playwright']} is installed but the study pins "
            f"{PINNED_PLAYWRIGHT}. Reprovision per TOOLING.md rather than measuring with an "
            "instrument the pre-registration did not declare."
        )

    return {
        "claim_id": CLAIM_ID,
        "gate_id": gate["id"],
        "methodology_hash": live_hash,
        "barriers_from_frozen_gate": list(value["browser_barriers_seconds"]),
        "required_completed_samples": value["required_completed_samples"],
        "tooling": tools,
    }


# --- B0: identity and liveness (diagnostic, never a success oracle) ------------------


def _git_identity(repo: Path) -> dict:
    def _run(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=30
        ).stdout.strip()

    porcelain = _run("status", "--porcelain")
    return {
        "repo": str(repo),
        "commit": _run("rev-parse", "HEAD"),
        "dirty": bool(porcelain),
        "dirty_paths": porcelain.splitlines()[:50],
    }


def _unit_identity(unit: str) -> dict:
    """`systemctl show` is a read. It does not start, stop, restart, or reload anything."""
    props = "ActiveState,SubState,MainPID,ExecStart,FragmentPath,ActiveEnterTimestamp,NRestarts"
    out = subprocess.run(
        ["systemctl", "show", unit, "-p", props], capture_output=True, text=True, timeout=30
    ).stdout.strip()
    parsed = dict(line.split("=", 1) for line in out.splitlines() if "=" in line)
    return {"unit": unit, **parsed}


def _health(url: str) -> dict:
    """Liveness. methodology.md §Outcomes: recorded separately, and it *cannot make a failed
    browser sample pass*. It is a diagnostic that explains a browser result, never one that
    overrides it."""
    started = _now()
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:  # GET. Read-only.
            body = resp.read()
            return {
                "url": url,
                "status": resp.status,
                "body_sha256": _sha256_bytes(body),
                "body_bytes": len(body),
                "body_text": body.decode("utf-8", "replace")[:500],
                "observed_at": started,
                "error": None,
            }
    except Exception as e:  # noqa: BLE001 — a dead liveness probe is data, not a crash
        return {"url": url, "status": None, "observed_at": started, "error": f"{type(e).__name__}: {e}"}


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

    Every request the page issues is recorded, including its method, so a reviewer can verify
    from the artifact alone that the observation was read-only rather than take this
    docstring's word for it.
    """
    from playwright.sync_api import sync_playwright

    console_errors: list[dict] = []
    page_errors: list[str] = []
    failed_requests: list[dict] = []
    requests: list[dict] = []
    responses: list[dict] = []

    started_at = _now()
    t0 = time.monotonic()

    with sync_playwright() as p:
        browser = p.chromium.launch()  # fresh browser => fresh cache/storage, per B1
        tool = {**tooling(), "browser_version": browser.version}
        context = browser.new_context()
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

        response = page.goto(url, wait_until="load", timeout=NAV_TIMEOUT_MS)

        time.sleep(dwell_s)  # B2: after load completion, wait 1 second, then capture.

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
                r for r in responses
                if not r["ok"] and r["resource_type"] in BEHAVIOR_CRITICAL
            ],
            "requests": requests,
            "responses": responses,
            "tool": tool,
        }
        context.close()
        browser.close()

    sample["mechanical_outcome"] = mechanical_outcome(sample)
    return sample


def mechanical_outcome(sample: dict) -> dict:
    """Apply the pass criterion `methodology.md` §Outcomes fixed *before* the run.

    Deterministic and pre-registered, so computing it here is measurement, not selection: a
    sample passes only when the browser reached the declared route, received the expected
    application identity, and recorded no failed behavior-critical request and no JavaScript
    error.

    **Attribution is deliberately absent.** Whether a failure is due to artifact-set
    incoherence — as opposed to network, TLS, or an unrelated application fault — is the
    reviewed epistemic step, and §Falsification says an unresolvable attribution is
    *inconclusive*, not supportive. This function never writes that word.
    """
    reasons: list[str] = []

    if not sample["response"]["ok"]:
        reasons.append(f"http status {sample['response']['status']} is not ok")
    if EXPECTED_IDENTITY not in sample["visible_text"]:
        reasons.append(f"expected application identity {EXPECTED_IDENTITY!r} not in visible text")
    if sample["failed_requests"]:
        reasons.append(f"{len(sample['failed_requests'])} network-failed request(s)")
    bad = sample.get("bad_behavior_critical_responses", [])
    if bad:
        # The 404-on-a-hashed-bundle case. See BEHAVIOR_CRITICAL.
        reasons.append(
            f"{len(bad)} behavior-critical request(s) returned an error status: "
            + ", ".join(f"{r['status']} {r['resource_type']}" for r in bad[:5])
        )
    if sample["console_errors"]:
        reasons.append(f"{len(sample['console_errors'])} console error(s)")
    if sample["page_errors"]:
        reasons.append(f"{len(sample['page_errors'])} uncaught javascript error(s)")

    return {
        "pass": not reasons,
        "reasons": reasons,
        "criterion": "methodology.md §Outcomes (pre-registered, hash-bound)",
        "attribution": "NOT COMPUTED — reviewed epistemic step, see §Falsification",
    }


# --- the run -------------------------------------------------------------------------


@dataclass(frozen=True)
class RunPlan:
    """Everything `_execute` needs, supplied explicitly. The seam between the real run and the
    fixture suite.

    The fixture suite builds one of these directly with a no-op `sleep`, a stub `sampler`, and a
    short barrier list, so it finishes in seconds instead of sitting through 1/30/120. The
    production path builds one via `production_plan()`, which takes those values from the frozen
    gate and cannot be told otherwise. Nothing on the CLI reaches this object.
    """

    run_id: str
    url: str
    barriers: tuple[int, ...]
    runs_root: Path
    sampler: Callable[..., dict]
    sleep: Callable[[float], None]
    b0: dict
    preflight_result: dict | None = None
    extra: dict = field(default_factory=dict)

    @property
    def is_preregistered_subject(self) -> bool:
        return self.url == SUBJECT_URL


def production_plan(run_id: str) -> RunPlan:
    """The one real plan. Barriers come from the frozen gate; the clock is the real clock."""
    checked = preflight()
    return RunPlan(
        run_id=run_id,
        url=SUBJECT_URL,
        barriers=BARRIERS,
        runs_root=RUNS_ROOT,
        sampler=capture_sample,
        sleep=time.sleep,
        b0=b0_identity(),
        preflight_result=checked,
    )


def execute_run(run_id: str) -> Path:
    """Production entry point. Takes a run id and **nothing else** — no barrier override, no
    sampler injection, no URL, no preflight skip. The pre-registered schedule is not a
    parameter."""
    return _execute(production_plan(run_id))


def _execute(plan: RunPlan) -> Path:
    """Execute a plan idempotently. Emits raw artifacts and nothing else.

    Resume semantics:
      - a **completed** sample on disk is never re-run and never replaced;
      - an **aborted** sample carries no outcome and does not fill its slot, so the run stays
        partial until that slot is genuinely completed;
      - retries are recorded as additional abort artifacts, never as replacements.
    """
    checked = plan.preflight_result
    run_dir = plan.runs_root / EVAL_ID / plan.run_id
    (run_dir / "samples").mkdir(parents=True, exist_ok=True)
    (run_dir / "aborts").mkdir(parents=True, exist_ok=True)

    sched, take, url = plan.barriers, plan.sampler, plan.url
    is_target = plan.is_preregistered_subject

    b0_record = plan.b0
    (run_dir / "b0.json").write_text(
        json.dumps(b0_record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    t0 = time.monotonic()
    completed = aborted = resumed = 0

    for barrier in sched:
        slot = run_dir / "samples" / f"b{barrier}s.json"
        if slot.exists():
            resumed += 1
            completed += 1
            continue  # never re-run, never replace

        wait = barrier - (time.monotonic() - t0)
        if wait > 0:
            plan.sleep(wait)

        try:
            sample = take(url, barrier_seconds=barrier)
        except Exception as e:  # noqa: BLE001
            aborted += 1
            n = len(list((run_dir / "aborts").glob(f"b{barrier}s-attempt-*.json"))) + 1
            # No observed_at. No mechanical_outcome. An abort has nowhere to put a result.
            (run_dir / "aborts" / f"b{barrier}s-attempt-{n}.json").write_text(
                json.dumps(
                    {
                        "barrier_seconds": barrier,
                        "status": "aborted",
                        "attempt": n,
                        "aborted_at": _now(),
                        "abort_reason": f"{type(e).__name__}: {e}",
                        "note": "An abort carries no outcome. It does not fill its sample slot "
                                "and does not shrink the denominator.",
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            continue

        slot.write_text(json.dumps(sample, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        completed += 1

    manifest = {
        "eval_id": EVAL_ID,
        "run_id": plan.run_id,
        "generated_at": _now(),
        "tooling": tooling(),
        "claim_id": CLAIM_ID,
        "frozen_gate_id": GATE_ID,
        "preflight": checked,
        "subject": {"name": SUBJECT, "url": url, "unit": SUBJECT_UNIT},
        "is_preregistered_subject": is_target,
        "barrier_schedule": list(sched),
        "barrier_interpretation": BARRIER_INTERPRETATION,
        "post_load_dwell_s": POST_LOAD_DWELL_S,
        "expected_identity": EXPECTED_IDENTITY,
        "required_completed_samples": REQUIRED_SAMPLES,
        "samples_completed": completed,
        "samples_resumed": resumed,
        "samples_aborted": aborted,
        "partial": completed < REQUIRED_SAMPLES,
        "b0": b0_record,
        "protocol_deviation": {
            "path": DEVIATION,
            "content_hash": hash_file(REPO_ROOT / DEVIATION),
            "note": "The subject was consulted out-of-band before probe entry. That access is "
                    "recorded, void, and inadmissible; it appears in the subject's logs and is "
                    "referenced here so no future reader finds it unexplained.",
        },
        "emits_evidence": False,
        "read_only": True,
        "note": (
            "Raw artifacts only. This run emits no Evidence, attributes nothing, and concludes "
            "nothing. Evidence emission closes the frozen gate's pre-registration window "
            "permanently and is a reviewed act performed from these artifacts."
        ),
    }
    mpath = run_dir / "manifest.json"
    mpath.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    hashes = {
        str(p.relative_to(run_dir)): hash_file(p)
        for p in sorted(run_dir.rglob("*.json"))
        if p != mpath
    }
    (run_dir / "artifact-hashes.json").write_text(
        json.dumps(hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return run_dir


def main() -> int:
    """The production CLI. It accepts a run id. It accepts nothing else, on purpose."""
    import sys

    if len(sys.argv) != 2:
        print("usage: executor.py <run_id>", file=sys.stderr)
        return 2
    run_dir = execute_run(sys.argv[1])
    manifest = json.loads((run_dir / "manifest.json").read_text())
    print(f"run dir: {run_dir}")
    print(
        f"completed {manifest['samples_completed']}/{manifest['required_completed_samples']}, "
        f"aborted {manifest['samples_aborted']}, partial={manifest['partial']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

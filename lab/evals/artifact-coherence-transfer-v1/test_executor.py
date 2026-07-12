"""Verifiable assertions for the artifact-coherence-transfer-v1 executor.

    PYTHONPATH=. .venv/bin/python lab/evals/artifact-coherence-transfer-v1/test_executor.py

**No test here touches the pre-registered subject.** Every browser assertion runs against a local
fixture server on 127.0.0.1 serving synthetic pages, and no test writes into the real canon store.
Pointing this suite at launchpad-lint would be an unlogged observation outside a run directory —
which is the exact protocol deviation this study already has one of, and one is enough.

## Why the fail-injection suite exists

The executor's author had already seen the subject serving a healthy 200 before this file was
written (see `PROTOCOL-DEVIATION-2026-07-12-preprobe-target-consultation.md`). An author who
expects a pass can write a detector that cannot fail and never notice, because the run passes
either way. Promising to have been careful is not a control.

So the control is mechanical: the executor is made to **produce a failing sample on demand**, once
per failure channel the pre-registered criterion names. A detector that has been shown to fire is a
detector; one that has only ever been shown to stay quiet is a light switch with no bulb in it.

What the suite actually established, stated precisely because an earlier draft of this docstring
overstated it: the executor's original three channels (console errors, uncaught exceptions,
`requestfailed`) *would* have caught a stale bundle — but only incidentally. Chromium aborts a
404'd `<script>` and console-logs a 404'd `fetch`. Both are Chromium **logging policy**, not the
pre-registered criterion. The `bad_behavior_critical_responses` channel observes the condition
`methodology.md` actually names.

## The second review pass

Ten blocking findings came back on the first executor from an independent Codex review. The
regressions for them are grouped under `--- blocking review` below. The ones that would have
silently corrupted the science, rather than merely crashed:

- **resume re-timed the schedule** — a B1 from yesterday could be spliced with a B120 from today
  and filed as one run;
- **read-only was observed, not enforced** — a subject page could have issued a POST and the
  executor would have faithfully recorded the mutation it permitted;
- **preflight did not require probe entry** — the executor could run against a Claim that, on
  replay, was never in a state where observation was authorized. That is precisely the hole the
  recorded deviation fell through;
- **identity used substring containment** — a page rendering the expected sentence *plus* an error
  banner would have passed.
"""

from __future__ import annotations

import http.server
import importlib.util
import json
import os
import shutil
import socket
import sys
import tempfile
import threading
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

# The study directory is named for the study, not for Python — `artifact-coherence-transfer-v1` is
# not an importable identifier. Load the executor by path rather than renaming the study directory
# to suit the import system.
_spec = importlib.util.spec_from_file_location(
    "acx_executor", Path(__file__).parent / "executor.py"
)
executor = importlib.util.module_from_spec(_spec)
# Register before exec: @dataclass resolves annotations via sys.modules[cls.__module__], and a
# module loaded by path is not there yet.
sys.modules["acx_executor"] = executor
_spec.loader.exec_module(executor)

RESULTS: list[str] = []


def _ok(msg: str) -> None:
    RESULTS.append(msg)
    print(f"  ok   {msg}")


IDENTITY = executor.EXPECTED_IDENTITY

PAGES: dict[str, tuple[int, str, bytes]] = {
    "/healthy": (200, "text/html", f"<html><body>{IDENTITY}</body></html>".encode()),
    "/wrong-identity": (200, "text/html", b"<html><body>Some other service</body></html>"),
    # The identity string is present, but so is an error banner. Substring containment passes this
    # page; exact comparison does not. This is the shape a contaminated author is most likely to
    # wave through.
    "/identity-plus-error": (
        200, "text/html",
        f"<html><body>{IDENTITY}<p>Internal Server Error: upstream unavailable</p>"
        f"</body></html>".encode(),
    ),
    "/console-error": (
        200, "text/html",
        f"<html><body>{IDENTITY}<script>console.error('boom')</script></body></html>".encode(),
    ),
    "/js-error": (
        200, "text/html",
        f"<html><body>{IDENTITY}<script>throw new Error('kaboom')</script></body></html>".encode(),
    ),
    # The artifact-incoherence shape: a 200 document with the right identity, referencing a hashed
    # bundle that is gone. What the Command incident looked like from a browser.
    "/stale-bundle": (
        200, "text/html",
        f"<html><body>{IDENTITY}<script src='/assets/app.9f3c1a.js'></script></body></html>".encode(),
    ),
    # The same incoherence as a 404'd data fetch. Chromium aborts a 404'd <script> (so
    # `requestfailed` fires), but a 404'd fetch() is a completed exchange and fires none — so this
    # page separates the response-status channel from the network-failure channel.
    "/stale-fetch": (
        200, "text/html",
        f"<html><body>{IDENTITY}<script>fetch('/api/data.json')</script></body></html>".encode(),
    ),
    "/dead-socket": (
        200, "text/html",
        f"<html><body>{IDENTITY}<script src='http://127.0.0.1:1/x.js'></script></body></html>".encode(),
    ),
    # A hostile subject: the page tries to mutate its own server. The route gate must abort this
    # before it reaches the network.
    "/tries-to-mutate": (
        200, "text/html",
        f"<html><body>{IDENTITY}"
        f"<script>fetch('/mutate',{{method:'POST',body:'x'}})</script></body></html>".encode(),
    ),
}


class _Handler(http.server.BaseHTTPRequestHandler):
    seen: list[tuple[str, str]] = []

    def do_GET(self) -> None:  # noqa: N802
        _Handler.seen.append(("GET", self.path))
        if self.path in PAGES:
            status, ctype, body = PAGES[self.path]
        elif self.path.endswith(".js"):
            # A missing bundle served the way a real origin serves one: 404 with a JS content-type.
            # The MIME type is deliberate — a `text/plain` 404 would additionally trip Chromium's
            # Opaque Response Blocking, and the fixture would then be testing ORB rather than the
            # study's failure mode.
            status, ctype, body = 404, "application/javascript", b"// gone"
        else:
            status, ctype, body = 404, "text/plain", b"not found"
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _record_and_405(self) -> None:
        _Handler.seen.append((self.command, self.path))
        self.send_response(405)
        self.end_headers()

    do_POST = do_PUT = do_DELETE = do_PATCH = _record_and_405  # type: ignore[assignment]

    def log_message(self, *a) -> None:  # silence
        pass


class fixture_server:
    """A local synthetic subject. Never the pre-registered one."""

    def __enter__(self) -> str:
        _Handler.seen = []
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()
        self.httpd = http.server.HTTPServer(("127.0.0.1", port), _Handler)
        self.t = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.t.start()
        return f"http://127.0.0.1:{port}"

    def __exit__(self, *exc) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()


class relocated_store:
    """Point the canon store at a scratch dir. The real store is read, never written."""

    def __enter__(self) -> Path:
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["SYNAPLEX_CANON_ROOT"] = self._tmp.name
        return Path(self._tmp.name)

    def __exit__(self, *exc) -> None:
        os.environ.pop("SYNAPLEX_CANON_ROOT", None)
        self._tmp.cleanup()


def _sample(base: str, path: str) -> dict:
    return executor.capture_sample(f"{base}{path}", barrier_seconds=1, dwell_s=0.2)


def _stub_sampler(url, *, barrier_seconds, **kw) -> dict:
    return {
        "barrier_seconds": barrier_seconds, "status": "completed",
        "observed_at": "2026-07-12T00:00:00Z", "consulted_at": "2026-07-12T00:00:00Z",
        "response": {"ok": True, "status": 200},
        "visible_text": IDENTITY, "console_errors": [], "page_errors": [],
        "failed_requests": [], "bad_behavior_critical_responses": [], "blocked_requests": [],
        "mechanical_outcome": {"pass": True, "reasons": []},
    }


def _fixture_plan(td: str, **over) -> "executor.RunPlan":
    """A RunPlan with an injected clock. The fixture suite must never sit through 1/30/120 — a test
    that takes two and a half minutes is a test that gets skipped, and a skipped denominator check
    protects nothing. The *schedule* is real; only the waiting is stubbed."""
    slept: list[float] = []
    base = dict(
        run_id="fixture",
        url="http://127.0.0.1:1/",
        barriers=(1, 30, 120),
        runs_root=Path(td),
        sampler=_stub_sampler,
        sleep=slept.append,
        b0_fn=lambda: {"fixture": True},
        clock=lambda: 1_000_000.0,
        preflight_result=None,
    )
    base.update(over)
    plan = executor.RunPlan(**base)
    plan.extra["slept"] = slept
    return plan


# --- the executor can pass, and can fail. Both are proven. ---------------------------


def test_a_healthy_page_passes() -> None:
    """The control. If this failed, every failure below would be meaningless."""
    with fixture_server() as base:
        s = _sample(base, "/healthy")
    assert s["mechanical_outcome"]["pass"], s["mechanical_outcome"]["reasons"]
    assert s["status"] == "completed" and s["observed_at"] and s["consulted_at"]
    _ok("PASS  a healthy page yields a passing sample (the detector is not stuck on FAIL)")


def test_wrong_identity_fails() -> None:
    with fixture_server() as base:
        s = _sample(base, "/wrong-identity")
    assert not s["mechanical_outcome"]["pass"]
    assert not s["mechanical_outcome"]["identity_exact"]
    _ok("FAIL  a 200 without the pre-registered application identity fails")


def test_console_error_fails() -> None:
    with fixture_server() as base:
        s = _sample(base, "/console-error")
    assert not s["mechanical_outcome"]["pass"]
    assert s["console_errors"], "console error was not captured at all"
    _ok("FAIL  a console error fails the sample")


def test_uncaught_javascript_error_fails() -> None:
    with fixture_server() as base:
        s = _sample(base, "/js-error")
    assert not s["mechanical_outcome"]["pass"]
    assert s["page_errors"], "uncaught JS exception was not captured at all"
    _ok("FAIL  an uncaught JavaScript error fails the sample")


def test_stale_bundle_404_fails() -> None:
    with fixture_server() as base:
        s = _sample(base, "/stale-bundle")
    assert s["bad_behavior_critical_responses"], "the 404 on a <script> was not recorded at all"
    assert not s["mechanical_outcome"]["pass"], (
        "A stale document referencing a bundle that no longer exists PASSED. This is the exact "
        "failure the study is built to detect."
    )
    _ok("FAIL  a 404 on a behavior-critical <script> fails (the stale-bundle shape)")


def test_stale_fetch_404_fails() -> None:
    """The case that separates the response-status channel from the network-failure channel. The
    premise assertions pin *observed* browser behavior, which is the only reason the author's
    original guess about it got corrected."""
    with fixture_server() as base:
        s = executor.capture_sample(f"{base}/stale-fetch", barrier_seconds=1, dwell_s=0.5)

    assert not s["failed_requests"], (
        "premise check: a 404'd fetch() is not a network failure, so requestfailed must stay empty. "
        f"It did not: {s['failed_requests']}. Recheck the BEHAVIOR_CRITICAL reasoning."
    )
    assert not s["page_errors"], "premise check: no uncaught exception"
    assert s["bad_behavior_critical_responses"], "the 404'd fetch was not recorded"
    assert not s["mechanical_outcome"]["pass"]
    assert "behavior-critical" in " ".join(s["mechanical_outcome"]["reasons"])
    _ok("FAIL  a 404'd fetch fails; response-status channel fires where requestfailed cannot")


def test_network_failed_request_fails() -> None:
    with fixture_server() as base:
        s = _sample(base, "/dead-socket")
    assert not s["mechanical_outcome"]["pass"]
    assert s["failed_requests"], "connection-refused script was not captured"
    _ok("FAIL  a network-failed behavior-critical request fails the sample")


# --- blocking review #9: identity is exact, not a substring --------------------------


def test_identity_plus_error_banner_fails() -> None:
    """Review finding 9. The page renders the expected sentence AND an error. Substring
    containment — what the executor used to do — passes it."""
    with fixture_server() as base:
        s = _sample(base, "/identity-plus-error")
    mo = s["mechanical_outcome"]
    assert mo["identity_contains"], "premise: the expected identity IS present as a substring"
    assert not mo["identity_exact"], "the page is not exactly the healthy application"
    assert not mo["pass"], (
        "a page rendering the expected identity plus 'Internal Server Error' PASSED. Substring "
        "containment is too permissive a comparator for a criterion this load-bearing."
    )
    _ok("ID    identity+error-banner fails: comparison is exact after whitespace normalization")


# --- blocking review #5: read-only is ENFORCED, not observed -------------------------


def test_a_mutating_request_is_blocked_before_it_reaches_the_network() -> None:
    """Review finding 5. The old executor recorded a request's method *after* allowing it. A
    hostile or broken subject page could therefore mutate its own server and the executor would
    faithfully log the mutation it had just permitted.

    Proven from the fixture server's own request log: it must never see the POST.
    """
    with fixture_server() as base:
        s = _sample(base, "/tries-to-mutate")
        methods = {m for m, _ in _Handler.seen}

    assert "POST" not in methods, (
        f"the fixture server RECEIVED a mutating request: {[x for x in _Handler.seen if x[0] != 'GET']}. "
        "Read-only is not enforced."
    )
    assert methods == {"GET"}, f"non-GET reached the network: {methods - {'GET'}}"
    assert s["blocked_requests"], "the blocked mutation attempt was not recorded"
    assert s["mechanical_outcome"]["protocol_invalid"] is True
    assert not s["mechanical_outcome"]["pass"], "a sample with a blocked mutation attempt passed"
    _ok("RO    a page's POST is aborted at the route gate; the server never sees it")


def test_the_executor_only_ever_issues_gets() -> None:
    with fixture_server() as base:
        _sample(base, "/healthy")
        methods = {m for m, _ in _Handler.seen}
    assert methods == {"GET"}, f"executor issued non-GET methods: {methods - {'GET'}}"
    _ok("RO    every request the executor issued was a GET (server-side log)")


def _code_only(path: Path) -> tuple[list[str], list[str], list[str]]:
    """Split a module into (executable string literals, imported names, attribute names).

    Docstrings are excluded. A text scan cannot tell a docstring promising *"the MCP endpoint is
    never invoked"* from code invoking it — it flags both — so it is worthless for exactly the file
    whose docstring explains its own restraint. `guard.py` walks the AST for the same reason.
    """
    import ast

    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                if isinstance(body[0].value.value, str):
                    docstrings.add(id(body[0].value))

    strings, imports, attrs = [], [], []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if id(node) not in docstrings:
                strings.append(node.value)
        elif isinstance(node, ast.Import):
            imports += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            imports += [f"{node.module}.{a.name}" for a in node.names if node.module]
        elif isinstance(node, ast.Attribute):
            attrs.append(node.attr)
    return strings, imports, attrs


def test_source_contains_no_mutating_operation() -> None:
    strings, _, attrs = _code_only(Path(executor.__file__))

    banned = ("systemctl start", "systemctl stop", "systemctl restart", "systemctl reload",
              "npm run build", "wrangler", "git push", "docker")
    for s in strings:
        for token in banned:
            assert token not in s, f"executor's executable code contains {token!r} in {s!r}"

    # HTTP verbs are matched exactly, not as substrings — "NOT COMPUTED" contains "PUT", and a check
    # that flags the word "computed" as a mutation is a check nobody will keep.
    for s in strings:
        assert s.strip().upper() not in {"POST", "PUT", "DELETE", "PATCH"}, (
            f"executor's executable code names a mutating HTTP method: {s!r}"
        )
    for verb in ("post", "put", "patch"):
        assert verb not in attrs, f"executor calls a mutating method: .{verb}()"

    assert not any("/mcp" in s for s in strings), (
        "executor's executable code references the authenticated MCP endpoint. methodology.md "
        "forbids substituting it for the browser outcome."
    )
    _ok("RO    executor's executable code has no mutating operation and no MCP substitution")


def test_the_executor_cannot_emit_evidence() -> None:
    strings, imports, attrs = _code_only(Path(executor.__file__))

    for mod in imports:
        assert "canon.emit" not in mod, f"executor imports the canon emitter: {mod!r}"
    for fn in ("emit_evidence", "emit_decision", "emit_claim", "emit_frozen_gate",
               "emit_phase_transition", "emit_methodology_log"):
        assert fn not in attrs, f"executor calls the canon emitter: {fn}()"
        assert not any(fn in s for s in strings), f"executor reaches the emitter dynamically: {fn}"

    assert "importlib.import_module" not in imports, "executor can import dynamically"
    assert "import_module" not in attrs and "__import__" not in attrs
    _ok("EV    executor cannot emit Evidence, a Decision, a Claim, or a gate (import+call graph)")


# --- blocking review #6: probe entry is a precondition, not a convention -------------


def test_production_preflight_refuses_without_probe_entry() -> None:
    """Review finding 6, and the hole the recorded deviation fell through.

    The Claim is in canon and the gate is frozen, but no `phase_transition(-> probe)` and no
    `methodology_log` exist. Canon says a Claim's phase lives in the event log, so on replay this
    Claim was never in a state where observing its subject was authorized. Production must refuse.
    Asserted against the REAL store, which this test reads and never writes.
    """
    executor.verify_pre_registration()  # the pre-registration itself is intact

    try:
        executor.preflight()
    except executor.ProtocolRefusal as r:
        msg = str(r)
        assert "probe" in msg or "methodology_log" in msg, msg
    else:
        raise AssertionError(
            "preflight ACCEPTED a run against a Claim that has never entered probe. The executor "
            "would observe the subject with no probe-entry event in canon — exactly the ordering "
            "violation the recorded protocol deviation is about."
        )
    _ok("PROBE production refuses to observe: the Claim has not entered probe (real store)")


def test_preflight_accepts_once_probe_entry_exists() -> None:
    """The same check must PASS once probe entry is legitimately emitted — otherwise it is not a
    gate, it is a wall. Runs entirely in a relocated store; the real one is untouched."""
    from lab.canon import store as canon_store

    with relocated_store() as root:
        for kind, envelope_id in (("claims", executor.CLAIM_ID), ("policies", executor.GATE_ID)):
            (root / kind).mkdir(parents=True, exist_ok=True)
            shutil.copy(REPO / "lab" / ".canon" / kind / f"{envelope_id}.json",
                        root / kind / f"{envelope_id}.json")

        from lab.canon.emit import artifact_pointer, emit_methodology_log, emit_phase_transition

        emit_phase_transition(claim=executor.CLAIM_ID, from_phase="draft", to_phase="probe")
        emit_methodology_log(
            claim=executor.CLAIM_ID,
            artifact=artifact_pointer(executor.METHODOLOGY),
            summary="probe entry for artifact-coherence-transfer-v1",
        )
        assert canon_store.canon_root() == root  # the relocation really took

        checked = executor.preflight()
        assert checked["claim_id"] == executor.CLAIM_ID
        assert checked["gate_id"] == executor.GATE_ID
        assert checked["barriers_from_frozen_gate"] == [1, 30, 120]
        assert checked["required_completed_samples"] == 3
        assert checked["probe_entered_at"]
        assert checked["methodology_log_ids"] and checked["phase_transition_ids"]
    _ok("PROBE preflight accepts once phase_transition(->probe) + methodology_log exist")


def test_preflight_refuses_a_methodology_that_changed_after_probe_entry() -> None:
    """A methodology_log pointing at a hash the live file no longer has means the pre-registration
    moved after probe entry. The run is void."""
    with relocated_store() as root:
        for kind, envelope_id in (("claims", executor.CLAIM_ID), ("policies", executor.GATE_ID)):
            (root / kind).mkdir(parents=True, exist_ok=True)
            shutil.copy(REPO / "lab" / ".canon" / kind / f"{envelope_id}.json",
                        root / kind / f"{envelope_id}.json")

        from lab.canon.emit import artifact_pointer, emit_methodology_log, emit_phase_transition

        emit_phase_transition(claim=executor.CLAIM_ID, from_phase="draft", to_phase="probe")
        # Log a DIFFERENT artifact — stands in for "the methodology was edited after probe entry".
        emit_methodology_log(
            claim=executor.CLAIM_ID,
            artifact=artifact_pointer(executor.DEVIATION),
            summary="wrong artifact",
        )
        try:
            executor.preflight()
        except executor.ProtocolRefusal as r:
            assert "methodology" in str(r).lower()
        else:
            raise AssertionError("preflight accepted a methodology_log for the wrong artifact")
    _ok("PROBE preflight refuses when the methodology_log hash != the live methodology")


# --- blocking review #1, #2: the run boundary and the absolute anchor ----------------


def test_b0_does_not_consult_the_subject_before_the_run_boundary_exists() -> None:
    """Review finding 1. B0 consults the target. If it runs before the run directory and anchor are
    on disk, a crash between B0 and the first write loses the observation entirely — the same
    failure class as the recorded deviation, which is an unlogged consultation."""
    saw: dict = {}

    with tempfile.TemporaryDirectory() as td:
        run_dir = Path(td) / executor.EVAL_ID / "boundary"

        def _b0():
            saw["run_json_existed"] = (run_dir / "run.json").is_file()
            saw["anchor"] = json.loads((run_dir / "run.json").read_text())["anchor_epoch"]
            return {"observed_at": "2026-07-12T00:00:00Z", "fixture": True}

        executor._execute(_fixture_plan(td, run_id="boundary", b0_fn=_b0))

        assert saw["run_json_existed"], (
            "B0 consulted the subject BEFORE run.json existed. A crash there leaves an observation "
            "that touched the target and preserved nothing."
        )
        assert saw["anchor"] == 1_000_000.0
        assert (run_dir / "b0.json").is_file()
    _ok("B0    the run boundary + anchor are durable before the subject is consulted")


def test_resume_schedules_against_the_persisted_anchor_and_never_samples_late() -> None:
    """Review finding 2, the one that would have silently corrupted the science.

    The old executor reset `time.monotonic()` on every invocation, so a resume re-timed the whole
    schedule. A B1 captured today and a B120 captured tomorrow would both be "completed" and the
    manifest would call them one run. They are not one run.
    """
    sampled: list[int] = []

    def _only_b1(url, *, barrier_seconds, **kw):
        if barrier_seconds != 1:
            raise executor.CaptureAborted("navigate", "simulated crash", consulted_at=None)
        sampled.append(barrier_seconds)
        return _stub_sampler(url, barrier_seconds=barrier_seconds)

    def _completes_anything(url, *, barrier_seconds, **kw):
        sampled.append(barrier_seconds)
        return _stub_sampler(url, barrier_seconds=barrier_seconds)

    with tempfile.TemporaryDirectory() as td:
        run_dir = Path(td) / executor.EVAL_ID / "anchored"

        # Attempt 1 at T. Only B1 completes; B30/B120 die.
        executor._execute(_fixture_plan(td, run_id="anchored", sampler=_only_b1))
        anchor1 = json.loads((run_dir / "run.json").read_text())["anchor_epoch"]
        assert sampled == [1]

        # Attempt 2, a day later, with a sampler that WOULD happily complete anything.
        sampled.clear()
        plan = _fixture_plan(td, run_id="anchored", sampler=_completes_anything,
                             clock=lambda: 1_000_000.0 + 86_400)
        executor._execute(plan)

        anchor2 = json.loads((run_dir / "run.json").read_text())["anchor_epoch"]
        assert anchor2 == anchor1, "resume moved the anchor; the schedule is not absolute"
        assert sampled == [], (
            f"resume sampled barriers {sampled} a day after the anchor. A B120 taken 24h after its "
            "B1 is not part of the same run."
        )

        missed = sorted(p.name for p in (run_dir / "aborts").glob("*-missed.json"))
        assert missed == ["b120s-missed.json", "b30s-missed.json"], missed
        rec = json.loads((run_dir / "aborts" / "b30s-missed.json").read_text())
        assert rec["abort_kind"] == "missed_barrier"
        assert rec["consulted_at"] is None
        assert "mechanical_outcome" not in rec and "observed_at" not in rec

        m = json.loads((run_dir / "manifest.json").read_text())
        assert m["samples_completed"] == 1 and m["barriers_missed"] == 2
        assert m["partial"] is True
        assert m["resumed_run"] is True
    _ok("ANCH  a closed barrier becomes a neutral missed_barrier; it is never sampled late")


# --- blocking review #3: an existing file is not a completed sample until it proves it ---


def test_a_tampered_sample_refuses_rather_than_counting_or_rerunning() -> None:
    with tempfile.TemporaryDirectory() as td:
        run_dir = Path(td) / executor.EVAL_ID / "tamper"
        executor._execute(_fixture_plan(td, run_id="tamper", barriers=(1,)))

        slot = run_dir / "samples" / "b1s.json"
        slot.write_text(slot.read_text().replace('"pass": true', '"pass": false'))  # tear/tamper

        try:
            executor._execute(_fixture_plan(td, run_id="tamper", barriers=(1,)))
        except executor.ProtocolRefusal as r:
            assert "hash mismatch" in str(r)
        else:
            raise AssertionError("a tampered completed sample was silently counted or re-run")
    _ok("TAMP  a modified sample refuses on its hash sidecar (never counted, never re-run)")


def test_a_truncated_sample_refuses() -> None:
    with tempfile.TemporaryDirectory() as td:
        run_dir = Path(td) / executor.EVAL_ID / "trunc"
        executor._execute(_fixture_plan(td, run_id="trunc", barriers=(1,)))
        slot = run_dir / "samples" / "b1s.json"
        slot.write_bytes(slot.read_bytes()[: len(slot.read_bytes()) // 2])  # a torn write

        try:
            executor._execute(_fixture_plan(td, run_id="trunc", barriers=(1,)))
        except executor.ProtocolRefusal:
            pass
        else:
            raise AssertionError("a truncated sample was counted as completed")
    _ok("TAMP  a torn/truncated sample refuses")


def test_a_symlinked_sample_refuses() -> None:
    with tempfile.TemporaryDirectory() as td:
        run_dir = Path(td) / executor.EVAL_ID / "link"
        executor._execute(_fixture_plan(td, run_id="link", barriers=(1,)))
        slot = run_dir / "samples" / "b1s.json"
        elsewhere = Path(td) / "elsewhere.json"
        elsewhere.write_text(slot.read_text())
        slot.unlink()
        slot.symlink_to(elsewhere)

        try:
            executor._execute(_fixture_plan(td, run_id="link", barriers=(1,)))
        except executor.ProtocolRefusal as r:
            assert "symlink" in str(r)
        else:
            raise AssertionError("a symlinked sample was followed and counted")
    _ok("TAMP  a symlinked sample refuses (O_NOFOLLOW)")


def test_a_sample_filed_under_the_wrong_barrier_refuses() -> None:
    with tempfile.TemporaryDirectory() as td:
        run_dir = Path(td) / executor.EVAL_ID / "wrongbar"
        executor._execute(_fixture_plan(td, run_id="wrongbar", barriers=(1,)))
        slot = run_dir / "samples" / "b1s.json"
        sample = json.loads(slot.read_text())
        sample["barrier_seconds"] = 999
        executor._write_json(slot, sample)  # valid JSON, valid sidecar, wrong content

        try:
            executor._execute(_fixture_plan(td, run_id="wrongbar", barriers=(1,)))
        except executor.ProtocolRefusal as r:
            assert "barrier" in str(r)
        else:
            raise AssertionError("a sample holding the wrong barrier filled the slot")
    _ok("TAMP  a sample whose barrier does not match its slot refuses")


# --- blocking review #4: run ids do not choose where they live ----------------------


def test_run_id_cannot_escape_the_run_root() -> None:
    for bad in ("../../etc", "..", ".", "a/b", "a\\b", "", "A" * 80, "has space", "-leading"):
        try:
            executor._resolve_run_dir(Path("/tmp/x"), bad)
        except executor.ProtocolRefusal:
            continue
        raise AssertionError(f"run_id {bad!r} was accepted and can write outside the run root")
    assert executor._resolve_run_dir(Path("/tmp/x"), "run-2026-07-12a").name == "run-2026-07-12a"
    _ok("PATH  a run id is a conservative slug and cannot escape lab/runs/<eval>/")


# --- blocking review #8: an abort must not pretend nothing happened -----------------


def test_an_abort_after_consultation_preserves_that_reality_was_touched() -> None:
    """Review finding 8. If the capture dies *after* navigation, the subject WAS consulted. An
    abort record that looks identical whether or not that happened is how an unlogged observation
    is born — which this study has already paid for once."""
    def _dies_after_navigating(url, *, barrier_seconds, **kw):
        raise executor.CaptureAborted(
            "capture", "TimeoutError: inner_text timed out",
            consulted_at="2026-07-12T16:30:00Z",
            partial={"responses": [{"url": url, "status": 200, "ok": True,
                                    "resource_type": "document"}], "console_errors": []},
        )

    with tempfile.TemporaryDirectory() as td:
        run_dir = Path(td) / executor.EVAL_ID / "aborted"
        executor._execute(_fixture_plan(td, run_id="aborted", barriers=(1,),
                                        sampler=_dies_after_navigating))

        rec = json.loads((run_dir / "aborts" / "b1s-attempt-1.json").read_text())
        assert rec["abort_kind"] == "capture_failed"
        assert rec["subject_was_consulted"] is True
        assert rec["consulted_at"] == "2026-07-12T16:30:00Z"
        assert rec["stage"] == "capture"
        assert rec["partial_observations"]["responses"], "partial browser facts were discarded"
        # ...and still no result, anywhere.
        assert "observed_at" not in rec and "mechanical_outcome" not in rec

        m = json.loads((run_dir / "manifest.json").read_text())
        assert m["samples_completed"] == 0 and m["samples_aborted"] == 1 and m["partial"] is True
        assert not list((run_dir / "samples").glob("*.json")), "an abort filled a sample slot"
    _ok("ABRT  an abort records consulted_at + partials, and still carries no outcome")


def test_capture_raises_capture_aborted_not_a_bare_exception() -> None:
    """The real `capture_sample`, against a dead port: it must raise the typed abort carrying its
    stage, not leak a raw playwright error that `_execute` would file as `sampler_error`."""
    try:
        executor.capture_sample("http://127.0.0.1:1/", barrier_seconds=1, dwell_s=0.1)
    except executor.CaptureAborted as e:
        assert e.stage == "navigate", e.stage
        assert e.consulted_at is None, "the browser never reached the subject; consulted_at must be None"
    else:
        raise AssertionError("capture_sample completed against a dead port")
    _ok("ABRT  capture_sample raises CaptureAborted(stage=navigate, consulted_at=None)")


# --- blocking review #10: a failed diagnostic must not read as a verified one -------


def test_a_failed_identity_command_is_recorded_not_silently_emptied() -> None:
    """Review finding 10. `git rev-parse` in a non-repo used to return '' and render as a verified
    commit of ''. A diagnostic that cannot fail loudly is worse than no diagnostic."""
    with tempfile.TemporaryDirectory() as td:
        ident = executor._git_identity(Path(td))  # not a git repo
    assert ident["ok"] is False
    assert "commit" not in ident, "a failed git identity produced a commit key anyway"
    assert ident["error"]
    cmd = ident["commands"][0]
    assert cmd["returncode"] not in (0, None) and cmd["stderr"], cmd
    _ok("DIAG  a failed identity command records returncode+stderr and yields no commit")


# --- the denominator and the production seam ----------------------------------------


def test_denominator_cannot_be_shrunk_from_the_executor() -> None:
    """The sample count does not live in this repo's source — it lives in an unamendable,
    append-only canon envelope. Editing the constant makes the run REFUSE, not shrink."""
    original = executor.BARRIERS
    try:
        executor.BARRIERS = (1, 30)  # drop a sample, as a results-reading party might wish to
        try:
            executor.verify_pre_registration()
        except executor.ProtocolRefusal as r:
            assert "frozen gate" in str(r)
        else:
            raise AssertionError(
                "preflight ACCEPTED a 2-sample schedule against a frozen gate demanding 3. The "
                "denominator is editable by the party reading the results."
            )
    finally:
        executor.BARRIERS = original
    executor.verify_pre_registration()  # unmodified, it passes
    _ok("DEN   a shrunken barrier schedule is refused against the frozen gate")


def test_production_constants_are_the_pre_registered_schedule() -> None:
    """The fixture suite stubs the *clock*, never the schedule. So the schedule itself is asserted
    here, and the production entry point is asserted to have no seam a test could reach through."""
    import inspect

    assert executor.BARRIERS == (1, 30, 120), executor.BARRIERS
    assert executor.REQUIRED_SAMPLES == 3
    assert executor.POST_LOAD_DWELL_S == 1.0
    assert executor.ALLOWED_METHODS == frozenset({"GET", "HEAD"})

    params = list(inspect.signature(executor.execute_run).parameters)
    assert params == ["run_id"], f"execute_run grew a test-reachable override: {params}"

    src = Path(executor.__file__).read_text()
    assert "def production_plan(run_id: str) -> RunPlan:" in src
    assert "preflight_result=preflight()" in src, (
        "production_plan does not run preflight; the production path could observe without probe "
        "entry"
    )
    _ok("PROD  production schedule is [1,30,120]x3, read-only enforced, CLI has no override seam")


def test_the_fixture_suite_does_not_sit_through_the_real_schedule() -> None:
    with tempfile.TemporaryDirectory() as td:
        plan = _fixture_plan(td, run_id="clock-test")
        started = time.monotonic()
        executor._execute(plan)
        elapsed = time.monotonic() - started

    assert plan.barriers == (1, 30, 120), "premise: the real schedule was executed"
    assert sum(plan.extra["slept"]) > 100, "premise: the schedule really did ask to wait ~150s"
    assert elapsed < 5, f"fixture run took {elapsed:.1f}s of real time; the clock is not injected"
    _ok(f"FAST  the real [1,30,120] schedule runs in {elapsed:.2f}s against an injected clock")


def test_resume_never_replaces_a_completed_sample() -> None:
    calls: list[int] = []

    def _counting(url, *, barrier_seconds, **kw):
        calls.append(barrier_seconds)
        return _stub_sampler(url, barrier_seconds=barrier_seconds)

    with tempfile.TemporaryDirectory() as td:
        first = executor._execute(_fixture_plan(td, run_id="resume", sampler=_counting))
        before = (first / "samples" / "b1s.json").read_bytes()

        second = executor._execute(_fixture_plan(td, run_id="resume", sampler=_counting))
        after = (second / "samples" / "b1s.json").read_bytes()

        assert calls == [1, 30, 120], f"resume re-ran completed samples: {calls}"
        assert before == after, "resume rewrote a completed sample byte-for-byte"
        m = json.loads((second / "manifest.json").read_text())
        assert m["samples_resumed"] == 3 and m["samples_completed"] == 3
    _ok("IDEM  resume skips completed samples, re-runs nothing, replaces nothing")


def test_a_fixture_run_can_never_pose_as_the_real_subject() -> None:
    with tempfile.TemporaryDirectory() as td:
        run_dir = executor._execute(_fixture_plan(td, barriers=()))
        m = json.loads((run_dir / "manifest.json").read_text())
        assert m["is_preregistered_subject"] is False
        assert m["emits_evidence"] is False
    _ok("SUBJ  a run against a non-declared URL is stamped is_preregistered_subject=false")


# --- blocking review #7: one reproducible root ---------------------------------------


def test_the_manifest_binds_every_artifact_and_the_executing_source() -> None:
    """Review finding 7. A future Evidence ArtifactPointer must be able to cite the manifest as one
    reproducible root, rather than citing a directory and hoping."""
    import hashlib

    with tempfile.TemporaryDirectory() as td:
        run_dir = executor._execute(_fixture_plan(td, run_id="digest"))
        m = json.loads((run_dir / "manifest.json").read_text())

        raw = (run_dir / "artifact-hashes.json").read_bytes()
        expect = f"sha256:{hashlib.sha256(raw).hexdigest()}"
        assert m["artifacts_digest"] == expect, "the manifest does not bind artifact-hashes.json"

        hashes = json.loads(raw)
        for required in ("b0.json", "run.json", "samples/b1s.json"):
            assert required in hashes, f"{required} is not covered by the artifact hash list"
        assert "manifest.json" not in hashes, "the manifest hashes itself; that is circular"

        for src in ("src::executor", "src::methodology", "src::protocol_deviation"):
            assert src in hashes, f"{src} is not bound into the artifact set"
        assert m["code"]["executor"] == hashes["src::executor"]
    _ok("ROOT  manifest binds artifact-hashes.json + the executing source as one digest")


TESTS = [
    test_a_healthy_page_passes,
    test_wrong_identity_fails,
    test_console_error_fails,
    test_uncaught_javascript_error_fails,
    test_stale_bundle_404_fails,
    test_stale_fetch_404_fails,
    test_network_failed_request_fails,
    test_identity_plus_error_banner_fails,
    test_a_mutating_request_is_blocked_before_it_reaches_the_network,
    test_the_executor_only_ever_issues_gets,
    test_source_contains_no_mutating_operation,
    test_the_executor_cannot_emit_evidence,
    test_production_preflight_refuses_without_probe_entry,
    test_preflight_accepts_once_probe_entry_exists,
    test_preflight_refuses_a_methodology_that_changed_after_probe_entry,
    test_b0_does_not_consult_the_subject_before_the_run_boundary_exists,
    test_resume_schedules_against_the_persisted_anchor_and_never_samples_late,
    test_a_tampered_sample_refuses_rather_than_counting_or_rerunning,
    test_a_truncated_sample_refuses,
    test_a_symlinked_sample_refuses,
    test_a_sample_filed_under_the_wrong_barrier_refuses,
    test_run_id_cannot_escape_the_run_root,
    test_an_abort_after_consultation_preserves_that_reality_was_touched,
    test_capture_raises_capture_aborted_not_a_bare_exception,
    test_a_failed_identity_command_is_recorded_not_silently_emptied,
    test_denominator_cannot_be_shrunk_from_the_executor,
    test_production_constants_are_the_pre_registered_schedule,
    test_the_fixture_suite_does_not_sit_through_the_real_schedule,
    test_resume_never_replaces_a_completed_sample,
    test_a_fixture_run_can_never_pose_as_the_real_subject,
    test_the_manifest_binds_every_artifact_and_the_executing_source,
]


def main() -> int:
    print(f"artifact-coherence-transfer-v1 executor — {len(TESTS)} assertions\n")
    failed = 0
    for t in TESTS:
        try:
            t()
        except AssertionError as e:
            failed += 1
            print(f"  FAIL {t.__name__}:\n       {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  ERR  {t.__name__}: {type(e).__name__}: {e}")
    print()
    if failed:
        print(f"{failed}/{len(TESTS)} FAILED")
        return 1
    print(f"all {len(TESTS)} assertions hold")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

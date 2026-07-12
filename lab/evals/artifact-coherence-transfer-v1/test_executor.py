"""Verifiable assertions for the artifact-coherence-transfer-v1 executor.

    PYTHONPATH=. .venv/bin/python lab/evals/artifact-coherence-transfer-v1/test_executor.py

**No test here touches the pre-registered subject.** Every browser assertion runs against a
local fixture server on 127.0.0.1 serving synthetic pages. Pointing the test suite at
launchpad-lint would be an unlogged observation outside a run directory — which is the exact
protocol deviation this study already has one of, and one is enough.

## Why the fail-injection suite exists

The executor's author had already seen the subject serving a healthy 200 before this file was
written (see `PROTOCOL-DEVIATION-2026-07-12-preprobe-target-consultation.md`). An author who
expects a pass can write a detector that cannot fail and never notice, because the run passes
either way. Promising to have been careful is not a control.

So the control is mechanical: the executor is made to **produce a failing sample on demand**,
once per failure channel the pre-registered criterion names. A detector that has been shown to
fire is a detector. One that has only ever been shown to stay quiet is a light switch with no
bulb in it.

What the suite actually established, stated precisely because the first draft of this docstring
overstated it: the executor's original three channels (console errors, uncaught exceptions,
`requestfailed`) *would* have caught a stale bundle — but only incidentally. Chromium aborts a
404'd `<script>` (so `requestfailed` fires) and console-logs "Failed to load resource" for a
404'd `fetch` (so `console_errors` fires). Both are Chromium **logging policy**, not the
pre-registered criterion, and detecting "a behavior-critical request failed" by pattern-matching
an English console string is inference that silently changes meaning when the browser does. The
`bad_behavior_critical_responses` channel observes the condition `methodology.md` actually names.
The channels overlap; that is redundancy, not waste, on the one failure mode this study exists to
detect.
"""

from __future__ import annotations

import http.server
import importlib.util
import json
import socket
import sys
import tempfile
import threading
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

# The study directory is named for the study, not for Python — `artifact-coherence-transfer-v1`
# is not an importable identifier. Load the executor by path rather than renaming the study
# directory to suit the import system.
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
    # The healthy shape: identity present, nothing else on the page.
    "/healthy": (200, "text/html", f"<html><body>{IDENTITY}</body></html>".encode()),
    # Wrong application identity — the route answered, but not as itself.
    "/wrong-identity": (200, "text/html", b"<html><body>Some other service</body></html>"),
    # A console error.
    "/console-error": (
        200, "text/html",
        f"<html><body>{IDENTITY}<script>console.error('boom')</script></body></html>".encode(),
    ),
    # An uncaught JavaScript exception.
    "/js-error": (
        200, "text/html",
        f"<html><body>{IDENTITY}<script>throw new Error('kaboom')</script></body></html>".encode(),
    ),
    # THE ARTIFACT-INCOHERENCE SHAPE: a document referencing a hashed bundle that is gone.
    # Serves 200 with the right identity; the <script> 404s. This is what the Command incident
    # looked like from a browser.
    "/stale-bundle": (
        200, "text/html",
        f"<html><body>{IDENTITY}<script src='/assets/app.9f3c1a.js'></script></body></html>".encode(),
    ),
    # The same incoherence arriving as a 404'd data fetch instead of a 404'd <script>. Chromium
    # aborts a 404'd <script> (so `requestfailed` fires), but a 404'd `fetch()` is a completed
    # exchange and fires no `requestfailed` at all — so this page is what separates the
    # response-status channel from the network-failure channel. Chromium *does* still console-log
    # it; see the module docstring for why that overlap is not a reason to drop the channel.
    "/stale-fetch": (
        200, "text/html",
        f"<html><body>{IDENTITY}<script>fetch('/api/data.json')</script></body></html>".encode(),
    ),
    # A network-level failure (not an HTTP error): connection refused on a script.
    "/dead-socket": (
        200, "text/html",
        f"<html><body>{IDENTITY}<script src='http://127.0.0.1:1/x.js'></script></body></html>".encode(),
    ),
}


class _Handler(http.server.BaseHTTPRequestHandler):
    seen: list[tuple[str, str]] = []

    def do_GET(self) -> None:  # noqa: N802
        _Handler.seen.append(("GET", self.path))
        if self.path in PAGES:
            status, ctype, body = PAGES[self.path]
        elif self.path.endswith(".js"):
            # A missing bundle served the way a real origin serves one: 404 with a JS
            # content-type. The MIME type is deliberate — a `text/plain` 404 would additionally
            # trip Chromium's Opaque Response Blocking, and the fixture would then be testing ORB
            # rather than the study's failure mode.
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


def _sample(base: str, path: str) -> dict:
    return executor.capture_sample(f"{base}{path}", barrier_seconds=1, dwell_s=0.2)


# --- the executor can pass, and can fail. Both are proven. ---------------------------


def test_a_healthy_page_passes() -> None:
    """The control. If this failed, every failure below would be meaningless."""
    with fixture_server() as base:
        s = _sample(base, "/healthy")
    assert s["mechanical_outcome"]["pass"], s["mechanical_outcome"]["reasons"]
    assert s["status"] == "completed" and s["observed_at"]
    _ok("PASS  a healthy page yields a passing sample (the detector is not stuck on FAIL)")


def test_wrong_identity_fails() -> None:
    with fixture_server() as base:
        s = _sample(base, "/wrong-identity")
    assert not s["mechanical_outcome"]["pass"]
    assert any("identity" in r for r in s["mechanical_outcome"]["reasons"])
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
    """A 200 document carrying the right identity, referencing a hashed bundle that 404s — the
    artifact-incoherence symptom, and what the Command incident looked like from a browser.

    Chromium happens to abort a 404'd `<script>` (`net::ERR_ABORTED`), so *both* channels catch
    this one. Belt and braces is fine; what is not fine is concluding from this test alone that
    the response-status channel is doing any work. See `test_stale_fetch_404_fails`, which is
    the case where it is the only thing standing between the study and a false clean run.
    """
    with fixture_server() as base:
        s = _sample(base, "/stale-bundle")
    assert s["bad_behavior_critical_responses"], "the 404 on a <script> was not recorded at all"
    assert not s["mechanical_outcome"]["pass"], (
        "A stale document referencing a bundle that no longer exists PASSED. This is the exact "
        "failure the study is built to detect, and the executor is blind to it."
    )
    _ok("FAIL  a 404 on a behavior-critical <script> fails (the stale-bundle shape)")


def test_stale_fetch_404_fails() -> None:
    """A `fetch()` that 404s: the document still renders the correct identity, the fetch promise
    resolves normally, and no network failure occurs — yet the application's data is missing.

    This test pins the *observed* behavior of each channel rather than the author's guess about
    it, which is the only reason the guess got corrected:

      - `requestfailed` stays **empty** — a 404 is a completed HTTP exchange, not a network fault;
      - `console_errors` **fires**, because Chromium logs "Failed to load resource" — a logging
        policy, not the pre-registered criterion;
      - `bad_behavior_critical_responses` **fires**, because a behavior-critical request returned
        an error status, which is the condition `methodology.md` actually names.

    If a future browser stops console-logging resource errors, the third channel still holds and
    this test tells us which one carried the weight.
    """
    with fixture_server() as base:
        s = executor.capture_sample(f"{base}/stale-fetch", barrier_seconds=1, dwell_s=0.5)

    assert not s["failed_requests"], (
        "premise check: a 404'd fetch() is not a network failure, so requestfailed must stay "
        f"empty. It did not: {s['failed_requests']}. Recheck the BEHAVIOR_CRITICAL reasoning."
    )
    assert IDENTITY in s["visible_text"], "premise check: the identity string still renders"
    assert not s["page_errors"], "premise check: no uncaught exception"

    assert s["bad_behavior_critical_responses"], (
        "the 404'd fetch was not recorded by the response-status channel — the one channel that "
        "implements the criterion rather than inferring it from a console string"
    )
    assert not s["mechanical_outcome"]["pass"], (
        "A page whose data fetch 404s — correct identity, no network failure — was reported "
        "CLEAN. This is the failure mode the study was built to detect."
    )
    reasons = " ".join(s["mechanical_outcome"]["reasons"])
    assert "behavior-critical" in reasons, reasons
    _ok("FAIL  a 404'd fetch fails; response-status channel fires where requestfailed cannot")


def test_network_failed_request_fails() -> None:
    with fixture_server() as base:
        s = _sample(base, "/dead-socket")
    assert not s["mechanical_outcome"]["pass"]
    assert s["failed_requests"], "connection-refused script was not captured"
    _ok("FAIL  a network-failed behavior-critical request fails the sample")


# --- read-only against the subject ---------------------------------------------------


def test_the_executor_only_ever_issues_gets() -> None:
    """Proven from the fixture server's own request log, not from the executor's promises."""
    with fixture_server() as base:
        _sample(base, "/healthy")
        methods = {m for m, _ in _Handler.seen}
    assert methods == {"GET"}, f"executor issued non-GET methods: {methods - {'GET'}}"
    _ok("RO    every request the executor issued was a GET (server-side log)")


def _code_only(path: Path) -> tuple[list[str], list[str], list[str]]:
    """Split a module into (executable string literals, imported names, attribute names).

    Docstrings are excluded. A text scan cannot tell a docstring promising *"the MCP endpoint
    is never invoked"* from code invoking it — it flags both — so it is worthless for exactly
    the file whose docstring explains its own restraint. `guard.py` learned this and walks the
    AST for the same reason; so does this.
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
    """The executor must not contain the *vocabulary of a write* anywhere it can execute.
    `systemctl show` is a read; `systemctl restart` is not."""
    strings, _, attrs = _code_only(Path(executor.__file__))

    banned = ("systemctl start", "systemctl stop", "systemctl restart", "systemctl reload",
              "npm run build", "wrangler", "git push", "docker")
    for s in strings:
        for token in banned:
            assert token not in s, f"executor's executable code contains {token!r} in {s!r}"

    # HTTP verbs are matched *exactly*, not as substrings — "NOT COMPUTED" contains "PUT", and a
    # check that flags the word "computed" as a mutation is a check nobody will keep.
    for s in strings:
        assert s.strip().upper() not in {"POST", "PUT", "DELETE", "PATCH"}, (
            f"executor's executable code names a mutating HTTP method: {s!r}"
        )

    for verb in ("post", "put", "delete", "patch"):
        assert verb not in attrs, f"executor calls a mutating method: .{verb}()"

    assert not any("/mcp" in s for s in strings), (
        "executor's executable code references the authenticated MCP endpoint. methodology.md "
        "forbids substituting it for the browser outcome."
    )
    _ok("RO    executor's executable code has no mutating operation and no MCP substitution")


def test_the_executor_cannot_emit_evidence() -> None:
    """Evidence closes the frozen gate's pre-registration window permanently. A script must not
    be able to do that as a side effect of finishing, so the emitter is unreachable from here —
    asserted on the import graph and the call graph, not on prose."""
    strings, imports, attrs = _code_only(Path(executor.__file__))

    for mod in imports:
        assert "canon.emit" not in mod, f"executor imports the canon emitter: {mod!r}"

    for fn in ("emit_evidence", "emit_decision", "emit_claim", "emit_frozen_gate",
               "emit_phase_transition", "emit_methodology_log"):
        assert fn not in attrs, f"executor calls the canon emitter: {fn}()"
        assert not any(fn in s for s in strings), f"executor reaches the emitter dynamically: {fn}"

    # Nothing may reach the emitter by dynamic import either. `importlib.metadata.version` is
    # fine — it reads a package version. `importlib.import_module` and `__import__` are the ways
    # to reach a module the import graph does not mention, so those are what is banned.
    assert "importlib.import_module" not in imports, "executor can import dynamically"
    assert "import_module" not in attrs, "executor calls importlib.import_module()"
    assert "__import__" not in attrs, "executor calls __import__()"
    _ok("EV    executor cannot emit Evidence, a Decision, a Claim, or a gate (import+call graph)")


# --- the denominator ------------------------------------------------------------------


def test_denominator_cannot_be_shrunk_from_the_executor() -> None:
    """The sample count does not live in this repo's source — it lives in an unamendable,
    append-only canon envelope. Editing the constant makes the run REFUSE, not shrink."""
    original = executor.BARRIERS
    try:
        executor.BARRIERS = (1, 30)  # drop a sample, as a results-reading party might wish to
        try:
            executor.preflight()
        except executor.ProtocolRefusal as r:
            assert "frozen gate" in str(r)
        else:
            raise AssertionError(
                "preflight ACCEPTED a 2-sample schedule against a frozen gate demanding 3. The "
                "denominator is editable by the party reading the results."
            )
    finally:
        executor.BARRIERS = original
    executor.preflight()  # unmodified, it passes
    _ok("DEN   a shrunken barrier schedule is refused against the frozen gate")


def _fixture_plan(td: str, **over) -> "executor.RunPlan":
    """A RunPlan with a no-op clock. The fixture suite must never sit through 1/30/120 — a test
    that takes two and a half minutes is a test that gets skipped, and a skipped denominator
    check protects nothing."""
    slept: list[float] = []
    base = dict(
        run_id="fixture",
        url="http://127.0.0.1:1/",
        barriers=(1, 30, 120),          # the REAL schedule...
        runs_root=Path(td),
        sampler=_stub_sampler,
        sleep=slept.append,             # ...with the waiting stubbed out, not the schedule.
        b0={"fixture": True},
        preflight_result=None,
    )
    base.update(over)
    plan = executor.RunPlan(**base)
    plan.extra["slept"] = slept
    return plan


def _stub_sampler(url, *, barrier_seconds, **kw) -> dict:
    return {
        "barrier_seconds": barrier_seconds, "status": "completed",
        "observed_at": "2026-07-12T00:00:00Z", "response": {"ok": True, "status": 200},
        "visible_text": IDENTITY, "console_errors": [], "page_errors": [],
        "failed_requests": [], "bad_behavior_critical_responses": [],
        "mechanical_outcome": {"pass": True, "reasons": []},
    }


def test_production_constants_are_the_pre_registered_schedule() -> None:
    """The fixture suite stubs the *clock*, never the schedule. So the schedule itself is
    asserted here, against the frozen gate, and the production entry point is asserted to have
    no seam a test could reach through."""
    import inspect

    assert executor.BARRIERS == (1, 30, 120), executor.BARRIERS
    assert executor.REQUIRED_SAMPLES == 3
    assert executor.POST_LOAD_DWELL_S == 1.0

    plan = executor.production_plan("assert-only")
    assert plan.barriers == (1, 30, 120)
    assert plan.sleep is time.sleep, "the production plan does not use a real clock"
    assert plan.sampler is executor.capture_sample
    assert plan.url == executor.SUBJECT_URL
    assert plan.is_preregistered_subject

    # The production CLI takes a run id and nothing else. If a barrier/sampler/url override ever
    # appears here, a fast fixture run could be filed as the pre-registered one.
    params = list(inspect.signature(executor.execute_run).parameters)
    assert params == ["run_id"], f"execute_run grew a test-reachable override: {params}"
    _ok("PROD  production schedule is [1,30,120]x3 w/ real clock; CLI has no override seam")


def test_aborted_sample_carries_no_outcome_and_does_not_fill_its_slot() -> None:
    """An abort is not a result. The schema gives it nowhere to put one."""
    def _always_aborts(url, *, barrier_seconds, **kw):
        raise TimeoutError("simulated tooling failure")

    with tempfile.TemporaryDirectory() as td:
        plan = _fixture_plan(td, run_id="abort-test", sampler=_always_aborts)
        run_dir = executor._execute(plan)

        manifest = json.loads((run_dir / "manifest.json").read_text())
        assert manifest["samples_completed"] == 0
        assert manifest["samples_aborted"] == 3
        assert manifest["partial"] is True
        assert not list((run_dir / "samples").glob("*.json")), "an abort filled a sample slot"

        abort = json.loads(next((run_dir / "aborts").glob("*.json")).read_text())
        assert "observed_at" not in abort, "an aborted sample carries an observation timestamp"
        assert "mechanical_outcome" not in abort, "an aborted sample carries an outcome"
    _ok("DEN   an abort has no outcome, no observed_at, and leaves its slot unfilled")


def test_resume_never_replaces_a_completed_sample() -> None:
    calls: list[int] = []

    def _counting(url, *, barrier_seconds, **kw):
        calls.append(barrier_seconds)
        return _stub_sampler(url, barrier_seconds=barrier_seconds)

    with tempfile.TemporaryDirectory() as td:
        first = executor._execute(_fixture_plan(td, run_id="resume-test", sampler=_counting))
        before = (first / "samples" / "b1s.json").read_bytes()

        second = executor._execute(_fixture_plan(td, run_id="resume-test", sampler=_counting))
        after = (second / "samples" / "b1s.json").read_bytes()

        assert calls == [1, 30, 120], f"resume re-ran completed samples: {calls}"
        assert before == after, "resume rewrote a completed sample byte-for-byte"
        m = json.loads((second / "manifest.json").read_text())
        assert m["samples_resumed"] == 3 and m["samples_completed"] == 3
    _ok("IDEM  resume skips completed samples, re-runs nothing, replaces nothing")


def test_the_fixture_suite_does_not_sit_through_the_real_schedule() -> None:
    """The clock is injected, so the full 1/30/120 schedule executes with zero wall-clock wait.
    Asserted, because a suite that quietly took 151 seconds would get run less often, and these
    are the assertions standing between a contaminated author and a detector that cannot fail."""
    with tempfile.TemporaryDirectory() as td:
        plan = _fixture_plan(td, run_id="clock-test")
        started = time.monotonic()
        executor._execute(plan)
        elapsed = time.monotonic() - started

    assert plan.barriers == (1, 30, 120), "premise: the real schedule was executed"
    assert sum(plan.extra["slept"]) > 100, "premise: the schedule really did ask to wait ~150s"
    assert elapsed < 5, f"fixture run took {elapsed:.1f}s of real time; the clock is not injected"
    _ok(f"FAST  the real [1,30,120] schedule runs in {elapsed:.2f}s against an injected clock")


def test_a_fixture_run_can_never_pose_as_the_real_subject() -> None:
    with tempfile.TemporaryDirectory() as td:
        run_dir = executor._execute(_fixture_plan(td, barriers=()))
        m = json.loads((run_dir / "manifest.json").read_text())
        assert m["is_preregistered_subject"] is False
        assert m["emits_evidence"] is False
    _ok("SUBJ  a run against a non-declared URL is stamped is_preregistered_subject=false")


def test_preflight_accepts_the_live_pre_registration() -> None:
    """The pre-registration is intact right now: methodology hash matches the Claim, the frozen
    gate authorizes exactly 3 samples at [1, 30, 120] against launchpad-lint."""
    checked = executor.preflight()
    assert checked["claim_id"] == "bda4396c7638e63f"
    assert checked["gate_id"] == "5273e9a31e92f6c3"
    assert checked["barriers_from_frozen_gate"] == [1, 30, 120]
    assert checked["required_completed_samples"] == 3
    _ok("PRE   preflight verifies claim, gate, methodology hash, and schedule against canon")


TESTS = [
    test_a_healthy_page_passes,
    test_wrong_identity_fails,
    test_console_error_fails,
    test_uncaught_javascript_error_fails,
    test_stale_bundle_404_fails,
    test_stale_fetch_404_fails,
    test_network_failed_request_fails,
    test_the_executor_only_ever_issues_gets,
    test_source_contains_no_mutating_operation,
    test_the_executor_cannot_emit_evidence,
    test_denominator_cannot_be_shrunk_from_the_executor,
    test_production_constants_are_the_pre_registered_schedule,
    test_the_fixture_suite_does_not_sit_through_the_real_schedule,
    test_aborted_sample_carries_no_outcome_and_does_not_fill_its_slot,
    test_resume_never_replaces_a_completed_sample,
    test_a_fixture_run_can_never_pose_as_the_real_subject,
    test_preflight_accepts_the_live_pre_registration,
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

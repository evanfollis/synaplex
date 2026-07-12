"""Model access for the lab. Subscription CLIs only — no metered API, ever (ADR-0036).

ADR-0036 (accepted 2026-06-11, principal directive): AI spend is capped at the two existing
subscriptions. **No metered API keys are provisioned without a new, explicit principal
authorization.** If a provider's subscription limit is hit, route to the other subscription
provider (Claude ↔ Codex). Hard-stop only when both are blocked, or when the failure is not
a capacity failure.

This module is the only way the lab talks to a model, and it physically cannot spend metered
tokens: it shells out to the `claude` and `codex` CLIs, which authenticate against the
subscription plans. There is no API-key code path to accidentally re-enable.

A note on what this replaces. The previous version of this file constructed an Anthropic API
client and reported a missing `ANTHROPIC_API_KEY` as a *blocker*. ADR-0036 had already
closed that a month earlier, in terms: *"This is a deliberate cost decision, not a credential
blocker. Reflection and synthesis jobs must stop carrying it forward as a blocker."* The key
was never the obstacle. Reading `supervisor/decisions/` before escalating would have caught
it.

## Failover is capacity-only, and the distinction is load-bearing

A capacity failure (rate limit, quota, plan exhaustion) means *this provider cannot serve
right now* — so we try the other one. Any other failure (bad prompt, crash, timeout,
malformed output) means *something is wrong*, and silently retrying it on a second provider
would launder a bug into a result produced by a model we did not intend to use. Only the
first class fails over. The second class raises.
"""

from __future__ import annotations

import os
import re
import subprocess
import time
from dataclasses import dataclass

from intake import friction

# Capacity exhaustion, as the CLIs report it. Matched case-insensitively against combined
# stdout+stderr. Anything not matching here is NOT a capacity failure and must not fail over.
_CAPACITY_PATTERNS = re.compile(
    r"rate limit|rate-limit|quota|usage limit|too many requests|429|"
    r"capacity|overloaded|plan limit|limit reached|try again later",
    re.IGNORECASE,
)

CHARS_PER_TOKEN = 4  # estimate; the CLIs do not expose exact counts

# Credentials that would route a subscription CLI onto metered billing if it found them.
#
# `claude` bills against the subscription plan when it authenticates from its own config, and
# against METERED API credit the moment it sees ANTHROPIC_API_KEY / ANTHROPIC_AUTH_TOKEN in
# its environment. `codex` behaves the same way with OPENAI_API_KEY. So the enforcement point
# is not "does this variable exist somewhere on the host" — it is "can the child process see
# it". We strip them from the child env and let the CLI fall through to subscription auth.
#
# The vendor keys are here for one reason only: if one is ever set for some unrelated purpose,
# a child must still not inherit it. Their presence in this tuple is a deletion list, not a
# dependency.
METERED_CREDENTIAL_VARS = (
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "OPENAI_API_KEY",
    "LETTA_API_KEY",
    "MEM0_API_KEY",
)


def child_env(base: dict[str, str] | None = None) -> dict[str, str]:
    """The environment a subscription CLI child is allowed to see.

    Every metered credential is removed. Nothing else is touched — PATH, HOME, and the CLI's
    own config location must survive or the child cannot authenticate at all.

    This replaces an earlier `assert_no_metered_keys()` that *refused to run* whenever a
    metered key existed anywhere in the parent environment. That was the wrong control in two
    ways. It blocked the entire pipeline over a variable it never used — a clog, not a
    safeguard — and it made the lab's liveness depend on unrelated host state. Prohibiting
    spend does not require refusing to work; it requires making the spend unreachable. So we
    make it unreachable and keep running.
    """
    env = dict(base if base is not None else os.environ)
    for var in METERED_CREDENTIAL_VARS:
        env.pop(var, None)
    return env


class CapacityExhausted(RuntimeError):
    """This provider cannot serve right now. Try the other subscription."""


class ProviderFailed(RuntimeError):
    """Something is wrong. Do NOT fail over — that would launder a bug into a result."""


@dataclass(frozen=True)
class Completion:
    text: str
    provider: str
    model: str
    input_tokens_est: int
    output_tokens_est: int
    latency_ms: int
    fallback_from: str | None = None


@dataclass(frozen=True)
class CliProvider:
    """One subscription CLI."""

    name: str          # 'claude' | 'codex'
    argv: tuple[str, ...]
    model: str

    def complete(self, prompt: str, timeout_s: int = 180) -> Completion:
        started = time.monotonic()
        try:
            proc = subprocess.run(
                list(self.argv), input=prompt, capture_output=True,
                text=True, timeout=timeout_s,
                env=child_env(),  # metered credentials stripped; CLI falls through to subscription auth
            )
        except subprocess.TimeoutExpired as e:
            raise ProviderFailed(f"{self.name} timed out after {timeout_s}s") from e

        latency_ms = int((time.monotonic() - started) * 1000)
        combined = f"{proc.stdout}\n{proc.stderr}"

        if proc.returncode != 0:
            if _CAPACITY_PATTERNS.search(combined):
                raise CapacityExhausted(f"{self.name}: {combined.strip()[:200]}")
            raise ProviderFailed(
                f"{self.name} exited {proc.returncode}: {combined.strip()[:300]}"
            )
        # A zero exit that still says "rate limit" is capacity exhaustion wearing a success
        # code. The CLIs do this; trusting the exit code alone would silently record an error
        # message as a model answer.
        if _CAPACITY_PATTERNS.search(combined) and not proc.stdout.strip():
            raise CapacityExhausted(f"{self.name}: {combined.strip()[:200]}")

        text = proc.stdout.strip()
        return Completion(
            text=text,
            provider=self.name,
            model=self.model,
            input_tokens_est=len(prompt) // CHARS_PER_TOKEN,
            output_tokens_est=len(text) // CHARS_PER_TOKEN,
            latency_ms=latency_ms,
        )


def claude_cli(model: str = "sonnet") -> CliProvider:
    return CliProvider("claude", ("claude", "-p", "--model", model), model)


def codex_cli(model: str = "gpt-5.4") -> CliProvider:
    return CliProvider("codex", ("codex", "exec", "--sandbox", "read-only", "-"), model)


@dataclass
class SubscriptionPool:
    """Claude ↔ Codex, with capacity-only failover and usage telemetry (ADR-0036)."""

    providers: tuple[CliProvider, ...]
    role: str = "lab-runner"

    def complete(self, prompt: str, timeout_s: int = 180) -> Completion:
        exhausted: list[str] = []
        for i, provider in enumerate(self.providers):
            try:
                c = provider.complete(prompt, timeout_s)
            except CapacityExhausted as e:
                exhausted.append(provider.name)
                self._telemetry(provider, "throttled", 0, str(e)[:120], None)
                continue
            except ProviderFailed as e:
                # NOT a capacity failure. Do not try the other provider.
                self._telemetry(provider, "failure", 0, str(e)[:160], None)
                raise

            fallback_from = exhausted[-1] if exhausted else None
            c = Completion(**{**c.__dict__, "fallback_from": fallback_from})
            self._telemetry(provider, "success", c.latency_ms, "", fallback_from, c)
            return c

        raise CapacityExhausted(
            f"both subscription providers exhausted ({', '.join(exhausted)}). ADR-0036: "
            f"hard-stop rather than falling back to metered API. Wait for limits to recover."
        )

    def _telemetry(
        self, provider: CliProvider, status: str, latency_ms: int,
        reason: str, fallback_from: str | None, c: Completion | None = None,
    ) -> None:
        """ADR-0036: every automated LLM call emits provider, model, role, status, latency,
        fallback source, and token counts — clearly labelled as estimates, because the
        subscription CLIs do not expose exact counts and pretending precision is worse than
        admitting the estimate."""
        friction.emit(
            layer="lab", source="llm",
            eventType="success" if status == "success" else status,  # type: ignore[arg-type]
            reason=reason or f"{provider.name} {provider.model} ok",
            ref="lab/runner/providers.py",
            extra={
                "provider": provider.name,
                "model": provider.model,
                "role": self.role,
                "status": status,
                "latency_ms": latency_ms or (c.latency_ms if c else 0),
                "fallback_from": fallback_from,
                "input_tokens_est": c.input_tokens_est if c else 0,
                "output_tokens_est": c.output_tokens_est if c else 0,
                "token_counts_are_estimates": True,
                "billing": "subscription",
            },
        )


def default_pool(role: str = "lab-runner") -> SubscriptionPool:
    """Claude first, Codex on capacity exhaustion. Both are subscription-billed."""
    return SubscriptionPool(providers=(claude_cli(), codex_cli()), role=role)

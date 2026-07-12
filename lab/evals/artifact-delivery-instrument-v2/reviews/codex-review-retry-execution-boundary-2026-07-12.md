# Codex review retry — execution-boundary failure

Recorded: 2026-07-12T20:27:00Z  
Scientific state: `BLOCKED_PRE_ENTRY`  
Evidence emitted: **zero**  
Prospective subject accessed: **no**

The scheduled `synaplex-cycle-v2-review-retry.service` did not test model
availability or capacity. Its transient unit invoked bare `codex` through
`env` under systemd. The process exited `127` after 14 ms because the unit PATH
could not resolve that executable.

Primary execution-boundary record:

- unit result: `exit-code`, status `127/n/a`;
- start and exit: 2026-07-12T20:21:04Z;
- captured stderr: `env: ‘codex’: No such file or directory`;
- private runtime log:
  `/opt/workspace/runtime/reviews/synaplex-cycle-v2-review-continuation-codex.log`;
- log SHA-256:
  `cdb9325be84995f7c3236eefbd0fa0e5ecc30164e5071786b640fecb3a4309e8`;
- log byte length: 44;
- installed subscription CLI:
  `/root/.nvm/versions/node/v22.22.0/bin/codex`.

This is launcher Evidence only. It is not a methodological verdict, capacity
signal, lab Evidence, or authorization to enter probe. All five frozen inputs
were subsequently re-hashed and matched `frozen-inputs.json` before continuing.


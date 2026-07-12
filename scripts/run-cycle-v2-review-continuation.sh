#!/bin/bash
set -euo pipefail

CONFIG=/opt/workspace/projects/synaplex/deploy/subscription-cli-paths.env
TASK=/opt/workspace/runtime/reviews/synaplex-cycle-v2-review-continuation-task.md
LOG=/opt/workspace/runtime/reviews/synaplex-cycle-v2-review-continuation-codex.log

# shellcheck disable=SC1090
source "$CONFIG"
[[ "$CODEX_BIN" = /* && -x "$CODEX_BIN" ]] || {
  echo "configured absolute Codex CLI is not executable" >&2
  exit 127
}

export PATH="$(dirname "$CODEX_BIN"):$(dirname "$CLAUDE_BIN"):/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
exec env -u ANTHROPIC_API_KEY -u ANTHROPIC_AUTH_TOKEN -u OPENAI_API_KEY \
  "$CODEX_BIN" -c 'approval_policy="never"' exec --skip-git-repo-check \
  --dangerously-bypass-approvals-and-sandbox --model gpt-5.6-sol - \
  < "$TASK" >> "$LOG" 2>&1


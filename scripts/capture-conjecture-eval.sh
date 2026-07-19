#!/bin/bash
set -euo pipefail

CONFIG=/opt/workspace/projects/synaplex/deploy/subscription-cli-paths.env
PROMPTEVAL=/opt/workspace/supervisor/scripts/prompteval
TRACE=/opt/workspace/runtime/conjectures/traces.jsonl

# shellcheck disable=SC1090
source "$CONFIG"
[[ "$CODEX_BIN" = /* && -x "$CODEX_BIN" && "$CLAUDE_BIN" = /* && -x "$CLAUDE_BIN" ]] || {
  echo "configured absolute subscription CLI paths are not executable" >&2
  exit 127
}
[[ -f "$TRACE" ]] || exit 0

export PATH="$(dirname "$CODEX_BIN"):$(dirname "$CLAUDE_BIN"):/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
exec env -u ANTHROPIC_API_KEY -u ANTHROPIC_AUTH_TOKEN -u OPENAI_API_KEY \
  "$PROMPTEVAL" capture /opt/workspace/projects/synaplex \
  --id cross-domain-conjecture-v2 --from-jsonl "$TRACE" \
  --fields source_records --output-field output --limit 50

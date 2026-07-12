from pathlib import Path

root = Path(__file__).resolve().parents[1]
config = (root / "deploy/subscription-cli-paths.env").read_text()
launcher = (root / "scripts/run-cycle-v2-review-continuation.sh").read_text()
unit = (root / "deploy/synaplex-cycle-v2-review-retry.service").read_text()

assert "CODEX_BIN=/" in config and "CLAUDE_BIN=/" in config
assert '"$CODEX_BIN"' in launcher
assert "env -u ANTHROPIC_API_KEY -u ANTHROPIC_AUTH_TOKEN -u OPENAI_API_KEY" in launcher
assert "ExecStart=/bin/bash /opt/workspace/projects/synaplex/scripts/run-cycle-v2-review-continuation.sh" in unit
assert " codex " not in unit
print("subscription CLI launcher assertions: 5/5")

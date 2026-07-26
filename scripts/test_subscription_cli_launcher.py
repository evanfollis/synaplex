from pathlib import Path

root = Path(__file__).resolve().parents[1]
config = (root / "deploy/subscription-cli-paths.env").read_text()
launcher = (root / "scripts/run-cycle-v2-review-continuation.sh").read_text()
unit = (root / "deploy/synaplex-cycle-v2-review-retry.service").read_text()

assert "CODEX_BIN=/" in config and "CLAUDE_BIN=/" in config
assert "--require-executable artifact-delivery-instrument-v2" in launcher
assert launcher.index("--require-executable artifact-delivery-instrument-v2") < launcher.index('source "$CONFIG"')
assert '"$CODEX_BIN"' in launcher
assert "env -u ANTHROPIC_API_KEY -u ANTHROPIC_AUTH_TOKEN -u OPENAI_API_KEY" in launcher
assert "EnvironmentFile=-/etc/synaplex/paths.env" in unit
assert 'ExecStart=/bin/bash -lc' in unit
assert " codex " not in unit
assert "UMask=0077" in unit and "ProtectSystem=strict" in unit
assert "[Install]" not in unit
print("subscription CLI launcher assertions: 10/10")

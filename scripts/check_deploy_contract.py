"""Static checks for versioned, hardened systemd deployment sources."""
from __future__ import annotations

from pathlib import Path

from synaplex_paths import REPO_ROOT

REQUIRED = (
    "EnvironmentFile=-/etc/synaplex/paths.env",
    "UMask=0077",
    "NoNewPrivileges=true",
    "ProtectSystem=strict",
    "PrivateTmp=true",
)


def main() -> None:
    units = sorted((REPO_ROOT / "deploy").glob("*-v2.service"))
    if not units:
        raise SystemExit("no versioned v2 service sources")
    errors: list[str] = []
    for unit in units:
        text = unit.read_text(encoding="utf-8")
        for requirement in REQUIRED:
            if requirement not in text:
                errors.append(f"{unit.name}: missing {requirement}")
        if "ExecStart=/bin/bash" not in text:
            errors.append(f"{unit.name}: launcher must resolve configured paths")
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"deployment contract: clean ({len(units)} units)")


if __name__ == "__main__":
    main()

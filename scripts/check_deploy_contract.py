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

INBOX_REQUIRED = (
    "User=synaplex-inbox",
    "Group=synaplex-inbox",
    "UMask=0077",
    "ReadOnlyPaths=/opt/workspace/runtime/inbox",
    "NoNewPrivileges=true",
    "CapabilityBoundingSet=\n",
    "AmbientCapabilities=\n",
    "PrivateTmp=true",
    "PrivateDevices=true",
    "ProtectSystem=strict",
    "ProtectKernelTunables=true",
    "ProtectKernelModules=true",
    "ProtectControlGroups=true",
    "LockPersonality=true",
    "RestrictNamespaces=true",
    "RestrictSUIDSGID=true",
    "IPAddressDeny=any",
    "IPAddressAllow=localhost",
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
    inbox = REPO_ROOT / "deploy" / "synaplex-inbox.service"
    if not inbox.is_file():
        errors.append("synaplex-inbox.service: missing versioned source")
    else:
        text = inbox.read_text(encoding="utf-8")
        for requirement in INBOX_REQUIRED:
            if requirement not in text:
                errors.append(
                    f"synaplex-inbox.service: missing {requirement.rstrip()}"
                )
        if "ReadWritePaths=" in text:
            errors.append(
                "synaplex-inbox.service: read-only server must not gain a host write path"
            )
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"deployment contract: clean ({len(units)} v2 units + inbox)")


if __name__ == "__main__":
    main()

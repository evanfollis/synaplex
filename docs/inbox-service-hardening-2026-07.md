# Inbox service hardening — 2026-07-27

This is an operational hardening receipt, not scientific Evidence. It records
the canary, rollback boundary, installed controls, and observed outcome for
`synaplex-inbox.service`.

## Required access

The server reads the nonce-gated static tree at
`/opt/workspace/runtime/inbox` and the existing Python launcher at
`/opt/workspace/supervisor/scripts/lib/inbox-server.py`. It binds only
`127.0.0.1:8088`. It requires no host write path, so the unit declares the
inbox tree with `ReadOnlyPaths` and deliberately has no `ReadWritePaths`
allowance. Its isolated private `/tmp` remains available to the process.

The installed process uses the dedicated `synaplex-inbox:synaplex-inbox`
system identity rather than root. Before canary startup, that identity was
verified to traverse and read the inbox and launcher paths.

## Mandatory controls

The versioned unit enables:

- `NoNewPrivileges=true`, empty capability and ambient-capability sets, and
  `RestrictSUIDSGID=true`;
- `ProtectSystem=strict`, `ProtectHome=true`, owner-only `UMask=0077`, and the
  explicit read-only inbox path;
- `PrivateTmp=true`, `PrivateDevices=true`, and process visibility protection;
- kernel tunable, module, log, clock, hostname, and control-group protection;
- namespace, realtime, personality, architecture, and system-call restrictions;
- default-deny IP policy with localhost as the only allowed destination and
  only `AF_UNIX`, `AF_INET`, and `AF_INET6` address families.

The repository deployment-contract check asserts these controls and rejects
adding a host `ReadWritePaths` allowance to this read-only service.

## Canary, installation, and rollback

The previous root-running unit is retained with mode 0600 at:

`/opt/workspace/runtime/.meta/synaplex-inbox.service.before-hardening-2026-07-27T00-27-39Z`

Its SHA-256 digest is
`4a5c832f5b3d2a781039ede74a7ce1a5d7c561a13b1f2528c96d6f66325915dc`.
Rollback is the bounded operation of installing that file back to
`/etc/systemd/system/synaplex-inbox.service`, running
`systemctl daemon-reload`, restarting the service, and repeating the
nonce-gated payload check.

The exact candidate unit was first installed under the transient canary unit
name. The production unit was stopped, the canary was started on the real
loopback port, and a nonce-gated GET returned 4354 bytes with SHA-256
`caff845d611110d2e6f1116263f864258f5393a6a861bb5266d50c753d37a5af`,
identical to the pre-canary payload. Effective canary properties showed the
dedicated identity, strict filesystem protection, private temp/devices, empty
capabilities, all required kernel and namespace controls, no host write paths,
and localhost-only IP policy. `systemd-analyze security` rated it `1.3 OK`.
The canary was then removed and the original service was successfully restored
before permanent installation.

Permanent installation used an automatic failure trap that would restore the
retained unit on any restart, payload, or control-check failure. No rollback
was triggered. The installed and repository unit bytes are identical at
`sha256:4fcc085a87f58145b4710625e8b1cc1b2b7491b887b1297c349848f835711acd`.
The service is enabled and has remained active since
2026-07-27T00:29:26Z. It listens only on `127.0.0.1:8088`; its post-install
nonce-gated response is the same 4354-byte payload with the same digest.
The workspace runtime containment audit reports zero findings at every
severity, and the installed unit retains the `1.3 OK` systemd exposure rating
(improved from `9.6 UNSAFE`).

Independent executive/operator verification then confirmed the effective
dedicated identity, empty capability set, strict filesystem protection,
`NoNewPrivileges`, private temp/devices, `ActiveState=active`, and
`NRestarts=0`. Its separate nonce-scoped GET returned HTTP 200 with the same
4354 bytes and payload digest, and the central auditor independently reported
zero findings for the unit.

## Smallest dated exception

2026-07-27: `PrivateNetwork=true` is not enabled because it would place the
server in a separate loopback namespace and break its required host-loopback
consumer route. This exception does not relax any other sandbox control.
Compensating controls are the launcher's fixed `127.0.0.1` bind,
`IPAddressDeny=any`, `IPAddressAllow=localhost`, and the restricted address
families. The observed listener is only `127.0.0.1:8088`.

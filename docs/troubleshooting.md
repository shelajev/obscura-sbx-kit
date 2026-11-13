# Troubleshooting

Start inside the sandbox with `command -v obscura` and `obscura --version`.
`/opt/obscura/obscura` and `/opt/obscura/obscura-worker` must exist together. A loader error
usually means a musl base, missing libgcc or glibc older than 2.35. The launcher
also needs `/usr/bin/python3` (3.11+). Do not work around package requirements
by copying host libraries into the sandbox.

The v0.2.6 transport does not consistently honor proxy environment variables
across CLI/MCP/CDP. In our SBX, even the implicit reqwest proxy path tried to
resolve the gateway and failed its SSRF guard. Direct upstream invocation with
an explicit gateway hostname failed too. The kit launcher selects
`OBSCURA_PROXY`, then `HTTPS_PROXY`/`https_proxy`, `HTTP_PROXY`/`http_proxy`, then
`ALL_PROXY`/`all_proxy`, resolves only that endpoint and passes `--proxy` with an
IP literal. An explicit `--proxy` overrides the environment and is resolved in
the same way. HTTP and SOCKS5 with an explicit port are supported; authenticated
and HTTPS proxy URLs are rejected rather than exposing credentials in argv.
The operator-configured proxy must be trusted. IPv4 is preferred on dual-stack
DNS; IPv6-only endpoints work. There is no automatic connection retry to another
address; an operator can supply a reachable literal endpoint if needed.

Proxy resolution happens once per browser process. Reconnect by restarting if
the gateway address changes. `NO_PROXY` does not bypass the selected proxy. To
run a deliberate local test, clear proxy variables for that process and use
`--allow-private-network` only on the fixture invocation. That flag permits all
private targets for that process; never set it globally to fix proxy failures.
Never use it to enable host services or metadata endpoints.

The launcher defaults `SSL_CERT_FILE` to `/etc/ssl/certs/ca-certificates.crt`;
an existing nonempty operator value wins. SBX must surface its interception CA
there (or set `SSL_CERT_FILE` to its public trust bundle). The kit embeds no
host-specific CA. A certificate error requires fixing the trust bundle, not
turning off verification. Controlled TLS tests prove an untrusted CA fails and
a supplied CA succeeds. Public HTTPS through the actual SBX proxy also passed;
removing SSL_CERT_FILE alone did not fail here because system trust was present.

A 403 or failed CONNECT can be a policy denial. Inspect `sbx policy log` from
native host control and read the response body. Ask for just the required
hostname and port with its purpose. Organization denials require IT; a local
deny must be removed by its owner rather than overridden by an allow. Do not
add wildcard grants. An asset or redirect can need a second approved domain.

If an MCP session unexpectedly shares cookies/storage, remove inherited
`OBSCURA_STORAGE_DIR` and any `--storage-dir` arguments, then start separate
stdio MCP processes. Do not connect multiple agents to one HTTP/CDP process.
If a screenshot differs from Chrome, compare upstream's supported rendering
features; this kit makes no pixel-equivalence claim.

To remove agent wiring, use `codex mcp remove obscura` or
`claude mcp remove --scope user obscura`, then remove only this mixin's kit entry
and recreate the sandbox. Preserve other settings and servers. The kit creates
no state directory to delete by default.

Codex 0.164.0's local stdio environment allowlist excludes proxy variables.
The upstream `codex-rs/rmcp-client/src/utils.rs` allowlist was inspected. Use README's additive `env_vars` key in `[mcp_servers.obscura]` to forward
current proxy and CA values. A live Codex 0.164.0 session with this configuration completed native MCP
HTTPS navigation and snapshot through the SBX proxy. Registry-based native SBX
installation remains unverified; Python-spawned checks alone do not prove agent
forwarding.
The launcher removes raw proxy environment variables after constructing the
explicit literal `--proxy`; upstream's multiworker server forwards that explicit
proxy to its own workers. Empty `SSL_CERT_FILE` selects the default bundle.

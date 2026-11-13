# Obscura for Docker Sandboxes

Add [Obscura](https://www.obscura.sh/) to an existing SBX agent as a browser
mixin. The kit installs Obscura 0.2.6 and its worker, with native stdio MCP,
CLI and loopback CDP. It adds no credentials or browsing network grants.

**Status:** source builds and Docker runtime checks pass. Native AMD64 and
ARM64 GitHub checks passed on commit `2553b4b`; changes after it need a fresh
CI run. GHCR publication and native SBX registry composition are pending.
The registry names below are planned destinations, not published images.
To try a local checkout before publication, see [setup](docs/setup.md).

## Add it to your agent

Use [Docker Sandboxes](https://docs.docker.com/ai/sandboxes/) (SBX)
with v3 kit support (target: 0.53.0) and a Debian-compatible Linux agent
workload containing `/usr/bin/python3` (3.11+), glibc 2.35+, libgcc and a CA store. The mixin
checks Python at install and requires the native libraries explicitly; Alpine/musl is unsupported. ARM64 is tested
natively; see [verification](docs/verification.md) for AMD64 coverage and limits.

Once the release is published to GHCR, add this entry to your existing
`sbxenv.yaml` **without replacing its other entries or settings**:

```yaml
kits:
  # Keep your existing workload and other mixins here.
  - source: ghcr.io/shelajev/obscura-sbx-kit-mixin:0.1.0
```

Prefer the verified release digest over a tag. GHCR must be permitted by your
SBX kit-source policy; retain existing entries when adding only
`ghcr.io/shelajev/`. For source builds and standalone use, see
[setup](docs/setup.md).

On your host, from the directory containing your environment file, inspect and
apply the configuration:

```sh
sbx env plan ./sbxenv.yaml
sbx env run ./sbxenv.yaml
```

The plan shows the selected kits; `run` creates the sandbox and attaches to the
agent. Kit changes require recreation of an existing sandbox. Save needed
container files, review `sbx env rm ./sbxenv.yaml`, then run the environment
again. Keep the environment file outside writable sandbox workspace mounts;
see the [environment-file guide](https://docs.docker.com/ai/sandboxes/configuration/environment-files/).

Inside the created sandbox, check `obscura --version`, then register MCP with
one of the following additive commands. Choose an unused server name if
`obscura` already exists:

```sh
codex mcp list
codex mcp add obscura -- /usr/local/bin/obscura mcp
```

```sh
claude mcp list
claude mcp add --transport stdio --scope user obscura -- /usr/local/bin/obscura mcp
```

Codex filters the environment of stdio MCP children. After adding the server,
add this key **inside the existing `[mcp_servers.obscura]` table** in the
sandbox's `~/.codex/config.toml`, preserving its `command`, `args` and all other
tables:

```toml
env_vars = ["OBSCURA_PROXY", "HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy", "SSL_CERT_FILE", "SSL_CERT_DIR"]
```

This passes current sandbox values without storing gateway addresses or secrets
in the configuration. Do not create a duplicate TOML table. Claude Code inherits
the launching sandbox environment; launch it from the SBX session without clearing proxy or CA variables.

Restart the agent and ask it to navigate `https://example.com` and take a
snapshot. Expect the title `Example Domain`. Test form filling and clicking
on a separately approved site that has a form. Each agent starts its own native MCP process;
no shared HTTP service or browser profile is created. Settings files are never
rewritten by the kit. Codex syntax follows the [official MCP guide](https://developers.openai.com/codex/mcp/)
and was checked against Codex 0.164.0. A live Codex session with the forwarding
configuration completed native MCP navigation and snapshot through the SBX
proxy. This does not establish native registry installation. Claude's example follows its
[stdio MCP documentation](https://code.claude.com/docs/en/mcp); its CLI was not
available for an execution check.

Grant only the browsing domains your task requires through the host's SBX
network policy. For a documentation example, an operator may approve
`example.com:443` with `sbx policy allow network example.com:443` on the host
if access is not already allowed; redirects and assets may need their own explicit grants.
The browser cannot grant itself access. See [troubleshooting](docs/troubleshooting.md)
for proxy and certificate checks.

## CLI and CDP

```sh
obscura fetch https://example.com --dump text
obscura fetch https://example.com --eval 'document.title' --screenshot /tmp/page.png
obscura serve --host 127.0.0.1 --port 9222
```

Connect a CDP client **inside the same sandbox** to `http://127.0.0.1:9222`.
The port is unauthenticated and must remain on loopback. Stop the server when
finished. Native MCP needs no port. Do not publish browser ports to the host.

Obscura is a lightweight browser engine, not full Chrome. CDP and rendering
cover a subset of browser behavior; successful fixture tests do not establish
site compatibility, CAPTCHA bypass or Chrome parity. The pinned build enables
rendering and uses ordinary TLS transport, without stealth impersonation.

## State and security

No `--storage-dir`, shared volume, private-network opt-in, file access, host
profile or host credential access is enabled by this kit. Cookies and web
storage remain process-local by default. Do not export `OBSCURA_STORAGE_DIR`
if you want independent sessions. Deliberate persistence must use a separate
private directory per agent; it can contain sensitive site state.

The launcher adapts only the configured proxy URL to Obscura's `--proxy` flag,
resolving the **proxy** to an IP literal to avoid upstream's proxy DNS rejection.
Target URLs still go through upstream URL checks and SBX policy. With a forward
proxy, destination DNS enforcement belongs to that proxy; preserve SBX's private
network restrictions. `NO_PROXY` is not used by the launcher: proxied browsing
stays subject to policy. No TLS verification bypass is used.

[Build and test](docs/verification.md) · [Updates and release](docs/maintenance.md)
· [Changelog](CHANGELOG.md) · [Apache-2.0 license](LICENSE)

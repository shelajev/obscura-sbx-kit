# Setup

The primary package is `mixin/`: add it to an existing v3 agent workload.
`standalone/` supplies a shell workload with the same browser installation.
Neither starts a browser service automatically. The standalone shell has no
agent or model credential; use the CLI directly, or compose your own agent.
See the [README prerequisites](../README.md#add-it-to-your-agent) first.

## Local checkout and standalone shell

Until GHCR publication, build from a checkout of this repository. On your host,
from the repository root, use one of these commands:

```sh
sbx run codex --kit ./mixin .
sbx run ./standalone .
```

The first adds the browser to the builtin Codex workload. It still needs your
normal SBX Codex model access. The second opens a shell without an agent.
Local and Git sources trigger a source build and require an available Docker
builder on the machine where SBX resolves the source. A stopped host Docker
blocks that path on SBX 0.53.0; use a published registry kit when available.
Do not infer native SBX composition from the Docker runtime checks alone.

Inside the standalone shell, check the version and fetch an approved page:

```sh
obscura --version
obscura fetch https://example.com --eval 'document.title' --screenshot /tmp/page.png
```

Expect version `0.2.6`, title `Example Domain` and `/tmp/page.png` to exist.
On the host, allow `example.com:443` through your SBX network policy if needed:
`sbx policy allow network example.com:443`. Assets and redirects need separate
scoped grants. For agent MCP registration, return to the README.

## Git and registry sources

For a commit already available in the public Git repository, replace `COMMIT`
with its full reviewed SHA and choose the mixin or standalone form:

```sh
sbx run codex \
  --kit 'git+https://github.com/shelajev/obscura-sbx-kit.git#ref=COMMIT&dir=mixin' .
sbx run 'git+https://github.com/shelajev/obscura-sbx-kit.git#ref=COMMIT&dir=standalone' .
```

After GHCR publication, the registry equivalents avoid source builds:

```sh
sbx run codex --kit ghcr.io/shelajev/obscura-sbx-kit-mixin:0.1.0 .
sbx run ghcr.io/shelajev/obscura-sbx-kit:0.1.0 .
```

Prefer each release's verified digest instead of its version tag. These are
planned destinations until publication; check [verification](verification.md)
for what has actually run.

Remote sources must be allowed by `kit.allowedSources`. Read its current value
with `sbx settings get kit.allowedSources`; add only `github.com/shelajev/` for
Git or `ghcr.io/shelajev/` for OCI while retaining every existing prefix. For
example, if the only existing prefix is `docker.io/`, this enables GHCR:

```sh
sbx settings set kit.allowedSources '["docker.io/","ghcr.io/shelajev/"]'
```

See [kit-source policy](https://docs.docker.com/ai/sandboxes/customize/use-kits/#restrict-kit-sources).
Source builds download from `github.com:443`, release redirects (currently
`release-assets.githubusercontent.com:443`), `dhi.io:443` for the shell base,
and Docker Hub for the pinned frontends (`registry-1.docker.io:443`,
`auth.docker.io:443` and layer redirects, commonly `production.cloudflare.docker.com:443`).
Inspect exact denials before granting any redirect host. Dockerfile and
schema frontend pins are in both kit directories; BuildKit's pin is in
`scripts/verify.sh` and the workflows. These downloads are separate from browser
runtime grants. Never allow arbitrary networks to install the kit.

## Environment files

`examples/codex/sbxenv.yaml` uses builtin `agent: codex`; merge only its browser
kit entry into your existing agent environment. Preserve credentials, workspace,
policy and other settings. `examples/standalone/sbxenv.yaml` is a complete shell
template, selecting its own workload. Copy it to your environment directory and
set `workspace` to your project path. Both examples refer to pending GHCR images.
Keep environment files outside writable workspace mounts and inspect them first.

On the host, from the environment directory:

```sh
sbx env plan ./sbxenv.yaml
sbx env run ./sbxenv.yaml
```

`plan` previews changes; `run` creates and attaches. Existing sandboxes retain
their composition. Save needed container files and review
`sbx env rm ./sbxenv.yaml`, then run again to apply kit changes.

The mixin has a scratch final image and overlays only `/opt/obscura` and one
`/usr/local/bin/obscura` launcher. Its native package requirements and Python
install check reject incompatible workloads. The standalone uses Docker's
pinned shell template, including the SBX runtime floor and Python. No host
browser installation is required.

References: [v3 usage](https://docs.docker.com/ai/sandboxes/customize/use-kits/),
[distribution](https://docs.docker.com/ai/sandboxes/customize/author/distribute/),
[environment files](https://docs.docker.com/ai/sandboxes/configuration/environment-files/).

# Setup

The primary package is `mixin/`: add it to an existing v3 agent workload.
`standalone/` supplies a shell workload with the same browser installation.
Neither starts a browser service automatically. The standalone shell has no
agent or model credential; use the CLI directly, or compose your own agent.

For local development, the current official SBX source syntax is:

```sh
sbx run docker.io/docker/sbx-kit-codex:0.162.1 --kit ./mixin .
sbx run ./standalone .
```

Run these through native SBX control on your host, using a build location
permitted by your environment. For this project's acceptance, all Docker
builds and browser execution must remain in its dedicated guest; the host
leader must use the guest-built artifacts rather than triggering a host build.
Native composition is still a required external check, not proven by Docker.

Once the source commit is published, Git distribution can select the mixin:

```sh
sbx run docker.io/docker/sbx-kit-codex:0.162.1 \
  --kit 'git+https://github.com/shelajev/obscura-sbx-kit.git#ref=COMMIT&dir=mixin' .
```

Replace `COMMIT` with a reviewed commit SHA; do not use that placeholder
literally. A scoped kit-source policy must permit this repository. Source
builds need `github.com:443` and GitHub's release-asset redirect hosts (currently
`release-assets.githubusercontent.com:443`), plus the pinned OCI registries.
These are build downloads, not browser runtime grants. Do not permit arbitrary
networks to install this kit.

After publication, the registry equivalents are:

```sh
sbx run docker.io/docker/sbx-kit-codex:0.162.1 \
  --kit ghcr.io/shelajev/obscura-sbx-kit-mixin:0.1.0 .
sbx run ghcr.io/shelajev/obscura-sbx-kit:0.1.0 .
```

The examples under `examples/` are consumer environment files. Review and merge
only the kit entry into an existing environment; keep your agent, credentials,
workspace, network policy and other settings. Their GHCR destinations are
pending publication. Use `sbx env plan` to inspect before `sbx env run`.
Creating a new sandbox is necessary to apply a changed composition.

The mixin has a scratch final image and overlays only `/opt/obscura` and one
`/usr/local/bin/obscura` launcher. Its native package requirements and Python install check reject incompatible
workloads. The standalone uses Docker's pinned shell template, which includes
the SBX runtime floor and Python. Nothing copies host configuration or requires
a host browser installation.

References: [official v3 usage](https://docs.docker.com/ai/sandboxes/customize/use-kits/),
[distribution](https://docs.docker.com/ai/sandboxes/customize/author/distribute/),
[environment files](https://docs.docker.com/ai/sandboxes/configuration/environment-files/).

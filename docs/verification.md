# Verification and compatibility

All development execution occurred inside the ARM64 SBX guest, using its Docker
29.7.2 daemon. No host browser, profiles or host Docker were used.

| Check | Measured result |
| --- | --- |
| ARM64/AMD64 upstream archives | SHA256 matched GitHub release metadata for v0.2.6 |
| Official v3 frontend | Pinned `docker/sandbox-kit:3` digest identifies 3.0.0-m.11 |
| Official kit-tck 3.0.0-m.11 | Both multiarch mixin/workload layouts: 19/19 checks |
| ARM64 native CLI | Fixture navigation, JS extraction, PNG; private URL denial |
| Native stdio MCP | Initialize, tools/list, navigate, snapshot, fill, click, evaluate |
| Session isolation | Two simultaneous processes: independent DOM, cookies, localStorage |
| Trust roots | Untrusted fixture CA rejected; supplied CA accepted |
| Actual SBX proxy | Public HTTPS CLI and MCP pass; private/localhost/metadata URLs denied |
| ARM64 Docker | CLI/MCP/render/TLS fixture tests and Puppeteer CDP pass |
| AMD64 guest Docker + QEMU user mode | Native archive CLI/MCP/render/TLS fixture tests pass under emulation |
| AMD64 native runner | CI prepared; not run during guest development |
| Official resolver/assembler | Published shell workload + final mixin resolve and compose; composed Docker CLI/MCP/TLS/render/CDP pass |
| Native SBX 0.53.0 composition | Pending host control-plane check |
| Public GitHub CI / GHCR publication | Prepared; not run or published |
| Host editorial/fresh-reader route | Required handoff; not claimed complete |

The AMD64 emulation test invokes the upstream binary through QEMU in an AMD64
container, not the Python launcher; launcher unit tests and native ARM64 tests
cover proxy handling. This is not proof of native AMD64 SBX behavior. CDP was
checked with development-only puppeteer-core 24.26.1 on ARM64; no generic browser
framework is shipped in either kit.

For reproducible guest checks, install Go 1.26.11 and the pinned TCK, create a
Buildx container builder, then run from the repository root:

```sh
go install github.com/docker/sandbox-kit-spec/v3/cmd/kit-tck@v3.0.0-m.11
docker buildx create --name obscura-kit --driver docker-container \
  --driver-opt image=moby/buildkit:v0.25.1@sha256:79cc6476ab1a3371c9afd8b44e7c55610057c43e18d9b39b68e2b0c2475cc1b6 --use
scripts/verify.sh
```

Use `BUILD_CA_FILE=/path/to/public-ca-bundle` only if the build environment needs
an interception root. It is a BuildKit secret, not retained in the image. The
normal public registry build needs no secret or credential. Do not bypass TLS.
The shell base includes Python and OpenSSL; Node/npm are needed only in the
development environment for Puppeteer. CI uses each architecture's native runner.

For a multiarch OCI artifact (build execution stays on the build machine):

```sh
docker buildx build mixin -f mixin/obscura-mixin.yaml \
  --platform linux/amd64,linux/arm64 -t obscura-mixin:0.1.0 \
  --output type=oci,dest=.local/mixin-layout,tar=false
kit-tck validate --layout .local/mixin-layout 0.1.0 --verbose
```

Repeat with `standalone`, `standalone/obscura.yaml` and a separate output layout.
The guest also composed the published shell kit
`docker.io/docker/sbx-kit-shell@sha256:a72c2ead8a2ab26ac552e4578ea0e23b5e777e81e8a90108e676be09cffa69a4`
with this mixin through the official m.11 resolver and `assemble.Merge` API,
preserving base entrypoint/user, then ran the fixture suite and Puppeteer in
that composed image. A local experiment harness produced this evidence; it is
not runtime glue shipped in the kit. The initial Python package-alias requirement
failed because DHI names its package `python-3.14`; the mixin now verifies the
Python executable at install while retaining libc/libgcc package requirements.

TCK validates kit metadata and content, not a live SBX control plane. Plain
Dockerfile images used in runtime tests are not substitutes for published kits.

Unit tests use Python's standard library:

```sh
python3 -m unittest discover -s tests -v
```

`tests/runtime.py` executes actual binaries. Its local fixture clears proxy
variables and opts into private networking only for that process. Set
`OBSCURA_PUBLIC_HTTPS=https://example.com` to request the separate approved
public HTTPS test. `OBSCURA_COMMAND` can select a launcher or Docker invocation.
The test assumes that public URL has title `Example Domain`.

The initial hostname-proxy probe failed upstream's DNS SSRF guard. Passing the
configured proxy as a literal through `--proxy` succeeded without relaxing
private-target blocking. A negative run without custom-root variables also
succeeded using this guest's system trust; the controlled test provides the
meaningful positive/negative trust-root evidence. Initial TLS fixture and
frontend namespace mistakes are retained in local evidence, not hidden.

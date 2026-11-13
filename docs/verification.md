# Verification and compatibility

The source checks below used an ARM64 SBX sandbox and its Docker 29.7.2
daemon. Subsequent GitHub checks ran on native AMD64 and ARM64 runners.
No host browser or profiles were used.

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
| ARM64 Docker | Standalone and actual mixin OCI overlay: CLI/MCP/render/TLS/proxy fixture tests and Puppeteer CDP |
| AMD64 sandbox Docker + QEMU user mode | Native archive CLI/MCP/render/TLS fixture tests pass under emulation |
| Native AMD64 and ARM64 GitHub runners | Both architecture checks passed for 0.1.1 tag source `c57f192` and merged main `2259a26` |
| Official resolver/assembler | Published shell workload + final mixin resolve and compose; composed Docker CLI/MCP/TLS/render/CDP pass |
| Live Codex 0.167.2 native MCP | Published mixin on native ARM64 SBX: HTTPS navigation and snapshot passed with explicit proxy/CA forwarding |
| Native ARM64 SBX 0.53.0 registry composition | Both published immutable digests created sandboxes; each passed all five runtime tests and loopback CDP checks |
| Native AMD64 outer SBX composition | Untested; native AMD64 GitHub CI is separate coverage |
| Published registry TCK | Both digest-preserving copies and layout guards passed; mixin and standalone each completed 19/19 |
| GHCR publication | 0.1.1 succeeded for both kits; 0.1.0 partial failure retained |

The AMD64 emulation test invokes the upstream binary through QEMU in an AMD64
container, not the Python launcher; launcher unit tests and native ARM64 tests
cover proxy handling. This is not proof of native AMD64 SBX behavior. CDP was
checked with development-only puppeteer-core 24.26.1 on ARM64; no generic browser
framework is shipped in either kit.

To reproduce checks, use a build environment with Docker/Buildx, Python 3.11+,
Go 1.26.11, Node 24.11.1 and npm 11.19.1 (supports the seven-day age hold).
The commands below install the pinned TCK and create a Buildx container builder.
Run them from the repository root, with Docker available:

```sh
go install github.com/docker/sandbox-kit-spec/v3/cmd/kit-tck@v3.0.0-m.11
docker buildx create --name obscura-kit --driver docker-container \
  --driver-opt image=moby/buildkit:v0.25.1@sha256:79cc6476ab1a3371c9afd8b44e7c55610057c43e18d9b39b68e2b0c2475cc1b6 --use
bash scripts/verify.sh
```

`verify.sh` runs Python unit tests and version consistency checks, builds each
kit for the current architecture into `.local/`, and runs TCK (expect 19/19).
It builds and loads standalone and composed-overlay runtime images, runs the
CLI/MCP/render/TLS/proxy/isolation fixture suite in both, checks license files,
then runs `npm ci --ignore-scripts` and Puppeteer CDP against both images.
No separate npm install is needed. A pass exits zero after both CDP summaries;
a build or test failure stops the script. It does not run native SBX control
or publish images. It needs the source-build endpoints listed in [setup](setup.md),
the Go module endpoints and npm registry permitted by your build environment.
The deterministic browser fixtures need no public browsing grant.

Use `BUILD_CA_FILE=/path/to/public-ca-bundle` only if the build environment needs
an interception root. It is a BuildKit secret, not retained in the image. The
normal public registry build needs no secret or credential. Do not bypass TLS.
The shell base includes Python and OpenSSL; Node/npm are needed only in the
development environment for Puppeteer. CI uses each architecture's native runner.

For a multiarch OCI artifact (build execution stays on the build machine):

```sh
docker buildx build mixin -f mixin/obscura-mixin.yaml \
  --platform linux/amd64,linux/arm64 -t obscura-mixin:0.1.1 \
  --output type=oci,dest=.local/mixin-layout,tar=false,oci-mediatypes=true,compression=gzip,force-compression=true
kit-tck validate --layout .local/mixin-layout 0.1.1 --verbose
```

Repeat with `standalone`, `standalone/obscura.yaml` and a separate output layout.
A sandbox experiment also composed the published shell kit
`docker.io/docker/sbx-kit-shell@sha256:a72c2ead8a2ab26ac552e4578ea0e23b5e777e81e8a90108e676be09cffa69a4`
with this mixin through the official m.11 resolver and `assemble.Merge` API,
preserving base entrypoint/user, then ran the fixture suite and Puppeteer in
that composed image. A local experiment harness produced this evidence; it is
not runtime glue shipped in the kit. The initial Python package-alias requirement
failed because DHI names its package `python-3.14`; the mixin now verifies the
Python executable at install while retaining libc/libgcc package requirements.

TCK validates kit metadata and content, not a live SBX control plane. Plain
Dockerfile images used in runtime tests are not substitutes for published kits.

The verification script also loads the actual frontend-produced mixin OCI layout
as a named build context, overlays it onto the pinned shell base, and runs the
same runtime/CDP checks as the standalone. Both images retain LICENSE, NOTICE
and bundled dependency license texts. Deterministic proxy fixtures run in CI:
HTTPS CONNECT with a supplied test CA and external script; CDP HTTP proxy with
a reserved synthetic origin; live private-target denials without SSRF opt-in.

Unit tests use Python's standard library:

```sh
python3 -m unittest discover -s tests -v
```

To run only the binary fixture suite from the repository root, after installing
the launcher and browser in your test sandbox:

```sh
python3 tests/runtime.py
```

`tests/runtime.py` executes actual binaries. Its local fixture clears proxy
variables and opts into private networking only for that process. Set
`OBSCURA_PUBLIC_HTTPS=https://example.com` to request the separate approved
public HTTPS test. `OBSCURA_COMMAND` can select a launcher or Docker invocation.
The test assumes that public URL has title `Example Domain`.

The initial hostname-proxy probe failed upstream's DNS SSRF guard. Passing the
configured proxy as a literal through `--proxy` succeeded without relaxing
private-target blocking. A negative run without custom-root variables also
succeeded using the sandbox's system trust; the controlled test provides the
meaningful positive/negative trust-root evidence. Initial TLS fixture and
frontend namespace mistakes are retained in local evidence, not hidden.

Release 0.1.0 run `43404277441` published the mixin OCI index
`sha256:dc1ed99195b00eecf4143a6767e151c123a6ebf3cfa28c126ea1cef440e9f2b4`
and failed copying the standalone index. No GitHub release was published.
The standalone tag returned `manifest unknown`; partial blobs may remain.
Neither registry destination nor `v0.1.0` may be overwritten or deleted.

Saved local layouts and fresh Buildx 0.36.1/0.38.2 exports already have OCI
indexes and OCI children. A sandbox-local registry reproduced the precise
preserved-digest failure: inherited zstd workload layers cause Skopeo to add
`io.github.containers.compression.zstd` annotations to platform descriptors.
An unrestricted diagnostic copy exposed that index change. Skopeo 1.13.3
(the Actions version) reproduced the error and successfully copied both fixed
0.1.1 kits with `--all --preserve-digests` to a sandbox-local registry. The
registry returned byte-for-byte identical tagged index blobs for both kits. The fix explicitly
exports OCI with gzip and forces recompression of inherited layers; provenance
remains enabled. The release layout check traverses the actual tagged blob and
children, verifying their digests and media types and rejecting non-gzip image
layers. TCK and OCI-to-OCI copies alone did not catch this registry-copy behavior.

## Published 0.1.1 validation

[Native source CI](https://github.com/shelajev/obscura-sbx-kit/actions/runs/43414488782)
passed on real AMD64 and ARM64 runners for tag source
`c57f192289b59f1fb33278aa50dfacc474a0bdda`.
[Merged-main CI](https://github.com/shelajev/obscura-sbx-kit/actions/runs/43415406091)
also passed at `2259a26`. Each architecture ran unit, build, layout/TCK,
standalone and composed runtime, and Puppeteer CDP checks. The optional public
HTTPS runtime test was skipped in CI; it passed separately in native ARM64 SBX.

[Release run 43415479048](https://github.com/shelajev/obscura-sbx-kit/actions/runs/43415479048)
published both kits from that merged main using immutable `v0.1.1`.
The raw published index bytes matched these SHA256 references, now pinned in
[setup](setup.md) and both consumer examples:

- `ghcr.io/shelajev/obscura-sbx-kit-mixin@sha256:29aa5cd0daf043d4599a64dc885deddab43824b1d2f2849b165f4ff502d85c36`
- `ghcr.io/shelajev/obscura-sbx-kit@sha256:40759258242928bcd042ce10b23e35279fcd50e278480ae459a50abe6b9888a8`

Both packages were anonymously readable. Digest-preserving copies and layout
guards passed for both published kits. The final registry TCK completed
19/19 checks for each, including the standalone check that was still running
when the initial publication evidence was recorded.

Native ARM64 SBX 0.53.0 created a standalone sandbox and composed the published
mixin with the official agent kit
`docker.io/sbx/codex@sha256:5aa3f585b5a42cca80f5921e99890c9f0035b31d21553efd3d1d2171e46eb572`
(Codex 0.167.2, Python 3.14.10). Each passed all five `tests/runtime.py` tests:
CLI JS/render/SSRF, positive/negative TLS trust, MCP interactions and independent
state, proxied HTTPS subresources and live SSRF denial, and public HTTPS CLI/MCP
with private/metadata/localhost denial. Separate `/json/version` and kernel TCP
listener checks confirmed CDP bound only to `127.0.0.1`. The mixin retained the
binaries, worker, LICENSE/NOTICE and V8 notice. A live Codex turn used registered
native MCP navigation and snapshot to return the Example Domain title and
first visible sentence. Existing configuration was preserved; only the scoped
`example.com:443` browsing grant was added.

Host-native `sbx env plan` passed for both updated consumer YAML files,
selecting the expected agents and published digests. The example environments
were planned only; runtime tests used separate native sandboxes. Live Claude
CLI registration and native AMD64 outer SBX composition remain untested. These checks do not establish Chrome, CAPTCHA or general
site compatibility.

The fresh patch exports used Buildx 0.38.2 and the pinned BuildKit/frontend in
an ARM64 SBX. DHI began returning anonymous-token HTTP 401 during testing;
subsequent builds used a local registry mirror reconstructed from existing SBX
content. Every base blob and the original pinned index digest were verified.
Both architecture configs retain identical inherited uncompressed layer IDs.
Initial authentication, disk exhaustion and transient exporter lock errors are
retained in private local evidence. That earlier mirror-based experiment did not itself establish native AMD64
runtime behavior or GHCR publication; the later CI and publication checks above
provide those separate results.

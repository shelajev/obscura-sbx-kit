# Updates and release

Keep browser upgrades separate from changes to network authority. The mixin
has no default runtime egress and no lifecycle hook that rewrites agent files.

For each update:

1. Read the upstream release notes and wait at least seven days after publication.
   Verify each Linux render/non-stealth archive digest against GitHub metadata;
   update `VERSION` and `ARCHIVES` in `mixin/scripts/install-browser.py` and copy
   that file to `standalone/scripts/`. Keep both native executables together.
2. Update both descriptors' browser provides and kit versions, changelog, example
   tags and release workflow version guards together. Keep the two download
   stages and scripts identical; unit tests detect drift. Inspect upstream
   licenses and runtime dependencies before retaining compatibility claims.
3. Renew OCI base/frontend/BuildKit digests only after the same seven-day hold.
   Read the pinned frontend version and match kit-tck to it. Verify official
   schema changes before changing capabilities. No floating executable installers.
4. Run unit tests, native architecture runtime checks, controlled TLS, actual
   scoped-proxy HTTPS, independent MCP session checks, CDP and both OCI layouts'
   conformance. Use native AMD64 and ARM64 runners before declaring native support.
   Obtain native outer SBX validation when runtime composition changes.
5. Obtain independent technical review of current source/evidence and host-routed
   blog-writer plus fresh-reader review for public docs. Preserve failures and
   actual reviewer model metadata privately under `.local/`.

Renovate has a seven-day `minimumReleaseAge`, SHA pin renewal for Actions, OCI
Dockerfile digest renewal and TCK version discovery. Enable Renovate on the
repository; configuration alone does not activate the app. Frontend/BuildKit
syntax directives and custom browser archive hashes require manual verification
and synchronized updates. `.npmrc` enforces a seven-day npm hold on tooling
resolution; `package-lock.json` pins the test-only dependency graph. Use a recent
npm that supports `min-release-age`; no browser framework is in the runtime.

## Host publication plan

Nothing is pushed or published from the development guest. The host leader
integrates the reviewed feature commit, runs native SBX checks and receives the
required editorial review. It then verifies both native CI jobs passed for the
exact candidate and creates an immutable `v0.1.0` tag on main.

Before dispatching publication, configure the GitHub `release` environment with
required reviewers and a main-only deployment policy. Repository default token
permissions stay read-only. Confirm GHCR permits this repository's Actions token
to create its two packages, and set package visibility as intended. No Docker
Hub secret or long-lived registry token is required.

Dispatch `Publish release kits` **from main** with tag `v0.1.0`. The job rejects
other versions, requires the tag commit to be on main, builds both architectures
with the official frontend and validates both layouts before logging in. It
copies those validated OCI layouts to:

- `ghcr.io/shelajev/obscura-sbx-kit-mixin:0.1.0`
- `ghcr.io/shelajev/obscura-sbx-kit:0.1.0`

Only that job has `packages: write`, using ephemeral `GITHUB_TOKEN` and a temporary
registry auth file. All workflows run only on push/manual events; no PR events.
A partial registry copy can leave one package published if the second fails:
inspect digests before retrying. Do not move existing release tags to hide a
failure. Record both published OCI index digests, run registry TCK, test native
SBX using those digests and update consumer examples to immutable references.

This workflow is prepared, not a successful publication claim. It does not
create signatures or attest independent review. If signature enforcement is
required, the host must add and validate its intended signing path first.

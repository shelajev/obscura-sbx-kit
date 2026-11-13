# Updates and release

Keep browser upgrades separate from changes to network authority. The mixin
has no default runtime egress and no lifecycle hook that rewrites agent files.

For each update:

1. Read the upstream release notes and wait at least seven days after publication.
   Verify each Linux render/non-stealth archive digest against GitHub metadata;
   update `VERSION` and `ARCHIVES` in `mixin/scripts/install-browser.py` and copy
   that file to `standalone/scripts/`. Keep both native executables together.
2. Update both descriptors' browser provides and kit versions, changelog, example
   tags, package.json and package-lock.json versions together. Keep the two download
   stages and scripts identical; unit tests detect drift. Inspect upstream
   licenses and runtime dependencies before retaining compatibility claims.
3. Renew OCI base/frontend/BuildKit digests only after the same seven-day hold.
   Read the pinned frontend version and match kit-tck to it. Verify official
   schema changes before changing capabilities. No floating executable installers.
4. Run unit tests, native architecture runtime checks, controlled TLS, actual
   scoped-proxy HTTPS, independent MCP session checks, CDP and both OCI layouts'
   conformance. Use native AMD64 and ARM64 runners before declaring native support.
   Obtain native outer SBX validation when runtime composition changes.
5. Obtain independent technical review of current source/evidence and audience
   review for public setup instructions. Keep review evidence private and
   preserve failed checks alongside successes.

Dependabot renews GitHub Actions pins weekly with a seven-day cooldown; its
configuration is built in at `.github/dependabot.yml`. Its update PRs do not
trigger CI: maintainers must run manual checks on those branches before merging.
Renovate has a seven-day `minimumReleaseAge`, SHA pin renewal for Actions, OCI
Dockerfile digest renewal and TCK version discovery. Enable Renovate on the
repository; configuration alone does not activate the app. Frontend/BuildKit
syntax directives and custom browser archive hashes require manual verification
and synchronized updates. `.npmrc` enforces a seven-day npm hold on tooling
resolution; `package-lock.json` pins the test-only dependency graph. Use a recent
npm that supports `min-release-age`; no browser framework is in the runtime.

## Publish a release

Integrate the reviewed candidate into main and verify both native architecture
CI jobs passed for that exact source. Configure the GitHub `release` environment
with a main-only deployment policy. No required human-reviewer gate is needed.
Keep repository default token permissions read-only, and confirm the Actions
token can create both GHCR packages. Set package visibility for intended users.
No Docker Hub secret or long-lived registry token is required.

For the next patch release, from an up-to-date main checkout after checks pass:

```sh
python3 scripts/release.py v0.1.1
git tag v0.1.1
git push origin refs/tags/v0.1.1
gh workflow run release.yml --ref main -f tag=v0.1.1
```

The local validator prints `0.1.1` and rejects mismatched descriptor, package
or lockfile versions. For later releases, bump all those versions and the
changelog/examples, then use the new `vMAJOR.MINOR.PATCH` tag. Do not force or
move an existing Git tag.

The manual workflow accepts only main and requires the reviewed tag commit to
be an ancestor of that main checkout. It derives the version from the tag and
validates it against both kit descriptors and package manifests. It builds both
architectures and validates both OCI layouts before registry login, then copies
those exact layouts with digest preservation to:

- `ghcr.io/shelajev/obscura-sbx-kit-mixin:0.1.1`
- `ghcr.io/shelajev/obscura-sbx-kit:0.1.1`

Only the publication job has `packages: write`, using ephemeral `GITHUB_TOKEN`
and a temporary auth file removed on exit. The workflow checks both destinations
before any copy and refuses if either version already exists. Authentication,
TLS, network and ambiguous lookup failures also stop publication. Release jobs
are serialized. Limit other writers to these packages: GHCR provides no atomic
create-only tag operation here, so an unrelated publisher could race the check.

A partial copy leaves an immutable partial release. A rerun refuses to overwrite
it; inspect and retain its digest, fix the cause, and prepare a new patch version
through the normal review path. Do not delete or retag published versions to
hide failures. Successful copies record each `ghcr.io/...@sha256:...` reference
in the Actions job summary. Record both, run registry TCK and native SBX consumer
checks using those digests, then update examples to the verified digest references.

Release 0.1.0 is a failed partial publication: manual run `43404277441`
published the mixin index
`sha256:dc1ed99195b00eecf4143a6767e151c123a6ebf3cfa28c126ea1cef440e9f2b4`,
then failed copying the standalone index. The standalone tag returned
`manifest unknown`; blobs may remain. No GitHub release was published.
Retain `v0.1.0` on `d3d17a8` and both registry destinations; never rerun 0.1.0.
Prepare 0.1.1 through review and fresh native CI instead.

Exports must set `oci-mediatypes=true,compression=gzip,force-compression=true`.
The inherited workload base has zstd layers. Skopeo adds compression annotations
to its index during registry copy, which violates `--preserve-digests` even when
the original tagged index is already OCI. Explicit OCI media types alone do not
fix this. Forcing gzip also recompresses inherited layers; retain provenance.
The pre-login layout check reads the actual tagged blob and its child manifests,
checks their digests/media types and rejects non-gzip image layers. An OCI layout
wrapper and a successful OCI-to-OCI copy alone do not prove registry compatibility.
Test a preserved-digest copy to a disposable registry before publication.

0.1.1 GHCR publication and native registry consumption remain pending.
The workflow does not sign kits or attest
independent review. Environments requiring signatures need a separately validated
signing path before consumption. All workflows use push/manual events only.

Distribution notice texts live under each kit's `licenses/` and are copied into
`/opt/obscura/licenses`, alongside `/opt/obscura/LICENSE` and `NOTICE`. Their
`SOURCES.md` records provenance; preserve texts when updating binaries. The
upstream archive supplies no consolidated binary SBOM; this project does not
claim an exhaustive independently rebuilt dependency inventory.

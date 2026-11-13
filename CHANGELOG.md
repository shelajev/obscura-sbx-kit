# Changelog

## 0.1.1 — unreleased

- Export explicit OCI media types and force gzip layers, including inherited
  base layers, so Skopeo can copy both kits to registries with digest preservation.
  Retain provenance; OCI media types alone do not prevent zstd index annotation
  rewrites during registry copy.
- Accept single-platform OCI image manifests as well as tagged OCI indexes;
  check tagged and child manifest blobs before login, rejecting
  non-OCI manifests and image layers requiring compression annotation rewrites.
- Pin the tested Buildx CLI to v0.38.2 in validation and release workflows.
- Bump both kits, development package/lockfile and consumer examples together.

## 0.1.0 — partial publication (2026-11-13)

Manual release run `43404277441` published the mixin, then failed copying the
standalone index with digest preservation. No GitHub release was published.
The immutable `v0.1.0` tag remains on `d3d17a8`. Preserve both destinations;
never rerun, overwrite or delete this version. The anonymously readable mixin
index is `sha256:dc1ed99195b00eecf4143a6767e151c123a6ebf3cfa28c126ea1cef440e9f2b4`.
The standalone tag returned `manifest unknown`; partial blobs may remain.

Original changes:

- Add reusable SBX v3 Obscura mixin and standalone shell workload.
- Pin render-enabled Obscura 0.2.6 Linux archives for ARM64 and AMD64.
- Adapt SBX proxy endpoints without disabling native SSRF or TLS checks.
- Document native stdio MCP, CLI, loopback CDP and independent agent state.
- Add fixture, transport, session-isolation, render and CDP checks;
  official v3 conformance; push/manual CI and manual GHCR release preparation.
- Complete public setup and Codex proxy forwarding instructions; distinguish
  measured checks from pending registry consumption.
- Add built-in Actions dependency renewal, synchronized release version checks
  and fail-closed protection against overwriting either published kit version.
- Initialize ephemeral registry authentication as JSON and handle signal-exited
  CDP browser processes without hanging cleanup.

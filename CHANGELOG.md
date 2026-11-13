# Changelog

## 0.1.0 — unreleased

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

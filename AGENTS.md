# Repository maintenance

This repository packages Obscura as a reusable Docker Sandboxes v3 browser
mixin and a standalone shell workload. Read README.md and docs/maintenance.md
before changing installation, transport or release behavior.

- Keep mixin and standalone launcher/installer sources and download stages in
  sync. Pin browser archives with SHA256 and container bases by digest.
- Preserve upstream SSRF and TLS verification defaults, loopback browser
  servers, independent agent sessions and explicit scoped network access.
- Prefer native stdio MCP for agents; document CLI/CDP compatibility limits.
- Hold dependency releases for at least seven days. Pin Actions to full SHAs,
  use read-only default permissions and never add pull_request or
  pull_request_target workflow triggers. Publish only through the guarded
  manual release workflow; never overwrite version tags.
- Run affected Python unit tests and release checks. Changes to runtime or
  composition require the relevant Docker/runtime/TCK checks and native
  AMD64/ARM64 CI. Keep unrun platform checks and external validation explicit.
- Obtain independent technical review of substantive behavior changes and
  audience review of public setup instructions. Keep private review packets,
  identity resources and execution reports out of commits.
- Use .local/ for reports and optional .beans/ plus .beans.yml for local task
  tracking; all are ignored. Never commit credentials or private environments.
- Update CHANGELOG.md and document changed prerequisites and release behavior.

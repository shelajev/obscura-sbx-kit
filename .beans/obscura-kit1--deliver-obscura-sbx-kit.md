---
id: obscura-kit1
title: Deliver a reusable Obscura SBX kit
status: in-progress
type: feature
priority: normal
---

User requested a complete SBX browser kit for https://www.obscura.sh/,
using agy-sbx-kit as an example, a GitHub repository, project-local Beans,
pinned GitHub Actions, and no workflows triggered by pull requests.
User selected a Herdr crew for this task.

Deliverable: an installable browser mixin for existing SBX agents, a useful
standalone workload/example, agent MCP integration, secure defaults,
documentation, and GitHub CI/release preparation.

Next use: agents and developers should be able to follow the documented
installation and use the browser inside SBX, with explicit network grants
and no host browser profiles, credentials, or browser services.

Independent QA must verify actual installation/composition and representative
CLI, MCP, and CDP behavior; authentication/bind defaults; compatibility with
SBX proxy/certificate/network enforcement; architecture claims; pinned
downloads and workflow actions; tests; and usable reader instructions.

Current status: operator selected one-off codex-obscura-kit execution with
Codex implementation and independent Gemini Carbon review. Herdr sequencing
above is superseded. Reading upstream v0.2.6 and current SBX v3 specification;
critical proxy/runtime feasibility experiment precedes implementation.
Local evidence and resource requests live under .local/. Host handles native
outer SBX validation, editorial routing and GitHub integration. No publishing
or host execution is authorized from this guest.

Implemented (one-off route): reusable mixin and standalone workload with native
Obscura 0.2.6, proxy adaptation, additive MCP instructions, loopback CDP,
Python prerequisite check, archive/base pins, CI/release preparation and docs.
Measured: 10 unit tests; native ARM64 and emulated AMD64 fixture browser checks;
actual scoped SBX HTTPS via CLI/MCP; isolated process state; trusted/untrusted
TLS fixture; Puppeteer CDP; both multiarch OCI layouts pass official m.11 TCK.
Official resolver + assembler composition with Docker shell also passes runtime
and CDP checks. Carbon review in progress; exact reports remain .local/.

Remaining acceptance is host-routed: native SBX 0.53.0 creation from guest-built
artifacts, native AMD64 CI, scoped blog-writer/fresh Gemini audience review,
GitHub integration and eventual GHCR publication. No guest push/PR/release.

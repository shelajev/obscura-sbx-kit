---
id: obscura-kit1
title: Deliver a reusable Obscura SBX kit
status: todo
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

Current status: blocked before crew provisioning. Operator approved the host
factory diagnostic and dashboard registration/sampler/watchdog for this task.
Diagnostic verified driver/source identity; stale unrelated Learnmap watchdog
registration fails its monitoring check. More importantly, the Herdr security
restoration is not accepted/promoted: see central ai-contrib-hs12 and
../.local/herdr-factory/security-20261112/STATE.md. Recorded default still uses
the old template. No crew has been provisioned or started; no restoration
workers or services have been restarted. Awaiting operator choice to wait for
restoration or use a verified patched one-off SBX route.

GitHub repository created: https://github.com/shelajev/obscura-sbx-kit
It is empty. Local Git initialized on main with origin configured. Actions
default token is read-only, Actions cannot approve PR reviews, and allowed
Actions are restricted to GitHub-owned plus named Docker build/publish actions.
No workflows or PR triggers exist. All eventual workflow references must be
pinned to full commit SHAs. No browser kit implementation or checks are claimed.

Keep implementation tasks in this store. A single central Bean is required
only for Herdr lifecycle, acceptance, usage preservation, and cleanup.

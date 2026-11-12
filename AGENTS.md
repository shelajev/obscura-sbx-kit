# Obscura SBX kit

Build a reusable Obscura browser mixin and standalone example for Docker SBX.
The repository is https://github.com/shelajev/obscura-sbx-kit, owned by the
operator. Detailed work belongs in this project's Beans store.

## Execution and review

The operator selected one-off SBX with Codex implementing and Gemini reviewing,
following the blog-writing model. No Herdr server or crew. All code, package
tools, builds, diagnostics and tests execute inside codex-obscura-kit; never
execute project code on the host. The development environment declaration is
host-private and must not be copied into this public repository. It uses a
verified local blog security template, not an external consumer prerequisite.

Use Gemini gemini-4-carbon for consultation and independent review when access
is verified; the operator explicitly permits gemini-4-argon as fallback. Treat
timeouts/errors/truncation as incomplete reviews. Review the current source
and evidence, address material findings, and record actual model and results.
No additional agents or orchestration frameworks. Model API keys remain in
the SBX proxy; never print them or add host credentials/mounts/forwarding.

Implement and test on feat/obscura-browser-kit. All implementation belongs in
this new standalone repository. Host leader handles GitHub publication and
any required external validation using native SBX control; no guest GitHub
credential is supplied. Do not push main directly. Keep reports under .local/.

## Acceptance

Read .local/brief.md for the task contract; its Herdr-specific sequencing is
superseded by the operator's one-off selection above. Deliver usable source,
actual CLI/MCP/CDP/browser installation and composition evidence, tests,
secure defaults, documentation and CI/release setup. Do not claim unsupported
Chrome parity, successful publication or unrun platform checks. The host's
current SBX is 0.53.0 and uses v3 kits; inspect the current official schema.

Never enable pull_request or pull_request_target workflows. Pin every Action
to a full commit SHA, use read-only default workflow permissions, restrict
publishing to the intended release path, and configure dependency renewal.
Pin browser archives with SHA256 and container bases by digest. Respect package
age holds of at least seven days. Avoid floating executable installers and
TLS-verification bypasses. Retain upstream SSRF defaults and bind browser
servers to loopback. Agent browser sessions must be independent by default.

Prefer Obscura native stdio MCP for agents and support CLI/CDP as documented.
Explicitly test SBX proxy and trust-root behavior: upstream ignores HTTP_PROXY
and HTTPS_PROXY. Do not broadly allow networks or host/private targets to
make a test pass. A localhost test fixture can deliberately opt into private
network access in tests only. Request missing external domains with purpose.

Public docs need scoped blog-writer editorial review and a fresh Gemini
audience review before final handoff. Host leader arranges that route. Keep
private identity resources and review packets out of commits.

Commit meaningful passing implementation with an imperative subject under
72 characters, add a changelog, and report exact commit, test outcomes,
review evidence and unresolved limitations. Preserve failed checks in reports.

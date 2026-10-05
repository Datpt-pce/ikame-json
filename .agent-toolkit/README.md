# Installed project tools

Shared rules: [MASTER.MD](../MASTER.MD).
Paseo SLP policy: [policies/paseo-slp.md](policies/paseo-slp.md).
Windows Codex Room updater: [paseo/SETUP-WINDOWS.md](paseo/SETUP-WINDOWS.md).
Advisory routing: [paseo/routing.json](paseo/routing.json).
On Windows with Paseo installed, toolkit bootstrap refreshes the three host profiles from the pinned upstream commit and applies paseo/local-policy.toml unless --dry-run or --skip-paseo-update is used; --paseo-source latest is an explicit opt-in.
Acceptance workflow for SLP work: [paseo/SLP-WORKFLOW.md](paseo/SLP-WORKFLOW.md).
Read-only usage reporter: [paseo/slp-budget.py](paseo/slp-budget.py); optional governor plugin source is distributed but never auto-installed.
Run `node .agent-toolkit/codegraph.mjs status --json` from this project.
CodeGraph and its npm lockfile live in `codegraph/`.
MCP configuration takes effect after reloading the clients.

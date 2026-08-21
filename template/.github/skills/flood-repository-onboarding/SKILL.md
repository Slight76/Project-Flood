---
name: flood-repository-onboarding
description: Establish or refresh an evidence-backed Project Flood profile, routes, commands, harness capabilities, and environment setup before substantial work.
---

# Flood Repository Onboarding

Use for a new installation, an unverified profile, or a structural/tooling change that invalidates current routes.

1. Read the contract, profile, routing, memory index, harness matrix, policy, and current focus.
2. Have Flood Scout inspect manifests, runtimes, entry points, major directories, tests, CI/CD, deployment, generated code, ownership, and documented security constraints.
3. Verify non-destructive restore, build, lint, test, migration, and local-run commands where the environment supports them. Record unknowns as unknown.
4. Detect the intended Copilot surfaces and record capability gaps; do not assume prompt files, hooks, session tools, or MCP tools exist everywhere.
5. Propose repository-specific routes, protected paths, external-tool allowlist entries, CODEOWNERS entries based on `.project-flood/CODEOWNERS.example`, least-privilege cloud-agent restore/build steps in `copilot-setup-steps.yml`, and—only for approved adapter installs—a conflict-aware merge of `copilot-settings.adapter.example.json`.
6. Require human review for architecture, ownership, security, external access, and policy choices.
7. Have Flood Librarian update approved profile/memory state and regenerate the index.

Do not edit product code. Return evidence, proposed changes, contradictions, unknowns, and decisions requiring approval.

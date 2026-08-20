---
name: repository-onboarding
description: Build or refresh Project Flood's evidence-backed repository profile and routing map before substantial work, or after major structural, tooling, or architecture changes.
---

# Repository Onboarding

Use this skill when `.agent-team/project-profile.md` is not onboarded, when verified commands are missing, or when a major refactor makes the profile unreliable.

## Outcome

Produce a compact, reviewable repository map that helps future agents find authoritative context without copying the codebase into Markdown.

## Workflow

1. Read `AGENTS.md`, existing profile, decisions, routing, and current focus.
2. Ask Scout to inspect in parallel where useful:
   - manifests, lockfiles, solution/workspace files, and runtime versions;
   - entry points and major directories;
   - build, lint, format, test, migration, and local-run commands;
   - CI/CD workflows and deployment descriptors;
   - architecture boundaries, generated-code markers, and ownership files;
   - security, data sensitivity, and environment constraints that are explicitly documented.
3. Verify commands using non-destructive execution when the environment supports them. Record unavailable commands as unknown, not inferred.
4. Reconcile findings against active decisions and current code. Flag contradictions.
5. Propose repository-specific routes based on actual paths and domains.
6. Have the human review choices that affect architecture, security, ownership, or policy.
7. Ask Librarian to update the profile, routing, current focus, and appropriate role histories.

## Evidence rules

- Cite exact paths, symbols, commands, or primary documentation.
- Record versions only when a manifest, tool output, or policy establishes them.
- Keep repository memory as an index; link to source rather than duplicating it.
- Never record secrets, personal data, production values, or machine-specific paths.
- Do not modify product code during onboarding.

Use the [handoff schema](../../../.agent-team/schemas/handoff.md) for the consolidated output.

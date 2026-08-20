---
description: Least-privilege guidance for GitHub Actions and Azure Pipelines configuration.
applyTo: "**/.github/workflows/*.yml,**/.github/workflows/*.yaml,**/azure-pipelines*.yml,**/azure-pipelines*.yaml"
---

# CI/CD

- Preserve the repository's deployment environments, approvals, branch protections, and separation of duties.
- Grant the minimum workflow, token, service connection, cloud, and repository permissions required.
- Pin third-party actions/tasks according to organizational policy and verify provenance before adding them.
- Never echo secrets or pass them through untrusted scripts, artifacts, caches, pull-request code, or command-line arguments when a safer channel exists.
- Separate build/test from deployment. Production deployment must retain explicit human and environment gates where policy requires them.
- Make artifacts traceable to source revision and verify integrity across stages.
- Avoid destructive cleanup, infrastructure mutation, or broad repository writes without explicit authorization and rollback planning.
- Validate syntax and, when available, run local/static workflow checks before claiming completion.

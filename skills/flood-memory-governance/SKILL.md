---
name: flood-memory-governance
description: Verify, promote, supersede, archive, or reject durable Project Flood memory after accepted work, explicit decisions, or revalidation.
---

# Flood Memory Governance

Flood Librarian owns canonical writes.

## Storage contract

- Canonical durable knowledge is one Markdown record with YAML frontmatter under `.agent-team/memory/`.
- The Markdown body contains rationale, evidence, exceptions, and consequences.
- Frontmatter contains identifiers, classification, status, scope, owner, confidence, dates, review trigger, tags, sources, and optional permission/tooling metadata.
- `.agent-team/memory/memory-index.yaml` is generated and contains no unique knowledge.
- Live coordination uses gitignored JSON under `.agent-team/runtime/`; activated worktree leases use the uncommitted Git common directory.
- Native session or Copilot Memory is supplemental and never overrides Git-tracked records.

## Promotion gate

1. Verify scope, owner, evidence, confidence, sensitivity, conflicts, and review condition.
2. Reject secrets, personal data, raw logs, transient failures, speculation, rejected-change claims, and facts cheap to rediscover.
3. Require path/symbol evidence for code facts, a successful run for commands, human approval or accepted change for architecture, and successful reuse for a new skill.
4. Preserve identifiers; archive superseded records with replacement links.
5. Regenerate and validate the YAML index.

Report promoted, merged, superseded, archived, pending, and rejected candidates explicitly.

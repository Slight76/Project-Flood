---
name: context-hygiene
description: Compact, archive, and revalidate Project Flood repository memory when active context becomes large, duplicated, stale, or inconsistent after milestones and refactors.
---

# Context Hygiene

Use this skill after a milestone, major refactor, dependency or policy change, repeated contradictions, or when active memory becomes difficult to scan. Run a dry review before edits.

## Review

1. Inventory active decisions, profile facts, role histories, current focus, inbox candidates, orchestration summaries, and skills.
2. Find duplication, unsupported claims, expired review conditions, contradictions, oversized narrative, and facts cheaply rediscoverable from code.
3. Revalidate affected entries against current code, tests, manifests, and policy.
4. Propose actions before writing:
   - keep unchanged;
   - condense while preserving evidence and meaning;
   - merge duplicates;
   - supersede and archive;
   - downgrade to pending;
   - discard sensitive or valueless material;
   - revalidate an earned skill through current use.
5. Have Librarian perform approved changes and record a dated summary.

## Invariants

- Preserve decision identifiers, rationale, and supersession links.
- Do not turn unverified summaries into facts.
- Do not compact away active constraints, unresolved risks, or human ownership.
- Keep current active files concise; retain necessary history in `.agent-team/archive/`.
- Never store secrets or personal data during archival.

Report which context was condensed, archived, revalidated, left pending, or rejected and why.

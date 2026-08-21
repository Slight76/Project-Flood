---
name: flood-context-hygiene
description: Revalidate, compact, archive, or discard stale Project Flood repository context when memory or orchestration state has become noisy or contradictory.
---

# Flood Context Hygiene

Use after a major refactor, milestone, dependency change, repeated contradiction, or health finding—not after every task.

1. Inventory active memory records, project profile, role histories, current focus, inbox candidates, orchestration summaries, runtime state, and scratch files.
2. Verify active claims against current code, tests, accepted changes, policy, or explicit human direction.
3. Classify each item as keep, revise with evidence, supersede, archive, delete if ephemeral, or escalate.
4. Preserve identifiers and links. Never silently rewrite an architectural decision.
5. Close expired shared task leases with `task-close`, then remove obsolete local runtime manifests and scratch output; do not promote them.
6. Have Flood Librarian apply approved durable changes and regenerate the memory index.

Return changed context, archived or rejected material, evidence, remaining contradictions, and the next review trigger.

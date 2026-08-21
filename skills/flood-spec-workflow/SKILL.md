---
name: flood-spec-workflow
description: Add proportional specification rigor before implementation when product behavior, interfaces, migrations, or cross-team contracts are materially unresolved.
---

# Flood Spec Workflow

Use for large or ambiguous features. Skip it for a small change whose acceptance criteria and interface are already settled.

Use an existing repository specification convention when one exists. Otherwise create a compact feature folder under the repository's documentation area with these artifacts:

1. **Constitution reference:** applicable repository principles and immutable constraints; do not duplicate `AGENTS.md`.
2. **Specification:** what and why, actors, user-visible behavior, scenarios, non-goals, and measurable acceptance criteria. Avoid implementation choices.
3. **Clarifications:** material ambiguities, chosen answers, owner, and date.
4. **Technical plan:** architecture, interfaces, data/migration, failure modes, rollout, observability, security, rollback, and alternatives.
5. **Tasks:** dependency-ordered slices with exact ownership, acceptance evidence, and reviewer.
6. **Consistency check:** map every requirement to plan and tasks; resolve gaps before implementation.

Human approval is required for unresolved product behavior, public contracts, destructive migration, or architectural choice. After approval, hand the task graph to `flood-run-feature`; do not create a competing execution system.

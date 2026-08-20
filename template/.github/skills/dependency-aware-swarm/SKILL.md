---
name: dependency-aware-swarm
description: Decide whether a complex development task should use a temporary swarm, then produce safe execution waves, dependencies, exclusive ownership, gates, and fan-in criteria.
---

# Dependency-Aware Swarm

Use this skill when a request contains multiple substantial concerns, broad repository analysis, several independent review perspectives, or potentially disjoint implementation areas. Do not use it merely because multiple agents exist.

## Choose squad or swarm

Return **SQUAD** when work is mostly sequential, one agent owns nearly all files, coordination cost exceeds parallel benefit, or the task is too small.

Return **SWARM** only when two or more tasks can make useful progress without consuming another task's unpublished result.

## Build the plan

1. Define the final acceptance criteria and verification gate.
2. Decompose work into bounded tasks with one accountable role each.
3. Record dependencies and group independent tasks into waves.
4. Assign exact read scope and exclusive write scope.
5. Keep research, architecture, verification, and security tasks read-only.
6. For parallel Builders, require disjoint paths or isolated Git worktrees based on committed state.
7. Limit each wave to three workers.
8. Define the synchronization artifact each task returns using the [handoff schema](../../../.agent-team/schemas/handoff.md).
9. Define fan-in: who reconciles conflicts, what evidence wins, and which verifier gates completion.
10. Add stop conditions for missing expertise, authorization, environment, conflicting evidence, or ownership overlap.

## Output

Include:

- `SQUAD` or `SWARM` decision and rationale;
- task table with role, dependencies, mode, paths, acceptance criteria, and reviewer;
- ordered waves and critical path;
- file-ownership matrix;
- fan-in and rollback plan;
- authorization and escalation points.

Do not start workers until Squad Lead accepts the ownership and dependency plan.

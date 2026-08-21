---
name: flood-dependency-aware-swarm
description: Decide whether multi-part work merits a bounded squad or swarm, then define safe waves, dependencies, ownership, gates, and convergence.
---

# Flood Dependency-Aware Swarm

Use only when at least two substantial concerns might progress independently or independent review perspectives materially reduce risk.

Return `SQUAD` when work is mostly sequential, ownership overlaps, requirements or interfaces are unsettled, or coordination cost erases the benefit.

For `SWARM`:

1. Define final acceptance criteria and verification/security gates.
2. Decompose work into tasks with one accountable role each.
3. Record dependencies and group only independent tasks into waves of at most three.
4. Make research and review read-only.
5. Give editors disjoint paths. If parallel implementation is necessary, use separate worktree sessions and the `flood-worktree-swarm` skill.
6. Define synchronization artifacts, fan-in owner and order, evidence precedence, rollback, authorization, and stop conditions.

Do not launch workers until Flood Squad Lead accepts the plan.

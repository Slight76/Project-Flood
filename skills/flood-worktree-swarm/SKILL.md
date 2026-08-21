---
name: flood-worktree-swarm
description: Plan and control parallel implementation in isolated Git worktree sessions with a validated ownership manifest and explicit fan-in.
---

# Flood Worktree Swarm

Use only after requirements, interfaces, base commit, and independent workstreams are settled. Ordinary subagents share a workspace and are not write isolation.

1. Ask Flood Swarm Analyst for dependencies, waves, exact paths, gates, and integration order.
2. Create `.agent-team/runtime/task-manifest.json` using the repository schema. Include task ID, expiry, base commit, coordinator and worker session keys from SessionStart context, wave, role, branch, worktree, dependencies, write paths, acceptance criteria, and status. Use exact files or directory prefixes ending in `/**`; arbitrary globs are rejected.
3. Run `python .project-flood/flood.py task-validate --root .`, then `task-activate --root .`. Activation atomically publishes the lease under Git's shared common directory so every worktree hook sees the same ownership.
4. Use separate Agent Host sessions with **New Worktree** when session orchestration exists. Otherwise give the human exact manual session assignments; do not silently fall back to shared-workspace editors.
5. Keep at most three active workers, and require structured, committed handoffs from each worktree.
6. Independently verify each result before Flood Integrator performs authorized fan-in in dependency order.
7. Verify the integrated result again. Run `task-close --root . --status complete` before worktrees are archived or removed; use `cancelled` when abandoning the plan.

Cross-session messages require user confirmation. Never delete a branch or worktree containing unintegrated work.

---
name: flood-run-feature
description: Coordinate a bounded feature or fix from evidence and acceptance criteria through implementation, independent verification, and memory reflection.
---

# Flood Run Feature

Use for an implementation request that is sufficiently specified to change code.

1. Restate outcome, acceptance criteria, constraints, authorization, and definition of done.
2. Ground the task in current code and relevant canonical memory.
3. Select Direct, Squad, or Swarm based on real dependencies. Use `flood-spec-workflow` first when material requirements remain unresolved.
4. Assign exclusive paths and create a runtime task manifest for a build swarm.
5. Route implementation to Flood Builder; reserve Flood Integrator for verified worktree fan-in.
6. Require Flood Verifier for behavior changes and Flood Security Reviewer for security-sensitive changes.
7. Permit one focused correction after rejection, then transfer ownership; escalate the third failure.
8. Ask Flood Librarian to classify only durable, evidence-backed lessons after validation succeeds.

Do not infer permission to commit, push, open or merge a pull request, deploy, or change external resources.

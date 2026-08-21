---
name: flood-squad-health
description: Audit Project Flood discovery, routing, memory freshness, hooks, manifests, ownership, compatibility, and current blockers without changing files.
---

# Flood Squad Health

Run read-only unless the human separately approves maintenance.

1. Run `python .project-flood/flood.py doctor --root .` and retain its exact results.
2. Check custom agent, skill, instruction, prompt, hook, and plugin discovery on the active harness.
3. Verify namespaced roles, least-privilege tools, non-nested agents, and lead allowlists.
4. Check memory evidence/review conditions, index freshness, legacy rollups, inbox age, local runtime state, Git-common-dir lease, scratch, and orchestration compaction.
5. Compare routes, profile, setup workflow, policy allowlists, and protected paths with current repository structure.
6. Review hook audit output and Agent Debug logs for denied tools, silent tool omissions, routing failures, errors, and excessive fan-out.

Return prioritized findings, evidence, severity, and a bounded maintenance plan. Do not claim harness loading was tested when only file schemas were validated.

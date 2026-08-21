# Project Flood State

This directory separates durable, reviewable repository knowledge from short-lived coordination.

| Path | Authority | Retention |
| --- | --- | --- |
| `charter.md` | Human | Durable team purpose and boundaries |
| `project-profile.md` | Flood Librarian after evidence review | Current verified repository map |
| `routing.md` | Human/Flood Librarian | Revalidate after structural change |
| `harnesses.md` | Project Flood | Capability matrix; verify against current tooling |
| `memory/**/*.md` | Flood Librarian | Canonical durable memory with YAML frontmatter |
| `memory/memory-index.yaml` | Generator | Derived index; never canonical |
| `decisions.md` | Migration compatibility | v0.1 entries only; do not add new decisions |
| `decisions/inbox/` | Workers/Flood Librarian | Temporary memory candidates |
| `roles/*/history.md` | Flood Librarian | Compact specialist lessons |
| `now.md` | Flood Librarian | Current milestone and blockers |
| `orchestration/` | Flood Librarian | Significant append-only summaries |
| `runtime/` | Hook/lead/session owners | Ephemeral authoring/audit JSON; gitignored |
| `scratch/` | Any agent | Ephemeral; gitignored |

Current code and enforced policy remain authoritative. A record should point to evidence instead of duplicating code. Run `python .project-flood/flood.py memory-index --root .` after an approved canonical-memory change.

`task-activate` publishes an active task lease to `<git-common-dir>/project-flood/task-manifest.json`, which is shared by all worktrees and removed by `task-close` after a local archival copy is written.

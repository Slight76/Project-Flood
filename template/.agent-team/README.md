# Agent Team State

This directory stores Project Flood's reviewable repository memory and coordination state.

| Path | Owner | Retention |
| --- | --- | --- |
| `charter.md` | Human/Librarian | Durable |
| `project-profile.md` | Librarian | Current verified repository map |
| `routing.md` | Human/Librarian | Durable; revalidate after structural changes |
| `decisions.md` | Librarian | Active decisions only |
| `decisions/inbox/` | Workers/Librarian | Temporary candidates |
| `roles/*/history.md` | Librarian | Compact role-specific lessons |
| `now.md` | Librarian | Current milestone and blockers |
| `orchestration/` | Librarian | Significant squad/swarm summaries |
| `archive/` | Librarian | Superseded or compacted material |
| `scratch/` | Any agent | Ephemeral and gitignored |

The codebase remains the primary source of truth. Memory should point to evidence instead of copying large portions of code or documentation.

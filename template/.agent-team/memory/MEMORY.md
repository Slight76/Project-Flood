# Canonical Repository Memory

Each durable memory is an individual Markdown file in `architecture/`, `decisions/`, `conventions/`, `pitfalls/`, or `archive/`.

The Markdown body is authoritative for the claim, reasoning, evidence, exceptions, and consequences. YAML frontmatter carries identity, lifecycle, ownership, confidence, dates, scope, tags, sources, and optional permission/tool metadata. `memory-index.yaml` is generated from those headers and must never contain unique knowledge.

Promotion lifecycle:

`candidate → evidence/conflict review → Librarian promotion → index generation → periodic revalidation → archive or supersede`

Runtime task authoring remains under `.agent-team/runtime/`; activated worktree leases live transiently in the Git common directory and are not memory.

Run:

```bash
python .project-flood/flood.py memory-index --root .
python .project-flood/flood.py validate --root .
```

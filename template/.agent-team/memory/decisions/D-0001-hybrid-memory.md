---
id: D-0001
type: decision
status: active
scope:
  - .agent-team/memory/**
  - .agent-team/runtime/**
  - .git/project-flood/**
owner: human
confidence: high
created: 2026-08-21
updated: 2026-08-21
review_when: Project Flood changes its canonical memory or index format
tags:
  - memory
  - markdown
  - yaml
  - governance
sources:
  - explicit user direction from the Project Flood YAML hybrid design discussion
permissions:
  write: Flood Librarian after evidence review
  approve: human for policy or architecture changes
tooling:
  index_command: python .project-flood/flood.py memory-index --root .
  validation_command: python .project-flood/flood.py validate --root .
---

# Markdown is canonical; YAML is metadata

Project Flood stores durable repository knowledge as Markdown records with YAML frontmatter. The body retains decisions, explanations, evidence, exceptions, lessons, and guidance in a form humans and agents can review naturally.

YAML frontmatter stores only structured metadata needed for identity, lifecycle, ownership, confidence, scope, dates, tags, sources, and validation. The generated `memory-index.yaml` is derived from canonical records and may not contain unique knowledge.

Temporary coordination and hook audit data are separate JSON under `.agent-team/runtime/`. For worktree swarms, the validated active ownership lease is atomically copied to the repository's Git common directory so every worktree sees one transient source; closing the task archives a local copy and removes the shared lease. None of this runtime state is promoted merely because it existed during a task.

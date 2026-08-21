---
description: Governance rules for Project Flood canonical memory, generated indexes, runtime state, skills, and orchestration summaries.
applyTo: ".agent-team/**,.github/skills/**/SKILL.md"
---

# Project Flood State

- Only Flood Librarian routinely edits canonical memory and earned skills.
- Durable records are Markdown with complete YAML frontmatter. Keep reasoning and evidence in the body.
- `memory-index.yaml` is generated and must never contain unique knowledge.
- Runtime authoring and hook audit records are ephemeral JSON; activated worktree leases live uncommitted in the Git common directory.
- Keep entries concise, scoped, dated, evidence-backed, and useful for a future decision.
- Preserve identifiers and archive superseded material rather than silently changing history.
- Use source links, paths, symbols, test output, accepted changes, policy, or explicit user directives as evidence.
- Do not store secrets, personal data, raw commands/tool input, transient failures, speculation, or large copies of code.
- Do not promote findings from rejected work as active truth.
- Skills must describe repeatable workflows with discriminating triggers; do not turn one-off project trivia into a skill.
- Native/session memory is supplemental, not canonical. When current code contradicts memory, mark the memory for revalidation and treat code as authoritative.

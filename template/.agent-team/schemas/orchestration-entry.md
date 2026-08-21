# Orchestration Summary

Create a canonical Markdown entry only for significant squad or swarm work.

```markdown
---
id: ORCH-YYYYMMDD-NNN
type: orchestration
status: complete | partial | blocked | rejected
mode: squad | research-swarm | build-swarm | review-swarm
requested_by: human
started: ISO-8601
completed: ISO-8601
---

# Task summary

## Routing and ownership

| Task | Agent/session | Why | Dependencies | Read scope | Exclusive write scope | Wave |
| --- | --- | --- | --- | --- | --- | --- |

## Verification gates

| Gate | Reviewer | Verdict | Evidence |
| --- | --- | --- | --- |

## Memory and final risk
```

Completed entries are append-only. Correct mistakes with a dated amendment.

# Memory Candidate

Store temporary candidates under `.agent-team/decisions/inbox/` only when Squad Lead or Librarian requests a file. Otherwise return the same fields in the specialist handoff.

```markdown
### MC-YYYYMMDD-NNN — Short title

- **Proposed class:** Decision | Project profile | Role history | Skill | Current focus | Archive | Discard
- **Proposed destination:** Exact file or role
- **Scope:** Affected paths, components, or workflows
- **Owner:** Human or accountable role
- **Observed:** YYYY-MM-DD
- **Confidence:** Low | Medium | High
- **Evidence:** File/symbol, test output, merged PR/commit, policy, or explicit user directive
- **Claim:** Concise durable information
- **Why it matters later:** Future decision this changes
- **Review when:** Date or triggering condition
- **Conflicts checked:** Entries inspected and result
- **Sensitive-data check:** Confirm no secret or personal data is included
```

Low-confidence candidates remain pending. Code-derived facts need source evidence. A repeatable skill requires at least one successful use and should not encode one-off project trivia.

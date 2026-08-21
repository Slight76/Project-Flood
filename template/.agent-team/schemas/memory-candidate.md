# Memory Candidate

Create a temporary file under `.agent-team/decisions/inbox/` only when Flood Squad Lead or Flood Librarian requests it. Otherwise return these fields in the handoff.

```markdown
---
id: MC-YYYYMMDD-NNN
proposed_type: architecture | decision | convention | pitfall | profile | role-history | skill | current-focus | archive | discard
proposed_destination: exact path or role
scope: [affected/path/**]
owner: accountable human or role
observed: YYYY-MM-DD
confidence: low | medium | high
sources: [path/symbol, test, accepted change, policy, or explicit directive]
review_when: date or triggering condition
permissions:
  write: accountable role or path
  approve: human, accepted change, or verification gate
tooling:
  validation_command: command, if the claim depends on one
---

# Short claim

## Claim and future consequence

## Evidence and conflicts checked

## Sensitive-data check
```

Low-confidence candidates remain pending. Rejected implementation claims, secrets, personal data, transient output, and cheaply rediscovered facts are discarded.

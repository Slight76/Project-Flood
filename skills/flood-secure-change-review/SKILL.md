---
name: flood-secure-change-review
description: Review a security-sensitive change involving trust boundaries, identity, input, data, dependencies, CI/CD, hooks, MCP, or external tools.
---

# Flood Secure Change Review

1. Identify assets, actors, entry points, trust boundaries, and realistic abuse cases.
2. Trace authentication and authorization separately, including object and tenant boundaries.
3. Review validation, encoding, injection, deserialization, file/path handling, and error disclosure.
4. Inspect secrets, logs, telemetry, sensitive data, retention, deletion, and encryption expectations.
5. Check runtime, repository, workflow, hook, MCP, token, and cloud permissions for least privilege.
6. Verify dependency provenance, pinned integrity, maintenance, advisories, failure behavior, observability, and rollback using current primary sources.
7. For agent configuration, include prompt injection, memory poisoning, policy self-modification, ownership bypass, and tool exfiltration.

Return `APPROVE`, `REJECT`, or `BLOCKED`. Rank concrete findings, with evidence, impact, preconditions, remediation, residual risk, and review limitations.

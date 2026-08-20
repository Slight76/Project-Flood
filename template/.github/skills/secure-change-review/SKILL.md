---
name: secure-change-review
description: Review security-sensitive code, configuration, dependencies, pipelines, authentication, authorization, data handling, or external integrations using concrete threat and evidence analysis.
---

# Secure Change Review

Use this skill when a change touches trust boundaries, identity, permissions, secrets, user-controlled input, sensitive data, dependencies, CI/CD, cloud resources, network access, or externally exposed behavior.

## Review

1. Identify assets, actors, entry points, trust boundaries, and abuse cases affected by the change.
2. Trace authentication and authorization separately, including object- and tenant-level checks.
3. Review input validation, output encoding, injection surfaces, file/path handling, deserialization, and error disclosure.
4. Check secrets, logs, telemetry, personal data, encryption expectations, retention, and deletion behavior.
5. Review runtime, repository, workflow, token, and cloud permissions for least privilege.
6. Inspect new or changed dependencies for provenance, version policy, integrity controls, maintenance, and known advisories using current primary sources.
7. Check secure failure, abuse resistance, observability, rollback, and incident response implications.

## Findings

Rank findings as Critical, High, Medium, Low, or Informational. For each, include evidence, realistic impact, exploit/precondition, required remediation, and residual risk.

Return `APPROVE`, `REJECT`, or `BLOCKED`. Never claim full security or compliance from this focused review, and never reproduce full sensitive values.

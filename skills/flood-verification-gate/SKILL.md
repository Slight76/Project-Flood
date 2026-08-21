---
name: flood-verification-gate
description: Independently verify a behavior-changing implementation against acceptance criteria, regression risk, and observable evidence before completion.
---

# Flood Verification Gate

Read the request, accepted specification or criteria, plan, diff, Builder/Integrator handoff, tests, and relevant decisions. Identify each claim that needs observable proof.

1. Inspect scope, unintended changes, error handling, compatibility, and missing tests.
2. Run focused tests for changed behavior.
3. Run relevant format, lint, type, compile, static, integration, and security checks.
4. Exercise important failure paths and boundary inputs.
5. Run broader regression checks when risk warrants them.
6. Separate implementation failure from unavailable environment, credentials, data, or infrastructure.

Return `APPROVE`, `REJECT`, or `BLOCKED` with a criterion-to-evidence map. Never claim an unrun check passed or weaken criteria.

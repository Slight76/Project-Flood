---
description: Test design and verification guidance for test source files.
applyTo: "**/*test*,**/*spec*,**/tests/**,**/Tests/**"
---

# Tests

- Test externally meaningful behavior and failure paths rather than implementation trivia.
- Follow existing framework, fixture, naming, assertion, and test-data conventions.
- Keep tests deterministic, isolated, readable, and safe to run repeatedly.
- Prefer the smallest appropriate test level; add integration coverage where component boundaries are the risk.
- Make time, randomness, locale, concurrency, network, and external dependencies controllable.
- Do not weaken, delete, skip, or broadly mock a failing test solely to make a build pass.
- When fixing a defect, reproduce it with a failing test when practical, then verify the fix.
- Report quarantined, flaky, skipped, environment-dependent, and unrun tests explicitly.

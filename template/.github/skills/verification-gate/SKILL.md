---
name: verification-gate
description: Independently verify a behavior-changing implementation against acceptance criteria, repository checks, regression risk, and observable evidence before completion is claimed.
---

# Verification Gate

Use this skill after implementation or when completion claims are disputed. Verifier should not be the implementation author.

## Prepare

Read the user request, acceptance criteria, plan, changed files, Builder handoff, existing tests, and relevant active decisions. Identify claims that need observable proof.

## Verify in layers

1. Inspect the diff for scope, unintended changes, error handling, compatibility, and missing tests.
2. Run focused tests for changed behavior.
3. Run relevant format, lint, type, compile, and static checks.
4. Exercise important failure paths and boundary inputs.
5. Run broader regression checks when change radius or repository policy warrants them.
6. Separate implementation failure from missing environment, credentials, test data, or infrastructure.

Never claim an unrun check passed. Do not weaken tests or acceptance criteria.

## Verdict

- **APPROVE:** every acceptance criterion has sufficient evidence and no blocking regression is found.
- **REJECT:** the implementation is testable but fails a criterion or introduces a blocking defect.
- **BLOCKED:** verification cannot reach a trustworthy conclusion because required environment, data, dependency, or permission is unavailable.

For rejection, provide concrete corrections and reviewer evidence. Under Project Flood's retry policy, the original Builder receives one focused correction; a second rejection transfers ownership to a fresh Builder; a third escalates to the human.

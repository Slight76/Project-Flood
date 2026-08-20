# Work Routing

Routes are evaluated in this order: explicit named assignment, most-specific repository path/domain, applicable skill, then Squad Lead fallback. Update the repository-specific table during onboarding.

## Role routing

| Work type | Route to | Examples |
| --- | --- | --- |
| Repository discovery | Scout | Locate entry points, trace flows, find existing patterns |
| Architecture | Architect | Boundaries, APIs, migrations, trade-offs |
| Implementation | Builder | Product code, configuration, targeted tests |
| Verification | Verifier | Test execution, regression analysis, acceptance review |
| Security/privacy | Security Reviewer | Auth, credentials, permissions, input handling, dependencies |
| Memory/knowledge | Librarian | Decisions, profile, role history, context maintenance |
| Parallel decomposition | Swarm Analyst | Dependencies, ownership, concurrency, acceptance criteria |
| Final synthesis or ambiguity | Squad Lead | User-facing answer, escalation, cross-domain decision |

## Repository-specific routes

| Path or domain | Primary | Required reviewer | Notes |
| --- | --- | --- | --- |
| Not yet mapped | Squad Lead | As risk requires | Populate during onboarding |

## Routing rules

1. Name-directed work routes to the named qualified role.
2. The most specific verified path route wins.
3. Security-sensitive changes always include Security Reviewer.
4. Behavior-changing implementation always includes Verifier.
5. Cross-cutting work starts with Architect or Swarm Analyst before Builder.
6. If expertise is absent, report a skill gap; do not silently assign an unqualified agent.
7. Log significant routing decisions and their rationale in `.agent-team/orchestration/` through Librarian.

# Work Routing

Evaluate routes in this order: explicit qualified assignment, most-specific verified path/domain, applicable `flood-*` skill, then Flood Squad Lead fallback.

## Role routing

| Work | Primary | Required gate |
| --- | --- | --- |
| Repository/primary-source discovery | Flood Scout | Evidence review |
| Architecture, interfaces, migration | Flood Architect | Human decision when material |
| Implementation | Flood Builder | Flood Verifier |
| Worktree fan-in | Flood Integrator | Flood Verifier after integration |
| Behavioral verification | Flood Verifier | Independent verdict |
| Security/privacy/tools/supply chain | Flood Security Reviewer | Security verdict |
| Memory and earned skills | Flood Librarian | Evidence/promotion gate |
| Parallel decomposition | Flood Swarm Analyst | Lead accepts graph/ownership |
| Ambiguity or synthesis | Flood Squad Lead | Human escalation as needed |

## Repository-specific routes

| Path/domain | Primary | Required reviewer | Notes |
| --- | --- | --- | --- |
| Not yet mapped | Flood Squad Lead | As risk requires | Populate during onboarding |

## Rules

1. Most-specific verified route wins after an explicit named assignment.
2. Behavior changes always include Flood Verifier.
3. Security-sensitive work always includes Flood Security Reviewer.
4. Cross-cutting work begins with Flood Architect or Flood Swarm Analyst.
5. Parallel implementation uses separate worktree sessions and a validated runtime task manifest.
6. Flood Integrator is not a general second Builder.
7. Missing expertise or harness capability is reported, not silently approximated.
8. Flood Librarian records significant routing rationale only after the result is accepted.

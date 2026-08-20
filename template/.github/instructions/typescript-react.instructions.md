---
description: TypeScript and React implementation guidance for frontend source and configuration.
applyTo: "**/*.ts,**/*.tsx,**/tsconfig*.json"
---

# TypeScript and React

- Preserve strict typing. Avoid `any`; prefer narrow types, discriminated unions, and runtime validation at external boundaries.
- Follow the repository's component, state-management, data-fetching, styling, routing, and testing conventions.
- Prefer small functional components and focused hooks. Keep side effects explicit and dependency arrays correct.
- Do not duplicate server state into local state without a demonstrated need.
- Preserve accessibility: semantic elements, labels, keyboard behavior, focus handling, meaningful status/error text, and appropriate ARIA only when native semantics are insufficient.
- Handle loading, empty, error, unauthorized, and partial-data states when the workflow can reach them.
- Avoid unsafe HTML injection. Treat URL, storage, API, and message content as untrusted.
- Add behavior-focused tests using existing tools; avoid snapshots as the sole evidence for important behavior.
- Run the package manager, lint, type-check, test, and build commands verified in the project profile.

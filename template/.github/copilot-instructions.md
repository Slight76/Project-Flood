# Repository-wide Copilot Instructions

- Follow `AGENTS.md`; do not duplicate or weaken its contract.
- Before substantial work, read the verified profile, routing, current focus, harness matrix, canonical memory index and relevant records, plus any active runtime task manifest.
- Treat executable code, tests, manifests, migrations, and enforced policy as stronger evidence than memory or prose.
- Use `flood-*` skills for portable workflows. Files under `.github/prompts/` are convenience wrappers for VS Code Local and are not available to Agent Host sessions.
- Prefer small, reversible changes that match existing architecture. Search before adding libraries, abstractions, schemas, or conventions.
- State assumptions and ask when a missing choice materially changes behavior, public interfaces, security, migration, or cost.
- Run relevant repository-provided format, build, lint, test, and security commands; report exact commands and results.
- Add behavior-focused tests. Do not weaken, skip, or delete checks merely to make work pass.
- Never add credentials, personal data, production endpoints, or secret-like placeholders.
- Only Flood Librarian routinely writes canonical memory. Regenerate its YAML index after an approved memory change.
- Do not claim a commit, push, pull request, merge, deployment, worktree cleanup, message, or other external action unless authorized and confirmed by the tool result.

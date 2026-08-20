# Repository-wide Copilot Instructions

- Follow the operating contract in `AGENTS.md`. Do not duplicate or contradict it.
- Before substantial work, read `.agent-team/project-profile.md`, `.agent-team/decisions.md`, `.agent-team/routing.md`, and `.agent-team/now.md` as relevant.
- Treat source code, tests, manifests, migrations, and enforced policy as the primary evidence for repository behavior.
- Prefer small, reversible changes that match existing architecture and naming.
- Search for existing patterns before introducing new libraries, abstractions, schemas, or conventions.
- State assumptions and ask when a missing choice would materially change the implementation.
- Run repository-provided format, build, lint, test, and security commands relevant to changed areas. Report the exact commands and results.
- Add or update tests for behavior changes. Do not weaken assertions merely to make a test pass.
- Never add real credentials, personal data, production endpoints, or secret-like placeholders.
- Do not modify generated files unless the repository documents the generator and the generated output is expected in source control.
- Do not modify canonical `.agent-team/` state unless acting as Librarian under the memory-governance workflow.
- Do not claim a commit, push, pull request, deployment, or external action occurred unless the user authorized it and the tool result confirms it.

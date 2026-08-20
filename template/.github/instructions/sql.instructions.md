---
description: SQL, database migration, query, and data-access guidance.
applyTo: "**/*.sql,**/Migrations/**,**/migrations/**"
---

# SQL and Data Changes

- Use parameterized data access. Never concatenate untrusted values into SQL.
- Match existing schema, naming, migration, transaction, and rollback conventions.
- Make data type, nullability, default, collation, timezone, and precision choices explicit.
- Evaluate indexes and query plans for materially changed access patterns; avoid speculative indexes.
- Keep migrations deployable across supported versions and consider mixed-version application/database rollout.
- Treat destructive, irreversible, or high-volume data changes as high risk. Require a rollback or recovery plan and human approval.
- Protect tenant/user boundaries and avoid returning more columns or rows than required.
- Do not place production data, connection strings, or credentials in migrations, fixtures, logs, or examples.
- Add database or integration tests when the repository supports them, and report environment-dependent tests honestly.

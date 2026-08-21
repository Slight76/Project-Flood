# Harness Support

The installed repository matrix is canonical at [`template/.agent-team/harnesses.md`](../template/.agent-team/harnesses.md).

Before dispatch, Flood Squad Lead capability-detects custom agents, skills, hooks, session/worktree tools, memory, approvals, and external tools. A missing capability becomes an explicit limitation or a different execution plan.

Important portability rules:

- `flood-*` skills carry critical workflows across supported Copilot surfaces.
- `.prompt.md` files are VS Code Local convenience wrappers only.
- Ordinary subagents isolate context, not filesystem writes.
- Worktree-backed sessions are required for parallel editors.
- `.github/workflows/copilot-setup-steps.yml` prepares GitHub cloud-agent environments only after it is present on the default branch.
- Copilot CLI can install the repository directly; cloud-agent adapter installs use a human-reviewed merge of the supplied Copilot settings example.
- Hooks are preview, deterministic guardrails. Repository permissions and required checks remain authoritative.

Use the VS Code Customizations diagnostics and Agent Debug view to verify what the active harness actually loaded.

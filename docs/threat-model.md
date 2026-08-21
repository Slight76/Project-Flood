# Threat Model

Project Flood is defense-in-depth for agent workflows. It does not replace operating-system isolation, repository permissions, branch protection, required reviews, CI, or secret management.

## Assets and trust boundaries

Protected assets include source code, credentials, user data, repository policy, canonical memory, CI configuration, external systems, and unmerged worktree results. Trust boundaries exist between the human, model, repository content, fetched content, tools/MCP servers, hook process, GitHub, and deployment systems.

## Main threats and controls

| Threat | v0.2 control | Residual risk |
| --- | --- | --- |
| Prompt injection in code, issues, dependencies, or webpages | Evidence-order contract; fetched/repository text is untrusted; external tool allowlist | A model can still misclassify malicious text |
| Memory poisoning or stale facts | Librarian-only promotion, evidence/conflict checks, current-code precedence, generated-index validation | Human-approved records can still be wrong |
| Overlapping parallel edits | Validated manifest, one Git-common-dir lease shared by worktrees, exclusive paths, hook checks | Tool inputs that hide paths require human judgment |
| Self-modifying controls | Protected-path hook prompts, CODEOWNERS guidance, pinned CI actions | Workspace hooks are preview and can be disabled by policy |
| Excessive agency or unintended external writes | Separate authorization language; external write and unknown tool prefixes ask | A broadly trusted external tool remains powerful |
| Destructive terminal use | Deny patterns for high-risk commands | Pattern matching cannot prove every command safe |
| MCP/plugin exfiltration | Empty external-tool allowlist by default; plugin review warning; no bundled MCP servers | Installed plugins and approved MCP servers execute with their granted access |
| Secret leakage through logs | Hook audit stores metadata and hashed session IDs only; secret scan | Terminal and provider logs are outside this script's control |
| Supply-chain compromise | Exact action commit pins and exact PyYAML version | Hosted runners and upstream artifacts remain dependencies |
| Worktree loss or unsafe fan-in | No deletion before verified integration; Integrator role; post-fan-in verification | Git history and human recovery practices still matter |

## Hook failure behavior

- Known dangerous commands are denied.
- Writes outside the repository, protected-path edits, unverifiable edit scopes, external writes, and unlisted external tool prefixes ask.
- Active task ownership violations are denied.
- Invalid or expired runtime manifests do not grant ownership.
- Policy parse failure falls back to conservative built-in defaults.

Review hook output and Agent Debug logs during adoption. Do not put secrets, prompts, command bodies, file contents, or raw tool inputs in hook audit records.

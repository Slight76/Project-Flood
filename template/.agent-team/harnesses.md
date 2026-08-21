# Harness Support Matrix

This is Project Flood's supported behavior as of v0.2. Recheck current product diagnostics because preview capabilities change.

| Capability | VS Code Local | Copilot Agent Host | Copilot CLI | GitHub cloud agent | Copilot code review |
| --- | --- | --- | --- | --- | --- |
| Workspace custom agents | Yes | Yes | Capability-detect | Yes | Not relied upon |
| `flood-*` Agent Skills | Yes | Yes | Yes | Yes | Not relied upon |
| Prompt wrappers | Yes | No | No | No | No |
| Workspace/plugin hooks | Yes, preview | Yes, preview | Capability-detect | Capability-detect | Not relied upon |
| Stateless subagents | Yes | Yes | Capability-detect | Service-controlled | No |
| Session/worktree orchestration | Manual | Yes when tools are exposed | Manual | Branch/PR isolation instead | No |
| Native session memory | Local | Local | Surface-specific | No | No |
| Copilot repository memory | Optional | Optional | Optional | Optional | Optional |
| `copilot-setup-steps.yml` | CI only | CI only | CI only | Yes | Reused by default |

Rules:

- Skills are the portable workflow authority; prompts only shorten local invocation.
- Unavailable or unrecognized tools may be silently ignored, so verify discovery with Customizations diagnostics and Agent Debug logs.
- A normal subagent is context isolation, not worktree isolation.
- Cloud agents cannot use local editor tools or context and are limited by their remote environment.
- Hooks are preview defense-in-depth. Branch protection, repository permissions, review, and CI remain mandatory controls.

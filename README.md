# Project Flood v0.2

Project Flood is a governed GitHub Copilot squad that can fan out into temporary research, review, or worktree-isolated build swarms. v0.2 turns the v0.1 operating contract into a portable Agent Plugins 1.0 package plus a repository-owned adapter.

The design stays intentionally bounded:

- one human-facing **Flood Squad Lead**;
- eight hidden specialists, including a dedicated **Flood Integrator**;
- maximum three active workers per wave;
- read-only research, architecture, verification, security, and swarm planning;
- separate worktree sessions and exclusive paths for parallel editors;
- deterministic hooks for dangerous commands, protected paths, ownership, and external writes;
- independent verification before completion and after fan-in;
- one Librarian for evidence-gated durable memory.

Project Flood does not train or modify a model. Its learning is reviewable repository context.

## Install

Project Flood requires Python 3.10+ and the pinned validator dependency:

```bash
python -m pip install --requirement requirements.txt
```

### Full repository install

Use this first. It copies the plugin capabilities and repository adapter into the target:

```bash
./scripts/install.sh --mode full /path/to/target-repository
```

```powershell
pwsh ./scripts/install.ps1 -Mode full -TargetPath C:\src\target-repository
```

If the Project Flood plugin is already installed globally, disable it for a full-mode workspace; plugin and workspace hooks otherwise both run.

### Plugin plus lightweight adapter

In VS Code, enable `chat.plugins.enabled`, run **Chat: Install Plugin From Source**, and enter `https://github.com/Slight76/Project-Flood`. Then install only the target-specific adapter:

```bash
./scripts/install.sh --mode adapter /path/to/target-repository
```

Adapter mode omits workspace copies of agents, skills, hooks, and hook code. The installed plugin supplies them; the repository keeps its contract, profile, routing, policy, setup workflow, canonical memory, runtime schema, and prompt wrappers.

Copilot CLI can install the same package directly with `copilot plugin install Slight76/Project-Flood`. For a cloud-agent adapter, review and merge `.project-flood/copilot-settings.adapter.example.json` into the target's existing `.github/copilot/settings.json`; do not overwrite existing settings.

Private repositories are supported when the current Git credentials can clone them. Review the plugin before trusting it because plugins may execute hooks.

## Start

1. Open the configured target in a current VS Code release with Copilot enabled.
2. Run **Chat: Open Customizations** and verify `Flood Squad Lead`, the `flood-*` skills, and hooks are discovered.
3. Select **Flood Squad Lead**.
4. Ask it to use `flood-repository-onboarding` before implementation.
5. Review the proposed project profile, routing, harness capabilities, CODEOWNERS additions, and cloud-agent setup steps.
6. Start with a bounded read-only task, then a small verified implementation.

Prompt files such as `flood-onboard` are local VS Code shortcuts. Skills are the portable workflow authority.

## What v0.2 adds

| Area | v0.2 behavior |
| --- | --- |
| Packaging | Agent Plugins 1.0 plus full or adapter repository installation |
| Portability | Namespaced agents, portable tool aliases, skills replacing critical prompts, harness matrix |
| Enforcement | Workspace/plugin hooks with deny/ask/allow decisions and metadata-only audit |
| Build swarms | Validated task manifest, worktree sessions, wave/dependency/path rules, Integrator fan-in |
| Memory | Canonical Markdown body + YAML frontmatter; generated YAML index; ephemeral runtime JSON |
| Setup | Cloud-agent setup workflow and CODEOWNERS guidance |
| Lifecycle | Baseline-hash manifest, `diff`, `doctor`, `upgrade`, v0.1 `migrate`, recoverable `uninstall` |
| Quality | Real YAML parsing, Windows/Linux CI, pinned actions, threat model, adversarial eval corpus |

See [architecture](docs/architecture.md), [harness support](docs/harness-support.md), [threat model](docs/threat-model.md), [upgrades](docs/upgrades.md), and [behavioral evaluations](docs/evaluations.md).

Release details are recorded in the [changelog](CHANGELOG.md).

## Hybrid memory

Durable knowledge lives in individual Markdown records under `.agent-team/memory/`:

- the body holds decisions, reasoning, evidence, exceptions, examples, and consequences;
- YAML frontmatter holds identity, type, lifecycle, owner, confidence, dates, scope, tags, sources, and optional permission/tool metadata;
- `memory-index.yaml` is generated and contains no unique knowledge;
- task authoring and hook audit data are gitignored JSON under `.agent-team/runtime/`, while activated worktree leases are shared transiently through Git's common directory;
- only Flood Librarian promotes or supersedes canonical memory after evidence review.

Current code and enforced policy outrank memory. Rejected work never becomes active knowledge.

## Validate and maintain

```bash
python scripts/sync_distribution.py --check
python scripts/flood.py validate --root . --distribution
python -m unittest discover -s tests -v
```

From an installed repository:

```bash
python .project-flood/flood.py validate --root .
python .project-flood/flood.py doctor --root .
python .project-flood/flood.py memory-index --root . --check
```

For an approved build swarm, validate and publish the shared worktree lease, then close it after verified fan-in:

```bash
python .project-flood/flood.py task-validate --root .
python .project-flood/flood.py task-activate --root .
python .project-flood/flood.py task-status --root .
python .project-flood/flood.py task-close --root . --status complete
```

Preview changes before upgrading:

```bash
python scripts/flood.py diff --target /path/to/target-repository
python scripts/flood.py upgrade --target /path/to/target-repository
```

Conflicts stop without modifying files. `--force` backs up conflicting files under the gitignored `.project-flood/backups/` directory before replacement. Migration and uninstall are dry runs unless explicitly applied. See the [lifecycle guide](docs/upgrades.md).

## License

Project Flood is licensed under the [Apache License 2.0](LICENSE). Copyright 2026 Jackson Hopkins; attribution details are recorded in [NOTICE](NOTICE).

## Limits

Hooks are preview defense-in-depth. They do not replace OS sandboxing, GitHub permissions, branch protection, required reviews, CI, or human approval. Tool and agent support varies by harness, and model behavior evaluations still need real harness runs. Project Flood bundles no MCP server and allowlists no external tool prefix by default.

## Platform references

- [Agent plugins](https://code.visualstudio.com/docs/agent-customization/agent-plugins)
- [Agent hooks](https://code.visualstudio.com/docs/agent-customization/hooks)
- [Agent harnesses and worktree sessions](https://code.visualstudio.com/docs/agents/run/agent-harnesses)
- [Agent skills](https://code.visualstudio.com/docs/agent-customization/agent-skills)
- [GitHub Copilot plugins](https://docs.github.com/en/copilot/concepts/agents/about-plugins)
- [Cloud-agent repository setup](https://docs.github.com/en/copilot/tutorials/cloud-agent/improve-a-project)

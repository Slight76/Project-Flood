# Project Flood

Project Flood is a reusable, repository-native GitHub Copilot configuration for a stable specialist squad that can create temporary swarms when parallel work is justified.

It is intentionally smaller and more conservative than a fully autonomous agent framework:

- one human-facing **Squad Lead** coordinates the work;
- focused subagents research, design, implement, verify, review security, and maintain memory;
- swarms are created only for independent tasks;
- durable repository memory is evidence-gated and written by one Librarian;
- research and review agents are read-only;
- parallel editors must have exclusive path ownership or isolated Git worktrees;
- external writes, commits, pushes, and pull requests still require human authorization.

Project Flood does not train or modify an AI model. Its "learning" is curated Markdown state committed with the repository so that it stays visible, reviewable, and reversible.

## Install into a repository

Clone Project Flood next to the repository you want to configure, then run one of the installers.

### PowerShell

```powershell
git clone <PROJECT-FLOOD-REPOSITORY-URL>
pwsh ./project-flood/scripts/install.ps1 -TargetPath C:\src\your-repository
```

### Bash

```bash
git clone <PROJECT-FLOOD-REPOSITORY-URL>
./project-flood/scripts/install.sh /path/to/your-repository
```

The installers perform a full conflict preflight. By default, they make no changes if any destination file already exists. Pass `-Force` in PowerShell or `--force` in Bash to back up conflicting files under `.project-flood-backup/<timestamp>/` before replacing them.

You can also copy the contents of [`template/`](template/) into a repository manually.

## Start using it in VS Code

1. Open the configured repository in a current VS Code release with GitHub Copilot enabled.
2. Open Chat and run `/agents` or **Chat: Open Customizations**.
3. Select **Squad Lead**.
4. Run `/onboard-repository` before asking the squad to implement anything.
5. Review the proposed repository profile, routes, and decisions.
6. Try a bounded task such as:

   ```text
   Investigate this repository's authentication flow. Use a read-only swarm if multiple independent areas need analysis. Return a diagram-free evidence summary and a recommended next step; do not edit code.
   ```

7. Then try an implementation task:

   ```text
   Add validation to the user-registration flow. Plan first, assign exclusive file ownership, implement the smallest change, run relevant tests, and have Verifier review it before declaring completion.
   ```

## What gets installed

| Path | Purpose |
| --- | --- |
| `AGENTS.md` | Human-owned operating contract for every agent |
| `.github/copilot-instructions.md` | Concise repository-wide development rules |
| `.github/agents/` | Squad Lead and hidden specialist subagents |
| `.github/instructions/` | File-scoped C#, TypeScript/React, SQL, test, CI/CD, and memory guidance |
| `.github/skills/` | On-demand workflows for onboarding, swarming, verification, security, memory, and context hygiene |
| `.github/prompts/` | Reusable entry prompts for onboarding, feature work, health checks, and reflection |
| `.agent-team/` | Versioned routing, decisions, role histories, current focus, schemas, and audit summaries |
| `.project-flood/` | Lightweight configuration validator |

## Operating model

The lead chooses one of three modes:

- **Direct:** answer a small factual question from already verified context.
- **Squad:** route a normal task to the smallest qualified set of specialists.
- **Swarm:** fan out two or more independent investigations, reviews, or isolated implementations, then fan results back into the lead.

A swarm is not a license to parallelize everything. Dependent work stays sequential. The initial concurrency ceiling is three workers, and only one worker may own a given path at a time.

## Validate the configuration

From the Project Flood repository:

```bash
python template/.project-flood/validate_config.py --root template
python -m unittest discover -s tests -v
```

From an installed target repository:

```bash
python .project-flood/validate_config.py --root .
```

The installed GitHub Actions workflow runs the same validation on pull requests and pushes that modify Copilot configuration.

## Customize after onboarding

The initial language instructions support the stack this project was designed around: C#, TypeScript/React, SQL, tests, and GitHub/Azure-style CI/CD. Delete instruction files that do not apply. Keep each rule in one authoritative location; VS Code can combine multiple instruction files without guaranteeing their order.

Do not treat `.agent-team/project-profile.md` as a substitute for the codebase. It should be a compact index of verified commands, boundaries, and conventions with source references.

## Updating

Pull the latest Project Flood changes and run the installer again. The safe default reports conflicts without changing the target. Review differences before using the force option, which creates a timestamped backup.

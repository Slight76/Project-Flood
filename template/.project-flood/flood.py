#!/usr/bin/env python3
"""Project Flood configuration, memory, installation, and maintenance CLI."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except ImportError as exc:  # pragma: no cover - exercised by real bootstrap failures
    raise SystemExit(
        "Project Flood requires PyYAML 6.0.3. "
        "Run: python -m pip install -r .project-flood/requirements.txt"
    ) from exc


VERSION = "0.2.0"
SCHEMA_VERSION = 1
MANIFEST_PATH = Path(".project-flood/install-manifest.yaml")
TASK_MANIFEST_PATH = Path(".agent-team/runtime/task-manifest.json")
SHARED_TASK_MANIFEST_PATH = Path("project-flood/task-manifest.json")

EXPECTED_AGENTS = {
    "Flood Squad Lead": "flood-squad-lead.agent.md",
    "Flood Scout": "flood-scout.agent.md",
    "Flood Architect": "flood-architect.agent.md",
    "Flood Builder": "flood-builder.agent.md",
    "Flood Integrator": "flood-integrator.agent.md",
    "Flood Verifier": "flood-verifier.agent.md",
    "Flood Security Reviewer": "flood-security-reviewer.agent.md",
    "Flood Librarian": "flood-librarian.agent.md",
    "Flood Swarm Analyst": "flood-swarm-analyst.agent.md",
}

EXPECTED_SKILLS = {
    "flood-context-hygiene",
    "flood-dependency-aware-swarm",
    "flood-memory-governance",
    "flood-repository-onboarding",
    "flood-run-feature",
    "flood-secure-change-review",
    "flood-spec-workflow",
    "flood-squad-health",
    "flood-verification-gate",
    "flood-worktree-swarm",
}

ROLE_HISTORY_SLUGS = {
    "Flood Scout": "scout",
    "Flood Architect": "architect",
    "Flood Builder": "builder",
    "Flood Integrator": "integrator",
    "Flood Verifier": "verifier",
    "Flood Security Reviewer": "security-reviewer",
    "Flood Librarian": "librarian",
    "Flood Swarm Analyst": "swarm-analyst",
}

READ_ONLY_AGENTS = {
    "Flood Scout",
    "Flood Architect",
    "Flood Verifier",
    "Flood Security Reviewer",
    "Flood Swarm Analyst",
}

ALLOWED_TOOL_ALIASES = {"execute", "read", "edit", "search", "agent", "web", "todo"}
MEMORY_TYPES = {"architecture", "decision", "convention", "pitfall", "archive"}
MEMORY_STATUSES = {"active", "experimental", "superseded", "archived"}
CONFIDENCE_VALUES = {"low", "medium", "high"}

COMMON_REQUIRED_PATHS = (
    "AGENTS.md",
    ".github/copilot-instructions.md",
    ".github/workflows/copilot-config-validation.yml",
    ".github/workflows/copilot-setup-steps.yml",
    ".agent-team/README.md",
    ".agent-team/charter.md",
    ".agent-team/project-profile.md",
    ".agent-team/routing.md",
    ".agent-team/now.md",
    ".agent-team/harnesses.md",
    ".agent-team/memory/MEMORY.md",
    ".agent-team/memory/memory-index.yaml",
    ".agent-team/schemas/handoff.md",
    ".agent-team/schemas/memory-candidate.md",
    ".agent-team/schemas/orchestration-entry.md",
    ".agent-team/schemas/task-manifest.schema.json",
    ".project-flood/VERSION",
    ".project-flood/flood.py",
    ".project-flood/.gitignore",
    ".project-flood/policy.yaml",
    ".project-flood/CODEOWNERS.example",
    ".project-flood/copilot-settings.adapter.example.json",
    ".project-flood/requirements.txt",
)

FULL_REQUIRED_PATHS = (
    ".github/hooks/project-flood.json",
    ".project-flood/hook.py",
)

LEGACY_PATHS = (
    ".github/agents/architect.agent.md",
    ".github/agents/builder.agent.md",
    ".github/agents/librarian.agent.md",
    ".github/agents/scout.agent.md",
    ".github/agents/security-reviewer.agent.md",
    ".github/agents/squad-lead.agent.md",
    ".github/agents/swarm-analyst.agent.md",
    ".github/agents/verifier.agent.md",
    ".github/prompts/onboard-repository.prompt.md",
    ".github/prompts/reflect.prompt.md",
    ".github/prompts/run-feature.prompt.md",
    ".github/prompts/squad-health.prompt.md",
    ".github/skills/context-hygiene/SKILL.md",
    ".github/skills/dependency-aware-swarm/SKILL.md",
    ".github/skills/memory-governance/SKILL.md",
    ".github/skills/repository-onboarding/SKILL.md",
    ".github/skills/secure-change-review/SKILL.md",
    ".github/skills/verification-gate/SKILL.md",
)

LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MEMORY_ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9]*-\d{4,}$")
SECRET_PATTERNS = {
    "GitHub personal access token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "OpenAI API key": re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}


class FloodError(RuntimeError):
    """Expected, user-actionable Project Flood failure."""


def _portable(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _portable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_portable(item) for item in value]
    return value


def load_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise FloodError(f"{path}: invalid YAML: {exc}") from exc


def write_yaml(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(_portable(value), sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def split_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise FloodError(f"{path}: missing opening YAML frontmatter delimiter")
    try:
        closing = next(index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration as exc:
        raise FloodError(f"{path}: missing closing YAML frontmatter delimiter") from exc
    try:
        metadata = yaml.safe_load("\n".join(lines[1:closing])) or {}
    except yaml.YAMLError as exc:
        raise FloodError(f"{path}: invalid YAML frontmatter: {exc}") from exc
    if not isinstance(metadata, dict):
        raise FloodError(f"{path}: YAML frontmatter must be a mapping")
    return metadata, "\n".join(lines[closing + 1 :])


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_common_dir(root: Path) -> Path | None:
    root = root.resolve()
    git_entry = root / ".git"
    if git_entry.is_symlink():
        return None
    if git_entry.is_dir():
        return git_entry.resolve()
    if not git_entry.is_file():
        return None
    try:
        marker = git_entry.read_text(encoding="utf-8").strip()
        if not marker.lower().startswith("gitdir:"):
            return None
        git_dir_value = marker.split(":", 1)[1].strip()
        git_dir = Path(git_dir_value)
        if not git_dir.is_absolute():
            git_dir = root / git_dir
        if git_dir.is_symlink():
            return None
        git_dir = git_dir.resolve()
        if not git_dir.is_dir():
            return None
        common_marker = git_dir / "commondir"
        if common_marker.is_file() and not common_marker.is_symlink():
            common_value = common_marker.read_text(encoding="utf-8").strip()
            common_dir = Path(common_value)
            if not common_dir.is_absolute():
                common_dir = git_dir / common_dir
            if common_dir.is_symlink():
                return None
            common_dir = common_dir.resolve()
        else:
            common_dir = git_dir
        return common_dir if common_dir.is_dir() else None
    except OSError:
        return None


def shared_task_manifest_path(root: Path) -> Path | None:
    common_dir = git_common_dir(root)
    return common_dir / SHARED_TASK_MANIFEST_PATH if common_dir else None


def _atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".task-manifest-", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        try:
            temporary.chmod(0o600)
        except OSError:
            pass
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def iter_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in {".git", "__pycache__", ".project-flood-backup"} for part in relative.parts):
            continue
        if relative.parts[:2] == (".project-flood", "backups"):
            continue
        if path.suffix in {".pyc", ".pyo"}:
            continue
        yield path


def iter_configuration_files(root: Path) -> Iterable[Path]:
    direct = (
        root / "AGENTS.md",
        root / ".github/copilot-instructions.md",
        root / ".github/workflows/copilot-config-validation.yml",
        root / ".github/workflows/copilot-setup-steps.yml",
    )
    directories = (
        root / ".github/agents",
        root / ".github/hooks",
        root / ".github/instructions",
        root / ".github/prompts",
        root / ".github/skills",
        root / ".agent-team",
        root / ".project-flood",
    )
    found: set[Path] = {path for path in direct if path.is_file() or path.is_symlink()}
    for directory in directories:
        if not directory.exists():
            continue
        found.update(
            path
            for path in directory.rglob("*")
            if (path.is_file() or path.is_symlink())
            and "__pycache__" not in path.parts
            and path.relative_to(root).parts[:2] != (".project-flood", "backups")
            and path.suffix not in {".pyc", ".pyo"}
        )
    yield from sorted(found)


def _as_string_list(value: Any, path: Path, field: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        errors.append(f"{path}: `{field}` must be a YAML list of strings")
        return []
    return value


def validate_agents(root: Path, errors: list[str]) -> None:
    agent_dir = root / ".github/agents"
    if not agent_dir.is_dir():
        errors.append(f"{agent_dir}: agent directory is missing")
        return

    parsed: dict[str, tuple[Path, dict[str, Any]]] = {}
    for path in sorted(agent_dir.glob("*.agent.md")):
        try:
            fields, body = split_frontmatter(path)
        except FloodError as exc:
            errors.append(str(exc))
            continue
        name = fields.get("name")
        if not isinstance(name, str) or not name:
            errors.append(f"{path}: missing agent name")
            continue
        if name in parsed:
            errors.append(f"{path}: duplicate agent name `{name}`")
        parsed[name] = (path, fields)
        if path.name != EXPECTED_AGENTS.get(name):
            errors.append(f"{path}: agent `{name}` must use its namespaced filename")
        if not isinstance(fields.get("description"), str) or not fields["description"].strip():
            errors.append(f"{path}: missing agent description")
        if not body.strip():
            errors.append(f"{path}: agent instructions are empty")
        tools = _as_string_list(fields.get("tools"), path, "tools", errors)
        agents = _as_string_list(fields.get("agents"), path, "agents", errors)
        for tool in tools:
            if tool in ALLOWED_TOOL_ALIASES or "/" in tool or tool == "*":
                continue
            errors.append(f"{path}: unrecognized portable tool alias `{tool}`")
        expected_invocable = name == "Flood Squad Lead"
        if fields.get("user-invocable") is not expected_invocable:
            errors.append(f"{path}: `user-invocable` must be {str(expected_invocable).lower()}")
        if name == "Flood Squad Lead":
            if fields.get("disable-model-invocation") is not True:
                errors.append(f"{path}: lead must require explicit user selection")
            if not {"agent", "edit", "execute"}.issubset(tools):
                errors.append(f"{path}: lead must coordinate agents and runtime state")
        elif fields.get("disable-model-invocation") is not False:
            errors.append(f"{path}: specialist must remain available to the lead")
        if name in READ_ONLY_AGENTS and "edit" in tools:
            errors.append(f"{path}: read-only agent `{name}` must not include `edit`")
        if name in {"Flood Builder", "Flood Integrator"} and not {"edit", "execute"}.issubset(tools):
            errors.append(f"{path}: `{name}` must include `edit` and `execute`")
        if name == "Flood Librarian" and ("edit" not in tools or "execute" in tools):
            errors.append(f"{path}: Librarian must include `edit` and omit `execute`")
        if name != "Flood Squad Lead" and agents:
            errors.append(f"{path}: specialists must not invoke nested agents")

    missing = set(EXPECTED_AGENTS) - set(parsed)
    extra = set(parsed) - set(EXPECTED_AGENTS)
    if missing:
        errors.append(f"Missing expected agents: {', '.join(sorted(missing))}")
    if extra:
        errors.append(f"Unexpected agents require contract review: {', '.join(sorted(extra))}")

    lead = parsed.get("Flood Squad Lead")
    if lead:
        lead_path, fields = lead
        tools = fields.get("tools", [])
        allowed_agents = fields.get("agents", [])
        expected_specialists = set(EXPECTED_AGENTS) - {"Flood Squad Lead"}
        if set(allowed_agents) != expected_specialists:
            errors.append(f"{lead_path}: lead agent allowlist must exactly match Flood specialists")

    for role_name, slug in ROLE_HISTORY_SLUGS.items():
        history = root / ".agent-team/roles" / slug / "history.md"
        if not history.exists():
            errors.append(f"Missing role history for {role_name}: {history.relative_to(root)}")


def validate_skills(root: Path, errors: list[str]) -> None:
    skill_dir = root / ".github/skills"
    if not skill_dir.is_dir():
        errors.append(f"{skill_dir}: skills directory is missing")
        return
    found: set[str] = set()
    for path in sorted(skill_dir.glob("*/SKILL.md")):
        try:
            fields, body = split_frontmatter(path)
        except FloodError as exc:
            errors.append(str(exc))
            continue
        name = fields.get("name")
        description = fields.get("description")
        if not isinstance(name, str) or not SKILL_NAME_PATTERN.fullmatch(name):
            errors.append(f"{path}: invalid skill name")
            continue
        if name != path.parent.name:
            errors.append(f"{path}: skill name `{name}` must match its directory")
        if not name.startswith("flood-"):
            errors.append(f"{path}: Project Flood skills must use the `flood-` namespace")
        if name in found:
            errors.append(f"{path}: duplicate skill name `{name}`")
        found.add(name)
        if not isinstance(description, str) or not description.strip() or len(description) > 1024:
            errors.append(f"{path}: skill description must contain 1-1024 characters")
        if not body.strip():
            errors.append(f"{path}: skill instructions are empty")
    if found != EXPECTED_SKILLS:
        missing = EXPECTED_SKILLS - found
        extra = found - EXPECTED_SKILLS
        if missing:
            errors.append(f"Missing expected skills: {', '.join(sorted(missing))}")
        if extra:
            errors.append(f"Unexpected skills require contract review: {', '.join(sorted(extra))}")


def validate_markdown_customizations(root: Path, errors: list[str]) -> None:
    for path in sorted((root / ".github/instructions").glob("*.instructions.md")):
        try:
            fields, body = split_frontmatter(path)
        except FloodError as exc:
            errors.append(str(exc))
            continue
        if not isinstance(fields.get("description"), str):
            errors.append(f"{path}: missing instruction description")
        if not isinstance(fields.get("applyTo"), str):
            errors.append(f"{path}: missing `applyTo` glob")
        if not body.strip():
            errors.append(f"{path}: instruction body is empty")

    prompt_dir = root / ".github/prompts"
    for path in sorted(prompt_dir.glob("*.prompt.md")):
        try:
            fields, body = split_frontmatter(path)
        except FloodError as exc:
            errors.append(str(exc))
            continue
        if fields.get("agent") != "Flood Squad Lead":
            errors.append(f"{path}: prompt must route to `Flood Squad Lead`")
        if not body.strip():
            errors.append(f"{path}: prompt body is empty")


def _memory_records(root: Path, errors: list[str] | None = None) -> list[tuple[Path, dict[str, Any]]]:
    records: list[tuple[Path, dict[str, Any]]] = []
    memory_root = root / ".agent-team/memory"
    record_roots = [memory_root / name for name in ("architecture", "decisions", "conventions", "pitfalls", "archive")]
    for folder in record_roots:
        for path in sorted(folder.glob("*.md")) if folder.exists() else []:
            try:
                fields, body = split_frontmatter(path)
            except FloodError as exc:
                if errors is not None:
                    errors.append(str(exc))
                continue
            local_errors: list[str] = []
            required = {
                "id", "type", "status", "scope", "owner", "confidence", "created", "updated",
                "review_when", "tags", "sources",
            }
            missing = sorted(required - set(fields))
            if missing:
                local_errors.append(f"{path}: missing memory metadata: {', '.join(missing)}")
            if not isinstance(fields.get("id"), str) or not MEMORY_ID_PATTERN.fullmatch(fields.get("id", "")):
                local_errors.append(f"{path}: invalid memory id")
            if fields.get("type") not in MEMORY_TYPES:
                local_errors.append(f"{path}: invalid memory type")
            if fields.get("status") not in MEMORY_STATUSES:
                local_errors.append(f"{path}: invalid memory status")
            if fields.get("confidence") not in CONFIDENCE_VALUES:
                local_errors.append(f"{path}: invalid memory confidence")
            if not isinstance(fields.get("owner"), str) or not fields["owner"].strip():
                local_errors.append(f"{path}: memory owner must be a non-empty string")
            for date_field in ("created", "updated"):
                if not isinstance(fields.get(date_field), (str, date, datetime)):
                    local_errors.append(f"{path}: `{date_field}` must be a date or string")
            if not isinstance(fields.get("review_when"), (str, date, datetime)):
                local_errors.append(f"{path}: `review_when` must be a date or triggering condition")
            for list_field in ("scope", "tags", "sources"):
                if not isinstance(fields.get(list_field), list) or not fields.get(list_field) or not all(
                    isinstance(item, str) for item in fields.get(list_field, [])
                ):
                    local_errors.append(f"{path}: `{list_field}` must be a non-empty YAML list of strings")
            for mapping_field in ("permissions", "tooling"):
                if mapping_field in fields and not isinstance(fields[mapping_field], dict):
                    local_errors.append(f"{path}: `{mapping_field}` must be a YAML mapping")
            if not body.strip():
                local_errors.append(f"{path}: memory body is empty")
            if errors is not None:
                errors.extend(local_errors)
            if not local_errors:
                records.append((path, fields))
    return records


def build_memory_index(root: Path, errors: list[str] | None = None) -> dict[str, Any]:
    seen: dict[str, Path] = {}
    output: list[dict[str, Any]] = []
    for path, fields in _memory_records(root, errors):
        memory_id = fields["id"]
        if memory_id in seen:
            if errors is not None:
                errors.append(f"{path}: duplicate memory id `{memory_id}` also used by {seen[memory_id]}")
            continue
        seen[memory_id] = path
        item = {
            "id": memory_id,
            "type": fields["type"],
            "status": fields["status"],
            "path": path.relative_to(root).as_posix(),
            "owner": fields["owner"],
            "confidence": fields["confidence"],
            "updated": _portable(fields["updated"]),
            "review_when": _portable(fields["review_when"]),
            "tags": fields["tags"],
            "scope": fields["scope"],
            "sources": fields["sources"],
        }
        for optional_field in ("permissions", "tooling"):
            if optional_field in fields:
                item[optional_field] = fields[optional_field]
        output.append(item)
    output.sort(key=lambda item: item["id"])
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_from": "canonical Markdown frontmatter; do not edit this file directly",
        "records": output,
    }


def validate_memory(root: Path, errors: list[str]) -> None:
    expected = build_memory_index(root, errors)
    index_path = root / ".agent-team/memory/memory-index.yaml"
    if not index_path.exists():
        errors.append(f"{index_path}: generated memory index is missing")
        return
    try:
        actual = load_yaml(index_path)
    except FloodError as exc:
        errors.append(str(exc))
        return
    if _portable(actual) != _portable(expected):
        errors.append(
            f"{index_path}: index is stale; run `python .project-flood/flood.py memory-index --root .`"
        )


def validate_policy(root: Path, errors: list[str]) -> None:
    policy_path = root / ".project-flood/policy.yaml"
    try:
        policy = load_yaml(policy_path)
    except FloodError as exc:
        errors.append(str(exc))
        return
    if not isinstance(policy, dict) or policy.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"{policy_path}: unsupported policy schema")
        return
    controls = policy.get("controls")
    if not isinstance(controls, dict):
        errors.append(f"{policy_path}: `controls` mapping is required")
    else:
        for name, choice in controls.items():
            if choice not in {"allow", "deny", "ask"}:
                errors.append(f"{policy_path}: control `{name}` must be allow, deny, or ask")
    for field in (
        "protected_paths",
        "external_write_tools",
        "built_in_tool_prefixes",
        "allowed_external_tool_prefixes",
    ):
        value = policy.get(field)
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            errors.append(f"{policy_path}: `{field}` must be a list of strings")
    dangerous = policy.get("dangerous_commands")
    if not isinstance(dangerous, list):
        errors.append(f"{policy_path}: `dangerous_commands` must be a list")
    else:
        for index, item in enumerate(dangerous, start=1):
            if (
                not isinstance(item, dict)
                or not isinstance(item.get("id"), str)
                or not isinstance(item.get("pattern"), str)
            ):
                errors.append(f"{policy_path}: dangerous command {index} requires string `id` and `pattern`")
                continue
            try:
                re.compile(item["pattern"])
            except re.error as exc:
                errors.append(f"{policy_path}: dangerous command `{item['id']}` has invalid regex: {exc}")


def validate_hooks_and_policy(root: Path, errors: list[str]) -> None:
    hook_path = root / ".github/hooks/project-flood.json"
    try:
        hook_data = json.loads(hook_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{hook_path}: invalid hook JSON: {exc}")
        return
    hooks = hook_data.get("hooks") if isinstance(hook_data, dict) else None
    if not isinstance(hooks, dict):
        errors.append(f"{hook_path}: top-level `hooks` mapping is required")
    else:
        for event in (
            "SessionStart",
            "UserPromptSubmit",
            "PreToolUse",
            "PostToolUse",
            "SubagentStart",
            "SubagentStop",
            "PreCompact",
            "Stop",
        ):
            entries = hooks.get(event)
            if not isinstance(entries, list) or not entries:
                errors.append(f"{hook_path}: missing `{event}` hook")
                continue
            for entry in entries:
                if not isinstance(entry, dict) or entry.get("type") != "command":
                    errors.append(f"{hook_path}: `{event}` entries must be command hooks")
                    continue
                if not any(isinstance(entry.get(key), str) for key in ("command", "windows", "linux", "osx")):
                    errors.append(f"{hook_path}: `{event}` command is missing")
                if "timeoutSec" in entry:
                    errors.append(f"{hook_path}: use the supported `timeout` property, not `timeoutSec`")

    validate_policy(root, errors)


def validate_task_manifest_data(data: Any, source: str = "task manifest") -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return [f"{source}: root must be an object"]
    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"{source}: unsupported schema version")
    if not isinstance(data.get("task_id"), str) or not data.get("task_id"):
        errors.append(f"{source}: `task_id` is required")
    coordinator_key = data.get("coordinator_session_key")
    if not isinstance(coordinator_key, str) or not coordinator_key:
        errors.append(f"{source}: `coordinator_session_key` is required")
    base_commit = data.get("base_commit")
    if not isinstance(base_commit, str) or not re.fullmatch(r"[0-9a-fA-F]{7,64}", base_commit):
        errors.append(f"{source}: `base_commit` must identify committed base state")
    expires_at = data.get("expires_at")
    if not isinstance(expires_at, str):
        errors.append(f"{source}: `expires_at` is required")
    else:
        try:
            expiry = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            if expiry.tzinfo is None:
                errors.append(f"{source}: `expires_at` must include a timezone")
            elif data.get("status") == "active" and expiry < datetime.now(timezone.utc):
                errors.append(f"{source}: active manifest is expired")
        except (ValueError, TypeError):
            errors.append(f"{source}: `expires_at` must be an ISO-8601 timestamp")
    if data.get("status") not in {"planned", "active", "paused", "complete", "cancelled"}:
        errors.append(f"{source}: invalid status")
    if data.get("status") == "active" and (
        not isinstance(coordinator_key, str) or not re.fullmatch(r"[0-9a-f]{12}", coordinator_key)
    ):
        errors.append(f"{source}: active coordinator session key must be a 12-character hash")
    mode = data.get("mode")
    if mode not in {"squad", "research-swarm", "build-swarm", "review-swarm"}:
        errors.append(f"{source}: invalid mode")
    workers = data.get("workers")
    if not isinstance(workers, list):
        return errors + [f"{source}: `workers` must be a list"]
    identifiers: set[str] = set()
    session_keys: set[str] = set()
    branches: set[str] = set()
    worktrees: set[str] = set()
    wave_counts: dict[int, int] = {}
    owners: list[tuple[str, str, int, str]] = []
    worker_waves: dict[str, int] = {}
    worker_dependencies: dict[str, list[str]] = {}
    for index, worker in enumerate(workers):
        label = f"{source}: worker {index + 1}"
        if not isinstance(worker, dict):
            errors.append(f"{label} must be an object")
            continue
        worker_id = worker.get("id")
        if not isinstance(worker_id, str) or not worker_id:
            errors.append(f"{label} requires an id")
            continue
        if worker_id in identifiers:
            errors.append(f"{label} duplicates worker id `{worker_id}`")
        identifiers.add(worker_id)
        if worker.get("status") not in {"planned", "active", "complete", "failed", "cancelled"}:
            errors.append(f"{label}: invalid status")
        if not isinstance(worker.get("role"), str) or worker.get("role") not in EXPECTED_AGENTS:
            errors.append(f"{label}: role must be a Project Flood agent")
        paths = worker.get("write_paths", [])
        if not isinstance(paths, list) or not all(isinstance(item, str) and item for item in paths):
            errors.append(f"{label}: `write_paths` must be a string list")
            paths = []
        for path in paths:
            candidate = Path(path)
            if candidate.is_absolute() or ".." in candidate.parts:
                errors.append(f"{label}: write path must remain inside the repository: `{path}`")
            elif not _valid_write_pattern(path):
                errors.append(
                    f"{label}: write path must be exact or a prefix ending in `/**`: `{path}`"
                )
        if worker.get("role") in READ_ONLY_AGENTS and paths:
            errors.append(f"{label}: read-only roles cannot own write paths")
        if mode in {"research-swarm", "review-swarm"} and paths:
            errors.append(f"{label}: {mode} workers must remain read-only")
        if (
            mode == "build-swarm"
            and worker.get("status") == "active"
            and worker.get("role") not in {"Flood Builder", "Flood Integrator"}
        ):
            errors.append(f"{label}: active build-swarm workers require Flood Builder or Flood Integrator")
        dependencies = worker.get("depends_on", [])
        if not isinstance(dependencies, list) or not all(isinstance(item, str) for item in dependencies):
            errors.append(f"{label}: `depends_on` must be a string list")
        elif len(dependencies) != len(set(dependencies)):
            errors.append(f"{label}: `depends_on` must not contain duplicates")
        criteria = worker.get("acceptance_criteria", [])
        if (
            not isinstance(criteria, list)
            or not criteria
            or not all(isinstance(item, str) and item for item in criteria)
        ):
            errors.append(f"{label}: `acceptance_criteria` must be a non-empty string list")
        wave = worker.get("wave", 1)
        if not isinstance(wave, int) or wave < 1:
            errors.append(f"{label}: wave must be a positive integer")
            wave = 1
        worker_waves[worker_id] = wave
        if isinstance(dependencies, list) and all(isinstance(item, str) for item in dependencies):
            worker_dependencies[worker_id] = dependencies
        status = str(worker.get("status", ""))
        if status in {"planned", "active"}:
            wave_counts[wave] = wave_counts.get(wave, 0) + 1
            for path in paths:
                owners.append((worker_id, path, wave, status))
        if status == "active":
            session_key = worker.get("session_key")
            if not isinstance(session_key, str) or not re.fullmatch(r"[0-9a-f]{12}", session_key):
                errors.append(f"{label}: active worker session key must be a 12-character hash")
            elif session_key in session_keys:
                errors.append(f"{label}: active worker session key must be unique")
            else:
                session_keys.add(session_key)
            if mode == "build-swarm":
                for field, seen in (("branch", branches), ("worktree", worktrees)):
                    value = worker.get(field)
                    if not isinstance(value, str) or not value:
                        errors.append(f"{label}: active build-swarm workers require `{field}`")
                    elif value in seen:
                        errors.append(f"{label}: active build-swarm `{field}` must be unique")
                    else:
                        seen.add(value)
    for wave, count in wave_counts.items():
        if count > 3:
            errors.append(f"{source}: wave {wave} exceeds the three-worker ceiling")
    for index, (left_owner, left_path, left_wave, left_status) in enumerate(owners):
        for right_owner, right_path, right_wave, right_status in owners[index + 1 :]:
            if left_owner == right_owner:
                continue
            concurrent = left_status == "active" and right_status == "active"
            if (concurrent or left_wave == right_wave) and _patterns_overlap(left_path, right_path):
                errors.append(
                    f"{source}: overlapping concurrent ownership `{left_path}` ({left_owner}) and "
                    f"`{right_path}` ({right_owner})"
                )
    for worker in workers:
        if not isinstance(worker, dict):
            continue
        dependencies = worker.get("depends_on", [])
        if not isinstance(dependencies, list):
            continue
        for dependency in dependencies:
            if dependency not in identifiers:
                errors.append(f"{source}: worker `{worker.get('id')}` has unknown dependency `{dependency}`")
            if dependency == worker.get("id"):
                errors.append(f"{source}: worker `{worker.get('id')}` cannot depend on itself")
            if dependency in worker_waves and worker_waves[dependency] >= worker_waves.get(str(worker.get("id")), 1):
                errors.append(
                    f"{source}: dependency `{dependency}` must be in an earlier wave than `{worker.get('id')}`"
                )

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(worker_id: str) -> bool:
        if worker_id in visiting:
            return True
        if worker_id in visited:
            return False
        visiting.add(worker_id)
        for dependency in worker_dependencies.get(worker_id, []):
            if dependency in worker_dependencies and visit(dependency):
                return True
        visiting.remove(worker_id)
        visited.add(worker_id)
        return False

    if any(visit(worker_id) for worker_id in worker_dependencies if worker_id not in visited):
        errors.append(f"{source}: worker dependencies contain a cycle")
    if isinstance(coordinator_key, str) and coordinator_key in session_keys:
        errors.append(f"{source}: coordinator and worker session keys must differ")
    return errors


def load_task_manifest(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FloodError(f"{path}: invalid task manifest: {exc}") from exc
    if not isinstance(data, dict):
        raise FloodError(f"{path}: task manifest root must be an object")
    return data


def activate_task_manifest(root: Path) -> dict[str, Any]:
    root = root.resolve()
    local_path = root / TASK_MANIFEST_PATH
    if _has_symlink_component(root, TASK_MANIFEST_PATH):
        raise FloodError(f"{local_path}: task manifest must not use symbolic links")
    data = load_task_manifest(local_path)
    errors = validate_task_manifest_data(data, str(local_path))
    if data.get("status") != "active":
        errors.append(f"{local_path}: set status to `active` before activation")
    if errors:
        joined = "\n".join(f"  {error}" for error in errors)
        raise FloodError(f"Task manifest cannot be activated:\n{joined}")

    shared_path = shared_task_manifest_path(root)
    if shared_path is None:
        raise FloodError("Task activation requires a Git repository or worktree")
    if shared_path.parent.is_symlink() or shared_path.is_symlink():
        raise FloodError(f"{shared_path}: shared task state must not use symbolic links")

    completed = subprocess.run(
        ["git", "cat-file", "-e", f"{data['base_commit']}^{{commit}}"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise FloodError(f"Base commit does not exist in this repository: {data['base_commit']}")

    if shared_path.is_file():
        existing = load_task_manifest(shared_path)
        if existing.get("status") == "active" and existing.get("task_id") != data.get("task_id"):
            raise FloodError(
                f"Another active task already owns the Git common directory: {existing.get('task_id', 'unknown')}"
            )
    _atomic_write_json(shared_path, data)
    return {"task_id": data["task_id"], "shared_manifest": str(shared_path)}


def task_manifest_status(root: Path) -> dict[str, Any]:
    root = root.resolve()
    shared_path = shared_task_manifest_path(root)
    local_path = root / TASK_MANIFEST_PATH
    if shared_path and (shared_path.is_symlink() or shared_path.parent.is_symlink()):
        raise FloodError(f"{shared_path}: shared task state must not use symbolic links")
    if (
        shared_path
        and shared_path.is_file()
        and not shared_path.is_symlink()
        and not shared_path.parent.is_symlink()
    ):
        return {"source": "git-common-dir", "path": str(shared_path), "manifest": load_task_manifest(shared_path)}
    if local_path.is_file() and not _has_symlink_component(root, TASK_MANIFEST_PATH):
        return {"source": "worktree-local", "path": str(local_path), "manifest": load_task_manifest(local_path)}
    return {"source": "none", "path": None, "manifest": None}


def close_task_manifest(root: Path, status: str) -> dict[str, Any]:
    if status not in {"complete", "cancelled"}:
        raise FloodError("Task close status must be `complete` or `cancelled`")
    root = root.resolve()
    shared_path = shared_task_manifest_path(root)
    if (
        shared_path is None
        or not shared_path.is_file()
        or shared_path.is_symlink()
        or shared_path.parent.is_symlink()
    ):
        raise FloodError("No safe shared active task manifest was found")
    data = load_task_manifest(shared_path)
    data["status"] = status
    local_path = root / TASK_MANIFEST_PATH
    if _has_symlink_component(root, TASK_MANIFEST_PATH):
        raise FloodError(f"{local_path}: local task state must not use symbolic links")
    _atomic_write_json(local_path, data)
    shared_path.unlink()
    return {"task_id": data.get("task_id"), "status": status, "archived_to": str(local_path)}


def _patterns_overlap(left: str, right: str) -> bool:
    clean_left = left.rstrip("/*")
    clean_right = right.rstrip("/*")
    return (
        clean_left == clean_right
        or clean_left.startswith(clean_right + "/")
        or clean_right.startswith(clean_left + "/")
        or fnmatch.fnmatch(clean_left, right)
        or fnmatch.fnmatch(clean_right, left)
    )


def _valid_write_pattern(value: str) -> bool:
    if not value or value in {".", "**"} or "\\" in value:
        return False
    core = value[:-3] if value.endswith("/**") else value
    return bool(core) and not core.endswith("/") and not any(character in core for character in "*?[]")


def validate_json_schemas(root: Path, errors: list[str]) -> None:
    schema_dir = root / ".agent-team/schemas"
    for path in sorted(schema_dir.glob("*.schema.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path}: invalid JSON schema: {exc}")
            continue
        if not isinstance(data, dict) or "$schema" not in data:
            errors.append(f"{path}: JSON schema must declare `$schema`")

    settings_path = root / ".project-flood/copilot-settings.adapter.example.json"
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{settings_path}: invalid JSON: {exc}")
    else:
        marketplaces = settings.get("extraKnownMarketplaces") if isinstance(settings, dict) else None
        plugins = settings.get("enabledPlugins") if isinstance(settings, dict) else None
        if not isinstance(marketplaces, dict) or "project-flood" not in marketplaces:
            errors.append(f"{settings_path}: Project Flood marketplace recommendation is missing")
        if not isinstance(plugins, dict) or plugins.get("project-flood@project-flood") is not True:
            errors.append(f"{settings_path}: Project Flood plugin recommendation is missing")


def _workflow_data(path: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        data = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    except (OSError, yaml.YAMLError) as exc:
        errors.append(f"{path}: invalid workflow YAML: {exc}")
        return None
    if not isinstance(data, dict):
        errors.append(f"{path}: workflow root must be a mapping")
        return None
    permissions = data.get("permissions")
    if not isinstance(permissions, dict) or permissions.get("contents") != "read":
        errors.append(f"{path}: workflow must default to read-only contents permission")
    elif any(value not in {"read", "none"} for value in permissions.values()):
        errors.append(f"{path}: workflow permissions must not grant write access")
    jobs = data.get("jobs")
    if not isinstance(jobs, dict) or not jobs:
        errors.append(f"{path}: workflow must define jobs")
        return data
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            errors.append(f"{path}: job `{job_name}` must be a mapping")
            continue
        job_permissions = job.get("permissions")
        if job_permissions is not None and (
            not isinstance(job_permissions, dict)
            or any(value not in {"read", "none"} for value in job_permissions.values())
        ):
            errors.append(f"{path}: job `{job_name}` must not grant write permissions")
        steps = job.get("steps", [])
        if not isinstance(steps, list):
            errors.append(f"{path}: job `{job_name}` steps must be a list")
            continue
        for step in steps:
            if not isinstance(step, dict) or "uses" not in step:
                continue
            action = step["uses"]
            pinned_repository_action = isinstance(action, str) and re.fullmatch(
                r"[^@\s]+@[0-9a-f]{40}", action
            )
            pinned_container_action = isinstance(action, str) and re.fullmatch(
                r"docker://[^@\s]+@sha256:[0-9a-f]{64}", action
            )
            local_action = isinstance(action, str) and action.startswith("./")
            if not (pinned_repository_action or pinned_container_action or local_action):
                errors.append(
                    f"{path}: action `{action}` must be local or pinned to a full commit SHA/digest"
                )
            if isinstance(action, str) and action.startswith("actions/checkout@"):
                options = step.get("with")
                if not isinstance(options, dict) or options.get("persist-credentials") != "false":
                    errors.append(f"{path}: checkout must set `persist-credentials: false`")
    return data


def validate_workflows(root: Path, errors: list[str]) -> None:
    validation_path = root / ".github/workflows/copilot-config-validation.yml"
    validation = _workflow_data(validation_path, errors)
    if validation:
        try:
            operating_systems = validation["jobs"]["validate"]["strategy"]["matrix"]["os"]
        except (KeyError, TypeError):
            errors.append(f"{validation_path}: validation job must use an OS matrix")
        else:
            required_systems = {"ubuntu-latest", "windows-latest"}
            if not isinstance(operating_systems, list) or not required_systems.issubset(operating_systems):
                errors.append(f"{validation_path}: validation matrix must cover Ubuntu and Windows")

    setup_path = root / ".github/workflows/copilot-setup-steps.yml"
    setup = _workflow_data(setup_path, errors)
    if setup:
        jobs = setup.get("jobs", {})
        job = jobs.get("copilot-setup-steps") if isinstance(jobs, dict) else None
        if not isinstance(job, dict):
            errors.append(f"{setup_path}: job must be named `copilot-setup-steps`")
        else:
            try:
                timeout = int(job.get("timeout-minutes", "0"))
            except ValueError:
                timeout = 0
            if timeout < 1 or timeout > 59:
                errors.append(f"{setup_path}: timeout must be between 1 and 59 minutes")


def validate_links(root: Path, errors: list[str], files: Iterable[Path] | None = None) -> None:
    candidates = files if files is not None else iter_files(root)
    for path in sorted(item for item in candidates if item.suffix == ".md"):
        if any(part in {".git", ".project-flood-backup"} for part in path.relative_to(root).parts):
            continue
        text = path.read_text(encoding="utf-8")
        for target in LINK_PATTERN.findall(text):
            target = target.strip().split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:", "sandbox:", "#")):
                continue
            resolved = (path.parent / target).resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                errors.append(f"{path}: local link escapes configuration root: {target}")
                continue
            if not resolved.exists():
                errors.append(f"{path}: broken local link: {target}")


def validate_secrets(root: Path, errors: list[str], files: Iterable[Path] | None = None) -> None:
    candidates = files if files is not None else iter_files(root)
    for path in candidates:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{path}: possible {label} detected")


def _configuration_mode(root: Path, requested: str) -> str:
    if requested in {"full", "adapter"}:
        return requested
    manifest = load_install_manifest(root)
    if manifest and manifest.get("mode") in {"full", "adapter"}:
        return str(manifest["mode"])
    return "full"


def validate_configuration(
    root: Path,
    require_manifest: bool = False,
    mode: str = "auto",
) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    try:
        selected_mode = _configuration_mode(root, mode)
    except FloodError as exc:
        return [str(exc)]
    required_paths = COMMON_REQUIRED_PATHS + (FULL_REQUIRED_PATHS if selected_mode == "full" else ())
    for relative in required_paths:
        if not (root / relative).exists():
            errors.append(f"Missing required path: {relative}")
    if errors:
        return errors
    if (root / ".project-flood/VERSION").read_text(encoding="utf-8").strip() != VERSION:
        errors.append(f"{root / '.project-flood/VERSION'}: expected version {VERSION}")
    if selected_mode == "full":
        validate_agents(root, errors)
        validate_skills(root, errors)
    validate_markdown_customizations(root, errors)
    validate_memory(root, errors)
    if selected_mode == "full":
        validate_hooks_and_policy(root, errors)
    else:
        validate_policy(root, errors)
    validate_json_schemas(root, errors)
    validate_workflows(root, errors)
    configuration_files = list(iter_configuration_files(root))
    for path in configuration_files:
        if path.is_symlink():
            errors.append(f"{path}: Project Flood configuration must not use symbolic links")
    validate_links(root, errors, configuration_files)
    validate_secrets(root, errors, configuration_files)
    for ignored in ("scratch/*", "runtime/*"):
        ignore_path = root / ".agent-team/.gitignore"
        if ignored not in ignore_path.read_text(encoding="utf-8"):
            errors.append(f"{ignore_path}: must ignore `{ignored}`")
    if require_manifest and not (root / MANIFEST_PATH).exists():
        errors.append(f"Missing installation manifest: {MANIFEST_PATH}")
    task_path = root / TASK_MANIFEST_PATH
    if task_path.exists():
        try:
            task = json.loads(task_path.read_text(encoding="utf-8"))
            errors.extend(validate_task_manifest_data(task, str(task_path)))
        except json.JSONDecodeError as exc:
            errors.append(f"{task_path}: invalid JSON: {exc}")
    return errors


def _compare_directories(left: Path, right: Path, label: str, errors: list[str]) -> None:
    left_files = {path.relative_to(left) for path in iter_files(left)} if left.exists() else set()
    right_files = {path.relative_to(right) for path in iter_files(right)} if right.exists() else set()
    if left_files != right_files:
        errors.append(f"{label}: packaged and workspace file sets differ")
        return
    for relative in sorted(left_files):
        if (left / relative).read_bytes() != (right / relative).read_bytes():
            errors.append(f"{label}: packaged copy is stale: {relative.as_posix()}")


def validate_distribution(root: Path) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    plugin_path = root / "plugin.json"
    try:
        plugin = json.loads(plugin_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{plugin_path}: invalid plugin manifest: {exc}"]
    if plugin.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json":
        errors.append(f"{plugin_path}: Agent Plugins 1.0 schema is required")
    if plugin.get("name") != "project-flood" or plugin.get("version") != VERSION:
        errors.append(f"{plugin_path}: plugin name/version does not match Project Flood {VERSION}")
    marketplace_path = root / ".github/plugin/marketplace.json"
    try:
        marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{marketplace_path}: invalid marketplace manifest: {exc}")
    else:
        if not isinstance(marketplace, dict):
            errors.append(f"{marketplace_path}: marketplace root must be an object")
        else:
            entries = marketplace.get("plugins")
            expected_entry = next(
                (entry for entry in entries if isinstance(entry, dict) and entry.get("name") == "project-flood"),
                None,
            ) if isinstance(entries, list) else None
            if marketplace.get("name") != "project-flood" or not isinstance(expected_entry, dict):
                errors.append(f"{marketplace_path}: Project Flood marketplace entry is missing")
            elif (
                expected_entry.get("version") != VERSION
                or expected_entry.get("source") != "."
                or expected_entry.get("strict") is not True
            ):
                errors.append(f"{marketplace_path}: Project Flood marketplace entry is stale or non-strict")
    template = root / "template"
    errors.extend(validate_configuration(template))
    _workflow_data(root / ".github/workflows/validate.yml", errors)
    _compare_directories(template / ".github/agents", root / "com.github.copilot/agents", "agents", errors)
    _compare_directories(template / ".github/skills", root / "skills", "skills", errors)
    for source, packaged, label in (
        (root / "scripts/flood.py", template / ".project-flood/flood.py", "installed CLI"),
        (root / "scripts/hook.py", template / ".project-flood/hook.py", "installed hook"),
        (root / "requirements.txt", template / ".project-flood/requirements.txt", "installed requirements"),
    ):
        if not packaged.exists() or source.read_bytes() != packaged.read_bytes():
            errors.append(f"{label}: packaged copy is stale")
    plugin_hooks = root / "com.github.copilot/hooks/hooks.json"
    try:
        hook_text = plugin_hooks.read_text(encoding="utf-8")
        hook_data = json.loads(hook_text)
        if "${PLUGIN_ROOT}" not in hook_text or not isinstance(hook_data.get("hooks"), dict):
            errors.append(f"{plugin_hooks}: plugin hooks must use `${{PLUGIN_ROOT}}`")
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{plugin_hooks}: invalid plugin hook JSON: {exc}")
    eval_path = root / "evals/cases.yaml"
    try:
        eval_data = load_yaml(eval_path)
        if not isinstance(eval_data, dict) or eval_data.get("schema_version") != SCHEMA_VERSION:
            errors.append(f"{eval_path}: unsupported evaluation schema")
        elif not isinstance(eval_data.get("cases"), list) or not eval_data["cases"]:
            errors.append(f"{eval_path}: at least one evaluation case is required")
        else:
            seen_cases: set[str] = set()
            for index, case in enumerate(eval_data["cases"], start=1):
                label = f"{eval_path}: case {index}"
                if not isinstance(case, dict):
                    errors.append(f"{label} must be a mapping")
                    continue
                case_id = case.get("id")
                if not isinstance(case_id, str) or not case_id:
                    errors.append(f"{label} requires an id")
                elif case_id in seen_cases:
                    errors.append(f"{label} duplicates id `{case_id}`")
                else:
                    seen_cases.add(case_id)
                for field in ("category", "prompt"):
                    if not isinstance(case.get(field), str) or not case[field].strip():
                        errors.append(f"{label} requires `{field}`")
                for field in ("expected", "forbidden"):
                    value = case.get(field)
                    if (
                        not isinstance(value, list)
                        or not value
                        or not all(isinstance(item, str) and item for item in value)
                    ):
                        errors.append(f"{label}: `{field}` must be a non-empty string list")
    except FloodError as exc:
        errors.append(str(exc))
    validate_links(root, errors)
    validate_secrets(root, errors)
    return errors


def source_files(source: Path, mode: str) -> dict[str, Path]:
    skipped_prefixes = (
        ".github/agents/",
        ".github/skills/",
        ".github/hooks/",
        ".project-flood/hook.py",
    )
    result: dict[str, Path] = {}
    for path in iter_files(source):
        relative = path.relative_to(source).as_posix()
        if relative == MANIFEST_PATH.as_posix():
            continue
        if mode == "adapter" and (relative == ".project-flood/hook.py" or relative.startswith(skipped_prefixes)):
            continue
        result[relative] = path
    return result


def _has_symlink_component(root: Path, relative: str | Path) -> bool:
    current = root
    for part in Path(relative).parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


def load_install_manifest(target: Path) -> dict[str, Any] | None:
    path = target / MANIFEST_PATH
    if _has_symlink_component(target, MANIFEST_PATH):
        raise FloodError(f"{path}: installation manifest must not be a symbolic link")
    if not path.exists():
        return None
    manifest = load_yaml(path)
    if not isinstance(manifest, dict) or manifest.get("schema_version") != SCHEMA_VERSION:
        raise FloodError(f"{path}: unsupported installation manifest")
    if not isinstance(manifest.get("files"), list):
        raise FloodError(f"{path}: manifest `files` must be a list")
    if manifest.get("mode") not in {"full", "adapter"}:
        raise FloodError(f"{path}: manifest mode must be `full` or `adapter`")
    if not isinstance(manifest.get("project_flood_version"), str):
        raise FloodError(f"{path}: manifest version is missing")
    seen: set[str] = set()
    for index, item in enumerate(manifest["files"], start=1):
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("path"), str)
            or not isinstance(item.get("sha256"), str)
        ):
            raise FloodError(f"{path}: file entry {index} requires string `path` and `sha256`")
        relative = Path(item["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise FloodError(f"{path}: managed path escapes the repository: {item['path']}")
        if item["path"] in seen:
            raise FloodError(f"{path}: duplicate managed path: {item['path']}")
        seen.add(item["path"])
        if not re.fullmatch(r"[0-9a-f]{64}", item["sha256"]):
            raise FloodError(f"{path}: invalid SHA-256 for {item['path']}")
    return manifest


def manifest_hashes(manifest: dict[str, Any] | None) -> dict[str, str]:
    if not manifest:
        return {}
    output: dict[str, str] = {}
    for item in manifest.get("files", []):
        if isinstance(item, dict) and isinstance(item.get("path"), str) and isinstance(item.get("sha256"), str):
            output[item["path"]] = item["sha256"]
    return output


def compare_installation(source: Path, target: Path, mode: str) -> list[dict[str, str]]:
    incoming_files = source_files(source, mode)
    incoming = {relative: sha256_file(path) for relative, path in incoming_files.items()}
    manifest = load_install_manifest(target)
    baseline = manifest_hashes(manifest)
    rows: list[dict[str, str]] = []
    for relative in sorted(set(incoming) | set(baseline)):
        if _has_symlink_component(target, relative):
            rows.append({"path": relative, "status": "unsafe-symlink"})
            continue
        destination = target / relative
        current = sha256_file(destination) if destination.is_file() else None
        old = baseline.get(relative)
        new = incoming.get(relative)
        if new is None:
            status = "remove" if current == old else "preserve-unmanaged"
        elif old is None:
            status = "new" if current is None else ("unchanged" if current == new else "conflict")
        elif current is None:
            status = "restore"
        elif current == old:
            status = "unchanged" if new == old else "update"
        elif new == old:
            status = "preserve-customized"
        else:
            status = "conflict"
        rows.append({"path": relative, "status": status})
    return rows


def _backup_paths(target: Path, relatives: Iterable[str], label: str) -> Path | None:
    paths = [relative for relative in relatives if (target / relative).is_file()]
    if not paths:
        return None
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    backup = target / ".project-flood/backups" / f"{label}-{timestamp}"
    for relative in paths:
        destination = backup / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target / relative, destination)
    return backup


def install(source: Path, target: Path, mode: str = "full", force: bool = False) -> dict[str, Any]:
    source = source.resolve()
    target = target.resolve()
    if mode not in {"full", "adapter"}:
        raise FloodError("Install mode must be `full` or `adapter`")
    if not source.is_dir() or not target.is_dir():
        raise FloodError("Source and target must both be existing directories")
    source_errors = validate_configuration(source, mode="full")
    if source_errors:
        joined = "\n".join(f"  {error}" for error in source_errors)
        raise FloodError(f"Source template is invalid:\n{joined}")
    incoming_files = source_files(source, mode)
    manifest = load_install_manifest(target)
    baseline = manifest_hashes(manifest)
    symlink_destinations = [
        relative
        for relative in set(incoming_files) | set(baseline)
        if _has_symlink_component(target, relative)
    ]
    if symlink_destinations:
        joined = "\n".join(f"  {path}" for path in sorted(symlink_destinations))
        raise FloodError(
            "No files were changed because managed destinations include symbolic links:\n"
            f"{joined}\nRemove or relocate them manually before installing."
        )
    incoming_hashes = {relative: sha256_file(path) for relative, path in incoming_files.items()}
    rows = compare_installation(source, target, mode) if manifest else []
    if not manifest:
        rows = []
        for relative, digest in sorted(incoming_hashes.items()):
            destination = target / relative
            if destination.is_file():
                status = "unchanged" if sha256_file(destination) == digest else "conflict"
            else:
                status = "new"
            rows.append({"path": relative, "status": status})
    conflicts = [row["path"] for row in rows if row["status"] == "conflict"]
    if conflicts and not force:
        joined = "\n".join(f"  {path}" for path in conflicts)
        raise FloodError(
            "No files were changed because customized destinations conflict with this version:\n"
            f"{joined}\nRun `diff`, merge manually, or use `--force` to back up and replace them."
        )

    backup_candidates = list(conflicts)
    backup_candidates.extend(row["path"] for row in rows if row["status"] == "remove")
    backup = _backup_paths(target, backup_candidates, "upgrade")

    preserved = {row["path"] for row in rows if row["status"] in {"preserve-customized", "preserve-unmanaged"}}
    removed: list[str] = []
    for row in rows:
        relative = row["path"]
        status = row["status"]
        if status == "remove":
            destination = target / relative
            if destination.is_file():
                destination.unlink()
                removed.append(relative)
            continue
        if relative not in incoming_files or relative in preserved:
            continue
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(incoming_files[relative], destination)

    manifest_value = {
        "schema_version": SCHEMA_VERSION,
        "project_flood_version": VERSION,
        "mode": mode,
        "installed_at": datetime.now(timezone.utc).isoformat(),
        "files": [
            {"path": relative, "sha256": digest}
            for relative, digest in sorted(incoming_hashes.items())
        ],
        "preserved_unmanaged": sorted(
            row["path"] for row in rows if row["status"] == "preserve-unmanaged"
        ),
    }
    write_yaml(target / MANIFEST_PATH, manifest_value)
    (target / ".agent-team/runtime").mkdir(parents=True, exist_ok=True)
    (target / ".agent-team/scratch").mkdir(parents=True, exist_ok=True)
    return {
        "mode": mode,
        "version": VERSION,
        "conflicts_replaced": conflicts if force else [],
        "preserved": sorted(preserved),
        "removed": removed,
        "backup": str(backup) if backup else None,
    }


def installation_drift(target: Path) -> list[dict[str, str]]:
    manifest = load_install_manifest(target)
    if not manifest:
        return [{"path": MANIFEST_PATH.as_posix(), "status": "missing-manifest"}]
    rows: list[dict[str, str]] = []
    for relative, baseline in sorted(manifest_hashes(manifest).items()):
        path = target / relative
        if relative == ".project-flood/.gitignore":
            preserved.append(relative)
            continue
        if _has_symlink_component(target, relative):
            rows.append({"path": relative, "status": "unsafe-symlink"})
        elif not path.is_file():
            rows.append({"path": relative, "status": "missing"})
        elif sha256_file(path) != baseline:
            rows.append({"path": relative, "status": "customized"})
    return rows


def uninstall(target: Path, apply: bool = False) -> dict[str, Any]:
    target = target.resolve()
    manifest = load_install_manifest(target)
    if not manifest:
        raise FloodError("Project Flood is not manifest-managed in this repository")
    removable: list[str] = []
    preserved: list[str] = []
    for relative, baseline in sorted(manifest_hashes(manifest).items()):
        path = target / relative
        if _has_symlink_component(target, relative):
            preserved.append(relative)
            continue
        if not path.is_file():
            continue
        if sha256_file(path) == baseline:
            removable.append(relative)
        else:
            preserved.append(relative)
    if not apply:
        return {"dry_run": True, "would_remove": removable, "would_preserve": preserved}
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    backup = target / ".project-flood/backups" / f"uninstall-{timestamp}"
    for relative in removable:
        source = target / relative
        destination = backup / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))
    manifest_target = backup / MANIFEST_PATH
    manifest_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(target / MANIFEST_PATH), str(manifest_target))
    return {"dry_run": False, "removed": removable, "preserved": preserved, "backup": str(backup)}


def doctor(root: Path) -> tuple[list[str], list[str]]:
    errors = validate_configuration(root, require_manifest=(root / MANIFEST_PATH).exists(), mode="auto")
    warnings: list[str] = []
    for row in installation_drift(root):
        if row["status"] == "customized":
            warnings.append(f"Framework-managed file customized: {row['path']}")
        elif row["status"] == "missing":
            errors.append(f"Framework-managed file missing: {row['path']}")
        elif row["status"] == "unsafe-symlink":
            errors.append(f"Framework-managed path contains a symbolic link: {row['path']}")
        elif row["status"] == "missing-manifest":
            warnings.append("No install manifest; run `migrate` for a v0.1 installation")
    if shutil.which("git") is None:
        warnings.append("Git is not available; worktree swarms cannot run")
    manifest = load_install_manifest(root)
    if manifest and manifest.get("mode") == "adapter":
        warnings.append("Adapter mode cannot prove that the Project Flood plugin is installed and enabled")
    task_state = task_manifest_status(root)
    if task_state["manifest"] is None:
        warnings.append("No active task manifest; ownership enforcement is currently advisory")
    elif task_state["source"] == "git-common-dir":
        errors.extend(validate_task_manifest_data(task_state["manifest"], str(task_state["path"])))
        if task_state["manifest"].get("status") != "active":
            warnings.append("Shared task manifest is not active; ownership enforcement is advisory")
    else:
        state = task_state["manifest"].get("status", "unknown")
        warnings.append(f"Worktree-local task manifest is `{state}` and not published to the Git common directory")
    return errors, warnings


def print_rows(rows: Iterable[dict[str, str]]) -> None:
    for row in rows:
        print(f"{row['status']:22} {row['path']}")


def _default_template_source() -> Path | None:
    script = Path(__file__).resolve()
    if script.parent.name == "scripts":
        return script.parents[1] / "template"
    return None


def _require_source(value: Path | None) -> Path:
    if value is None:
        raise FloodError(
            "`--source /path/to/Project-Flood/template` is required when running the installed CLI"
        )
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="flood", description="Manage Project Flood v0.2")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate a configured repository")
    validate_parser.add_argument("--root", type=Path, default=Path.cwd())
    validate_parser.add_argument("--distribution", action="store_true")
    validate_parser.add_argument("--mode", choices=("auto", "full", "adapter"), default="auto")

    index_parser = subparsers.add_parser("memory-index", help="Generate or check the memory index")
    index_parser.add_argument("--root", type=Path, default=Path.cwd())
    index_parser.add_argument("--check", action="store_true")

    doctor_parser = subparsers.add_parser("doctor", help="Diagnose configuration and install drift")
    doctor_parser.add_argument("--root", type=Path, default=Path.cwd())

    for name in ("install", "upgrade"):
        install_parser = subparsers.add_parser(name, help=f"{name.title()} Project Flood files")
        install_parser.add_argument("--source", type=Path, default=_default_template_source())
        install_parser.add_argument("--target", type=Path, required=True)
        install_parser.add_argument("--mode", choices=("full", "adapter"), default="full")
        install_parser.add_argument("--force", action="store_true")

    diff_parser = subparsers.add_parser("diff", help="Preview an install or upgrade")
    diff_parser.add_argument("--source", type=Path, default=_default_template_source())
    diff_parser.add_argument("--target", type=Path, required=True)
    diff_parser.add_argument("--mode", choices=("full", "adapter"), default="full")

    migrate_parser = subparsers.add_parser("migrate", help="Migrate a legacy v0.1 installation")
    migrate_parser.add_argument("--source", type=Path, default=_default_template_source())
    migrate_parser.add_argument("--target", type=Path, required=True)
    migrate_parser.add_argument("--apply", action="store_true")
    migrate_parser.add_argument("--mode", choices=("full", "adapter"), default="full")

    uninstall_parser = subparsers.add_parser("uninstall", help="Remove unchanged managed files recoverably")
    uninstall_parser.add_argument("--root", type=Path, default=Path.cwd())
    uninstall_parser.add_argument("--yes", action="store_true", help="Apply; default is a dry run")

    task_parser = subparsers.add_parser("task-validate", help="Validate a runtime task manifest")
    task_parser.add_argument("--root", type=Path, default=Path.cwd())
    task_parser.add_argument("--file", type=Path)

    activate_parser = subparsers.add_parser("task-activate", help="Publish an active task lease to all worktrees")
    activate_parser.add_argument("--root", type=Path, default=Path.cwd())

    status_parser = subparsers.add_parser("task-status", help="Show shared or local task state")
    status_parser.add_argument("--root", type=Path, default=Path.cwd())

    close_parser = subparsers.add_parser("task-close", help="Close and archive the shared task lease")
    close_parser.add_argument("--root", type=Path, default=Path.cwd())
    close_parser.add_argument("--status", choices=("complete", "cancelled"), required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            errors = (
                validate_distribution(args.root)
                if args.distribution
                else validate_configuration(args.root, mode=args.mode)
            )
            if errors:
                print(f"Project Flood validation failed with {len(errors)} error(s):", file=sys.stderr)
                for error in errors:
                    print(f"- {error}", file=sys.stderr)
                return 1
            scope = "distribution" if args.distribution else "configuration"
            print(f"Project Flood {scope} is valid for v{VERSION}.")
            return 0
        if args.command == "memory-index":
            expected = build_memory_index(args.root)
            path = args.root / ".agent-team/memory/memory-index.yaml"
            if args.check:
                actual = load_yaml(path) if path.exists() else None
                if _portable(actual) != _portable(expected):
                    print("Memory index is stale.", file=sys.stderr)
                    return 1
                print("Memory index is current.")
            else:
                write_yaml(path, expected)
                print(f"Wrote {path} with {len(expected['records'])} record(s).")
            return 0
        if args.command == "doctor":
            errors, warnings = doctor(args.root.resolve())
            for warning in warnings:
                print(f"WARN  {warning}")
            for error in errors:
                print(f"ERROR {error}")
            if errors:
                return 1
            print(f"Project Flood doctor passed with {len(warnings)} warning(s).")
            return 0
        if args.command in {"install", "upgrade"}:
            report = install(_require_source(args.source), args.target, args.mode, args.force)
            print(json.dumps(report, indent=2))
            return 0
        if args.command == "diff":
            print_rows(compare_installation(_require_source(args.source).resolve(), args.target.resolve(), args.mode))
            return 0
        if args.command == "migrate":
            version_path = args.target / ".project-flood/VERSION"
            legacy_version = version_path.read_text(encoding="utf-8").strip() if version_path.exists() else "unknown"
            if (args.target / MANIFEST_PATH).exists():
                raise FloodError("This installation already has a v0.2 manifest; use `upgrade`")
            if not args.apply:
                print(f"Legacy version detected: {legacy_version}")
                found = [path for path in LEGACY_PATHS if (args.target / path).is_file()]
                if found:
                    print("Legacy files that will be backed up and removed:")
                    for path in found:
                        print(f"  {path}")
                print("Dry run only. Re-run with `--apply` to back up conflicts and install v0.2.")
                return 0
            source = _require_source(args.source)
            source_errors = validate_configuration(source, mode="full")
            if source_errors:
                joined = "\n".join(f"  {error}" for error in source_errors)
                raise FloodError(f"Source template is invalid:\n{joined}")
            legacy_files = [path for path in LEGACY_PATHS if (args.target / path).is_file()]
            legacy_backup = _backup_paths(args.target.resolve(), legacy_files, "migration-v0.1")
            for relative in legacy_files:
                (args.target / relative).unlink()
            report = install(source, args.target, args.mode, force=True)
            report["migrated_from"] = legacy_version
            report["legacy_removed"] = legacy_files
            report["legacy_backup"] = str(legacy_backup) if legacy_backup else None
            print(json.dumps(report, indent=2))
            return 0
        if args.command == "uninstall":
            print(json.dumps(uninstall(args.root, args.yes), indent=2))
            return 0
        if args.command == "task-validate":
            path = args.file or args.root / TASK_MANIFEST_PATH
            data = json.loads(path.read_text(encoding="utf-8"))
            errors = validate_task_manifest_data(data, str(path))
            if errors:
                for error in errors:
                    print(f"- {error}", file=sys.stderr)
                return 1
            print(f"Task manifest is valid: {path}")
            return 0
        if args.command == "task-activate":
            print(json.dumps(activate_task_manifest(args.root), indent=2))
            return 0
        if args.command == "task-status":
            print(json.dumps(task_manifest_status(args.root), indent=2))
            return 0
        if args.command == "task-close":
            print(json.dumps(close_task_manifest(args.root, args.status), indent=2))
            return 0
    except (FloodError, OSError, json.JSONDecodeError) as exc:
        print(f"Project Flood error: {exc}", file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

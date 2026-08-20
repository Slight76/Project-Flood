#!/usr/bin/env python3
"""Validate a Project Flood configuration using only the Python standard library."""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path


REQUIRED_PATHS = (
    "AGENTS.md",
    ".github/copilot-instructions.md",
    ".github/agents/squad-lead.agent.md",
    ".agent-team/README.md",
    ".agent-team/charter.md",
    ".agent-team/project-profile.md",
    ".agent-team/routing.md",
    ".agent-team/decisions.md",
    ".agent-team/now.md",
    ".agent-team/schemas/handoff.md",
    ".agent-team/schemas/memory-candidate.md",
    ".agent-team/schemas/orchestration-entry.md",
    ".project-flood/VERSION",
)

EXPECTED_AGENT_NAMES = {
    "Squad Lead",
    "Scout",
    "Architect",
    "Builder",
    "Verifier",
    "Security Reviewer",
    "Librarian",
    "Swarm Analyst",
}

ROLE_HISTORY_SLUGS = {
    "Scout": "scout",
    "Architect": "architect",
    "Builder": "builder",
    "Verifier": "verifier",
    "Security Reviewer": "security-reviewer",
    "Librarian": "librarian",
    "Swarm Analyst": "swarm-analyst",
}

SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
SECRET_PATTERNS = {
    "GitHub personal access token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "OpenAI API key": re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}


def parse_frontmatter(path: Path) -> tuple[dict[str, str], str, list[str]]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text, [f"{path}: missing opening YAML frontmatter delimiter"]

    try:
        closing_index = next(index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration:
        return {}, text, [f"{path}: missing closing YAML frontmatter delimiter"]

    fields: dict[str, str] = {}
    for line in lines[1:closing_index]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            errors.append(f"{path}: malformed frontmatter line: {stripped}")
            continue
        key, value = stripped.split(":", 1)
        fields[key.strip()] = value.strip()

    body = "\n".join(lines[closing_index + 1 :])
    return fields, body, errors


def scalar(value: str | None) -> str:
    if value is None:
        return ""
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def inline_list(value: str | None, path: Path, field: str, errors: list[str]) -> list[str]:
    if value is None:
        errors.append(f"{path}: missing `{field}` frontmatter field")
        return []
    try:
        parsed = ast.literal_eval(value)
    except (SyntaxError, ValueError):
        errors.append(f"{path}: `{field}` must be an inline quoted list")
        return []
    if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
        errors.append(f"{path}: `{field}` must contain only strings")
        return []
    return parsed


def validate_agents(root: Path, errors: list[str]) -> None:
    agent_dir = root / ".github" / "agents"
    if not agent_dir.is_dir():
        errors.append(f"{agent_dir}: agent directory is missing")
        return

    names: dict[str, Path] = {}
    parsed_agents: dict[str, tuple[Path, dict[str, str]]] = {}
    for path in sorted(agent_dir.glob("*.agent.md")):
        fields, body, parse_errors = parse_frontmatter(path)
        errors.extend(parse_errors)
        name = scalar(fields.get("name"))
        description = scalar(fields.get("description"))
        if not name:
            errors.append(f"{path}: missing agent name")
        elif name in names:
            errors.append(f"Duplicate agent name `{name}` in {names[name]} and {path}")
        else:
            names[name] = path
            parsed_agents[name] = (path, fields)
        if not description:
            errors.append(f"{path}: missing agent description")
        if not body.strip():
            errors.append(f"{path}: agent instructions are empty")
        tools = inline_list(fields.get("tools"), path, "tools", errors)
        inline_list(fields.get("agents"), path, "agents", errors)
        expected_invocable = "true" if name == "Squad Lead" else "false"
        if scalar(fields.get("user-invocable")).lower() != expected_invocable:
            errors.append(f"{path}: `user-invocable` must be {expected_invocable} for `{name}`")
        if name in {"Scout", "Architect", "Verifier", "Security Reviewer", "Swarm Analyst"} and "edit" in tools:
            errors.append(f"{path}: read-only agent `{name}` must not include the `edit` tool set")
        if name == "Builder" and not {"edit", "execute"}.issubset(tools):
            errors.append(f"{path}: Builder must include `edit` and `execute` tool sets")
        if name == "Librarian" and ("edit" not in tools or "execute" in tools):
            errors.append(f"{path}: Librarian must include `edit` and omit `execute`")

    missing = EXPECTED_AGENT_NAMES - set(names)
    extra = set(names) - EXPECTED_AGENT_NAMES
    if missing:
        errors.append(f"Missing expected agents: {', '.join(sorted(missing))}")
    if extra:
        errors.append(f"Unexpected agents require contract review: {', '.join(sorted(extra))}")

    lead = parsed_agents.get("Squad Lead")
    if lead:
        lead_path, fields = lead
        tools = inline_list(fields.get("tools"), lead_path, "tools", errors)
        allowed_agents = inline_list(fields.get("agents"), lead_path, "agents", errors)
        if "agent" not in tools:
            errors.append(f"{lead_path}: Squad Lead must include the `agent` tool set")
        unknown = set(allowed_agents) - EXPECTED_AGENT_NAMES
        missing_specialists = (EXPECTED_AGENT_NAMES - {"Squad Lead"}) - set(allowed_agents)
        if unknown:
            errors.append(f"{lead_path}: references unknown subagents: {', '.join(sorted(unknown))}")
        if missing_specialists:
            errors.append(f"{lead_path}: does not allow specialists: {', '.join(sorted(missing_specialists))}")

    for role_name, slug in ROLE_HISTORY_SLUGS.items():
        history = root / ".agent-team" / "roles" / slug / "history.md"
        if not history.exists():
            errors.append(f"Missing role history for {role_name}: {history.relative_to(root)}")


def validate_skills(root: Path, errors: list[str]) -> None:
    skills_dir = root / ".github" / "skills"
    if not skills_dir.is_dir():
        errors.append(f"{skills_dir}: skills directory is missing")
        return

    found = 0
    names: set[str] = set()
    for skill_file in sorted(skills_dir.glob("*/SKILL.md")):
        found += 1
        fields, body, parse_errors = parse_frontmatter(skill_file)
        errors.extend(parse_errors)
        name = scalar(fields.get("name"))
        description = scalar(fields.get("description"))
        folder_name = skill_file.parent.name
        if not name:
            errors.append(f"{skill_file}: missing skill name")
        else:
            if name != folder_name:
                errors.append(f"{skill_file}: skill name `{name}` must match its directory `{folder_name}`")
            if not SKILL_NAME_PATTERN.fullmatch(name):
                errors.append(f"{skill_file}: skill name `{name}` is invalid")
            if name in names:
                errors.append(f"{skill_file}: duplicate skill name `{name}`")
            names.add(name)
        if not description:
            errors.append(f"{skill_file}: missing skill description")
        elif len(description) > 1024:
            errors.append(f"{skill_file}: skill description exceeds 1024 characters")
        if not body.strip():
            errors.append(f"{skill_file}: skill instructions are empty")

    if found == 0:
        errors.append(f"{skills_dir}: no skills found")


def validate_instructions(root: Path, errors: list[str]) -> None:
    instructions_dir = root / ".github" / "instructions"
    if not instructions_dir.is_dir():
        errors.append(f"{instructions_dir}: instructions directory is missing")
        return
    for path in sorted(instructions_dir.glob("*.instructions.md")):
        fields, body, parse_errors = parse_frontmatter(path)
        errors.extend(parse_errors)
        if not scalar(fields.get("description")):
            errors.append(f"{path}: missing instruction description")
        if not scalar(fields.get("applyTo")):
            errors.append(f"{path}: missing `applyTo` glob")
        if not body.strip():
            errors.append(f"{path}: instruction body is empty")


def validate_prompts(root: Path, errors: list[str]) -> None:
    prompts_dir = root / ".github" / "prompts"
    if not prompts_dir.is_dir():
        errors.append(f"{prompts_dir}: prompts directory is missing")
        return
    found = 0
    for path in sorted(prompts_dir.glob("*.prompt.md")):
        found += 1
        fields, body, parse_errors = parse_frontmatter(path)
        errors.extend(parse_errors)
        if not scalar(fields.get("description")):
            errors.append(f"{path}: missing prompt description")
        agent = scalar(fields.get("agent"))
        if agent not in EXPECTED_AGENT_NAMES:
            errors.append(f"{path}: prompt references unknown agent `{agent}`")
        if not body.strip():
            errors.append(f"{path}: prompt body is empty")
    if found == 0:
        errors.append(f"{prompts_dir}: no prompt files found")


def validate_links(root: Path, errors: list[str]) -> None:
    for path in sorted(root.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        for target in LINK_PATTERN.findall(text):
            target = target.strip().split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:", "sandbox:")):
                continue
            resolved = (path.parent / target).resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                errors.append(f"{path}: local link escapes configuration root: {target}")
                continue
            if not resolved.exists():
                errors.append(f"{path}: broken local link: {target}")


def validate_secrets(root: Path, errors: list[str]) -> None:
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{path}: possible {label} detected")


def validate(root: Path) -> list[str]:
    root = root.resolve()
    errors: list[str] = []

    for relative_path in REQUIRED_PATHS:
        path = root / relative_path
        if not path.exists():
            errors.append(f"Missing required path: {relative_path}")

    validate_agents(root, errors)
    validate_skills(root, errors)
    validate_instructions(root, errors)
    validate_prompts(root, errors)
    validate_links(root, errors)
    validate_secrets(root, errors)

    scratch_ignore = root / ".agent-team" / ".gitignore"
    if scratch_ignore.exists() and "scratch/*" not in scratch_ignore.read_text(encoding="utf-8"):
        errors.append(f"{scratch_ignore}: scratch directory must be ignored")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Project Flood Copilot configuration")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Configured repository root")
    args = parser.parse_args()

    errors = validate(args.root)
    if errors:
        print(f"Project Flood validation failed with {len(errors)} error(s):", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    agent_count = len(list((args.root / ".github" / "agents").glob("*.agent.md")))
    skill_count = len(list((args.root / ".github" / "skills").glob("*/SKILL.md")))
    print(f"Project Flood configuration is valid: {agent_count} agents, {skill_count} skills.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

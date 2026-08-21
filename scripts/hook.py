#!/usr/bin/env python3
"""Deterministic Project Flood hook policy for VS Code/Copilot agent sessions."""

from __future__ import annotations

import fnmatch
import hashlib
import json
import re
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # Baseline controls remain active without optional policy parsing.
    yaml = None


DEFAULT_POLICY: dict[str, Any] = {
    "schema_version": 1,
    "controls": {
        "dangerous_commands": "deny",
        "protected_paths": "ask",
        "ownership_violations": "deny",
        "external_writes": "ask",
        "outside_workspace_writes": "ask",
        "unverifiable_writes": "ask",
        "unlisted_external_tools": "ask",
        "shared_task_state": "deny",
    },
    "protected_paths": [
        "AGENTS.md",
        ".github/CODEOWNERS",
        ".github/copilot-instructions.md",
        ".github/copilot/settings.json",
        ".github/instructions/**",
        ".github/hooks/**",
        ".github/agents/**",
        ".github/prompts/**",
        ".github/skills/**",
        ".github/workflows/copilot-config-validation.yml",
        ".github/workflows/copilot-setup-steps.yml",
        ".agent-team/README.md",
        ".agent-team/.gitignore",
        ".agent-team/charter.md",
        ".agent-team/project-profile.md",
        ".agent-team/routing.md",
        ".agent-team/now.md",
        ".agent-team/harnesses.md",
        ".agent-team/decisions.md",
        ".agent-team/archive/**",
        ".agent-team/memory/**",
        ".agent-team/orchestration/**",
        ".agent-team/roles/**",
        ".agent-team/schemas/**",
        ".project-flood/**",
    ],
    "external_write_tools": [
        "push",
        "commitfiles",
        "createpullrequest",
        "mergepullrequest",
        "createfile",
        "updatefile",
        "deletefile",
        "createissue",
        "updateissue",
        "createcomment",
        "addcomment",
        "deploy",
        "publish",
        "upload",
        "sendmessage",
    ],
    "built_in_tool_prefixes": ["agent", "edit", "execute", "read", "search", "todo", "vscode", "web"],
    "allowed_external_tool_prefixes": [],
    "dangerous_commands": [
        {
            "id": "recursive-force-delete",
            "pattern": (
                r"(?:^|\s)(?:sudo\s+)?rm\b"
                r"(?=[^\r\n]*(?:--recursive\b|-[^\s]*r))"
                r"(?=[^\r\n]*(?:--force\b|-[^\s]*f))"
            ),
        },
        {
            "id": "powershell-recursive-force-delete",
            "pattern": r"remove-item\b(?=[^\r\n]*-(?:recurse|r)\b)(?=[^\r\n]*-(?:force|fo)\b)",
        },
        {"id": "hard-reset", "pattern": r"git\s+reset\s+--hard\b"},
        {
            "id": "destructive-clean",
            "pattern": (
                r"git\s+clean\b"
                r"(?=[^\r\n]*(?:-[^\s]*[dx]|--ignored\b|--directories\b))"
                r"(?=[^\r\n]*(?:-[^\s]*f|--force\b))"
            ),
        },
        {"id": "drop-database", "pattern": r"drop\s+(?:database|schema)\b"},
        {"id": "terraform-destroy", "pattern": r"terraform\s+destroy\b"},
        {"id": "disk-overwrite", "pattern": r"(?:^|\s)dd\s+[^\r\n]*\bof=/dev/"},
    ],
}

MUTATING_TOOL_WORDS = ("edit", "write", "createfile", "deletefile", "movefile", "renamefile", "applypatch")
COMMAND_TOOL_WORDS = ("terminal", "execute", "shell", "bash", "powershell", "command")
PATH_KEYS = {
    "path",
    "paths",
    "file",
    "files",
    "filename",
    "filepath",
    "filepaths",
    "uri",
    "target",
    "targetpath",
    "destination",
    "destinationpath",
    "oldpath",
    "oldfilepath",
    "newpath",
    "newfilepath",
}
COMMAND_KEYS = {"command", "cmd", "script", "shellcommand"}


def _display(value: Any, limit: int = 160) -> str:
    text = re.sub(r"[\x00-\x1f\x7f]+", " ", str(value)).strip()
    return text[:limit]


def _merge_policy(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in overlay.items():
        if key == "controls":
            if isinstance(value, dict):
                safe_controls = {
                    name: choice
                    for name, choice in value.items()
                    if choice in {"allow", "deny", "ask"}
                }
                merged[key] = {**base.get(key, {}), **safe_controls}
        elif key in {
            "protected_paths",
            "external_write_tools",
            "built_in_tool_prefixes",
            "allowed_external_tool_prefixes",
        } and isinstance(value, list):
            safe_items = [item for item in value if isinstance(item, str)]
            if not value or safe_items:
                merged[key] = safe_items
        elif key == "dangerous_commands" and isinstance(value, list):
            safe_commands = []
            for item in value:
                if not isinstance(item, dict) or not isinstance(item.get("pattern"), str):
                    continue
                try:
                    re.compile(item["pattern"])
                except re.error:
                    continue
                safe_commands.append(item)
            if not value or safe_commands:
                merged[key] = safe_commands
    return merged


def _has_symlink_component(root: Path, relative: str | Path) -> bool:
    current = root
    for part in Path(relative).parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


def load_policy(root: Path) -> dict[str, Any]:
    path = root / ".project-flood/policy.yaml"
    if _has_symlink_component(root, ".project-flood/policy.yaml") or not path.is_file() or yaml is None:
        return DEFAULT_POLICY
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return DEFAULT_POLICY
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        return DEFAULT_POLICY
    return _merge_policy(DEFAULT_POLICY, value)


def project_flood_active(root: Path) -> bool:
    markers = (".project-flood/policy.yaml", ".agent-team/charter.md")
    return all(
        not _has_symlink_component(root, marker) and (root / marker).is_file()
        for marker in markers
    )


def find_project_root(start: Path) -> Path | None:
    resolved = start.resolve()
    for candidate in (resolved, *resolved.parents):
        if project_flood_active(candidate):
            return candidate
    return None


def git_common_dir(root: Path) -> Path | None:
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
        git_dir = Path(marker.split(":", 1)[1].strip())
        if not git_dir.is_absolute():
            git_dir = root / git_dir
        if git_dir.is_symlink():
            return None
        git_dir = git_dir.resolve()
        common_marker = git_dir / "commondir"
        if common_marker.is_file() and not common_marker.is_symlink():
            common_dir = Path(common_marker.read_text(encoding="utf-8").strip())
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


def task_manifest_path(root: Path) -> Path:
    common_dir = git_common_dir(root)
    if common_dir:
        shared = common_dir / "project-flood/task-manifest.json"
        if shared.exists() or shared.is_symlink():
            return shared
    return root / ".agent-team/runtime/task-manifest.json"


def _walk_values(value: Any, wanted_keys: set[str]) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in wanted_keys:
                if isinstance(item, str):
                    found.append(item)
                elif isinstance(item, list):
                    found.extend(entry for entry in item if isinstance(entry, str))
            found.extend(_walk_values(item, wanted_keys))
    elif isinstance(value, list):
        for item in value:
            found.extend(_walk_values(item, wanted_keys))
    return found


def _relative_path(raw: str, root: Path, working_directory: Path | None = None) -> str | None:
    if raw.startswith(("http://", "https://", "git@")):
        return None
    if raw.startswith("file://"):
        parsed = urllib.parse.urlparse(raw)
        raw = urllib.parse.unquote(parsed.path)
    candidate = Path(raw)
    try:
        base = working_directory or root
        resolved = candidate.resolve() if candidate.is_absolute() else (base / candidate).resolve()
        return resolved.relative_to(root.resolve()).as_posix()
    except (OSError, ValueError):
        return "../outside-workspace"


def _decision(event: str, choice: str, reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": event,
            "permissionDecision": choice,
            "permissionDecisionReason": reason,
        }
    }


def _external_tool_prefix(tool_name: str) -> str | None:
    lowered = tool_name.lower()
    if "/" in lowered:
        return lowered.split("/", 1)[0]
    if lowered.startswith("mcp__"):
        parts = lowered.split("__")
        return parts[1] if len(parts) > 2 and parts[1] else "mcp"
    if lowered.startswith("mcp."):
        parts = lowered.split(".")
        return parts[1] if len(parts) > 2 and parts[1] else "mcp"
    return None


def _session_key(session_id: str | None) -> str:
    if not session_id:
        return "unknown"
    return hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:12]


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


def _manifest_is_safe(manifest: dict[str, Any]) -> bool:
    if manifest.get("mode") not in {"squad", "research-swarm", "build-swarm", "review-swarm"}:
        return False
    if not re.fullmatch(r"[0-9a-f]{12}", str(manifest.get("coordinator_session_key", ""))):
        return False
    if not re.fullmatch(r"[0-9a-fA-F]{7,64}", str(manifest.get("base_commit", ""))):
        return False
    workers = manifest.get("workers")
    if not isinstance(workers, list):
        return False
    session_keys: set[str] = set()
    worker_ids: set[str] = set()
    branches: set[str] = set()
    worktrees: set[str] = set()
    active_waves: dict[int, int] = {}
    owners: list[tuple[str, str]] = []
    read_only_roles = {
        "Flood Scout",
        "Flood Architect",
        "Flood Verifier",
        "Flood Security Reviewer",
        "Flood Swarm Analyst",
    }
    for worker in workers:
        if not isinstance(worker, dict) or worker.get("status") != "active":
            continue
        worker_id = worker.get("id")
        session_key = worker.get("session_key")
        wave = worker.get("wave")
        paths = worker.get("write_paths")
        if not isinstance(worker_id, str) or not worker_id or worker_id in worker_ids:
            return False
        worker_ids.add(worker_id)
        if not isinstance(session_key, str) or not re.fullmatch(r"[0-9a-f]{12}", session_key):
            return False
        if session_key in session_keys or session_key == manifest["coordinator_session_key"]:
            return False
        session_keys.add(session_key)
        if not isinstance(wave, int) or wave < 1:
            return False
        active_waves[wave] = active_waves.get(wave, 0) + 1
        if active_waves[wave] > 3:
            return False
        if not isinstance(paths, list) or not all(isinstance(path, str) and path for path in paths):
            return False
        for path in paths:
            candidate = Path(path)
            if candidate.is_absolute() or ".." in candidate.parts or not _valid_write_pattern(path):
                return False
            owners.append((worker_id, path))
        if worker.get("role") in read_only_roles and paths:
            return False
        if manifest.get("mode") in {"research-swarm", "review-swarm"} and paths:
            return False
        if manifest.get("mode") == "build-swarm":
            if worker.get("role") not in {"Flood Builder", "Flood Integrator"}:
                return False
            for field, seen in (("branch", branches), ("worktree", worktrees)):
                value = worker.get(field)
                if not isinstance(value, str) or not value or value in seen:
                    return False
                seen.add(value)
    for index, (left_owner, left_path) in enumerate(owners):
        for right_owner, right_path in owners[index + 1 :]:
            if left_owner != right_owner and _patterns_overlap(left_path, right_path):
                return False
    return True


def audit(root: Path, payload: dict[str, Any], decision: str, reason_code: str) -> None:
    runtime = root / ".agent-team/runtime"
    if _has_symlink_component(root, ".agent-team/runtime"):
        return
    try:
        runtime.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": payload.get("timestamp") or datetime.now(timezone.utc).isoformat(),
            "event": payload.get("hook_event_name", "unknown"),
            "session": _session_key(payload.get("session_id")),
            "tool": _display(payload.get("tool_name", "unknown"), 80),
            "decision": decision,
            "reason_code": reason_code,
        }
        with (runtime / "hook-audit.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(entry, separators=(",", ":")) + "\n")
    except OSError:
        pass


def _active_worker(root: Path, session_id: str | None) -> tuple[dict[str, Any] | None, bool]:
    path = task_manifest_path(root)
    local_path = path == root / ".agent-team/runtime/task-manifest.json"
    if path.is_symlink() or path.parent.is_symlink() or (
        local_path and _has_symlink_component(root, ".agent-team/runtime/task-manifest.json")
    ):
        return None, True
    if not path.is_file():
        return None, False
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, True
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        return None, True
    if manifest.get("status") != "active":
        return None, False
    expires = manifest.get("expires_at")
    if isinstance(expires, str):
        try:
            expiry = datetime.fromisoformat(expires.replace("Z", "+00:00"))
            if expiry.tzinfo is None or expiry < datetime.now(timezone.utc):
                return None, True
        except (ValueError, TypeError):
            return None, True
    else:
        return None, True
    if not _manifest_is_safe(manifest):
        return None, True
    session_key = _session_key(session_id)
    if session_id and manifest.get("coordinator_session_key") == session_key:
        return {
            "id": "coordinator",
            "role": "Flood Squad Lead",
            "write_paths": [".agent-team/runtime/**"],
        }, True
    workers = manifest["workers"]
    for worker in workers:
        if not isinstance(worker, dict) or worker.get("status") != "active":
            continue
        if session_id and worker.get("session_key") == session_key:
            return worker, True
    return None, True


def pre_tool_use(payload: dict[str, Any], root: Path) -> dict[str, Any]:
    policy = load_policy(root)
    controls = policy.get("controls", {})
    tool_name = str(payload.get("tool_name", ""))
    if not tool_name:
        choice = "ask"
        audit(root, payload, choice, "missing-tool-name")
        return _decision("PreToolUse", choice, "Project Flood could not identify the requested tool.")
    normalized_tool = re.sub(r"[^a-z0-9/]", "", tool_name.lower())
    tool_input = payload.get("tool_input", {})
    mutating = any(word in normalized_tool for word in MUTATING_TOOL_WORDS)
    prefix = _external_tool_prefix(tool_name)
    built_in = {str(item).lower() for item in policy.get("built_in_tool_prefixes", [])}
    allowed = {str(item).lower() for item in policy.get("allowed_external_tool_prefixes", [])}
    unlisted_external = prefix is not None and prefix not in built_in and prefix not in allowed
    external_write = prefix is not None and any(
        word in normalized_tool for word in policy.get("external_write_tools", [])
    )

    if any(word in normalized_tool for word in COMMAND_TOOL_WORDS):
        commands = [tool_input] if isinstance(tool_input, str) else _walk_values(tool_input, COMMAND_KEYS)
        for command in commands:
            normalized_command = command.replace("\\", "/").lower()
            if "project-flood/task-manifest.json" in normalized_command:
                choice = controls.get("shared_task_state", "deny")
                audit(root, payload, choice, "shared-task-state")
                return _decision(
                    "PreToolUse",
                    choice,
                    "Use Project Flood task commands instead of modifying the shared lease directly.",
                )
        for item in policy.get("dangerous_commands", []):
            if not isinstance(item, dict) or not isinstance(item.get("pattern"), str):
                continue
            if any(re.search(item["pattern"], command, flags=re.IGNORECASE) for command in commands):
                choice = controls.get("dangerous_commands", "deny")
                rule_id = _display(item.get("id", "unnamed"), 80)
                reason = f"Blocked by Project Flood dangerous-command policy ({rule_id})."
                audit(root, payload, choice, "dangerous-command")
                return _decision("PreToolUse", choice, reason)

    if external_write and not mutating:
        choice = controls.get("external_writes", "ask")
        audit(root, payload, choice, "external-write")
        return _decision("PreToolUse", choice, "External write requires explicit user confirmation.")

    if unlisted_external and not mutating:
        choice = controls.get("unlisted_external_tools", "ask")
        audit(root, payload, choice, "unlisted-external-tool")
        safe_prefix = _display(prefix, 80)
        return _decision(
            "PreToolUse",
            choice,
            f"Tool prefix `{safe_prefix}` is not on the repository allowlist.",
        )

    if mutating:
        working_directory = root
        try:
            candidate_cwd = Path(str(payload.get("cwd", root))).resolve()
            candidate_cwd.relative_to(root)
            working_directory = candidate_cwd
        except (OSError, ValueError):
            pass
        raw_paths = _walk_values(tool_input, PATH_KEYS)
        paths = [
            relative
            for raw in raw_paths
            if (relative := _relative_path(raw, root, working_directory)) is not None
        ]
        worker, manifest_active = _active_worker(root, payload.get("session_id"))
        if manifest_active:
            if worker is None:
                choice = "ask" if not payload.get("session_id") else controls.get("ownership_violations", "deny")
                audit(root, payload, choice, "unregistered-session")
                return _decision("PreToolUse", choice, "Active task ownership does not include this session.")
            allowed_paths = worker.get("write_paths", [])
            if not paths:
                choice = controls.get("ownership_violations", "deny")
                audit(root, payload, choice, "unverifiable-write-scope")
                return _decision(
                    "PreToolUse",
                    choice,
                    "The edit tool did not expose a path that ownership policy can verify.",
                )
            for path in paths:
                if not any(fnmatch.fnmatch(path, pattern) for pattern in allowed_paths):
                    choice = controls.get("ownership_violations", "deny")
                    audit(root, payload, choice, "path-outside-ownership")
                    return _decision(
                        "PreToolUse",
                        choice,
                        f"Path `{_display(path)}` is outside this session's assigned write scope.",
                    )
        elif not paths:
            choice = controls.get("unverifiable_writes", "ask")
            audit(root, payload, choice, "unverifiable-write-scope")
            return _decision(
                "PreToolUse",
                choice,
                "The edit tool did not expose a repository path that policy can verify.",
            )

        if external_write:
            choice = controls.get("external_writes", "ask")
            audit(root, payload, choice, "external-write")
            return _decision(
                "PreToolUse",
                choice,
                "External write requires explicit user confirmation after ownership checks.",
            )
        if unlisted_external:
            choice = controls.get("unlisted_external_tools", "ask")
            audit(root, payload, choice, "unlisted-external-tool")
            safe_prefix = _display(prefix, 80)
            return _decision(
                "PreToolUse",
                choice,
                f"Tool prefix `{safe_prefix}` is not on the repository allowlist.",
            )

        if any(path == "../outside-workspace" for path in paths):
            choice = controls.get("outside_workspace_writes", "ask")
            audit(root, payload, choice, "outside-workspace-write")
            return _decision(
                "PreToolUse",
                choice,
                "Writing outside the repository requires explicit confirmation.",
            )
        protected = policy.get("protected_paths", [])
        for path in paths:
            if any(fnmatch.fnmatch(path, pattern) for pattern in protected):
                choice = controls.get("protected_paths", "ask")
                audit(root, payload, choice, "protected-path")
                return _decision(
                    "PreToolUse",
                    choice,
                    f"Editing protected Project Flood path `{_display(path)}` requires confirmation.",
                )

    audit(root, payload, "allow", "policy-pass")
    return {"continue": True}


def lifecycle(payload: dict[str, Any], root: Path) -> dict[str, Any]:
    event = str(payload.get("hook_event_name", "unknown"))
    audit(root, payload, "allow", "lifecycle")
    if event == "SessionStart":
        version_path = root / ".project-flood/VERSION"
        version = "unknown"
        if not _has_symlink_component(root, ".project-flood/VERSION") and version_path.is_file():
            try:
                candidate_version = version_path.read_text(encoding="utf-8").strip()
                if re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?", candidate_version):
                    version = candidate_version
            except OSError:
                pass
        task_path = task_manifest_path(root)
        task = "none"
        local_task = task_path == root / ".agent-team/runtime/task-manifest.json"
        safe_task = not task_path.is_symlink() and not task_path.parent.is_symlink() and (
            not local_task or not _has_symlink_component(root, ".agent-team/runtime/task-manifest.json")
        )
        if safe_task and task_path.is_file():
            try:
                candidate_task = str(json.loads(task_path.read_text(encoding="utf-8")).get("task_id", "unknown"))
                task = candidate_task if re.fullmatch(r"[A-Za-z0-9._-]{1,80}", candidate_task) else "invalid"
            except Exception:
                task = "invalid"
        return {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": (
                    f"Project Flood v{version} is active. Canonical memory is Markdown with YAML frontmatter; "
                    f"runtime task manifest: {task}; this session key: {_session_key(payload.get('session_id'))}."
                ),
            }
        }
    return {"continue": True}


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps(_decision("PreToolUse", "ask", "Project Flood received invalid hook input.")))
        return 0
    if not isinstance(payload, dict):
        print(json.dumps(_decision("PreToolUse", "ask", "Project Flood hook input must be an object.")))
        return 0
    root_value = payload.get("cwd") or "."
    root = find_project_root(Path(root_value))
    if root is None:
        result = {"continue": True}
    elif payload.get("hook_event_name") == "PreToolUse":
        result = pre_tool_use(payload, root)
    else:
        result = lifecycle(payload, root)
    print(json.dumps(result, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

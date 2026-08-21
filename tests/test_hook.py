from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

import hook  # noqa: E402


def decision(result: dict) -> str | None:
    return result.get("hookSpecificOutput", {}).get("permissionDecision")


class HookPolicyTests(unittest.TestCase):
    def payload(self, event: str = "PreToolUse", tool: str = "editFiles", **tool_input) -> dict:
        return {
            "hook_event_name": event,
            "session_id": "session-one",
            "tool_name": tool,
            "tool_input": tool_input,
        }

    def test_dangerous_command_is_denied(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            result = hook.pre_tool_use(
                self.payload(tool="runInTerminal", command="rm -rf /tmp/example"),
                root,
            )
            self.assertEqual("deny", decision(result))

    def test_direct_shared_lease_command_is_denied(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = hook.pre_tool_use(
                self.payload(
                    tool="runInTerminal",
                    command="rm .git/project-flood/task-manifest.json",
                ),
                Path(temp_dir),
            )
            self.assertEqual("deny", decision(result))

    def test_plugin_hook_is_inert_without_repository_markers(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            payload = self.payload(tool="runInTerminal", command="rm -rf /tmp/example")
            payload["cwd"] = str(root)
            completed = subprocess.run(
                [sys.executable, str(REPOSITORY_ROOT / "scripts/hook.py")],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertEqual({"continue": True}, json.loads(completed.stdout))
            self.assertFalse((root / ".agent-team").exists())

    def test_hook_finds_project_markers_from_nested_cwd(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            nested = root / "src/nested"
            nested.mkdir(parents=True)
            policy = root / ".project-flood/policy.yaml"
            policy.parent.mkdir()
            policy.write_text("schema_version: 1\n", encoding="utf-8")
            charter = root / ".agent-team/charter.md"
            charter.parent.mkdir()
            charter.write_text("# Charter\n", encoding="utf-8")
            payload = self.payload(tool="runInTerminal", command="rm -rf /tmp/example")
            payload["cwd"] = str(nested)
            completed = subprocess.run(
                [sys.executable, str(REPOSITORY_ROOT / "scripts/hook.py")],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertEqual("deny", decision(json.loads(completed.stdout)))

    def test_protected_path_requires_confirmation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = hook.pre_tool_use(self.payload(path="AGENTS.md"), Path(temp_dir))
            self.assertEqual("ask", decision(result))

    def test_outside_workspace_write_requires_confirmation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            result = hook.pre_tool_use(self.payload(path=str(root.parent / "outside.txt")), root)
            self.assertEqual("ask", decision(result))

    def test_unverifiable_edit_requires_confirmation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = hook.pre_tool_use(self.payload(patch="opaque patch"), Path(temp_dir))
            self.assertEqual("ask", decision(result))

    def test_external_write_requires_confirmation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = hook.pre_tool_use(
                self.payload(tool="mcp__github__create_pull_request", title="test"),
                Path(temp_dir),
            )
            self.assertEqual("ask", decision(result))

    def test_external_file_write_cannot_bypass_active_ownership(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_manifest(root)
            result = hook.pre_tool_use(
                self.payload(tool="mcp__github__create_file", path="src/other/file.py"),
                root,
            )
            self.assertEqual("deny", decision(result))

    def test_unlisted_mcp_read_tool_requires_confirmation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = hook.pre_tool_use(
                self.payload(tool="mcp__github__get_issue", issue_number=1),
                Path(temp_dir),
            )
            self.assertEqual("ask", decision(result))

    def write_manifest(self, root: Path) -> None:
        runtime = root / ".agent-team/runtime"
        runtime.mkdir(parents=True)
        (runtime / "task-manifest.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "task_id": "TASK-1",
                    "coordinator_session_key": hook._session_key("lead-session"),
                    "status": "active",
                    "mode": "build-swarm",
                    "base_commit": "0123456789abcdef",
                    "expires_at": "2099-01-01T00:00:00Z",
                    "workers": [
                        {
                            "id": "one",
                            "role": "Flood Builder",
                            "status": "active",
                            "wave": 1,
                            "session_key": hook._session_key("session-one"),
                            "branch": "flood/one",
                            "worktree": "/tmp/one",
                            "depends_on": [],
                            "write_paths": ["src/owned/**"],
                            "acceptance_criteria": ["tests pass"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

    def test_active_owner_can_write_assigned_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_manifest(root)
            result = hook.pre_tool_use(self.payload(path="src/owned/file.py"), root)
            self.assertEqual({"continue": True}, result)

    def test_relative_edit_path_uses_nested_working_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "src").mkdir()
            self.write_manifest(root)
            payload = self.payload(path="owned/file.py")
            payload["cwd"] = str(root / "src")
            result = hook.pre_tool_use(payload, root)
            self.assertEqual({"continue": True}, result)

    def test_relative_edit_path_uses_resolved_root_alias(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            real_root = Path(temp_dir) / "real"
            alias_root = Path(temp_dir) / "alias"
            (real_root / "src").mkdir(parents=True)
            try:
                alias_root.symlink_to(real_root, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("directory symlinks are unavailable")
            self.write_manifest(real_root)
            payload = self.payload(path="owned/file.py")
            payload["cwd"] = str(alias_root / "src")
            result = hook.pre_tool_use(payload, alias_root)
            self.assertEqual({"continue": True}, result)

    def test_hook_reads_git_common_directory_lease(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_manifest(root)
            local = root / ".agent-team/runtime/task-manifest.json"
            shared = root / ".git/project-flood/task-manifest.json"
            shared.parent.mkdir(parents=True)
            shared.write_text(local.read_text(encoding="utf-8"), encoding="utf-8")
            local.unlink()
            result = hook.pre_tool_use(self.payload(path="src/owned/file.py"), root)
            self.assertEqual({"continue": True}, result)

    def test_active_owner_is_denied_outside_assigned_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_manifest(root)
            result = hook.pre_tool_use(self.payload(path="src/other/file.py"), root)
            self.assertEqual("deny", decision(result))

    def test_ownership_denial_is_stricter_than_protected_path_prompt(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_manifest(root)
            result = hook.pre_tool_use(self.payload(path="AGENTS.md"), root)
            self.assertEqual("deny", decision(result))

    def test_invalid_active_manifest_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_manifest(root)
            manifest_path = root / ".agent-team/runtime/task-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["workers"][0]["write_paths"] = ["../outside/**"]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = hook.pre_tool_use(self.payload(path="src/owned/file.py"), root)
            self.assertEqual("deny", decision(result))

    def test_coordinator_can_update_runtime_but_not_product(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_manifest(root)
            runtime_payload = self.payload(path=".agent-team/runtime/task-manifest.json")
            runtime_payload["session_id"] = "lead-session"
            self.assertEqual({"continue": True}, hook.pre_tool_use(runtime_payload, root))

            product_payload = self.payload(path="src/product.py")
            product_payload["session_id"] = "lead-session"
            self.assertEqual("deny", decision(hook.pre_tool_use(product_payload, root)))

    def test_session_start_exposes_only_hashed_session_key(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            raw_session = "private-session-id"
            result = hook.lifecycle(
                {
                    "hook_event_name": "SessionStart",
                    "session_id": raw_session,
                },
                Path(temp_dir),
            )
            context = result["hookSpecificOutput"]["additionalContext"]
            self.assertIn(hook._session_key(raw_session), context)
            self.assertNotIn(raw_session, context)

    def test_audit_does_not_store_command_or_input(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            secret_command = "rm -rf /tmp/never-log-this"
            hook.pre_tool_use(self.payload(tool="runInTerminal", command=secret_command), root)
            audit_text = (root / ".agent-team/runtime/hook-audit.jsonl").read_text(encoding="utf-8")
            self.assertNotIn(secret_command, audit_text)
            entry = json.loads(audit_text)
            self.assertEqual(
                {"timestamp", "event", "session", "tool", "decision", "reason_code"},
                set(entry),
            )


if __name__ == "__main__":
    unittest.main()

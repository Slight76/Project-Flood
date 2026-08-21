from __future__ import annotations

import hashlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

import flood  # noqa: E402


class ConfigurationTests(unittest.TestCase):
    def copy_template(self, destination: Path) -> Path:
        target = destination / "template"
        shutil.copytree(REPOSITORY_ROOT / "template", target)
        return target

    def test_distribution_is_valid(self):
        self.assertEqual([], flood.validate_distribution(REPOSITORY_ROOT))

    def test_missing_required_file_is_reported(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = self.copy_template(Path(temp_dir))
            (target / "AGENTS.md").unlink()
            errors = flood.validate_configuration(target)
            self.assertTrue(any("AGENTS.md" in error for error in errors))

    def test_duplicate_agent_name_is_reported(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = self.copy_template(Path(temp_dir))
            scout = target / ".github/agents/flood-scout.agent.md"
            scout.write_text(
                scout.read_text(encoding="utf-8").replace("name: Flood Scout", "name: Flood Architect", 1),
                encoding="utf-8",
            )
            errors = flood.validate_configuration(target)
            self.assertTrue(any("duplicate agent name" in error for error in errors))

    def test_stale_memory_index_is_reported(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = self.copy_template(Path(temp_dir))
            record = target / ".agent-team/memory/decisions/D-0001-hybrid-memory.md"
            record.write_text(
                record.read_text(encoding="utf-8").replace("confidence: high", "confidence: medium", 1),
                encoding="utf-8",
            )
            errors = flood.validate_configuration(target)
            self.assertTrue(any("index is stale" in error for error in errors))

    def test_duplicate_memory_id_is_reported(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = self.copy_template(Path(temp_dir))
            original = target / ".agent-team/memory/decisions/D-0001-hybrid-memory.md"
            duplicate = target / ".agent-team/memory/conventions/duplicate.md"
            duplicate.write_text(
                original.read_text(encoding="utf-8").replace("type: decision", "type: convention", 1),
                encoding="utf-8",
            )
            errors = flood.validate_configuration(target)
            self.assertTrue(any("duplicate memory id" in error for error in errors))


class TaskManifestTests(unittest.TestCase):
    def base_manifest(self) -> dict:
        return {
            "schema_version": 1,
            "task_id": "TASK-1",
            "coordinator_session_key": "c" * 12,
            "status": "active",
            "mode": "build-swarm",
            "base_commit": "0123456789abcdef",
            "expires_at": "2099-01-01T00:00:00Z",
            "workers": [],
        }

    @staticmethod
    def worker(identifier: str, path: str, wave: int = 1) -> dict:
        return {
            "id": identifier,
            "role": "Flood Builder",
            "status": "active",
            "wave": wave,
            "session_key": hashlib.sha256(identifier.encode("utf-8")).hexdigest()[:12],
            "branch": f"flood/{identifier}",
            "worktree": f"/tmp/{identifier}",
            "depends_on": [],
            "write_paths": [path],
            "acceptance_criteria": [f"{identifier} tests pass"],
        }

    def test_valid_non_overlapping_workers(self):
        manifest = self.base_manifest()
        manifest["workers"] = [self.worker("api", "src/api/**"), self.worker("web", "src/web/**")]
        self.assertEqual([], flood.validate_task_manifest_data(manifest))

    def test_overlapping_ownership_is_rejected(self):
        manifest = self.base_manifest()
        manifest["workers"] = [self.worker("one", "src/shared/**"), self.worker("two", "src/shared/config.ts")]
        errors = flood.validate_task_manifest_data(manifest)
        self.assertTrue(any("overlapping concurrent ownership" in error for error in errors))

    def test_more_than_three_active_workers_in_wave_is_rejected(self):
        manifest = self.base_manifest()
        manifest["workers"] = [self.worker(str(index), f"src/{index}/**") for index in range(4)]
        errors = flood.validate_task_manifest_data(manifest)
        self.assertTrue(any("three-worker ceiling" in error for error in errors))

    def test_repository_escape_is_rejected(self):
        manifest = self.base_manifest()
        manifest["workers"] = [self.worker("escape", "../outside/**")]
        errors = flood.validate_task_manifest_data(manifest)
        self.assertTrue(any("inside the repository" in error for error in errors))

    def test_ambiguous_write_glob_is_rejected(self):
        manifest = self.base_manifest()
        manifest["workers"] = [self.worker("ambiguous", "src/*/shared/**")]
        errors = flood.validate_task_manifest_data(manifest)
        self.assertTrue(any("exact or a prefix" in error for error in errors))

    def test_dependency_cycle_is_rejected(self):
        manifest = self.base_manifest()
        first = self.worker("first", "src/first/**", wave=1)
        second = self.worker("second", "src/second/**", wave=2)
        first["depends_on"] = ["second"]
        second["depends_on"] = ["first"]
        manifest["workers"] = [first, second]
        errors = flood.validate_task_manifest_data(manifest)
        self.assertTrue(any("contain a cycle" in error for error in errors))

    def test_read_only_role_cannot_own_build_paths(self):
        manifest = self.base_manifest()
        worker = self.worker("scout", "src/**")
        worker["role"] = "Flood Scout"
        manifest["workers"] = [worker]
        errors = flood.validate_task_manifest_data(manifest)
        self.assertTrue(any("read-only roles" in error for error in errors))


@unittest.skipUnless(shutil.which("git"), "Git is not available")
class TaskLeaseTests(unittest.TestCase):
    def git(self, root: Path, *arguments: str) -> str:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        return completed.stdout.strip()

    def test_activated_lease_is_shared_across_worktrees_and_closed_locally(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            repository = temp_root / "repository"
            worktree = temp_root / "worker"
            repository.mkdir()
            self.git(repository, "init")
            self.git(repository, "config", "user.name", "Project Flood Test")
            self.git(repository, "config", "user.email", "project-flood-test@example.invalid")
            (repository / "seed.txt").write_text("seed\n", encoding="utf-8")
            self.git(repository, "add", "seed.txt")
            self.git(repository, "commit", "-m", "seed")
            base_commit = self.git(repository, "rev-parse", "HEAD")
            self.git(repository, "worktree", "add", "--detach", str(worktree), base_commit)

            manifest_path = repository / flood.TASK_MANIFEST_PATH
            manifest_path.parent.mkdir(parents=True)
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "task_id": "TASK-SHARED",
                        "coordinator_session_key": "c" * 12,
                        "status": "active",
                        "mode": "build-swarm",
                        "base_commit": base_commit,
                        "expires_at": "2099-01-01T00:00:00Z",
                        "workers": [
                            {
                                "id": "worker",
                                "role": "Flood Builder",
                                "status": "active",
                                "wave": 1,
                                "session_key": "d" * 12,
                                "branch": "flood/task-shared-worker",
                                "worktree": str(worktree),
                                "depends_on": [],
                                "write_paths": ["src/**"],
                                "acceptance_criteria": ["tests pass"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = flood.activate_task_manifest(repository)
            shared = Path(report["shared_manifest"])
            self.assertTrue(shared.is_file())
            worker_state = flood.task_manifest_status(worktree)
            self.assertEqual("git-common-dir", worker_state["source"])
            self.assertEqual("TASK-SHARED", worker_state["manifest"]["task_id"])

            closed = flood.close_task_manifest(repository, "complete")
            self.assertFalse(shared.exists())
            self.assertEqual("complete", closed["status"])
            archived = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual("complete", archived["status"])


class InstallationTests(unittest.TestCase):
    def test_full_install_writes_manifest_and_validates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "target"
            target.mkdir()
            report = flood.install(REPOSITORY_ROOT / "template", target)
            self.assertEqual("full", report["mode"])
            self.assertTrue((target / flood.MANIFEST_PATH).is_file())
            self.assertEqual([], flood.validate_configuration(target))

    def test_adapter_install_omits_plugin_files_and_validates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "target"
            target.mkdir()
            flood.install(REPOSITORY_ROOT / "template", target, mode="adapter")
            self.assertFalse((target / ".github/agents").exists())
            self.assertFalse((target / ".github/skills").exists())
            self.assertFalse((target / ".github/hooks").exists())
            self.assertFalse((target / ".project-flood/hook.py").exists())
            self.assertEqual([], flood.validate_configuration(target))

    def test_conflict_refuses_all_changes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "target"
            target.mkdir()
            marker = target / "AGENTS.md"
            marker.write_text("user content\n", encoding="utf-8")
            with self.assertRaises(flood.FloodError):
                flood.install(REPOSITORY_ROOT / "template", target)
            self.assertEqual("user content\n", marker.read_text(encoding="utf-8"))
            self.assertFalse((target / flood.MANIFEST_PATH).exists())

    def test_symlinked_destination_tree_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "target"
            outside = root / "outside"
            target.mkdir()
            outside.mkdir()
            try:
                (target / ".github").symlink_to(outside, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symbolic links are unavailable: {exc}")
            with self.assertRaises(flood.FloodError):
                flood.install(REPOSITORY_ROOT / "template", target)
            self.assertEqual([], list(outside.iterdir()))

    def test_force_backs_up_and_replaces_conflict(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "target"
            target.mkdir()
            marker = target / "AGENTS.md"
            marker.write_text("user content\n", encoding="utf-8")
            report = flood.install(REPOSITORY_ROOT / "template", target, force=True)
            self.assertIn("AGENTS.md", report["conflicts_replaced"])
            self.assertNotEqual("user content\n", marker.read_text(encoding="utf-8"))
            backup = Path(report["backup"])
            self.assertEqual("user content\n", (backup / "AGENTS.md").read_text(encoding="utf-8"))

    def test_same_release_preserves_customized_managed_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "target"
            target.mkdir()
            flood.install(REPOSITORY_ROOT / "template", target)
            profile = target / ".agent-team/project-profile.md"
            profile.write_text(profile.read_text(encoding="utf-8") + "\nUser customization.\n", encoding="utf-8")
            report = flood.install(REPOSITORY_ROOT / "template", target)
            self.assertIn(".agent-team/project-profile.md", report["preserved"])
            self.assertIn("User customization.", profile.read_text(encoding="utf-8"))

    def test_upgrade_conflict_stops_when_source_and_target_changed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "target"
            source = root / "source"
            target.mkdir()
            shutil.copytree(REPOSITORY_ROOT / "template", source)
            flood.install(REPOSITORY_ROOT / "template", target)
            target_contract = target / "AGENTS.md"
            target_contract.write_text(
                target_contract.read_text(encoding="utf-8") + "\nTarget rule.\n",
                encoding="utf-8",
            )
            source_contract = source / "AGENTS.md"
            source_contract.write_text(
                source_contract.read_text(encoding="utf-8") + "\nFramework rule.\n",
                encoding="utf-8",
            )

            with self.assertRaises(flood.FloodError):
                flood.install(source, target)
            self.assertIn("Target rule.", target_contract.read_text(encoding="utf-8"))
            self.assertNotIn("Framework rule.", target_contract.read_text(encoding="utf-8"))

    def test_upgrade_removes_unchanged_retired_framework_file_recoverably(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "target"
            source = root / "source"
            target.mkdir()
            shutil.copytree(REPOSITORY_ROOT / "template", source)
            flood.install(REPOSITORY_ROOT / "template", target)
            retired = ".github/prompts/flood-reflect.prompt.md"
            (source / retired).unlink()

            report = flood.install(source, target)
            self.assertIn(retired, report["removed"])
            self.assertFalse((target / retired).exists())
            self.assertTrue((Path(report["backup"]) / retired).exists())

    def test_uninstall_is_dry_run_then_recoverable(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "target"
            target.mkdir()
            flood.install(REPOSITORY_ROOT / "template", target)
            profile = target / ".agent-team/project-profile.md"
            profile.write_text(profile.read_text(encoding="utf-8") + "\nKeep me.\n", encoding="utf-8")
            preview = flood.uninstall(target)
            self.assertTrue(preview["dry_run"])
            self.assertTrue((target / "AGENTS.md").exists())
            report = flood.uninstall(target, apply=True)
            self.assertTrue(profile.exists())
            self.assertIn(".agent-team/project-profile.md", report["preserved"])
            self.assertTrue((Path(report["backup"]) / "AGENTS.md").exists())
            self.assertFalse((target / flood.MANIFEST_PATH).exists())

    def test_v01_migration_removes_legacy_agent_recoverably(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "target"
            legacy = target / ".github/agents/scout.agent.md"
            legacy.parent.mkdir(parents=True)
            legacy.write_text("legacy scout\n", encoding="utf-8")
            version = target / ".project-flood/VERSION"
            version.parent.mkdir(parents=True)
            version.write_text("0.1.0\n", encoding="utf-8")

            output = io.StringIO()
            with redirect_stdout(output):
                result = flood.main(
                    [
                        "migrate",
                        "--source",
                        str(REPOSITORY_ROOT / "template"),
                        "--target",
                        str(target),
                        "--apply",
                    ]
                )

            self.assertEqual(0, result)
            self.assertFalse(legacy.exists())
            self.assertTrue((target / ".github/agents/flood-scout.agent.md").exists())
            report = json.loads(output.getvalue())
            self.assertEqual("0.1.0", report["migrated_from"])
            backup = Path(report["legacy_backup"])
            self.assertEqual("legacy scout\n", (backup / ".github/agents/scout.agent.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = REPOSITORY_ROOT / "template" / ".project-flood" / "validate_config.py"
SPEC = importlib.util.spec_from_file_location("project_flood_validator", VALIDATOR_PATH)
VALIDATOR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(VALIDATOR)


class ValidatorTests(unittest.TestCase):
    def test_template_is_valid(self):
        errors = VALIDATOR.validate(REPOSITORY_ROOT / "template")
        self.assertEqual([], errors)

    def test_missing_required_file_is_reported(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "template"
            shutil.copytree(REPOSITORY_ROOT / "template", target)
            (target / "AGENTS.md").unlink()
            errors = VALIDATOR.validate(target)
            self.assertTrue(any("AGENTS.md" in error for error in errors))

    def test_duplicate_agent_name_is_reported(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "template"
            shutil.copytree(REPOSITORY_ROOT / "template", target)
            scout = target / ".github" / "agents" / "scout.agent.md"
            content = scout.read_text(encoding="utf-8")
            scout.write_text(content.replace("name: Scout", "name: Architect", 1), encoding="utf-8")
            errors = VALIDATOR.validate(target)
            self.assertTrue(any("Duplicate agent name" in error for error in errors))

    def test_skill_folder_mismatch_is_reported(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "template"
            shutil.copytree(REPOSITORY_ROOT / "template", target)
            skill = target / ".github" / "skills" / "repository-onboarding" / "SKILL.md"
            content = skill.read_text(encoding="utf-8")
            skill.write_text(content.replace("name: repository-onboarding", "name: wrong-name", 1), encoding="utf-8")
            errors = VALIDATOR.validate(target)
            self.assertTrue(any("must match its directory" in error for error in errors))


if __name__ == "__main__":
    unittest.main()

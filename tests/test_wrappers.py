from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def find_supported_bash() -> str | None:
    if os.name != "nt":
        return shutil.which("bash")
    git = shutil.which("git")
    if not git:
        return None
    git_root = Path(git).resolve().parents[1]
    for candidate in (git_root / "bin/bash.exe", git_root / "usr/bin/bash.exe"):
        if candidate.is_file():
            return str(candidate)
    return None


BASH = find_supported_bash()


class WrapperSmokeTests(unittest.TestCase):
    @unittest.skipUnless(BASH, "a supported Bash installation is not available")
    def test_bash_installer(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "bash-target"
            target.mkdir()
            completed = subprocess.run(
                [BASH, str(REPOSITORY_ROOT / "scripts/install.sh"), str(target)],
                check=False,
                cwd=REPOSITORY_ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                0,
                completed.returncode,
                f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}",
            )
            self.assertTrue((target / ".project-flood/install-manifest.yaml").exists())

    @unittest.skipUnless(shutil.which("pwsh"), "PowerShell is not available")
    def test_powershell_installer(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "powershell-target"
            target.mkdir()
            completed = subprocess.run(
                [
                    "pwsh",
                    "-NoProfile",
                    "-File",
                    str(REPOSITORY_ROOT / "scripts/install.ps1"),
                    "-TargetPath",
                    str(target),
                ],
                check=False,
                cwd=REPOSITORY_ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                0,
                completed.returncode,
                f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}",
            )
            self.assertTrue((target / ".project-flood/install-manifest.yaml").exists())


if __name__ == "__main__":
    unittest.main()

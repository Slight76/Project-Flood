from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class WrapperSmokeTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("bash"), "bash is not available")
    def test_bash_installer(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "bash-target"
            target.mkdir()
            completed = subprocess.run(
                ["bash", str(REPOSITORY_ROOT / "scripts/install.sh"), str(target)],
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

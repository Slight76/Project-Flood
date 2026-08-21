#!/usr/bin/env python3
"""Synchronize generated plugin and installed copies from canonical Project Flood sources."""

from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def files(root: Path) -> dict[Path, Path]:
    if not root.exists():
        return {}
    return {
        path.relative_to(root): path
        for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }


def directory_matches(source: Path, destination: Path) -> bool:
    source_files = files(source)
    destination_files = files(destination)
    return source_files.keys() == destination_files.keys() and all(
        filecmp.cmp(source_files[relative], destination_files[relative], shallow=False)
        for relative in source_files
    )


def sync_directory(source: Path, destination: Path, check: bool) -> bool:
    if directory_matches(source, destination):
        return True
    if check:
        return False
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)
    return True


def sync_file(source: Path, destination: Path, check: bool) -> bool:
    if destination.exists() and filecmp.cmp(source, destination, shallow=False):
        return True
    if check:
        return False
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    operations = [
        ("directory", ROOT / "template/.github/agents", ROOT / "com.github.copilot/agents"),
        ("directory", ROOT / "template/.github/skills", ROOT / "skills"),
        ("file", ROOT / "scripts/flood.py", ROOT / "template/.project-flood/flood.py"),
        ("file", ROOT / "scripts/hook.py", ROOT / "template/.project-flood/hook.py"),
        ("file", ROOT / "requirements.txt", ROOT / "template/.project-flood/requirements.txt"),
    ]
    stale: list[str] = []
    for kind, source, destination in operations:
        matched = sync_directory(source, destination, args.check) if kind == "directory" else sync_file(source, destination, args.check)
        if not matched:
            stale.append(str(destination.relative_to(ROOT)))
    if stale:
        print("Generated distribution copies are stale:", file=sys.stderr)
        for path in stale:
            print(f"- {path}", file=sys.stderr)
        return 1
    print("Project Flood distribution copies are synchronized.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

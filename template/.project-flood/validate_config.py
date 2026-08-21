#!/usr/bin/env python3
"""Compatibility entry point for Project Flood v0.1 validation commands."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from flood import main as flood_main


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Project Flood configuration")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    print(
        "NOTICE: validate_config.py is deprecated; use "
        "`.project-flood/flood.py validate --root .`.",
        file=sys.stderr,
    )
    return flood_main(["validate", "--root", str(args.root)])


if __name__ == "__main__":
    raise SystemExit(main())

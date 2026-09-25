#!/usr/bin/env python3
"""Install My Taste into an isolated local runtime, then start ChatGPT test mode."""

from __future__ import annotations

import os
import subprocess
import sys
import venv
from pathlib import Path

REPO = "git+https://github.com/stoicsatvik/my-taste.git"


def main() -> None:
    root = Path.home() / ".my_taste" / "runtime"
    python = root / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

    if not python.exists():
        print(f"Creating isolated runtime at {root}")
        venv.EnvBuilder(with_pip=True).create(root)

    print("Installing/updating My Taste from GitHub...")
    subprocess.check_call(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--upgrade",
            REPO,
        ]
    )

    print("Starting My Taste ChatGPT connection...")
    os.execv(
        str(python),
        [
            str(python),
            "-m",
            "my_taste.cli",
            "connect",
            *sys.argv[1:],
        ],
    )


if __name__ == "__main__":
    main()

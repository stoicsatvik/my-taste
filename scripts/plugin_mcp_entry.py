#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import venv
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
STATE_ROOT = Path.home() / ".my_taste"
RUNTIME_ROOT = STATE_ROOT / "codex-runtime"
STAMP = RUNTIME_ROOT / ".source-stamp"


def runtime_python() -> Path:
    if os.name == "nt":
        return RUNTIME_ROOT / "Scripts" / "python.exe"
    return RUNTIME_ROOT / "bin" / "python"


def source_stamp() -> str:
    digest = hashlib.sha256()
    for relative in (
        "pyproject.toml",
        "src/my_taste/mcp_server.py",
        "src/my_taste/core/engine.py",
        "src/my_taste/core/store.py",
        "src/my_taste/skill_delivery.py",
        "skills/my-taste/SKILL.md",
    ):
        path = PLUGIN_ROOT / relative
        digest.update(relative.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def install_runtime() -> Path:
    STATE_ROOT.mkdir(parents=True, exist_ok=True)
    python = runtime_python()
    current = source_stamp()

    installed = STAMP.read_text(encoding="utf-8").strip() if STAMP.exists() else ""
    if python.exists() and installed == current:
        return python

    if not python.exists():
        venv.EnvBuilder(with_pip=True).create(RUNTIME_ROOT)

    python = runtime_python()

    # MCP speaks over stdout. Send all installation chatter to stderr so the
    # protocol stream remains clean even on first launch.
    subprocess.check_call(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--quiet",
            "--upgrade",
            str(PLUGIN_ROOT),
        ],
        stdout=sys.stderr,
        stderr=sys.stderr,
    )

    STAMP.write_text(current, encoding="utf-8")
    return python


def main() -> None:
    python = install_runtime()

    env = os.environ.copy()
    env["MY_TASTE_DB"] = str(STATE_ROOT / "taste.db")
    env["MY_TASTE_MCP_TRANSPORT"] = "stdio"

    os.execve(
        str(python),
        [str(python), "-m", "my_taste.mcp_server"],
        env,
    )


if __name__ == "__main__":
    main()

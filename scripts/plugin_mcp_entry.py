#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
STATE_ROOT = Path.home() / ".my_taste"
RUNTIME_ROOT = STATE_ROOT / "runtime"
STAMP = RUNTIME_ROOT / ".source-stamp"


def _bootstrap_python() -> Path:
    if sys.version_info >= (3, 10):
        return Path(sys.executable)

    for name in ("python3.13", "python3.12", "python3.11", "python3.10"):
        candidate = shutil.which(name)
        if candidate:
            return Path(candidate)

    raise RuntimeError("My Taste requires Python 3.10 or newer.")


def runtime_python() -> Path:
    if os.name == "nt":
        return RUNTIME_ROOT / "Scripts" / "python.exe"
    return RUNTIME_ROOT / "bin" / "python"


def source_stamp() -> str:
    digest = hashlib.sha256()
    paths: list[Path] = [PLUGIN_ROOT / "pyproject.toml"]
    for root in (PLUGIN_ROOT / "src" / "my_taste", PLUGIN_ROOT / "skills" / "my-taste"):
        if root.exists():
            paths.extend(path for path in root.rglob("*") if path.is_file())

    for path in sorted(paths):
        relative = path.relative_to(PLUGIN_ROOT).as_posix()
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
        bootstrap = _bootstrap_python()
        subprocess.check_call(
            [str(bootstrap), "-m", "venv", str(RUNTIME_ROOT)],
            stdout=sys.stderr,
            stderr=sys.stderr,
        )

    python = runtime_python()

    # MCP owns stdout. Keep installation chatter on stderr so the protocol
    # stream stays valid even on the first launch.
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
    # Deliberately shared across Codex and Claude Code.
    env["MY_TASTE_DB"] = str(STATE_ROOT / "taste.db")
    env["MY_TASTE_MCP_TRANSPORT"] = "stdio"

    os.execve(
        str(python),
        [str(python), "-m", "my_taste.mcp_server"],
        env,
    )


if __name__ == "__main__":
    main()

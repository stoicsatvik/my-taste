#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

STATE_ROOT = Path.home() / ".my_taste"
STATE_FILE = STATE_ROOT / "marketplace-refresh.json"
DEFAULT_INTERVAL = 6 * 60 * 60


def _enabled() -> bool:
    return os.getenv("MY_TASTE_MARKETPLACE_AUTO_UPDATE", "1").strip().lower() not in {
        "0", "false", "no", "off"
    }


def _interval() -> int:
    raw = os.getenv("MY_TASTE_MARKETPLACE_UPDATE_INTERVAL_SECONDS", str(DEFAULT_INTERVAL))
    try:
        return max(0, int(raw))
    except ValueError:
        return DEFAULT_INTERVAL


def _read_last_attempt() -> int:
    try:
        value = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return int(value.get("attempted_at") or 0) if isinstance(value, dict) else 0
    except (FileNotFoundError, json.JSONDecodeError, OSError, ValueError):
        return 0


def _mark_attempt() -> None:
    STATE_ROOT.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps({"attempted_at": int(time.time())}, sort_keys=True),
        encoding="utf-8",
    )


def main() -> None:
    if not _enabled():
        return

    now = int(time.time())
    if now - _read_last_attempt() < _interval():
        return

    codex = shutil.which("codex")
    if not codex:
        return

    _mark_attempt()

    kwargs: dict[str, object] = {
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "close_fds": True,
    }
    if os.name == "nt":
        kwargs["creationflags"] = (
            subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        )
    else:
        kwargs["start_new_session"] = True

    try:
        subprocess.Popen(
            [codex, "plugin", "marketplace", "upgrade", "my-taste"],
            **kwargs,
        )
    except OSError:
        # Runtime auto-update still covers the MCP engine if marketplace refresh
        # is unavailable.
        return


if __name__ == "__main__":
    main()

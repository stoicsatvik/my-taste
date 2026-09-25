#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import venv
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
STATE_ROOT = Path.home() / ".my_taste"
RUNTIME_ROOT = STATE_ROOT / "runtime"
UPDATE_STATE = STATE_ROOT / "update-state.json"

REPO = "stoicsatvik/my-taste"
BRANCH = "main"
HEAD_API = f"https://api.github.com/repos/{REPO}/commits/{BRANCH}"
ARCHIVE_URL = "https://github.com/stoicsatvik/my-taste/archive/{sha}.zip"

DEFAULT_UPDATE_INTERVAL_SECONDS = 15 * 60


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


def _read_state() -> dict[str, object]:
    try:
        value = json.loads(UPDATE_STATE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    return value if isinstance(value, dict) else {}


def _write_state(state: dict[str, object]) -> None:
    STATE_ROOT.mkdir(parents=True, exist_ok=True)
    tmp = UPDATE_STATE.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(state, ensure_ascii=False, sort_keys=True, indent=2),
        encoding="utf-8",
    )
    tmp.replace(UPDATE_STATE)


def _runtime_has_my_taste(python: Path) -> bool:
    if not python.exists():
        return False
    result = subprocess.run(
        [str(python), "-c", "import my_taste"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def _ensure_venv() -> Path:
    python = runtime_python()
    if python.exists():
        return python

    STATE_ROOT.mkdir(parents=True, exist_ok=True)
    bootstrap = _bootstrap_python()
    subprocess.check_call(
        [str(bootstrap), "-m", "venv", str(RUNTIME_ROOT)],
        stdout=sys.stderr,
        stderr=sys.stderr,
    )
    return runtime_python()


def _install_source(python: Path, source: str) -> None:
    # MCP owns stdout. Keep installer chatter on stderr.
    subprocess.check_call(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--quiet",
            "--upgrade",
            "--force-reinstall",
            source,
        ],
        stdout=sys.stderr,
        stderr=sys.stderr,
    )


def _install_local_fallback(python: Path) -> None:
    _install_source(python, str(PLUGIN_ROOT))


def _update_interval() -> int:
    raw = os.getenv(
        "MY_TASTE_UPDATE_INTERVAL_SECONDS",
        str(DEFAULT_UPDATE_INTERVAL_SECONDS),
    )
    try:
        return max(0, int(raw))
    except ValueError:
        return DEFAULT_UPDATE_INTERVAL_SECONDS


def _auto_update_enabled() -> bool:
    return os.getenv("MY_TASTE_AUTO_UPDATE", "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def _fetch_remote_head(state: dict[str, object]) -> tuple[str | None, str | None]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "my-taste-auto-updater",
    }
    etag = state.get("etag")
    if isinstance(etag, str) and etag:
        headers["If-None-Match"] = etag

    request = urllib.request.Request(HEAD_API, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=4) as response:
            payload = json.loads(response.read().decode("utf-8"))
            sha = payload.get("sha") if isinstance(payload, dict) else None
            return (str(sha) if sha else None, response.headers.get("ETag"))
    except urllib.error.HTTPError as exc:
        if exc.code == 304:
            installed = state.get("remote_sha")
            return (str(installed) if installed else None, str(etag) if etag else None)
        raise


def _maybe_auto_update(python: Path) -> tuple[str | None, bool]:
    state = _read_state()
    now = int(time.time())
    installed_sha = state.get("installed_sha")
    installed_sha = str(installed_sha) if installed_sha else None

    if not _auto_update_enabled():
        return installed_sha, False

    last_checked = int(state.get("checked_at") or 0)
    interval = _update_interval()
    runtime_ready = _runtime_has_my_taste(python)

    if runtime_ready and interval > 0 and now - last_checked < interval:
        return installed_sha, False

    try:
        remote_sha, etag = _fetch_remote_head(state)
    except Exception as exc:
        # Update failure must never break the last working runtime.
        print(f"[my-taste] update check skipped: {exc}", file=sys.stderr)
        state["checked_at"] = now
        _write_state(state)
        return installed_sha, False

    state["checked_at"] = now
    if etag:
        state["etag"] = etag
    if remote_sha:
        state["remote_sha"] = remote_sha

    if not remote_sha or (runtime_ready and remote_sha == installed_sha):
        _write_state(state)
        return installed_sha, False

    try:
        print(
            f"[my-taste] updating runtime to {remote_sha[:12]}...",
            file=sys.stderr,
        )
        _install_source(python, ARCHIVE_URL.format(sha=remote_sha))
    except Exception as exc:
        print(
            f"[my-taste] automatic update failed; using previous runtime: {exc}",
            file=sys.stderr,
        )
        _write_state(state)
        return installed_sha, False

    state["installed_sha"] = remote_sha
    state["installed_at"] = now
    _write_state(state)
    return remote_sha, True


def install_runtime() -> tuple[Path, str | None]:
    python = _ensure_venv()

    installed_sha, _updated = _maybe_auto_update(python)

    if not _runtime_has_my_taste(python):
        # Offline/first-run fallback: bundled marketplace copy is always usable.
        _install_local_fallback(python)
        state = _read_state()
        state.setdefault("installed_sha", "bundled")
        state["installed_at"] = int(time.time())
        _write_state(state)
        installed_sha = str(state["installed_sha"])

    return python, installed_sha


def main() -> None:
    python, installed_sha = install_runtime()

    env = os.environ.copy()
    # Deliberately shared across Codex and Claude Code.
    env["MY_TASTE_DB"] = str(STATE_ROOT / "taste.db")
    env["MY_TASTE_MCP_TRANSPORT"] = "stdio"
    env["MY_TASTE_AUTO_UPDATE"] = os.getenv("MY_TASTE_AUTO_UPDATE", "1")
    if installed_sha:
        env["MY_TASTE_RUNTIME_COMMIT"] = installed_sha

    os.execve(
        str(python),
        [str(python), "-m", "my_taste.mcp_server"],
        env,
    )


if __name__ == "__main__":
    main()

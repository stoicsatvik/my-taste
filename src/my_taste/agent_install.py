from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path

SERVER = {
    "command": "python3",
    "args": ["-m", "my_taste.mcp_server"],
}

@dataclass(frozen=True)
class Agent:
    name: str
    detected: bool
    configured: bool
    detail: str

def _merge_mcp(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise RuntimeError(f"Refusing to overwrite invalid JSON at {path}: {exc}") from exc
    servers = data.setdefault("mcpServers", {})
    servers["my-taste"] = SERVER
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

def _cursor() -> Agent:
    detected = bool(shutil.which("cursor") or (Path.home()/".cursor").exists())
    path = Path.home()/".cursor"/"mcp.json"
    if detected:
        _merge_mcp(path)
    return Agent("Cursor", detected, detected and path.exists(), str(path))

def _windsurf() -> Agent:
    root = Path.home()/".codeium"/"windsurf"
    detected = root.exists() or bool(shutil.which("windsurf"))
    path = root/"mcp_config.json"
    if detected:
        _merge_mcp(path)
    return Agent("Windsurf", detected, detected and path.exists(), str(path))

def _opencode() -> Agent:
    exe = shutil.which("opencode")
    if not exe:
        return Agent("OpenCode", False, False, "not detected")
    # OpenCode's native CLI owns its config format; do not hand-edit it.
    import subprocess
    proc = subprocess.run([exe, "mcp", "add", "my-taste", "--global", "--", "python3", "-m", "my_taste.mcp_server"],
                          text=True, capture_output=True)
    return Agent("OpenCode", True, proc.returncode == 0, (proc.stderr or proc.stdout).strip())

def _generic() -> list[Agent]:
    # Native plugin hosts consume the repository manifests themselves.
    return [
        Agent("Claude Code", bool(shutil.which("claude")), False, "native plugin manifest bundled"),
        Agent("Codex", bool(shutil.which("codex")), False, "native plugin manifest bundled"),
        Agent("GitHub Copilot", bool(shutil.which("copilot") or shutil.which("gh")), False, "host support varies; portable MCP manifest bundled"),
        Agent("Aider", bool(shutil.which("aider")), False, "instruction fallback; no config modified"),
        Agent("Kiro", bool(shutil.which("kiro")), False, "portable MCP manifest bundled"),
        Agent("Qoder", bool(shutil.which("qoder")), False, "portable MCP manifest bundled"),
    ]

def install_detected() -> list[Agent]:
    results = [_cursor(), _windsurf(), _opencode(), *_generic()]
    return results

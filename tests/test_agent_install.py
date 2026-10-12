from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from my_taste.agent_install import SERVER, _merge_mcp


def test_merge_mcp_preserves_existing_servers(tmp_path: Path) -> None:
    path = tmp_path / "mcp.json"
    path.write_text(json.dumps({"mcpServers": {"existing": {"command": "keep-me"}}, "other": True}))
    _merge_mcp(path)
    data = json.loads(path.read_text())
    assert data["other"] is True
    assert data["mcpServers"]["existing"]["command"] == "keep-me"
    assert data["mcpServers"]["my-taste"]["args"] == ["-m", "my_taste.mcp_server"]


def test_server_uses_installed_interpreter(tmp_path: Path) -> None:
    path = tmp_path / "mcp.json"
    _merge_mcp(path)
    saved = json.loads(path.read_text())["mcpServers"]["my-taste"]
    assert saved["command"] == sys.executable
    assert saved == SERVER


def test_merge_mcp_is_idempotent(tmp_path: Path) -> None:
    path = tmp_path / "mcp.json"
    _merge_mcp(path)
    first = path.read_text()
    _merge_mcp(path)
    assert path.read_text() == first


@pytest.mark.parametrize("raw", ['{not-json', '[]', '{"mcpServers":[]}', '{"mcpServers":"bad"}'])
def test_invalid_config_fails_closed(tmp_path: Path, raw: str) -> None:
    path = tmp_path / "mcp.json"
    path.write_text(raw)
    with pytest.raises(RuntimeError):
        _merge_mcp(path)
    assert path.read_text() == raw

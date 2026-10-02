from __future__ import annotations

import json
from pathlib import Path

import pytest

from my_taste.agent_install import _merge_mcp

def test_merge_mcp_preserves_existing_servers(tmp_path: Path) -> None:
    path = tmp_path / "mcp.json"
    path.write_text(json.dumps({"mcpServers": {"existing": {"command": "keep-me"}}, "other": True}))
    _merge_mcp(path)
    data = json.loads(path.read_text())
    assert data["other"] is True
    assert data["mcpServers"]["existing"]["command"] == "keep-me"
    assert data["mcpServers"]["my-taste"]["args"] == ["-m", "my_taste.mcp_server"]

def test_merge_mcp_is_idempotent(tmp_path: Path) -> None:
    path = tmp_path / "mcp.json"
    _merge_mcp(path)
    first = path.read_text()
    _merge_mcp(path)
    assert path.read_text() == first

def test_invalid_config_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "mcp.json"
    path.write_text("{not-json")
    with pytest.raises(RuntimeError):
        _merge_mcp(path)
    assert path.read_text() == "{not-json"

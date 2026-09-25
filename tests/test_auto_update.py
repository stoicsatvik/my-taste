from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_updater():
    path = Path(__file__).resolve().parents[1] / "scripts" / "plugin_mcp_entry.py"
    spec = importlib.util.spec_from_file_location("my_taste_plugin_mcp_entry", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_auto_update_defaults_on(monkeypatch):
    module = _load_updater()
    monkeypatch.delenv("MY_TASTE_AUTO_UPDATE", raising=False)
    assert module._auto_update_enabled() is True


def test_auto_update_can_be_disabled(monkeypatch):
    module = _load_updater()
    monkeypatch.setenv("MY_TASTE_AUTO_UPDATE", "false")
    assert module._auto_update_enabled() is False


def test_update_interval_is_bounded_at_zero(monkeypatch):
    module = _load_updater()
    monkeypatch.setenv("MY_TASTE_UPDATE_INTERVAL_SECONDS", "-10")
    assert module._update_interval() == 0


def test_update_interval_falls_back_on_invalid_value(monkeypatch):
    module = _load_updater()
    monkeypatch.setenv("MY_TASTE_UPDATE_INTERVAL_SECONDS", "banana")
    assert module._update_interval() == module.DEFAULT_UPDATE_INTERVAL_SECONDS

from __future__ import annotations

import pytest

from my_taste.connect import cloudflared_asset_name


@pytest.mark.parametrize(
    ("system", "machine", "expected"),
    [
        ("Darwin", "arm64", "cloudflared-darwin-arm64.tgz"),
        ("Darwin", "x86_64", "cloudflared-darwin-amd64.tgz"),
        ("Linux", "aarch64", "cloudflared-linux-arm64"),
        ("Linux", "x86_64", "cloudflared-linux-amd64"),
        ("Windows", "AMD64", "cloudflared-windows-amd64.exe"),
    ],
)
def test_cloudflared_asset_name(system, machine, expected):
    assert cloudflared_asset_name(system, machine) == expected


def test_cloudflared_asset_name_rejects_unknown_platform():
    with pytest.raises(RuntimeError):
        cloudflared_asset_name("Plan9", "quantum")

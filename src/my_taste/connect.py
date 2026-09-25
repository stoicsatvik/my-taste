from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request
from pathlib import Path

_CLOUDFLARED_RELEASE_API = "https://api.github.com/repos/cloudflare/cloudflared/releases/latest"
_TUNNEL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")


def cloudflared_asset_name(system: str | None = None, machine: str | None = None) -> str:
    system = (system or platform.system()).lower()
    machine = (machine or platform.machine()).lower()

    if system == "darwin":
        if machine in {"arm64", "aarch64"}:
            return "cloudflared-darwin-arm64.tgz"
        if machine in {"x86_64", "amd64"}:
            return "cloudflared-darwin-amd64.tgz"
    elif system == "linux":
        if machine in {"arm64", "aarch64"}:
            return "cloudflared-linux-arm64"
        if machine in {"x86_64", "amd64"}:
            return "cloudflared-linux-amd64"
    elif system == "windows":
        if machine in {"x86_64", "amd64"}:
            return "cloudflared-windows-amd64.exe"

    raise RuntimeError(f"Unsupported platform for automatic cloudflared setup: {system}/{machine}")


def _request_json(url: str) -> dict[str, object]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "my-taste-bootstrap",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _release_checksum(release: dict[str, object], asset_name: str, asset: dict[str, object]) -> str:
    digest = str(asset.get("digest") or "")
    if digest.startswith("sha256:"):
        return digest.removeprefix("sha256:")

    body = str(release.get("body") or "")
    match = re.search(
        rf"(?im)^\s*{re.escape(asset_name)}:\s*([0-9a-f]{{64}})\s*$",
        body,
    )
    if match:
        return match.group(1)

    raise RuntimeError(
        "Cloudflared release did not publish a SHA-256 checksum; refusing an unverified download."
    )


def _download(url: str, destination: Path) -> str:
    digest = hashlib.sha256()
    request = urllib.request.Request(url, headers={"User-Agent": "my-taste-bootstrap"})
    with urllib.request.urlopen(request, timeout=60) as response, destination.open("wb") as output:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            output.write(chunk)
    return digest.hexdigest()


def ensure_cloudflared(*, allow_download: bool = True) -> Path:
    existing = shutil.which("cloudflared")
    if existing:
        return Path(existing)

    cache_dir = Path.home() / ".my_taste" / "bin"
    cache_dir.mkdir(parents=True, exist_ok=True)
    executable = cache_dir / ("cloudflared.exe" if platform.system().lower() == "windows" else "cloudflared")
    if executable.exists():
        return executable

    if not allow_download:
        raise RuntimeError(
            "cloudflared was not found. Install it manually or rerun without --no-download-cloudflared."
        )

    release = _request_json(_CLOUDFLARED_RELEASE_API)
    asset_name = cloudflared_asset_name()
    assets = release.get("assets")
    if not isinstance(assets, list):
        raise RuntimeError("Unexpected cloudflared release metadata.")

    asset = next(
        (
            item
            for item in assets
            if isinstance(item, dict) and item.get("name") == asset_name
        ),
        None,
    )
    if not isinstance(asset, dict):
        raise RuntimeError(f"Could not find {asset_name} in the latest cloudflared release.")

    download_url = str(asset.get("browser_download_url") or "")
    if not download_url:
        raise RuntimeError("Cloudflared release asset has no download URL.")

    expected = _release_checksum(release, asset_name, asset)

    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / asset_name
        actual = _download(download_url, archive)
        if actual.lower() != expected.lower():
            raise RuntimeError(
                f"Cloudflared checksum mismatch: expected {expected}, got {actual}."
            )

        if asset_name.endswith(".tgz"):
            with tarfile.open(archive, "r:gz") as package:
                members = [
                    member
                    for member in package.getmembers()
                    if member.isfile() and Path(member.name).name == "cloudflared"
                ]
                if len(members) != 1:
                    raise RuntimeError("Cloudflared archive did not contain exactly one binary.")
                member = members[0]
                source = package.extractfile(member)
                if source is None:
                    raise RuntimeError("Could not extract cloudflared binary.")
                with executable.open("wb") as output:
                    shutil.copyfileobj(source, output)
        else:
            shutil.copy2(archive, executable)

    if platform.system().lower() != "windows":
        executable.chmod(0o755)
    return executable


def _wait_for_port(host: str, port: int, process: subprocess.Popen[object], timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"My Taste MCP server exited early with code {process.returncode}.")
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError(f"My Taste MCP server did not start on {host}:{port}.")


def run_chatgpt_connection(
    *,
    db_path: str | Path,
    port: int = 8000,
    allow_cloudflared_download: bool = True,
) -> None:
    cloudflared = ensure_cloudflared(allow_download=allow_cloudflared_download)

    env = os.environ.copy()
    env["MY_TASTE_DB"] = str(Path(db_path).expanduser())
    env["MY_TASTE_MCP_TRANSPORT"] = "streamable-http"
    env["MY_TASTE_MCP_HOST"] = "127.0.0.1"
    env["MY_TASTE_MCP_PORT"] = str(port)

    server = subprocess.Popen(
        [sys.executable, "-m", "my_taste.mcp_server"],
        env=env,
    )

    tunnel: subprocess.Popen[str] | None = None
    try:
        _wait_for_port("127.0.0.1", port, server)
        tunnel = subprocess.Popen(
            [
                str(cloudflared),
                "tunnel",
                "--url",
                f"http://127.0.0.1:{port}",
                "--no-autoupdate",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        tunnel_url = ""
        deadline = time.monotonic() + 30.0
        assert tunnel.stdout is not None
        while time.monotonic() < deadline:
            if tunnel.poll() is not None:
                raise RuntimeError(
                    f"cloudflared exited early with code {tunnel.returncode}."
                )
            line = tunnel.stdout.readline()
            if not line:
                time.sleep(0.1)
                continue
            match = _TUNNEL_RE.search(line)
            if match:
                tunnel_url = match.group(0)
                break

        if not tunnel_url:
            raise RuntimeError("Could not obtain a Cloudflare Quick Tunnel URL.")

        mcp_url = f"{tunnel_url}/mcp"
        print("\nMy Taste is running.")
        print(f"Database: {Path(db_path).expanduser()}")
        print(f"MCP URL:  {mcp_url}")
        print("\nIn ChatGPT: Settings -> Security and login -> Developer mode,")
        print("then Plugins -> + -> paste the MCP URL above.")
        print("\nKeep this terminal open while testing. Press Ctrl+C to stop.\n")

        while True:
            if server.poll() is not None:
                raise RuntimeError(f"My Taste MCP server stopped with code {server.returncode}.")
            if tunnel.poll() is not None:
                raise RuntimeError(f"Cloudflare tunnel stopped with code {tunnel.returncode}.")
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\nStopping My Taste.")
    finally:
        for process in (tunnel, server):
            if process is not None and process.poll() is None:
                process.terminate()
        for process in (tunnel, server):
            if process is not None:
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()

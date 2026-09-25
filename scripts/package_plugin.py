#!/usr/bin/env python3
from __future__ import annotations

import zipfile
from pathlib import Path

INCLUDE_ROOT_FILES = {
    "plugin.json",
    "mcp.json",
    ".mcp.json",
    "pyproject.toml",
    "README.md",
    "LICENSE",
}

INCLUDE_TREES = (
    "skills",
    "src",
    "scripts",
    ".codex-plugin",
    ".claude-plugin",
    "hooks",
)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    output_dir = repo_root / "dist"
    output_dir.mkdir(exist_ok=True)
    output = output_dir / "my-taste-plugin.zip"

    paths: list[Path] = []
    for name in INCLUDE_ROOT_FILES:
        path = repo_root / name
        if path.exists():
            paths.append(path)

    for tree in INCLUDE_TREES:
        root = repo_root / tree
        if root.exists():
            paths.extend(path for path in root.rglob("*") if path.is_file())

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(set(paths)):
            if "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            archive.write(path, path.relative_to(repo_root))

    print(output)


if __name__ == "__main__":
    main()

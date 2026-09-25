#!/usr/bin/env python3
from __future__ import annotations

import shutil
import tempfile
import zipfile
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    skill_root = repo_root / "skills" / "my-taste"
    output_dir = repo_root / "dist"
    output_dir.mkdir(exist_ok=True)
    output = output_dir / "my-taste-skill.zip"

    if not (skill_root / "SKILL.md").exists():
        raise SystemExit(f"Missing skill manifest: {skill_root / 'SKILL.md'}")

    with tempfile.TemporaryDirectory() as tmp:
        staging = Path(tmp) / "my-taste"
        shutil.copytree(skill_root, staging)

        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(staging.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(staging.parent))

    print(output)


if __name__ == "__main__":
    main()

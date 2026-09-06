from __future__ import annotations

import os
from pathlib import Path


def default_db_path() -> Path:
    configured = os.environ.get("MY_TASTE_DB")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".my_taste" / "taste.db"

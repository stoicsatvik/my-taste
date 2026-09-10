from __future__ import annotations

import re

_WHITESPACE_RE = re.compile(r"\s+")


def normalize_context(context: str) -> str:
    """Return a stable, human-readable key for context-scoped preferences."""
    return _WHITESPACE_RE.sub(" ", context.strip().lower())


def preference_instruction(feature: str, direction: str) -> str:
    """Convert an interpretable feature preference into an agent-facing instruction."""
    label = feature.replace("_", " ")
    if direction == "prefer_more":
        return f"Prefer more {label}."
    return f"Prefer less {label}."

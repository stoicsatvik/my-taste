from __future__ import annotations

from mcp.server import MCPServer

from .config import default_db_path
from .core.context_engine import ContextTasteEngine

mcp = MCPServer("My Taste v0.2")
engine = ContextTasteEngine(default_db_path())


@mcp.tool()
def observe_choice(
    preferred: str,
    rejected: str,
    domain: str = "writing",
    context: str = "",
) -> dict[str, object]:
    """Learn from an explicit pairwise preference, optionally scoped to context."""
    return engine.observe_choice(preferred, rejected, domain=domain, context=context)


@mcp.tool()
def observe_edit(
    original: str,
    edited: str,
    domain: str = "writing",
    context: str = "",
) -> dict[str, object]:
    """Learn from a user edit, optionally scoped to context."""
    return engine.observe_edit(original, edited, domain=domain, context=context)


@mcp.tool()
def rank_text(
    candidates: list[str],
    domain: str = "writing",
    context: str = "",
) -> list[dict[str, object]]:
    """Rank text candidates using global plus context-scoped preferences."""
    return [
        {
            "text": item.text,
            "score": item.score,
            "strongest_contributions": sorted(
                item.contributions.items(), key=lambda kv: abs(kv[1]), reverse=True
            )[:5],
        }
        for item in engine.rank_text(candidates, domain=domain, context=context)
    ]


@mcp.tool()
def taste_context(
    domain: str = "writing",
    context: str = "",
    limit: int = 8,
) -> dict[str, object]:
    """Return agent-ready preference instructions for a domain and context."""
    return engine.taste_context(domain=domain, context=context, limit=limit)


@mcp.tool()
def taste_provenance(
    domain: str = "writing",
    context: str | None = None,
    limit: int = 20,
) -> list[dict[str, object]]:
    """Return evidence records supporting the learned taste model."""
    return engine.provenance(domain=domain, context=context, limit=limit)


@mcp.tool()
def context_profile(
    domain: str = "writing",
    context: str = "",
    limit: int = 20,
) -> list[dict[str, object]]:
    """Inspect global, context, and effective preference weights."""
    return engine.context_profile(domain=domain, context=context, limit=limit)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()

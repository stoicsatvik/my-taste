from __future__ import annotations

import os

from mcp.server import MCPServer

from .config import default_db_path
from .core.engine import TasteEngine

mcp = MCPServer("My Taste")
engine = TasteEngine(default_db_path())


@mcp.tool()
def observe_choice(
    preferred: str,
    rejected: str,
    domain: str = "writing",
    context: str = "",
) -> dict[str, object]:
    """Learn from an explicit pairwise preference: preferred > rejected."""
    return engine.observe_choice(preferred, rejected, domain=domain, context=context)


@mcp.tool()
def observe_edit(
    original: str,
    edited: str,
    domain: str = "writing",
    context: str = "",
) -> dict[str, object]:
    """Learn from a user edit by treating edited text as preferred over original text."""
    return engine.observe_edit(original, edited, domain=domain, context=context)


@mcp.tool()
def rank_text(candidates: list[str], domain: str = "writing") -> list[dict[str, object]]:
    """Rank candidate text outputs according to the learned user preference model."""
    return [
        {
            "text": item.text,
            "score": item.score,
            "strongest_contributions": sorted(
                item.contributions.items(), key=lambda kv: abs(kv[1]), reverse=True
            )[:5],
        }
        for item in engine.rank_text(candidates, domain=domain)
    ]


@mcp.tool()
def taste_profile(domain: str = "writing", limit: int = 20) -> list[dict[str, object]]:
    """Return the strongest learned preferences for a domain."""
    return engine.profile(domain=domain, limit=limit)


@mcp.tool()
def explain_text(text: str, domain: str = "writing") -> dict[str, object]:
    """Explain how a text candidate interacts with learned preferences."""
    return engine.explain_text(text, domain=domain)


def main() -> None:
    transport = os.getenv("MY_TASTE_MCP_TRANSPORT", "stdio").strip().lower()

    if transport == "stdio":
        mcp.run()
        return

    if transport in {"streamable-http", "streamable_http", "http"}:
        host = os.getenv("MY_TASTE_MCP_HOST", "127.0.0.1")
        port = int(os.getenv("MY_TASTE_MCP_PORT", "8000"))
        mcp.run(
            transport="streamable-http",
            host=host,
            port=port,
            stateless_http=True,
            json_response=True,
        )
        return

    raise ValueError(
        "MY_TASTE_MCP_TRANSPORT must be 'stdio' or 'streamable-http'"
    )


if __name__ == "__main__":
    main()

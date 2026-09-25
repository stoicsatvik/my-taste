from __future__ import annotations

import os
from typing import Any

from mcp.server import MCPServer

from .config import default_db_path
from .core.engine import TasteEngine

mcp = MCPServer(
    "my-taste",
    version="0.2.0",
    title="My Taste",
    description="A local-first contextual preference layer for writing, UI, and video taste.",
    instructions="Use My Taste as the user's durable preference layer. If the user explicitly likes/dislikes an inspectable text, website, screenshot, UI, or video reference, inspect it with the host's available perception tools, derive a reusable style fingerprint, then call observe_artifact. Before generating taste-sensitive writing, UI/design, branding, or video/editing work, call taste_brief with a compact task context and apply high-confidence prefer/avoid guidance. Do not learn from silence or unrelated memory. Do not claim My Taste itself can see media; the host model performs perception and supplies derived features.",
    website_url="https://github.com/stoicsatvik/my-taste",
)
engine = TasteEngine(default_db_path())


@mcp.tool()
def observe_choice(
    preferred: str,
    rejected: str,
    domain: str = "writing",
    context: str = "",
) -> dict[str, object]:
    """Learn from an explicit pairwise text preference: preferred > rejected."""
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
def observe_artifact(
    domain: str,
    modality: str,
    features: dict[str, Any],
    context: dict[str, str] | None = None,
    preference: str = "positive",
    strength: float = 1.0,
    source_reference: str = "",
    note: str = "",
) -> dict[str, object]:
    """Persist a style fingerprint after the host has inspected an explicitly liked/disliked text, UI, screenshot, website, or video reference."""
    return engine.observe_artifact(
        domain=domain,
        modality=modality,
        features=features,
        context=context,
        preference=preference,
        strength=strength,
        source="explicit_artifact_preference",
        source_reference=source_reference,
        note=note,
    )


@mcp.tool()
def retrieve_taste(
    domain: str,
    context: dict[str, str] | None = None,
    modality: str = "",
    limit: int = 8,
) -> list[dict[str, object]]:
    """Retrieve individual context-relevant taste evidence, including provenance."""
    return engine.retrieve_taste(
        domain=domain,
        context=context,
        modality=modality,
        limit=limit,
    )


@mcp.tool()
def taste_brief(
    domain: str,
    context: dict[str, str] | None = None,
    modality: str = "",
    limit: int = 12,
) -> dict[str, object]:
    """Call before taste-sensitive writing/UI/video generation to get context-specific prefer, avoid, conflict, and confidence guidance."""
    return engine.taste_brief(
        domain=domain,
        context=context,
        modality=modality,
        limit=limit,
    )


@mcp.tool()
def rank_profiles(
    candidates: list[dict[str, Any]],
    domain: str,
    context: dict[str, str] | None = None,
    modality: str = "",
) -> list[dict[str, object]]:
    """Rank structured UI, video, writing-style, or other candidate fingerprints against learned taste."""
    return engine.rank_profiles(
        candidates,
        domain=domain,
        context=context,
        modality=modality,
    )


@mcp.tool()
def rank_text(candidates: list[str], domain: str = "writing") -> list[dict[str, object]]:
    """Rank raw text candidates using the interpretable lexical preference model."""
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
    """Return the strongest learned lexical preferences for a domain."""
    return engine.profile(domain=domain, limit=limit)


@mcp.tool()
def explain_text(text: str, domain: str = "writing") -> dict[str, object]:
    """Explain how a text candidate interacts with learned lexical preferences."""
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

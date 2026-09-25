from __future__ import annotations

import os
from typing import Any

from mcp.server import MCPServer

from .capture_store import compact_receipt, compact_website_capture, save_raw_capture
from .config import default_db_path
from .core.engine import TasteEngine
from .media_analysis import analyze_image_file as analyze_image_file_pixels
from .skill_delivery import SkillsExtension, register_skill_resources
from .web_analysis import analyze_website as analyze_live_website

skill_extension = SkillsExtension()

mcp = MCPServer(
    "my-taste",
    version="0.5.0",
    title="My Taste",
    description="A local-first contextual preference layer for writing, UI, and video taste.",
    instructions="Use My Taste as the user's durable preference layer. Minimize model-context cost. For explicit live-website style saves, call save_website_reference directly instead of analyze_website followed by observe_artifact: it performs deep browser capture, stores the full raw forensic capture locally, saves only a compact structured fingerprint, and returns a tiny receipt. Use analyze_website only when the user explicitly wants the analysis returned. For screenshots, use analyze_image_file plus a compact semantic fingerprint, then observe_artifact. Before taste-sensitive generation call taste_brief, which is compact by default. Do not call retrieve_taste unless provenance is specifically needed. Static screenshots cannot reveal motion. Never learn from silence or invent unavailable evidence.",
    website_url="https://github.com/stoicsatvik/my-taste",
    extensions=[skill_extension],
)
register_skill_resources(mcp, skill_extension)
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
def analyze_image_file(path: str, palette_size: int = 12) -> dict[str, object]:
    """Measure deterministic pixel-level evidence from a local screenshot/image path. This does not infer semantics, animation, or interaction."""
    return analyze_image_file_pixels(path, palette_size=palette_size)



@mcp.tool()
def save_image_reference(
    path: str,
    context: dict[str, str] | None = None,
    preference: str = "positive",
    strength: float = 1.0,
    semantic_features: dict[str, Any] | None = None,
) -> dict[str, object]:
    """Save a local screenshot/image reference in one token-efficient call.

    Pixel evidence is measured server-side. The host may add a compact semantic
    fingerprint, but the large intermediate pixel analysis is not echoed back.
    """
    pixels = analyze_image_file_pixels(path)
    fingerprint: dict[str, Any] = {
        "capture": {
            "kind": "static_raster",
            "motion_observable": False,
            "interaction_observable": False,
        },
        "pixels": pixels,
    }
    if semantic_features:
        fingerprint["semantic"] = semantic_features

    clean_context = dict(context or {})
    clean_context.setdefault("capture_fidelity", "static_raster")
    saved = engine.observe_artifact(
        domain="ui_design",
        modality="screenshot",
        features=fingerprint,
        context=clean_context,
        preference=preference,
        strength=strength,
        source="deep_image_capture",
        source_reference=f"sha256:{pixels['capture']['sha256']}",
        note="Static raster capture; motion and interaction intentionally unobserved.",
    )
    palette = pixels.get("palette") if isinstance(pixels.get("palette"), dict) else {}
    geometry = pixels.get("geometry") if isinstance(pixels.get("geometry"), dict) else {}
    return {
        "saved": True,
        "evidence_id": saved["evidence_id"],
        "domain": "ui_design",
        "modality": "screenshot",
        "fidelity": "static_raster",
        "dimensions": {
            "width_px": geometry.get("width_px"),
            "height_px": geometry.get("height_px"),
        },
        "dominant_colors": [
            row.get("hex")
            for row in (palette.get("dominant_colors") or [])[:5]
            if isinstance(row, dict)
        ],
    }


@mcp.tool()
def analyze_website(
    url: str,
    width: int = 1440,
    height: int = 1000,
    max_elements: int = 140,
    settle_ms: int = 700,
) -> dict[str, object]:
    """Return a compact forensic website fingerprint. Raw DOM/CSS/motion capture stays server-side to avoid flooding model context."""
    raw = analyze_live_website(
        url,
        width=width,
        height=height,
        max_elements=max_elements,
        settle_ms=settle_ms,
    )
    return compact_website_capture(raw)


@mcp.tool()
def save_website_reference(
    url: str,
    context: dict[str, str] | None = None,
    preference: str = "positive",
    strength: float = 1.0,
    semantic_features: dict[str, Any] | None = None,
    width: int = 1440,
    height: int = 1000,
    max_elements: int = 140,
    settle_ms: int = 700,
) -> dict[str, object]:
    """Deep-capture a live website and save it with minimal token output.

    Full forensic DOM/CSS/motion data is gzip-compressed locally. Only a compact
    preference fingerprint is stored in the taste DB and a tiny receipt is
    returned to the model.
    """
    raw = analyze_live_website(
        url,
        width=width,
        height=height,
        max_elements=max_elements,
        settle_ms=settle_ms,
    )
    fingerprint = compact_website_capture(raw)
    if semantic_features:
        fingerprint["semantic"] = semantic_features

    clean_context = dict(context or {})
    clean_context.setdefault("capture_fidelity", "live_forensic_compact")

    saved = engine.observe_artifact(
        domain="ui_design",
        modality="website",
        features=fingerprint,
        context=clean_context,
        preference=preference,
        strength=strength,
        source="deep_website_capture",
        source_reference=url,
        note="Full raw capture stored locally outside model context.",
    )
    evidence_id = str(saved["evidence_id"])
    raw_meta = save_raw_capture(engine.store.path, evidence_id, raw)
    return {
        "saved": True,
        "evidence_id": evidence_id,
        "domain": "ui_design",
        "modality": "website",
        "context": clean_context,
        "receipt": compact_receipt(fingerprint, raw_meta),
    }


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
    limit: int = 6,
    verbose: bool = False,
) -> dict[str, object]:
    """Return a token-efficient context-specific taste brief. Set verbose=true only when provenance/support details are needed."""
    full = engine.taste_brief(
        domain=domain,
        context=context,
        modality=modality,
        limit=max(1, min(int(limit), 12)),
    )
    if verbose:
        return full

    def compact_rows(rows: object, row_limit: int) -> list[dict[str, object]]:
        if not isinstance(rows, list):
            return []
        output: list[dict[str, object]] = []
        for row in rows[:row_limit]:
            if not isinstance(row, dict):
                continue
            output.append(
                {
                    "feature": row.get("feature"),
                    "value": row.get("value"),
                    "confidence": row.get("confidence"),
                }
            )
        return output

    max_items = max(1, min(int(limit), 8))
    return {
        "domain": full.get("domain"),
        "modality": full.get("modality"),
        "evidence_count": full.get("evidence_count"),
        "confidence": full.get("confidence"),
        "prefer": compact_rows(full.get("prefer"), max_items),
        "avoid": compact_rows(full.get("avoid"), max_items),
        "conflicts": compact_rows(full.get("conflicts"), min(3, max_items)),
    }


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

from __future__ import annotations

import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


def _capture_dir(db_path: str | Path) -> Path:
    root = Path(db_path).expanduser().resolve().parent / "captures"
    root.mkdir(parents=True, exist_ok=True)
    return root


def save_raw_capture(
    db_path: str | Path,
    evidence_id: str,
    payload: dict[str, Any],
) -> dict[str, object]:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    path = _capture_dir(db_path) / f"{evidence_id}.json.gz"
    with gzip.open(path, "wb", compresslevel=9) as handle:
        handle.write(raw)
    return {
        "stored": True,
        "sha256": digest,
        "raw_bytes": len(raw),
        "compressed_bytes": path.stat().st_size,
    }


def load_raw_capture(
    db_path: str | Path,
    evidence_id: str,
) -> dict[str, Any]:
    path = _capture_dir(db_path) / f"{evidence_id}.json.gz"
    if not path.is_file():
        raise ValueError(f"no raw capture stored for evidence {evidence_id}")
    with gzip.open(path, "rb") as handle:
        value = json.loads(handle.read().decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("stored capture is not a JSON object")
    return value


def _top(values: list[object], limit: int = 8) -> list[dict[str, object]]:
    counter = Counter(str(value) for value in values if value not in (None, "", "none", "normal"))
    total = sum(counter.values())
    if total <= 0:
        return []
    return [
        {"value": value, "count": count, "fraction": round(count / total, 4)}
        for value, count in counter.most_common(limit)
    ]


def _style_values(elements: list[dict[str, Any]], key: str) -> list[object]:
    values: list[object] = []
    for element in elements:
        style = element.get("style")
        if isinstance(style, dict):
            value = style.get(key)
            if value not in (None, ""):
                values.append(value)
    return values


def _representative_elements(
    elements: list[dict[str, Any]],
    limit: int = 14,
) -> list[dict[str, object]]:
    priority = {
        "h1": 0,
        "nav": 1,
        "header": 2,
        "button": 3,
        "h2": 4,
        "section": 5,
        "main": 6,
        "img": 7,
        "video": 8,
        "footer": 9,
    }
    ordered = sorted(
        elements,
        key=lambda item: (
            priority.get(str(item.get("tag")), 20),
            float((item.get("geometry") or {}).get("y_px") or 0),
        ),
    )
    rows: list[dict[str, object]] = []
    seen: set[tuple[object, ...]] = set()
    for element in ordered:
        geometry = element.get("geometry") if isinstance(element.get("geometry"), dict) else {}
        style = element.get("style") if isinstance(element.get("style"), dict) else {}
        key = (
            element.get("tag"),
            geometry.get("y_vh"),
            geometry.get("width_vw"),
            style.get("fontSize"),
            style.get("backgroundColor"),
        )
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "tag": element.get("tag"),
                "role": element.get("role"),
                "geometry": {
                    "x_vw": geometry.get("x_vw"),
                    "y_vh": geometry.get("y_vh"),
                    "width_vw": geometry.get("width_vw"),
                    "height_vh": geometry.get("height_vh"),
                },
                "style": {
                    "fontFamily": style.get("fontFamily"),
                    "fontSize": style.get("fontSize"),
                    "fontWeight": style.get("fontWeight"),
                    "lineHeight": style.get("lineHeight"),
                    "color": style.get("color"),
                    "backgroundColor": style.get("backgroundColor"),
                    "borderRadius": style.get("borderRadius"),
                    "boxShadow": style.get("boxShadow"),
                    "padding": style.get("padding"),
                    "gap": style.get("gap"),
                },
            }
        )
        if len(rows) >= limit:
            break
    return rows


def _animation_summary(animations: list[dict[str, Any]]) -> dict[str, object]:
    durations: list[object] = []
    delays: list[object] = []
    easings: list[object] = []
    target_tags: list[object] = []
    properties: list[object] = []
    examples: list[dict[str, object]] = []

    for animation in animations:
        timing = animation.get("timing") if isinstance(animation.get("timing"), dict) else {}
        target = animation.get("target") if isinstance(animation.get("target"), dict) else {}
        durations.append(timing.get("duration_ms"))
        delays.append(timing.get("delay_ms"))
        easings.append(timing.get("easing"))
        target_tags.append(target.get("tag"))

        frames = animation.get("keyframes")
        frame_props: set[str] = set()
        if isinstance(frames, list):
            for frame in frames:
                if isinstance(frame, dict):
                    frame_props.update(
                        key
                        for key in frame
                        if key not in {"computedOffset", "easing", "offset", "composite"}
                    )
        properties.extend(sorted(frame_props))

        if len(examples) < 6:
            examples.append(
                {
                    "target": {
                        "tag": target.get("tag"),
                        "id": target.get("id"),
                    },
                    "duration_ms": timing.get("duration_ms"),
                    "delay_ms": timing.get("delay_ms"),
                    "easing": timing.get("easing"),
                    "properties": sorted(frame_props),
                }
            )

    return {
        "count": len(animations),
        "durations": _top(durations, 8),
        "delays": _top(delays, 6),
        "easings": _top(easings, 6),
        "target_tags": _top(target_tags, 8),
        "properties": _top(properties, 10),
        "examples": examples,
    }


def compact_website_capture(raw: dict[str, Any]) -> dict[str, Any]:
    initial = raw.get("initial_state") if isinstance(raw.get("initial_state"), dict) else {}
    scrolled = raw.get("scrolled_state") if isinstance(raw.get("scrolled_state"), dict) else {}
    viewport = initial.get("viewport") if isinstance(initial.get("viewport"), dict) else {}
    elements = initial.get("elements") if isinstance(initial.get("elements"), list) else []
    animations = initial.get("animations") if isinstance(initial.get("animations"), list) else []
    scrolled_animations = (
        scrolled.get("animations") if isinstance(scrolled.get("animations"), list) else []
    )

    pixels = raw.get("rendered_pixels") if isinstance(raw.get("rendered_pixels"), dict) else {}
    palette = pixels.get("palette") if isinstance(pixels.get("palette"), dict) else {}
    density = pixels.get("visual_density") if isinstance(pixels.get("visual_density"), dict) else {}
    pixel_geometry = pixels.get("geometry") if isinstance(pixels.get("geometry"), dict) else {}

    tags = [element.get("tag") for element in elements if isinstance(element, dict)]
    positions = _style_values(elements, "position")
    displays = _style_values(elements, "display")

    css_variables = initial.get("cssVariables") if isinstance(initial.get("cssVariables"), dict) else {}
    selected_vars: dict[str, object] = {}
    preferred_tokens = (
        "color", "bg", "background", "font", "radius", "shadow",
        "space", "gap", "size", "width", "accent", "border",
    )
    for key, value in css_variables.items():
        lower = str(key).lower()
        if any(token in lower for token in preferred_tokens):
            selected_vars[str(key)] = value
        if len(selected_vars) >= 30:
            break

    fonts = initial.get("fonts") if isinstance(initial.get("fonts"), list) else []
    unique_fonts: list[dict[str, object]] = []
    seen_fonts: set[tuple[object, object, object]] = set()
    for font in fonts:
        if not isinstance(font, dict):
            continue
        key = (font.get("family"), font.get("weight"), font.get("style"))
        if key in seen_fonts:
            continue
        seen_fonts.add(key)
        unique_fonts.append(
            {
                "family": font.get("family"),
                "weight": font.get("weight"),
                "style": font.get("style"),
            }
        )
        if len(unique_fonts) >= 12:
            break

    document_height = int(viewport.get("documentHeight_px") or 0)
    viewport_height = max(1, int(viewport.get("height_px") or 1))

    return {
        "capture": {
            "kind": "live_forensic_compact",
            "fidelity": "dom_css+motion_timeline+rendered_pixels",
            "motion_observable": True,
            "interaction_observable": True,
            "source_url": initial.get("url"),
            "title": initial.get("title"),
        },
        "viewport": {
            "width_px": viewport.get("width_px"),
            "height_px": viewport.get("height_px"),
            "device_pixel_ratio": viewport.get("devicePixelRatio"),
            "document_height_px": document_height,
            "page_lengths": round(document_height / viewport_height, 2) if document_height else None,
        },
        "pixels": {
            "width_px": pixel_geometry.get("width_px"),
            "height_px": pixel_geometry.get("height_px"),
            "aspect_ratio": pixel_geometry.get("aspect_ratio"),
            "dominant_colors": (palette.get("dominant_colors") or [])[:8],
            "near_white_fraction": palette.get("near_white_fraction"),
            "near_black_fraction": palette.get("near_black_fraction"),
            "mean_saturation": palette.get("mean_saturation"),
            "edge_density": density.get("edge_density"),
            "luminance_stddev": density.get("luminance_stddev"),
        },
        "structure": {
            "sampled_element_count": len(elements),
            "tag_distribution": _top(tags, 12),
            "position_distribution": _top(positions, 8),
            "display_distribution": _top(displays, 8),
            "representative_elements": _representative_elements(elements),
        },
        "typography": {
            "loaded_fonts": unique_fonts,
            "font_families": _top(_style_values(elements, "fontFamily"), 8),
            "font_sizes": _top(_style_values(elements, "fontSize"), 10),
            "font_weights": _top(_style_values(elements, "fontWeight"), 8),
            "line_heights": _top(_style_values(elements, "lineHeight"), 8),
            "letter_spacing": _top(_style_values(elements, "letterSpacing"), 6),
        },
        "surface": {
            "text_colors": _top(_style_values(elements, "color"), 10),
            "background_colors": _top(_style_values(elements, "backgroundColor"), 10),
            "borders": _top(_style_values(elements, "border"), 8),
            "radii": _top(_style_values(elements, "borderRadius"), 8),
            "shadows": _top(_style_values(elements, "boxShadow"), 8),
            "padding": _top(_style_values(elements, "padding"), 8),
            "gaps": _top(_style_values(elements, "gap"), 8),
            "css_tokens": selected_vars,
        },
        "motion": {
            "initial": _animation_summary(animations),
            "after_scroll": _animation_summary(scrolled_animations),
            "transition_properties": _top(_style_values(elements, "transitionProperty"), 8),
            "transition_durations": _top(_style_values(elements, "transitionDuration"), 8),
            "transition_easing": _top(_style_values(elements, "transitionTimingFunction"), 8),
            "transition_delays": _top(_style_values(elements, "transitionDelay"), 6),
        },
        "responsive": {
            "media_queries": list(dict.fromkeys(initial.get("mediaQueries") or []))[:20],
        },
    }


def compact_receipt(
    fingerprint: dict[str, Any],
    raw_meta: dict[str, object] | None = None,
) -> dict[str, object]:
    structure = fingerprint.get("structure") if isinstance(fingerprint.get("structure"), dict) else {}
    motion = fingerprint.get("motion") if isinstance(fingerprint.get("motion"), dict) else {}
    initial_motion = motion.get("initial") if isinstance(motion.get("initial"), dict) else {}
    typography = fingerprint.get("typography") if isinstance(fingerprint.get("typography"), dict) else {}
    pixels = fingerprint.get("pixels") if isinstance(fingerprint.get("pixels"), dict) else {}

    return {
        "fidelity": "deep_compact",
        "sampled_elements": structure.get("sampled_element_count", 0),
        "animations_observed": initial_motion.get("count", 0),
        "top_fonts": [
            row.get("value")
            for row in (typography.get("font_families") or [])[:3]
            if isinstance(row, dict)
        ],
        "dominant_colors": [
            row.get("hex")
            for row in (pixels.get("dominant_colors") or [])[:5]
            if isinstance(row, dict)
        ],
        "raw_capture": raw_meta or {"stored": False},
    }

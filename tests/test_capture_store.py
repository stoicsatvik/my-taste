from __future__ import annotations

from my_taste.capture_store import compact_website_capture, load_raw_capture, save_raw_capture


def _sample_capture():
    element = {
        "tag": "h1",
        "role": None,
        "geometry": {
            "x_px": 120,
            "y_px": 100,
            "width_px": 900,
            "height_px": 120,
            "x_vw": 0.0833,
            "y_vh": 0.1,
            "width_vw": 0.625,
            "height_vh": 0.12,
        },
        "style": {
            "display": "block",
            "position": "static",
            "fontFamily": "Inter",
            "fontSize": "64px",
            "fontWeight": "700",
            "lineHeight": "64px",
            "letterSpacing": "-2px",
            "color": "rgb(20, 20, 20)",
            "backgroundColor": "rgba(0, 0, 0, 0)",
            "border": "0px none",
            "borderRadius": "0px",
            "boxShadow": "none",
            "opacity": "1",
            "gap": "normal",
            "padding": "0px",
            "margin": "0px",
            "transform": "none",
            "filter": "none",
            "transitionProperty": "opacity, transform",
            "transitionDuration": "0.6s",
            "transitionTimingFunction": "cubic-bezier(0.23, 1, 0.32, 1)",
            "transitionDelay": "0.1s",
        },
    }
    animation = {
        "target": {"tag": "h1", "id": "hero", "className": "hero"},
        "timing": {
            "delay_ms": 100,
            "duration_ms": 600,
            "easing": "cubic-bezier(0.23, 1, 0.32, 1)",
            "iterations": 1,
        },
        "keyframes": [
            {"opacity": "0", "transform": "translateY(18px)"},
            {"opacity": "1", "transform": "translateY(0px)"},
        ],
    }
    state = {
        "url": "https://example.test",
        "title": "Example",
        "viewport": {
            "width_px": 1440,
            "height_px": 1000,
            "devicePixelRatio": 2,
            "documentHeight_px": 4200,
        },
        "cssVariables": {"--color-bg": "#f5f5f2", "--radius-card": "12px"},
        "mediaQueries": ["(max-width: 768px)"],
        "fonts": [{"family": "Inter", "weight": "700", "style": "normal"}],
        "elements": [element],
        "animations": [animation],
    }
    return {
        "capture": {"kind": "live_dom_css_motion"},
        "rendered_pixels": {
            "geometry": {"width_px": 1440, "height_px": 4200, "aspect_ratio": 0.342857},
            "palette": {
                "dominant_colors": [{"hex": "#f5f5f2", "pixel_fraction": 0.7}],
                "near_white_fraction": 0.7,
                "near_black_fraction": 0.01,
                "mean_saturation": 0.12,
            },
            "visual_density": {"edge_density": 0.08, "luminance_stddev": 0.2},
        },
        "initial_state": state,
        "scrolled_state": state,
    }


def test_compact_capture_keeps_forensic_signal_without_raw_element_dump():
    raw = _sample_capture()
    compact = compact_website_capture(raw)

    assert compact["capture"]["fidelity"] == "dom_css+motion_timeline+rendered_pixels"
    assert compact["structure"]["sampled_element_count"] == 1
    assert compact["typography"]["font_families"][0]["value"] == "Inter"
    assert compact["motion"]["initial"]["count"] == 1
    assert compact["motion"]["initial"]["examples"][0]["duration_ms"] == 600
    assert compact["surface"]["css_tokens"]["--radius-card"] == "12px"
    assert "elements" not in compact
    assert "initial_state" not in compact


def test_raw_capture_is_compressed_and_round_trips(tmp_path):
    db_path = tmp_path / "taste.db"
    raw = _sample_capture()
    meta = save_raw_capture(db_path, "evidence-1", raw)

    assert meta["stored"] is True
    assert meta["compressed_bytes"] < meta["raw_bytes"]
    assert load_raw_capture(db_path, "evidence-1") == raw


def test_compaction_materially_reduces_large_browser_capture():
    raw = _sample_capture()
    base_element = raw["initial_state"]["elements"][0]
    raw["initial_state"]["elements"] = [
        {
            **base_element,
            "text": "Long visible text that should not be repeated into model context " * 8,
            "geometry": {
                **base_element["geometry"],
                "y_px": index * 48,
                "y_vh": index * 0.048,
            },
        }
        for index in range(120)
    ]
    raw["scrolled_state"]["elements"] = raw["initial_state"]["elements"]

    import json

    raw_bytes = len(json.dumps(raw, separators=(",", ":")).encode("utf-8"))
    compact = compact_website_capture(raw)
    compact_bytes = len(json.dumps(compact, separators=(",", ":")).encode("utf-8"))

    assert compact_bytes < raw_bytes * 0.25

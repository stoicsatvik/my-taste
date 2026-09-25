from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from PIL import Image, ImageFilter, ImageStat


def _hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def analyze_image_file(path: str | Path, *, palette_size: int = 12) -> dict[str, Any]:
    """Extract deterministic pixel-level evidence from a local screenshot/image.

    This complements, rather than replaces, semantic vision analysis. It measures
    what is actually present in the raster and never invents motion or interaction.
    """
    file_path = Path(path).expanduser().resolve()
    if not file_path.is_file():
        raise ValueError(f"image file does not exist: {file_path}")

    raw = file_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()

    with Image.open(file_path) as source:
        source.load()
        width, height = source.size
        if width <= 0 or height <= 0:
            raise ValueError("image has invalid dimensions")

        rgb = source.convert("RGB")
        # Bound analysis cost while preserving global pixel statistics.
        probe = rgb.copy()
        probe.thumbnail((512, 512), Image.Resampling.LANCZOS)
        total = probe.width * probe.height

        quantized = probe.quantize(
            colors=max(2, min(int(palette_size), 24)),
            method=Image.Quantize.MEDIANCUT,
        )
        palette = quantized.getpalette() or []
        counts = quantized.getcolors(maxcolors=256) or []
        counts.sort(reverse=True)

        dominant: list[dict[str, Any]] = []
        for count, index in counts[:palette_size]:
            base = index * 3
            color = tuple(palette[base : base + 3])
            if len(color) != 3:
                continue
            dominant.append(
                {
                    "hex": _hex((int(color[0]), int(color[1]), int(color[2]))),
                    "pixel_fraction": round(count / total, 6),
                }
            )

        pixels = list(probe.getdata())
        near_white = sum(1 for r, g, b in pixels if min(r, g, b) >= 240) / total
        near_black = sum(1 for r, g, b in pixels if max(r, g, b) <= 20) / total

        hsv = probe.convert("HSV")
        hsv_stat = ImageStat.Stat(hsv)
        mean_saturation = hsv_stat.mean[1] / 255.0
        mean_value = hsv_stat.mean[2] / 255.0

        gray = probe.convert("L")
        gray_stat = ImageStat.Stat(gray)
        mean_luminance = gray_stat.mean[0] / 255.0
        luminance_stddev = gray_stat.stddev[0] / 255.0

        edges = gray.filter(ImageFilter.FIND_EDGES)
        edge_hist = edges.histogram()
        edge_pixels = sum(edge_hist[48:])
        edge_density = edge_pixels / total

        orientation = (
            "landscape" if width > height else "portrait" if height > width else "square"
        )

        return {
            "capture": {
                "kind": "raster_pixel_analysis",
                "motion_observable": False,
                "interaction_observable": False,
                "sha256": digest,
            },
            "geometry": {
                "width_px": width,
                "height_px": height,
                "aspect_ratio": round(width / height, 6),
                "orientation": orientation,
            },
            "palette": {
                "dominant_colors": dominant,
                "near_white_fraction": round(near_white, 6),
                "near_black_fraction": round(near_black, 6),
                "mean_saturation": round(mean_saturation, 6),
                "mean_value": round(mean_value, 6),
            },
            "visual_density": {
                "mean_luminance": round(mean_luminance, 6),
                "luminance_stddev": round(luminance_stddev, 6),
                "edge_density": round(edge_density, 6),
            },
        }

from __future__ import annotations

from PIL import Image

from my_taste.media_analysis import analyze_image_file


def test_analyze_image_file_extracts_pixel_evidence(tmp_path):
    path = tmp_path / "sample.png"
    image = Image.new("RGB", (100, 50), (250, 250, 250))
    for x in range(50):
        for y in range(50):
            image.putpixel((x, y), (10, 20, 30))
    image.save(path)

    analysis = analyze_image_file(path, palette_size=4)

    assert analysis["geometry"]["width_px"] == 100
    assert analysis["geometry"]["height_px"] == 50
    assert analysis["geometry"]["aspect_ratio"] == 2.0
    assert analysis["capture"]["motion_observable"] is False
    assert analysis["capture"]["interaction_observable"] is False
    assert len(analysis["capture"]["sha256"]) == 64
    assert analysis["palette"]["dominant_colors"]

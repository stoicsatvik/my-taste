from __future__ import annotations

from my_taste.core.engine import TasteEngine


def test_observe_choice_updates_profile(tmp_path):
    engine = TasteEngine(tmp_path / "taste.db")
    result = engine.observe_choice(
        "The landing page loads in 1.2 seconds and shows the price immediately.",
        "Leverage innovative solutions to unlock seamless digital transformation.",
    )
    assert result["evidence_id"]
    profile = engine.profile()
    assert profile
    names = {item["feature"] for item in profile}
    assert "corporate_language" in names


def test_repeated_choices_rank_matching_candidate_higher(tmp_path):
    engine = TasteEngine(tmp_path / "taste.db")
    preferred = "Revenue grew 18% because checkout fell from four steps to two."
    rejected = "Leverage innovative seamless solutions to transform your dynamic ecosystem."
    for _ in range(8):
        engine.observe_choice(preferred, rejected)
    ranked = engine.rank_text([rejected, preferred])
    assert ranked[0].text == preferred
    assert ranked[0].score > ranked[1].score


def test_edit_is_pairwise_signal(tmp_path):
    engine = TasteEngine(tmp_path / "taste.db")
    original = "We provide innovative cutting-edge solutions."
    edited = "We build checkout systems that cut failed payments."
    engine.observe_edit(original, edited)
    evidence = engine.store.recent_evidence("writing", 1)[0]
    assert evidence.source == "user_edit"
    assert evidence.payload["preferred"] == edited
    assert evidence.payload["rejected"] == original


def test_empty_rank_is_safe(tmp_path):
    engine = TasteEngine(tmp_path / "taste.db")
    assert engine.rank_text([]) == []


def test_identical_choice_is_rejected(tmp_path):
    engine = TasteEngine(tmp_path / "taste.db")
    try:
        engine.observe_choice("same", "same")
    except ValueError as exc:
        assert "must differ" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_observe_and_retrieve_ui_artifact(tmp_path):
    engine = TasteEngine(tmp_path / "taste.db")
    saved = engine.observe_artifact(
        domain="ui_design",
        modality="website",
        context={"surface": "landing_page", "industry": "saas"},
        features={
            "density": "low",
            "whitespace": "high",
            "palette": ["neutral", "single_accent"],
            "border_radius": "medium",
        },
        source_reference="https://example.test",
    )
    assert saved["feature_count"] == 4

    hits = engine.retrieve_taste(
        domain="ui_design",
        modality="website",
        context={"surface": "landing_page", "industry": "saas"},
    )
    assert hits[0]["source_reference"] == "https://example.test"
    assert hits[0]["features"]["density"] == "low"


def test_context_retrieval_prefers_closer_match(tmp_path):
    engine = TasteEngine(tmp_path / "taste.db")
    engine.observe_artifact(
        domain="writing",
        modality="text",
        context={"surface": "cold_email", "audience": "founder"},
        features={"tone": "direct", "sentence_length": "short"},
        source_reference="cold",
    )
    engine.observe_artifact(
        domain="writing",
        modality="text",
        context={"surface": "essay", "audience": "student"},
        features={"tone": "reflective", "sentence_length": "long"},
        source_reference="essay",
    )

    hits = engine.retrieve_taste(
        domain="writing",
        modality="text",
        context={"surface": "cold_email", "audience": "founder"},
    )
    assert hits[0]["source_reference"] == "cold"


def test_video_style_can_be_saved_and_retrieved(tmp_path):
    engine = TasteEngine(tmp_path / "taste.db")
    engine.observe_artifact(
        domain="video",
        modality="video",
        context={"platform": "instagram", "format": "reel"},
        features={
            "hook": "immediate",
            "pacing": "fast",
            "captions": "minimal",
            "cuts_per_minute": 18,
            "camera_motion": "restrained",
        },
        source_reference="video:fixture-1",
    )

    hits = engine.retrieve_taste(
        domain="video",
        modality="video",
        context={"platform": "instagram", "format": "reel"},
    )
    assert hits
    assert hits[0]["features"]["pacing"] == "fast"


def test_rank_profiles_uses_positive_and_negative_evidence(tmp_path):
    engine = TasteEngine(tmp_path / "taste.db")
    context = {"surface": "dashboard"}
    engine.observe_artifact(
        domain="ui_design",
        modality="website",
        context=context,
        features={"density": "low", "shadow": "subtle", "palette": ["neutral"]},
        preference="positive",
    )
    engine.observe_artifact(
        domain="ui_design",
        modality="website",
        context=context,
        features={"density": "high", "shadow": "heavy", "palette": ["neon"]},
        preference="negative",
    )

    ranked = engine.rank_profiles(
        [
            {
                "id": "quiet",
                "features": {"density": "low", "shadow": "subtle", "palette": ["neutral"]},
            },
            {
                "id": "loud",
                "features": {"density": "high", "shadow": "heavy", "palette": ["neon"]},
            },
        ],
        domain="ui_design",
        modality="website",
        context=context,
    )
    assert ranked[0]["id"] == "quiet"
    assert ranked[0]["score"] > ranked[1]["score"]


def test_taste_brief_applies_video_context_and_avoids_opposite_style(tmp_path):
    engine = TasteEngine(tmp_path / "taste.db")
    reel = {"platform": "instagram", "format": "reel", "goal": "retention"}

    engine.observe_artifact(
        domain="video",
        modality="video",
        context=reel,
        features={"pacing": "fast", "captions": "minimal", "ending": "hard-stop"},
        preference="positive",
    )
    engine.observe_artifact(
        domain="video",
        modality="video",
        context=reel,
        features={"pacing": "slow", "captions": "dense", "ending": "long-outro"},
        preference="negative",
    )
    engine.observe_artifact(
        domain="video",
        modality="video",
        context={"platform": "youtube", "format": "documentary", "goal": "explanation"},
        features={"pacing": "slow", "captions": "minimal", "ending": "resolved"},
        preference="positive",
        source_reference="unrelated-documentary",
    )

    brief = engine.taste_brief(
        domain="video",
        modality="video",
        context=reel,
    )

    preferred = {(row["feature"], str(row["value"])) for row in brief["prefer"]}
    avoided = {(row["feature"], str(row["value"])) for row in brief["avoid"]}

    assert ("pacing", "fast") in preferred
    assert ("pacing", "slow") in avoided
    assert brief["evidence_count"] >= 2
    assert brief["confidence"] > 0


def test_context_relevance_penalizes_wrong_surface(tmp_path):
    engine = TasteEngine(tmp_path / "taste.db")
    engine.observe_artifact(
        domain="ui_design",
        modality="website",
        context={"surface": "landing_page", "goal": "conversion"},
        features={"density": "low"},
        source_reference="landing",
    )
    engine.observe_artifact(
        domain="ui_design",
        modality="website",
        context={"surface": "admin_dashboard", "goal": "operations"},
        features={"density": "high"},
        source_reference="dashboard",
    )

    hits = engine.retrieve_taste(
        domain="ui_design",
        modality="website",
        context={"surface": "landing_page", "goal": "conversion"},
    )

    scores = {item["source_reference"]: item["relevance"] for item in hits}
    assert scores["landing"] > scores["dashboard"]


def test_nested_deep_capture_features_rank_recursively(tmp_path):
    engine = TasteEngine(tmp_path / "taste.db")
    context = {"surface": "landing_page", "capture_fidelity": "static_raster"}

    engine.observe_artifact(
        domain="ui_design",
        modality="screenshot",
        context=context,
        features={
            "geometry": {"hero_height_ratio": 0.72, "content_width_ratio": 0.84},
            "surface": {"radius_px": 12, "shadow": "subtle"},
            "typography": {"display_scale": "oversized", "body_density": "low"},
        },
        preference="positive",
    )

    ranked = engine.rank_profiles(
        [
            {
                "id": "matching",
                "features": {
                    "geometry": {"hero_height_ratio": 0.70, "content_width_ratio": 0.82},
                    "surface": {"radius_px": 12, "shadow": "subtle"},
                    "typography": {"display_scale": "oversized", "body_density": "low"},
                },
            },
            {
                "id": "different",
                "features": {
                    "geometry": {"hero_height_ratio": 0.30, "content_width_ratio": 0.55},
                    "surface": {"radius_px": 2, "shadow": "heavy"},
                    "typography": {"display_scale": "small", "body_density": "high"},
                },
            },
        ],
        domain="ui_design",
        modality="screenshot",
        context=context,
    )

    assert ranked[0]["id"] == "matching"


def test_taste_brief_flattens_nested_features(tmp_path):
    engine = TasteEngine(tmp_path / "taste.db")
    engine.observe_artifact(
        domain="ui_design",
        modality="screenshot",
        context={"surface": "landing_page"},
        features={
            "typography": {"display": {"weight": 700, "style": "clean-sans"}},
            "surface": {"radius_px": 14},
        },
    )

    brief = engine.taste_brief(
        domain="ui_design",
        modality="screenshot",
        context={"surface": "landing_page"},
    )
    names = {row["feature"] for row in brief["prefer"]}
    assert "typography.display.weight" in names
    assert "typography.display.style" in names
    assert "surface.radius_px" in names

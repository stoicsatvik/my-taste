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

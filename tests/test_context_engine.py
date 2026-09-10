from __future__ import annotations

from my_taste.core.context_engine import ContextTasteEngine


def test_context_preferences_do_not_collapse_into_one_global_rule(tmp_path):
    engine = ContextTasteEngine(tmp_path / "taste.db")

    concise = "Price: ₹30,000. Delivery: 3 days."
    expansive = (
        "We begin by explaining the architecture, trade-offs, implementation details, "
        "testing strategy, deployment model, and the reasoning behind each decision."
    )

    for _ in range(6):
        engine.observe_choice(
            concise,
            expansive,
            context="sales landing page",
        )
        engine.observe_choice(
            expansive,
            concise,
            context="technical explanation",
        )

    sales_ranked = engine.rank_text(
        [expansive, concise],
        context="sales landing page",
    )
    technical_ranked = engine.rank_text(
        [concise, expansive],
        context="technical explanation",
    )

    assert sales_ranked[0].text == concise
    assert technical_ranked[0].text == expansive


def test_context_is_normalized(tmp_path):
    engine = ContextTasteEngine(tmp_path / "taste.db")
    engine.observe_choice(
        "Use the number 42.",
        "Use vague language.",
        context="  Product   Page  ",
    )

    assert engine.get_context_weights("writing", "product page")
    assert engine.get_context_weights("writing", "PRODUCT PAGE")


def test_provenance_can_be_filtered_by_context(tmp_path):
    engine = ContextTasteEngine(tmp_path / "taste.db")
    engine.observe_choice("A 10% gain.", "A meaningful gain.", context="investor update")
    engine.observe_choice("Short copy.", "Long generic copy.", context="landing page")

    evidence = engine.provenance(context="investor update")

    assert len(evidence) == 1
    assert evidence[0]["context"] == "investor update"
    assert evidence[0]["preferred"] == "A 10% gain."


def test_taste_context_returns_agent_instructions(tmp_path):
    engine = ContextTasteEngine(tmp_path / "taste.db")
    for _ in range(3):
        engine.observe_choice(
            "Revenue grew 18%.",
            "We achieved innovative transformation.",
            context="founder update",
        )

    compiled = engine.taste_context(context="founder update")

    assert compiled["context"] == "founder update"
    assert compiled["instructions"]
    assert compiled["evidence_ids"]

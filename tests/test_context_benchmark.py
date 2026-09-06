from __future__ import annotations

from my_taste.benchmark import synthetic_context_benchmark
from my_taste.core.engine import TasteEngine


def test_context_conditioning_can_reverse_same_pair(tmp_path):
    engine = TasteEngine(tmp_path / "taste.db")
    concise = "Revenue rose 18% after checkout dropped from four steps to two."
    expansive = "We leverage innovative seamless solutions to transform a dynamic ecosystem with comprehensive strategic capabilities."
    for _ in range(4):
        engine.observe_choice(concise, expansive, context="status update")
        engine.observe_choice(expansive, concise, context="ceremonial speech")

    assert engine.pairwise_probability(concise, expansive, context="status update") > 0.5
    assert engine.pairwise_probability(expansive, concise, context="ceremonial speech") > 0.5


def test_context_does_not_cross_domain(tmp_path):
    engine = TasteEngine(tmp_path / "taste.db")
    engine.observe_choice("short concrete copy", "innovative seamless ecosystem", domain="writing", context="status")
    assert engine.pairwise_probability("short concrete copy", "innovative seamless ecosystem", domain="music", context="status") == 0.5


def test_synthetic_benchmark_reports_matched_baselines():
    result = synthetic_context_benchmark()
    assert set(result) == {"v0_1_no_context", "v0_2_context"}
    for metrics in result.values():
        assert 0.0 <= metrics["accuracy"] <= 1.0
        assert 0.0 <= metrics["brier"] <= 1.0

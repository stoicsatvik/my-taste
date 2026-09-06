from __future__ import annotations

from my_taste.tastebench import deterministic_context_cases, run_domain_leakage_check, run_sealed_context_benchmark


def test_sealed_pairs_are_disjoint_from_training_wording():
    for case in deterministic_context_cases():
        train_text = {(pair.preferred, pair.rejected, pair.context) for pair in case.train}
        sealed_text = {(pair.preferred, pair.rejected, pair.context) for pair in case.sealed}
        assert train_text.isdisjoint(sealed_text)


def test_tastebench_is_deterministic():
    assert run_sealed_context_benchmark() == run_sealed_context_benchmark()


def test_tastebench_reports_matched_metrics():
    result = run_sealed_context_benchmark()
    assert result["sealed_pairs"] == 4.0
    for key in ("v0_1_accuracy", "v0_1_brier", "v0_2_accuracy", "v0_2_brier"):
        assert 0.0 <= result[key] <= 1.0


def test_domain_leakage_check_is_deterministic():
    assert run_domain_leakage_check() == run_domain_leakage_check()


def test_training_one_domain_does_not_move_control_domain():
    result = run_domain_leakage_check()
    assert result["trained_domain_probability"] > 0.5
    assert result["control_before"] == 0.5
    assert result["control_after"] == 0.5
    assert result["absolute_leakage"] == 0.0

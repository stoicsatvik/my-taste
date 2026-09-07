from __future__ import annotations

from my_taste.tastebench import deterministic_context_cases, run_domain_leakage_check, run_sealed_context_benchmark


def test_sealed_pairs_are_disjoint_from_training_wording():
    for case in deterministic_context_cases():
        train_text = {(pair.preferred, pair.rejected, pair.context) for pair in case.train}
        sealed_text = {(pair.preferred, pair.rejected, pair.context) for pair in case.sealed}
        assert train_text.isdisjoint(sealed_text)


def test_sealed_candidate_strings_never_appear_in_training_evidence():
    cases = deterministic_context_cases()
    training_strings = {
        text
        for case in cases
        for pair in case.train
        for text in (pair.preferred, pair.rejected)
    }
    sealed_strings = {
        text
        for case in cases
        for pair in case.sealed
        for text in (pair.preferred, pair.rejected)
    }
    assert training_strings.isdisjoint(sealed_strings)


def test_tastebench_reaches_frozen_minimum_sample_floor():
    cases = deterministic_context_cases()
    assert sum(len(case.sealed) for case in cases) == 32
    assert len({pair.context for case in cases for pair in case.sealed}) == 8


def test_tastebench_is_deterministic():
    assert run_sealed_context_benchmark() == run_sealed_context_benchmark()


def test_tastebench_reports_matched_metrics():
    result = run_sealed_context_benchmark()
    assert result["sealed_pairs"] == 32.0
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

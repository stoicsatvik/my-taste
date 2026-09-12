from __future__ import annotations

import pytest

from my_taste.driftbench import run_asymmetric_drift_matrix, run_preference_drift_benchmark


def test_drift_benchmark_is_deterministic():
    first = run_preference_drift_benchmark()
    second = run_preference_drift_benchmark()
    assert first == second


def test_drift_benchmark_preserves_reversal_trajectory():
    result = run_preference_drift_benchmark(pre_updates=8, post_updates=8)
    assert result.pre_drift_probability > 0.5
    assert len(result.post_drift_probabilities) == 8
    assert all(0.0 <= p <= 1.0 for p in result.post_drift_probabilities)
    assert all(a <= b for a, b in zip(result.post_drift_probabilities, result.post_drift_probabilities[1:]))
    if result.recovery_updates is not None:
        assert 1 <= result.recovery_updates <= 8
        assert result.post_drift_probabilities[result.recovery_updates - 1] > 0.5


def test_asymmetric_drift_matrix_is_deterministic_and_bounded():
    first = run_asymmetric_drift_matrix()
    second = run_asymmetric_drift_matrix()
    assert first == second
    assert [(c.pre_updates, c.post_updates) for c in first] == [(8, 2), (32, 2), (128, 2), (128, 8)]
    for case in first:
        assert len(case.result.post_drift_probabilities) == case.post_updates
        assert 0.0 <= case.result.final_probability <= 1.0
        assert all(a <= b for a, b in zip(case.result.post_drift_probabilities, case.result.post_drift_probabilities[1:]))


def test_asymmetric_drift_matrix_rejects_invalid_case_sets():
    with pytest.raises(ValueError):
        run_asymmetric_drift_matrix(cases=())
    with pytest.raises(ValueError):
        run_asymmetric_drift_matrix(cases=((8, 2), (8, 2)))
    with pytest.raises(ValueError):
        run_asymmetric_drift_matrix(cases=((8, 0),))


def test_drift_benchmark_rejects_invalid_budgets():
    with pytest.raises(ValueError):
        run_preference_drift_benchmark(pre_updates=0)
    with pytest.raises(ValueError):
        run_preference_drift_benchmark(post_updates=0)

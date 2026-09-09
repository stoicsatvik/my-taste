import pytest

from my_taste.temporalbench import (
    run_adversarial_temporal_gate,
    run_temporal_policy_matrix,
    run_temporal_window_comparison,
)


def test_temporal_comparison_is_deterministic_and_bounded():
    first = run_temporal_window_comparison()
    second = run_temporal_window_comparison()
    assert first == second
    assert len(first.accumulator_trajectory) == 8
    assert len(first.windowed_trajectory) == 8
    assert all(0.0 <= p <= 1.0 for p in first.accumulator_trajectory + first.windowed_trajectory)
    assert 0.0 <= first.stable_accumulator <= 1.0
    assert 0.0 <= first.stable_windowed <= 1.0


def test_temporal_challenger_contract_does_not_encode_a_promotion_result():
    result = run_temporal_window_comparison(pre_updates=32, post_updates=4, window=8)
    assert result.pre_updates == 32
    assert result.post_updates == 4
    assert result.window == 8
    assert result.accumulator_trajectory
    assert result.windowed_trajectory


def test_temporal_policy_matrix_is_deterministic_matched_and_bounded():
    first = run_temporal_policy_matrix()
    second = run_temporal_policy_matrix()
    assert first == second
    assert tuple(score.window for score in first) == (4, 8, 16, 32)
    assert all(score.cases == 5 for score in first)
    for score in first:
        assert 0.0 <= score.mean_post_drift_brier <= 1.0
        assert 0.0 <= score.worst_post_drift_brier <= 1.0
        assert 0.0 <= score.mean_stable_brier <= 1.0
        assert 0.0 <= score.worst_stable_brier <= 1.0
        assert score.mean_post_drift_brier <= score.worst_post_drift_brier
        assert score.mean_stable_brier <= score.worst_stable_brier


def test_temporal_policy_matrix_does_not_hardcode_a_winner():
    scores = run_temporal_policy_matrix(windows=(4, 16), cases=((32, 2), (128, 8)))
    assert [score.window for score in scores] == [4, 16]
    assert all(score.cases == 2 for score in scores)


def test_adversarial_gate_is_deterministic_complete_and_bounded():
    first = run_adversarial_temporal_gate()
    second = run_adversarial_temporal_gate()
    assert first == second
    assert tuple(score.window for score in first) == (4, 8, 16, 32)
    for score in first:
        assert 0.0 <= score.mean_post_drift_brier <= 1.0
        assert 0.0 <= score.worst_stable_brier <= 1.0
        assert 0.0 <= score.neighboring_context_delta <= 1.0
        assert 0.0 <= score.oscillation_phase_end_accuracy <= 1.0
        assert 0.0 <= score.oscillation_phase_end_brier <= 1.0
        assert 0.0 <= score.source_conflict_probability <= 1.0
        assert 0.0 <= score.source_conflict_distance <= 0.5
        assert isinstance(score.passes_gate, bool)


def test_adversarial_gate_uses_requested_policy_set_without_hardcoded_winner():
    scores = run_adversarial_temporal_gate(windows=(4, 16))
    assert tuple(score.window for score in scores) == (4, 16)


@pytest.mark.parametrize("kwargs", [{"pre_updates": 0}, {"post_updates": 0}, {"window": 0}])
def test_temporal_comparison_fails_closed(kwargs):
    with pytest.raises(ValueError):
        run_temporal_window_comparison(**kwargs)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"windows": ()},
        {"cases": ()},
        {"windows": (0, 8)},
        {"windows": (8, 8)},
        {"cases": ((32, 0),)},
    ],
)
def test_temporal_policy_matrix_fails_closed(kwargs):
    with pytest.raises(ValueError):
        run_temporal_policy_matrix(**kwargs)


@pytest.mark.parametrize("windows", [(), (0, 8), (8, 8)])
def test_adversarial_gate_fails_closed(windows):
    with pytest.raises(ValueError):
        run_adversarial_temporal_gate(windows=windows)

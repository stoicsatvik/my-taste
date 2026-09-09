import pytest

from my_taste.temporalbench import run_temporal_window_comparison


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
    # Record both adaptation and retention; promotion thresholds must be preregistered separately.
    assert result.accumulator_trajectory
    assert result.windowed_trajectory


@pytest.mark.parametrize("kwargs", [{"pre_updates": 0}, {"post_updates": 0}, {"window": 0}])
def test_temporal_comparison_fails_closed(kwargs):
    with pytest.raises(ValueError):
        run_temporal_window_comparison(**kwargs)

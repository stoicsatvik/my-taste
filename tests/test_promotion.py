from my_taste.promotion import PromotionThresholds, evaluate_v02_promotion


def metrics(**overrides):
    values = {
        "v0_1_accuracy": 0.60,
        "v0_1_brier": 0.24,
        "v0_2_accuracy": 0.66,
        "v0_2_brier": 0.20,
        "sealed_pairs": 32.0,
    }
    values.update(overrides)
    return values


def test_current_four_pair_foundation_cannot_promote():
    result = evaluate_v02_promotion(
        metrics(sealed_pairs=4.0), {"absolute_leakage": 0.0},
        baseline_tests_passed=True, challenger_tests_passed=True,
    )
    assert result["sample_gate"] is False
    assert result["promote"] is False


def test_accuracy_path_promotes_only_when_all_hard_gates_pass():
    result = evaluate_v02_promotion(
        metrics(), {"absolute_leakage": 0.0},
        baseline_tests_passed=True, challenger_tests_passed=True,
    )
    assert result["accuracy_path"] is True
    assert result["promote"] is True


def test_calibration_path_allows_small_accuracy_tradeoff():
    result = evaluate_v02_promotion(
        metrics(v0_2_accuracy=0.59, v0_2_brier=0.21), {"absolute_leakage": 0.0},
        baseline_tests_passed=True, challenger_tests_passed=True,
    )
    assert result["accuracy_path"] is False
    assert result["calibration_path"] is True
    assert result["promote"] is True


def test_calibration_path_rejects_excess_accuracy_regression():
    result = evaluate_v02_promotion(
        metrics(v0_2_accuracy=0.57, v0_2_brier=0.18), {"absolute_leakage": 0.0},
        baseline_tests_passed=True, challenger_tests_passed=True,
    )
    assert result["calibration_path"] is False
    assert result["promote"] is False


def test_domain_leakage_and_test_failures_are_hard_vetoes():
    leaked = evaluate_v02_promotion(
        metrics(), {"absolute_leakage": 1e-6},
        baseline_tests_passed=True, challenger_tests_passed=True,
    )
    failed_tests = evaluate_v02_promotion(
        metrics(), {"absolute_leakage": 0.0},
        baseline_tests_passed=True, challenger_tests_passed=False,
    )
    assert leaked["promote"] is False
    assert failed_tests["promote"] is False


def test_missing_metrics_fail_closed():
    incomplete = metrics()
    del incomplete["v0_2_brier"]
    try:
        evaluate_v02_promotion(
            incomplete, {"absolute_leakage": 0.0},
            baseline_tests_passed=True, challenger_tests_passed=True,
        )
    except ValueError as exc:
        assert "v0_2_brier" in str(exc)
    else:
        raise AssertionError("missing metric must fail closed")

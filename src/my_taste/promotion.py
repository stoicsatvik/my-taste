from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PromotionThresholds:
    min_sealed_pairs: int = 32
    min_accuracy_gain: float = 0.05
    max_accuracy_regression_for_calibration_path: float = 0.02
    min_brier_improvement: float = 0.02
    max_absolute_domain_leakage: float = 1e-12


def evaluate_v02_promotion(
    benchmark: dict[str, float],
    leakage: dict[str, float],
    *,
    baseline_tests_passed: bool,
    challenger_tests_passed: bool,
    thresholds: PromotionThresholds = PromotionThresholds(),
) -> dict[str, object]:
    """Apply preregistered V0.2 gates without interpreting benchmark results post hoc."""
    required = {"v0_1_accuracy", "v0_1_brier", "v0_2_accuracy", "v0_2_brier", "sealed_pairs"}
    missing = sorted(required - benchmark.keys())
    if missing:
        raise ValueError(f"missing benchmark metrics: {', '.join(missing)}")
    if "absolute_leakage" not in leakage:
        raise ValueError("missing leakage metric: absolute_leakage")

    accuracy_gain = benchmark["v0_2_accuracy"] - benchmark["v0_1_accuracy"]
    brier_improvement = benchmark["v0_1_brier"] - benchmark["v0_2_brier"]
    sample_gate = benchmark["sealed_pairs"] >= thresholds.min_sealed_pairs
    accuracy_path = accuracy_gain >= thresholds.min_accuracy_gain
    calibration_path = (
        accuracy_gain >= -thresholds.max_accuracy_regression_for_calibration_path
        and brier_improvement >= thresholds.min_brier_improvement
    )
    leakage_gate = leakage["absolute_leakage"] <= thresholds.max_absolute_domain_leakage
    tests_gate = baseline_tests_passed and challenger_tests_passed
    evidence_gate = accuracy_path or calibration_path
    promote = sample_gate and leakage_gate and tests_gate and evidence_gate

    return {
        "promote": promote,
        "sample_gate": sample_gate,
        "leakage_gate": leakage_gate,
        "tests_gate": tests_gate,
        "accuracy_path": accuracy_path,
        "calibration_path": calibration_path,
        "accuracy_gain": accuracy_gain,
        "brier_improvement": brier_improvement,
        "sealed_pairs": benchmark["sealed_pairs"],
    }

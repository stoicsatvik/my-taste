from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from .core.engine import TasteEngine


CONCISE = "Revenue rose 18% after checkout dropped from four steps to two."
EXPANSIVE = "We leverage innovative seamless solutions to transform a dynamic ecosystem with comprehensive strategic capabilities."


@dataclass(frozen=True)
class TemporalComparison:
    pre_updates: int
    post_updates: int
    window: int
    accumulator_trajectory: tuple[float, ...]
    windowed_trajectory: tuple[float, ...]
    stable_accumulator: float
    stable_windowed: float


@dataclass(frozen=True)
class TemporalPolicyScore:
    window: int
    cases: int
    mean_post_drift_brier: float
    worst_post_drift_brier: float
    mean_stable_brier: float
    worst_stable_brier: float


@dataclass(frozen=True)
class AdversarialTemporalScore:
    window: int
    mean_post_drift_brier: float
    worst_stable_brier: float
    neighboring_context_delta: float
    oscillation_phase_end_accuracy: float
    oscillation_phase_end_brier: float
    source_conflict_probability: float
    source_conflict_distance: float
    passes_gate: bool


def _probability(history: list[tuple[str, str, str]], *, window: int | None = None) -> float:
    selected = history if window is None else history[-window:]
    with TemporaryDirectory() as directory:
        engine = TasteEngine(Path(directory) / "taste.db")
        for preferred, rejected, source in selected:
            engine.observe_choice(preferred, rejected, context="status update", source=source)
        return engine.pairwise_probability(EXPANSIVE, CONCISE, context="status update")


def _context_probability(
    history: list[tuple[str, str, str, str]],
    *,
    context: str,
    preferred: str,
    rejected: str,
    window: int | None,
) -> float:
    selected = history if window is None else history[-window:]
    with TemporaryDirectory() as directory:
        engine = TasteEngine(Path(directory) / "taste.db")
        for winner, loser, observation_context, source in selected:
            engine.observe_choice(winner, loser, context=observation_context, source=source)
        return engine.pairwise_probability(preferred, rejected, context=context)


def run_temporal_window_comparison(*, pre_updates: int = 128, post_updates: int = 8, window: int = 8) -> TemporalComparison:
    """Compare frozen accumulation with a bounded-history challenger under identical observations."""
    if pre_updates < 1 or post_updates < 1 or window < 1:
        raise ValueError("pre_updates, post_updates and window must be positive")

    history = [(CONCISE, EXPANSIVE, "synthetic_pre_drift") for _ in range(pre_updates)]
    accumulator: list[float] = []
    windowed: list[float] = []
    for _ in range(post_updates):
        history.append((EXPANSIVE, CONCISE, "synthetic_post_drift"))
        accumulator.append(_probability(history))
        windowed.append(_probability(history, window=window))

    stable = [(CONCISE, EXPANSIVE, "synthetic_stable") for _ in range(pre_updates + post_updates)]
    stable_accumulator = 1.0 - _probability(stable)
    stable_windowed = 1.0 - _probability(stable, window=window)
    return TemporalComparison(
        pre_updates=pre_updates,
        post_updates=post_updates,
        window=window,
        accumulator_trajectory=tuple(accumulator),
        windowed_trajectory=tuple(windowed),
        stable_accumulator=stable_accumulator,
        stable_windowed=stable_windowed,
    )


def run_temporal_policy_matrix(
    *,
    windows: tuple[int, ...] = (4, 8, 16, 32),
    cases: tuple[tuple[int, int], ...] = ((8, 2), (32, 2), (128, 2), (32, 8), (128, 8)),
) -> tuple[TemporalPolicyScore, ...]:
    """Score bounded-history policies on the frozen matched synthetic matrix."""
    if not windows or not cases or any(w < 1 for w in windows):
        raise ValueError("windows and cases must be non-empty and positive")
    if len(set(windows)) != len(windows) or any(pre < 1 or post < 1 for pre, post in cases):
        raise ValueError("windows must be unique and all case budgets positive")

    scores: list[TemporalPolicyScore] = []
    for window in windows:
        drift_briers: list[float] = []
        stable_briers: list[float] = []
        for pre_updates, post_updates in cases:
            result = run_temporal_window_comparison(pre_updates=pre_updates, post_updates=post_updates, window=window)
            drift_briers.append(sum((1.0 - p) ** 2 for p in result.windowed_trajectory) / len(result.windowed_trajectory))
            stable_briers.append((1.0 - result.stable_windowed) ** 2)
        scores.append(TemporalPolicyScore(window, len(cases), sum(drift_briers) / len(drift_briers), max(drift_briers), sum(stable_briers) / len(stable_briers), max(stable_briers)))
    return tuple(scores)


def _accumulator_mean_drift_brier() -> float:
    cases = ((8, 2), (32, 2), (128, 2), (32, 8), (128, 8))
    values = []
    for pre, post in cases:
        result = run_temporal_window_comparison(pre_updates=pre, post_updates=post, window=8)
        values.append(sum((1.0 - p) ** 2 for p in result.accumulator_trajectory) / len(result.accumulator_trajectory))
    return sum(values) / len(values)


def run_adversarial_temporal_gate(*, windows: tuple[int, ...] = (4, 8, 16, 32)) -> tuple[AdversarialTemporalScore, ...]:
    """Execute the regimes and thresholds frozen in TEMPORAL_PROMOTION_PROTOCOL_V01.md."""
    if not windows or any(w < 1 for w in windows) or len(set(windows)) != len(windows):
        raise ValueError("windows must be non-empty, unique and positive")

    matrix = {score.window: score for score in run_temporal_policy_matrix(windows=windows)}
    accumulator_mean = _accumulator_mean_drift_brier()
    scores: list[AdversarialTemporalScore] = []

    for window in windows:
        # Context-local reversal: neighboring context remains stable while target reverses.
        history: list[tuple[str, str, str, str]] = []
        for _ in range(8):
            history.append((CONCISE, EXPANSIVE, "status update", "synthetic_context_old"))
            history.append((CONCISE, EXPANSIVE, "release note", "synthetic_neighbor_stable"))
        neighbor_before = _context_probability(history, context="release note", preferred=CONCISE, rejected=EXPANSIVE, window=window)
        for _ in range(8):
            history.append((EXPANSIVE, CONCISE, "status update", "synthetic_context_new"))
        neighbor_after = _context_probability(history, context="release note", preferred=CONCISE, rejected=EXPANSIVE, window=window)
        neighbor_delta = abs(neighbor_after - neighbor_before)

        # Four equal oscillation phases. Score the preferred direction at each phase end.
        oscillation: list[tuple[str, str, str, str]] = []
        phase_probabilities: list[float] = []
        for phase in range(4):
            preferred, rejected = (CONCISE, EXPANSIVE) if phase % 2 == 0 else (EXPANSIVE, CONCISE)
            for _ in range(8):
                oscillation.append((preferred, rejected, "status update", f"synthetic_phase_{phase}"))
            phase_probabilities.append(_context_probability(oscillation, context="status update", preferred=preferred, rejected=rejected, window=window))
        oscillation_accuracy = sum(p > 0.5 for p in phase_probabilities) / len(phase_probabilities)
        oscillation_brier = sum((1.0 - p) ** 2 for p in phase_probabilities) / len(phase_probabilities)

        # Equal-count provenance conflict. Source labels are preserved in evidence.
        conflict: list[tuple[str, str, str, str]] = []
        for _ in range(8):
            conflict.append((CONCISE, EXPANSIVE, "status update", "synthetic_source_a"))
            conflict.append((EXPANSIVE, CONCISE, "status update", "synthetic_source_b"))
        conflict_probability = _context_probability(conflict, context="status update", preferred=CONCISE, rejected=EXPANSIVE, window=window)
        conflict_distance = abs(conflict_probability - 0.5)

        base = matrix[window]
        passes = (
            base.mean_post_drift_brier <= accumulator_mean * 0.75
            and base.worst_stable_brier <= 0.005
            and neighbor_delta <= 0.02
            and oscillation_accuracy >= 0.75
            and conflict_distance <= 0.15
        )
        scores.append(AdversarialTemporalScore(window, base.mean_post_drift_brier, base.worst_stable_brier, neighbor_delta, oscillation_accuracy, oscillation_brier, conflict_probability, conflict_distance, passes))
    return tuple(scores)

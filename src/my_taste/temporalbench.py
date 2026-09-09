from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from .core.engine import TasteEngine


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


def _probability(history: list[tuple[str, str, str]], *, window: int | None = None) -> float:
    concise = "Revenue rose 18% after checkout dropped from four steps to two."
    expansive = "We leverage innovative seamless solutions to transform a dynamic ecosystem with comprehensive strategic capabilities."
    selected = history if window is None else history[-window:]
    with TemporaryDirectory() as directory:
        engine = TasteEngine(Path(directory) / "taste.db")
        for preferred, rejected, source in selected:
            engine.observe_choice(preferred, rejected, context="status update", source=source)
        return engine.pairwise_probability(expansive, concise, context="status update")


def run_temporal_window_comparison(*, pre_updates: int = 128, post_updates: int = 8, window: int = 8) -> TemporalComparison:
    """Compare frozen accumulation with a bounded-history challenger under identical observations."""
    if pre_updates < 1 or post_updates < 1 or window < 1:
        raise ValueError("pre_updates, post_updates and window must be positive")

    concise = "Revenue rose 18% after checkout dropped from four steps to two."
    expansive = "We leverage innovative seamless solutions to transform a dynamic ecosystem with comprehensive strategic capabilities."
    history = [(concise, expansive, "synthetic_pre_drift") for _ in range(pre_updates)]
    accumulator: list[float] = []
    windowed: list[float] = []
    for _ in range(post_updates):
        history.append((expansive, concise, "synthetic_post_drift"))
        accumulator.append(_probability(history))
        windowed.append(_probability(history, window=window))

    stable = [(concise, expansive, "synthetic_stable") for _ in range(pre_updates + post_updates)]
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
    """Score bounded-history policies on a frozen matched synthetic matrix.

    Every policy sees identical pre/post observation budgets. Drift Brier is computed over the
    complete post-reversal trajectory, while stable Brier measures confidence loss on an equally
    long non-drifting stream. This function measures trade-offs only; it intentionally contains
    no promotion threshold and makes no real-user claim.
    """
    if not windows or not cases or any(w < 1 for w in windows):
        raise ValueError("windows and cases must be non-empty and positive")
    if len(set(windows)) != len(windows) or any(pre < 1 or post < 1 for pre, post in cases):
        raise ValueError("windows must be unique and all case budgets positive")

    scores: list[TemporalPolicyScore] = []
    for window in windows:
        drift_briers: list[float] = []
        stable_briers: list[float] = []
        for pre_updates, post_updates in cases:
            result = run_temporal_window_comparison(
                pre_updates=pre_updates, post_updates=post_updates, window=window
            )
            drift_briers.append(
                sum((1.0 - p) ** 2 for p in result.windowed_trajectory)
                / len(result.windowed_trajectory)
            )
            stable_briers.append((1.0 - result.stable_windowed) ** 2)
        scores.append(
            TemporalPolicyScore(
                window=window,
                cases=len(cases),
                mean_post_drift_brier=sum(drift_briers) / len(drift_briers),
                worst_post_drift_brier=max(drift_briers),
                mean_stable_brier=sum(stable_briers) / len(stable_briers),
                worst_stable_brier=max(stable_briers),
            )
        )
    return tuple(scores)

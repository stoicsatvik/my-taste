from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from .core.engine import TasteEngine


@dataclass(frozen=True)
class DriftResult:
    pre_drift_probability: float
    post_drift_probabilities: tuple[float, ...]
    recovery_updates: int | None
    final_probability: float


@dataclass(frozen=True)
class AsymmetricDriftCase:
    pre_updates: int
    post_updates: int
    result: DriftResult


def run_preference_drift_benchmark(*, pre_updates: int = 8, post_updates: int = 8) -> DriftResult:
    """Measure how quickly the current learner adapts after a preference reversal.

    This is a deterministic synthetic falsification surface, not a user-population claim.
    Recovery means the new preference becomes more likely than not under the same context.
    """
    if pre_updates < 1 or post_updates < 1:
        raise ValueError("pre_updates and post_updates must be positive")

    concise = "Revenue rose 18% after checkout dropped from four steps to two."
    expansive = "We leverage innovative seamless solutions to transform a dynamic ecosystem with comprehensive strategic capabilities."
    context = "status update"

    with TemporaryDirectory() as directory:
        engine = TasteEngine(Path(directory) / "taste.db")
        for _ in range(pre_updates):
            engine.observe_choice(concise, expansive, context=context, source="synthetic_pre_drift")

        pre = engine.pairwise_probability(concise, expansive, context=context)
        trajectory: list[float] = []
        recovery: int | None = None
        for update in range(1, post_updates + 1):
            engine.observe_choice(expansive, concise, context=context, source="synthetic_post_drift")
            probability = engine.pairwise_probability(expansive, concise, context=context)
            trajectory.append(probability)
            if recovery is None and probability > 0.5:
                recovery = update

        return DriftResult(
            pre_drift_probability=pre,
            post_drift_probabilities=tuple(trajectory),
            recovery_updates=recovery,
            final_probability=trajectory[-1],
        )


def run_asymmetric_drift_matrix(
    *,
    cases: tuple[tuple[int, int], ...] = ((8, 2), (32, 2), (128, 2), (128, 8)),
) -> tuple[AsymmetricDriftCase, ...]:
    """Falsify adaptation when stale history outweighs the reversal budget.

    Cases are intentionally asymmetric. This function freezes no promotion threshold and
    makes no claim about real-user drift; it exposes whether recovery depends on history size.
    """
    if not cases:
        raise ValueError("cases must not be empty")
    if len(set(cases)) != len(cases):
        raise ValueError("cases must be unique")
    results: list[AsymmetricDriftCase] = []
    for pre_updates, post_updates in cases:
        result = run_preference_drift_benchmark(pre_updates=pre_updates, post_updates=post_updates)
        results.append(AsymmetricDriftCase(pre_updates, post_updates, result))
    return tuple(results)

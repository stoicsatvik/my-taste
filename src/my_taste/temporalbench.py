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
    """Compare frozen accumulation with a bounded-history challenger under identical observations.

    The challenger is benchmark-only: it replays the latest ``window`` observations from
    provenance rather than changing production scoring. Stable retention is measured on an
    equally long non-drifting stream, so faster reversal cannot win by merely forgetting all
    signal. This synthetic comparison is a falsification surface, not a user-population claim.
    """
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
    # Retention is expressed as probability of the stable preferred direction.
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
